🌐 **Language**: [English](README.md) | 中文

# Llama 4 Scout API

自托管的 Llama 4 Scout（4-bit 量化版）多模态模型，通过 vLLM 部署，经由 ngrok 隧道（固定域名）对外提供
服务。该 API 与 OpenAI 接口兼容，任何 OpenAI SDK/客户端只需修改 `base_url` 和
`api_key` 即可直接使用。

| 模型 | `model` 字段 | 用途 |
|---|---|---|
| Llama 4 Scout | `llama-4-scout` | 文字对话 + 图片理解（视觉） |

## 连接信息

```
Base URL:  https://improper-faceless-savanna.ngrok-free.dev/v1
API Key:   <请向管理员索取——出于安全考虑没有写在这里>
Model:     llama-4-scout
```

> **注意：** 这个 Base URL 是固定的 ngrok 域名——重启或重连都不会变。如果请求
> 还是失败，可能是模型服务本身挂了，请找管理员看一下。
>
> API Key 故意**没有**写在这个文件里。请把它当密码一样对待——任何拿到它的人
> 都能调用这个模型。Key 会通过其他渠道单独发给你（找给你这份 README 的人要）。
> 不要把它粘贴到这个文件里、提交到仓库，或者分享给不该有权限的人。

## Python（OpenAI SDK）

```bash
pip install openai
```

```python
from openai import OpenAI

client = OpenAI(
    base_url="https://improper-faceless-savanna.ngrok-free.dev/v1",
    api_key="<你的 API Key>",
)

response = client.chat.completions.create(
    model="llama-4-scout",
    messages=[{"role": "user", "content": "你好！"}],
    max_tokens=1024,
)

print(response.choices[0].message.content)
```

## JavaScript / TypeScript（OpenAI SDK）

```bash
npm install openai
```

```javascript
import OpenAI from "openai";

const client = new OpenAI({
  baseURL: "https://improper-faceless-savanna.ngrok-free.dev/v1",
  apiKey: "<你的 API Key>",
});

const response = await client.chat.completions.create({
  model: "llama-4-scout",
  messages: [{ role: "user", content: "你好！" }],
  max_tokens: 1024,
});

console.log(response.choices[0].message.content);
```

## curl

```bash
curl https://improper-faceless-savanna.ngrok-free.dev/v1/chat/completions \
  -H "Authorization: Bearer <你的 API Key>" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama-4-scout",
    "messages": [{"role": "user", "content": "你好！"}],
    "max_tokens": 1024
  }'
```

## 流式输出（Streaming）

用法和 OpenAI API 完全一样——curl 传 `"stream": true`，Python SDK 传
`stream=True`，JS SDK 传 `stream: true`。

## 视觉能力（图片输入）

图片传入方式和 OpenAI 视觉 API 一样——在 content 里加一个 `image_url` 部分
（base64 data URI 或公网可访问的图片链接）。每个请求最多 4 张图片：

```python
import base64

with open("photo.jpg", "rb") as f:
    b64_image = base64.b64encode(f.read()).decode()

response = client.chat.completions.create(
    model="llama-4-scout",
    messages=[{
        "role": "user",
        "content": [
            {"type": "text", "text": "这张图片里有什么？"},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64_image}"}},
        ],
    }],
    max_tokens=1024,
)

print(response.choices[0].message.content)
```

## 其他接口

标准的 vLLM OpenAI 兼容路由都可以用，例如：
- `GET /v1/models` — 列出可用模型
- `POST /v1/completions` — 传统 completions 接口
- `GET /health` — 健康检查（不需要鉴权）

## 限制

- 上下文窗口：16,384 tokens（prompt + completion 总和）
