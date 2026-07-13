🌐 **Language**: [English](README.md) | 中文

# Qwen3-32B API

一个自托管的 Qwen3-32B 模型，通过 vLLM 部署，经由 Cloudflare Tunnel 对外提供服务。
该 API 与 OpenAI 接口兼容，任何 OpenAI SDK/客户端只需修改 `base_url` 和 `api_key`
即可直接使用。

## 连接信息

```
Base URL:  https://earned-fully-interactive-acids.trycloudflare.com/v1
API Key:   <请向管理员索取——出于安全考虑没有写在这里>
Model:     qwen3-32b
```

> **注意：** 这个 Base URL 是临时的 Cloudflare quick tunnel 地址。如果隧道服务
> 重启（比如主机重启），地址会发生变化。如果请求失败，请找管理员要最新地址。
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
    base_url="https://earned-fully-interactive-acids.trycloudflare.com/v1",
    api_key="<你的 API Key>",
)

response = client.chat.completions.create(
    model="qwen3-32b",
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
  baseURL: "https://earned-fully-interactive-acids.trycloudflare.com/v1",
  apiKey: "<你的 API Key>",
});

const response = await client.chat.completions.create({
  model: "qwen3-32b",
  messages: [{ role: "user", content: "你好！" }],
  max_tokens: 1024,
});

console.log(response.choices[0].message.content);
```

## curl

```bash
curl https://earned-fully-interactive-acids.trycloudflare.com/v1/chat/completions \
  -H "Authorization: Bearer <你的 API Key>" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen3-32b",
    "messages": [{"role": "user", "content": "你好！"}],
    "max_tokens": 1024
  }'
```

## 流式输出（Streaming）

用法和 OpenAI API 完全一样——curl 传 `"stream": true`，Python SDK 传
`stream=True`，JS SDK 传 `stream: true`。

## Qwen3 的"思考"模式

Qwen3 默认会先输出一段推理过程（放在单独的 `reasoning` 字段里），再给出最终答案。
这意味着：

- **`max_tokens` 要给得宽裕一些**（建议 1000 以上）。如果 `max_tokens` 太小，
  预算可能全部被推理过程占满，导致看不到最终答案（`content` 会是 `null`，
  `finish_reason` 是 `"length"`）。
- 如果想关闭思考模式、直接拿到答案，请求里加上：
  ```json
  "chat_template_kwargs": {"enable_thinking": false}
  ```

## 其他接口

标准的 vLLM OpenAI 兼容路由都可以用，例如：
- `GET /v1/models` — 列出可用模型
- `POST /v1/completions` — 传统 completions 接口
- `POST /v1/embeddings` — 不支持（这不是一个 embedding 模型）
- `GET /health` — 健康检查（不需要鉴权）

## 限制

- 上下文窗口：32,768 tokens（prompt + completion 总和）
- 并发数：约 4-5 个并发请求（受限于 KV cache 大小）
