"""
Stats-tracking reverse proxy in front of vLLM.

Sits on the public port (8000) and forwards everything to vLLM, which
listens only on an internal port (8080, not exposed publicly). Requests
are attributed to "chat" or "api" based on which API key was presented,
and further broken down by the caller-supplied OpenAI `user` field when
present. Cumulative token usage is persisted to disk so it survives both
vLLM restarts and redeploys of any client (e.g. the Streamlit app).
"""

import asyncio
import json
import os
from datetime import datetime, timezone
from pathlib import Path

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response, StreamingResponse

UPSTREAM = "http://localhost:8080"
STATS_FILE = Path(__file__).parent / "usage_stats.json"

VLLM_API_KEY = os.environ["VLLM_API_KEY"]  # used to authenticate to vLLM itself
CHAT_API_KEY = os.environ["VLLM_API_KEY_CHAT"]  # Streamlit app, tracked as "chat"
PUBLIC_API_KEY = os.environ["VLLM_API_KEY_PUBLIC"]  # README/external users, tracked as "api"

KEY_LABELS = {
    CHAT_API_KEY: "chat",
    PUBLIC_API_KEY: "api",
}

app = FastAPI()
_stats_lock = asyncio.Lock()


def _load_stats() -> dict:
    if STATS_FILE.exists():
        stats = json.loads(STATS_FILE.read_text())
    else:
        stats = {"chat": {"prompt_tokens": 0, "completion_tokens": 0},
                  "api": {"prompt_tokens": 0, "completion_tokens": 0}}
    stats.setdefault("by_user", {})
    return stats


async def _record_usage(label: str, prompt_tokens: int, completion_tokens: int, user: str | None):
    async with _stats_lock:
        stats = _load_stats()
        stats.setdefault(label, {"prompt_tokens": 0, "completion_tokens": 0})
        stats[label]["prompt_tokens"] += prompt_tokens
        stats[label]["completion_tokens"] += completion_tokens

        user_key = (user or "").strip() or "(unnamed)"
        by_user = stats["by_user"].setdefault(
            user_key, {"prompt_tokens": 0, "completion_tokens": 0, "source": label, "last_seen": None}
        )
        by_user["prompt_tokens"] += prompt_tokens
        by_user["completion_tokens"] += completion_tokens
        by_user["source"] = label
        by_user["last_seen"] = datetime.now(timezone.utc).isoformat()

        tmp = STATS_FILE.with_suffix(".tmp")
        tmp.write_text(json.dumps(stats))
        tmp.replace(STATS_FILE)


def _label_for_key(auth_header: str | None) -> str | None:
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    key = auth_header.removeprefix("Bearer ").strip()
    return KEY_LABELS.get(key)


@app.get("/usage")
async def usage():
    return JSONResponse(_load_stats())


@app.api_route("/{path:path}", methods=["GET", "POST"])
async def proxy(path: str, request: Request):
    auth_header = request.headers.get("authorization")
    is_tracked_endpoint = path in ("v1/chat/completions", "v1/completions")

    if is_tracked_endpoint:
        label = _label_for_key(auth_header)
        if label is None:
            return JSONResponse({"error": "Invalid API key"}, status_code=401)

    body = await request.body()

    caller_name = None
    if is_tracked_endpoint:
        try:
            caller_name = json.loads(body).get("user")
        except json.JSONDecodeError:
            pass

    upstream_headers = dict(request.headers)
    upstream_headers["authorization"] = f"Bearer {VLLM_API_KEY}"
    upstream_headers.pop("host", None)
    upstream_headers.pop("content-length", None)
    upstream_headers["accept-encoding"] = "identity"  # keep responses uncompressed for parsing

    client = httpx.AsyncClient(timeout=300.0)
    req = client.build_request(
        request.method, f"{UPSTREAM}/{path}",
        params=request.query_params, headers=upstream_headers, content=body,
    )
    upstream_resp = await client.send(req, stream=True)

    if not is_tracked_endpoint:
        content = await upstream_resp.aread()
        await upstream_resp.aclose()
        await client.aclose()
        return Response(
            content=content, status_code=upstream_resp.status_code,
            headers={k: v for k, v in upstream_resp.headers.items()
                     if k.lower() not in ("content-length", "content-encoding", "transfer-encoding")},
        )

    async def relay():
        usage_obj = None
        text_buffer = ""
        try:
            async for chunk in upstream_resp.aiter_bytes():
                yield chunk  # pass through byte-exact, unmodified
                text_buffer += chunk.decode("utf-8", errors="ignore")
                while "\n" in text_buffer:
                    line, text_buffer = text_buffer.split("\n", 1)
                    line = line.strip()
                    if line.startswith("data: ") and line != "data: [DONE]":
                        try:
                            payload = json.loads(line[len("data: "):])
                            if payload.get("usage"):
                                usage_obj = payload["usage"]
                        except json.JSONDecodeError:
                            pass
            if usage_obj is None and text_buffer.strip():
                try:
                    usage_obj = json.loads(text_buffer).get("usage")
                except json.JSONDecodeError:
                    pass
        finally:
            await upstream_resp.aclose()
            await client.aclose()
            if usage_obj:
                await _record_usage(label, usage_obj.get("prompt_tokens", 0),
                                     usage_obj.get("completion_tokens", 0), caller_name)

    media_type = upstream_resp.headers.get("content-type", "application/json")
    return StreamingResponse(relay(), status_code=upstream_resp.status_code, media_type=media_type)
