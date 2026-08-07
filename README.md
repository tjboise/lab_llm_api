🌐 **Language**: English | [中文](README.zh-CN.md)

# Qwen3-32B API

A self-hosted Qwen3-32B model, served via vLLM, exposed through an ngrok
tunnel on a fixed domain. The API is OpenAI-compatible, so any OpenAI
SDK/client works by just changing the `base_url` and `api_key`.

## Connection info

```
Base URL:  https://improper-faceless-savanna.ngrok-free.dev/v1
API Key:   <ask the admin for this — not written here on purpose>
Model:     qwen3-32b
```

> **Note:** The base URL is a fixed ngrok domain — it will stay the same
> across restarts and reboots. If requests still fail, the model server
> itself may be down; ask the admin to check.
>
> The API key is deliberately **not** included in this file. Treat it like
> a password — anyone with it can use the model. It's shared out-of-band
> (ask whoever gave you this README). Don't paste it into this file,
> commit it to a repo, or share it further than intended.

## Python (OpenAI SDK)

```bash
pip install openai
```

```python
from openai import OpenAI

client = OpenAI(
    base_url="https://improper-faceless-savanna.ngrok-free.dev/v1",
    api_key="<your API key>",
)

response = client.chat.completions.create(
    model="qwen3-32b",
    messages=[{"role": "user", "content": "Hello!"}],
    max_tokens=1024,
)

print(response.choices[0].message.content)
```

## JavaScript / TypeScript (OpenAI SDK)

```bash
npm install openai
```

```javascript
import OpenAI from "openai";

const client = new OpenAI({
  baseURL: "https://improper-faceless-savanna.ngrok-free.dev/v1",
  apiKey: "<your API key>",
});

const response = await client.chat.completions.create({
  model: "qwen3-32b",
  messages: [{ role: "user", content: "Hello!" }],
  max_tokens: 1024,
});

console.log(response.choices[0].message.content);
```

## curl

```bash
curl https://improper-faceless-savanna.ngrok-free.dev/v1/chat/completions \
  -H "Authorization: Bearer <your API key>" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen3-32b",
    "messages": [{"role": "user", "content": "Hello!"}],
    "max_tokens": 1024
  }'
```

## Please identify yourself

Pass the standard OpenAI `user` field with your name (or team/project name)
so usage can be attributed to you on the admin's usage dashboard:

```python
response = client.chat.completions.create(
    model="qwen3-32b",
    messages=[{"role": "user", "content": "Hello!"}],
    max_tokens=1024,
    user="your-name-or-project",
)
```

Requests without a `user` field still work, but show up as `(unnamed)`.

## Streaming

Works exactly like the OpenAI API — pass `"stream": true` (curl) or
`stream=True` (Python SDK) / `stream: true` (JS SDK).

## Qwen3 "thinking" mode

Qwen3 emits its reasoning as a separate `reasoning` field before the final
answer, and by default "thinking" is turned on. This means:

- **Set `max_tokens` generously** (1000+). With a small `max_tokens`, the
  budget can be consumed entirely by the reasoning trace, leaving no room
  for the actual answer (`content` will be `null`, `finish_reason: "length"`).
- To disable thinking and get a direct answer, add to your request:
  ```json
  "chat_template_kwargs": {"enable_thinking": false}
  ```

## Other endpoints

Standard vLLM OpenAI-compatible routes are all available, e.g.:
- `GET /v1/models` — list models
- `POST /v1/completions` — legacy completions
- `POST /v1/embeddings` — n/a (not an embedding model)
- `GET /health` — health check (no auth required)

## Limits

- Context window: 32,768 tokens (prompt + completion combined)
- Concurrency: ~4-5 simultaneous requests before KV cache is exhausted
