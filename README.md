🌐 **Language**: English | [中文](README.zh-CN.md)

# Llama 4 Scout API

A self-hosted Llama 4 Scout (4-bit quantized) multimodal model, served via vLLM, exposed through an ngrok
tunnel on a fixed domain. The API is OpenAI-compatible, so any OpenAI
SDK/client works by just changing the `base_url` and `api_key`.

| Model | `model` id | Use for |
|---|---|---|
| Llama 4 Scout | `llama-4-scout` | Text chat + image understanding (vision) |

## Connection info

```
Base URL:  https://improper-faceless-savanna.ngrok-free.dev/v1
API Key:   <ask the admin for this — not written here on purpose>
Model:     llama-4-scout
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
    model="llama-4-scout",
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
  model: "llama-4-scout",
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
    "model": "llama-4-scout",
    "messages": [{"role": "user", "content": "Hello!"}],
    "max_tokens": 1024
  }'
```

## Streaming

Works exactly like the OpenAI API — pass `"stream": true` (curl) or
`stream=True` (Python SDK) / `stream: true` (JS SDK).

## Vision (image input)

Pass images the same way as the OpenAI vision API — as a content list with
`image_url` parts (base64 data URI or a public URL). Up to 4 images per request:

```python
import base64

with open("photo.jpg", "rb") as f:
    b64_image = base64.b64encode(f.read()).decode()

response = client.chat.completions.create(
    model="llama-4-scout",
    messages=[{
        "role": "user",
        "content": [
            {"type": "text", "text": "What's in this image?"},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64_image}"}},
        ],
    }],
    max_tokens=1024,
)

print(response.choices[0].message.content)
```

## Other endpoints

Standard vLLM OpenAI-compatible routes are all available, e.g.:
- `GET /v1/models` — list models
- `POST /v1/completions` — legacy completions
- `GET /health` — health check (no auth required)

## Limits

- Context window: 16,384 tokens (prompt + completion combined)
