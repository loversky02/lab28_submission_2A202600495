# FPT Cloud AI — GPU & Inference Setup

Lab 28 uses **FPT Cloud AI Factory** instead of Kaggle GPU for Layer 1 (Compute).

## Credentials

- **Platform URL:** https://ai.fptcloud.com/AI-C6RXC2E4P
- **Region:** Hanoi 2 (Vietnam)
- **Plan:** Starter Plan ($100 free credits)
- **API Key:** Stored in `.env` as `FPT_API_KEY`

## Available Models (24+ models)

### LLM (Chat Completions)
- **Qwen2.5-7B-Instruct** (recommended for lab — fast, free tier friendly)
- Qwen3.6-27B, Qwen3-32B
- Llama-3.3-70B-Instruct
- DeepSeek-R1 (reasoning)
- Gemma-4-31B-it, Gemma-3-27b-it
- Nemotron-3-Super-120B
- GLM-4.7, GLM-5.1
- SaoLa4-small, SaoLa4-medium (Vietnamese-optimized)
- GPT-OSS-20B, GPT-OSS-120B

### Embeddings
- **Vietnamese_Embedding** (recommended for Vietnamese text)
- multilingual-e5-large
- FPT.AI-e5-large, FPT.AI-gte-base

### Reranking
- bge-reranker-v2-m3

### Speech
- FPT.AI-whisper-medium, whisper-large-v3-turbo

## API Endpoints

| Service | Endpoint |
|---------|----------|
| Chat Completions | `POST https://mkp-api.fptcloud.com/chat/completions` |
| Embeddings | `POST https://mkp-api.fptcloud.com/embeddings` |

## Authentication

All requests require HTTP header:
```
Authorization: Bearer <your-api-key>
```

## Example: Chat Completion

```bash
curl -X POST "https://mkp-api.fptcloud.com/chat/completions" \
  -H "Authorization: Bearer $FPT_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Qwen2.5-7B-Instruct",
    "messages": [{"role": "user", "content": "Explain AI platform engineering"}],
    "stream": false
  }'
```

## Example: Embedding

```bash
curl -X POST "https://mkp-api.fptcloud.com/embeddings" \
  -H "Authorization: Bearer $FPT_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "input": ["Trí tuệ nhân tạo đang phát triển mạnh mẽ tại Việt Nam"],
    "model": "Vietnamese_Embedding"
  }'
```

## API Reference

- GitHub: https://github.com/fpt-corp/ai-marketplace/
- User Guide: https://ai-docs.fptcloud.com/fpt-ai-marketplace/fpt-ai-inference
- API Keys: https://marketplace.fptcloud.com/en/my-account?tab=my-api-key
