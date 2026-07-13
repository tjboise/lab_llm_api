#!/usr/bin/env python3
"""Interactive chat with the locally-hosted Qwen3-32B API."""

import os
import sys
from pathlib import Path

from openai import OpenAI

BASE_URL = "http://localhost:8000/v1"
MODEL = "qwen3-32b"


def load_api_key() -> str:
    env_path = Path(__file__).parent / ".env"
    for line in env_path.read_text().splitlines():
        if line.startswith("VLLM_API_KEY="):
            return line.split("=", 1)[1].strip()
    raise RuntimeError(f"VLLM_API_KEY not found in {env_path}")


def main() -> None:
    client = OpenAI(base_url=BASE_URL, api_key=load_api_key())
    messages = []

    print(f"Connected to {BASE_URL} (model={MODEL}). Type 'exit' to quit.\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if user_input.lower() in ("exit", "quit"):
            break
        if not user_input:
            continue

        messages.append({"role": "user", "content": user_input})

        stream = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            max_tokens=2048,
            stream=True,
        )

        print("Qwen: ", end="", flush=True)
        reply = ""
        for chunk in stream:
            delta = chunk.choices[0].delta
            token = getattr(delta, "content", None)
            if token:
                print(token, end="", flush=True)
                reply += token
        print("\n")

        messages.append({"role": "assistant", "content": reply})


if __name__ == "__main__":
    sys.exit(main())
