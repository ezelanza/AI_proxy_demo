# AI Proxy Features (NJS)

The NGINX AI Proxy includes advanced validation, monitoring, control features, and **smart model routing** implemented in NGINX JavaScript (NJS).

## Smart Model Routing

**Key Feature**: Agents request `LLM_model` and NGINX automatically selects the optimal GPT model based on request characteristics.

### How It Works

1. **Agent requests**: `"model": "LLM_model"`
2. **NGINX analyzes**:
   - Token count (estimated)
   - Message count
   - System messages (complexity indicator)
   - Max tokens requested
3. **NGINX routes to**:
   - **gpt-4o-mini** (cheap, fast) for simple requests
   - **gpt-4o** (powerful, expensive) for complex requests

### Routing Logic

- **Cheap** (< 1000 tokens, < 5 messages, no system) → `gpt-4o-mini`
- **Medium** (1000-5000 tokens OR 5-10 messages) → `gpt-4o-mini`
- **Expensive** (> 5000 tokens OR > 10 messages OR system message OR > 2000 max_tokens) → `gpt-4o`

### Benefits

- **Cost optimization**: Simple requests use cheaper models
- **Performance**: Complex requests get powerful models
- **Transparent**: Agents don't need to know which model to use
- **Automatic**: No code changes needed in agents

## Other Features

### 1. **Request Validation**
- Validates message structure (must be array with role/content)
- Validates message roles (system/user/assistant only)
- Validates `max_tokens` (must be positive number)
- Validates `temperature` (must be 0-2)
- Returns detailed error messages for invalid requests

### 2. **Token Counting & Estimation**
- Estimates tokens before sending request (1 token ≈ 4 characters)
- Extracts actual token usage from responses
- Tracks prompt tokens, completion tokens, and total tokens
- Logs token counts for monitoring

### 3. **Rate Limiting**
- Per-user rate limiting (default: 60 requests/minute)
- Configurable per user in `rbac.json`
- Returns HTTP 429 when limit exceeded
- In-memory rate limit store (resets every minute)

### 4. **Request Size Limits**
- Maximum request size: 1MB
- Prevents oversized requests from consuming resources
- Returns HTTP 413 for oversized requests

### 5. **Cost Estimation**
- Calculates estimated cost per request
- Supports multiple OpenAI models (gpt-4o, gpt-4o-mini, gpt-4, gpt-3.5-turbo)
- Logs cost estimates for monitoring
- Uses current OpenAI pricing (as of 2024)

### 6. **Enhanced Logging**
- Logs user, model, token counts, and cost for each request
- Logs routing decisions (which model was selected)
- Logs failed requests with status codes
- Format: `[AI Proxy] User: X | Model: Y | Routing: LLM_model->gpt-4o-mini | Tokens: Z | Cost: $X.XXXXXX`

### 7. **Per-User Token Limits**
- Configurable `max_tokens_per_request` per user
- Warns when limit exceeded (can be configured to reject)
- Set in `rbac.json` under user config

## Configuration

Edit `docker/nginx/config/rbac.json` to configure routing and limits:

```json
{
  "users": {
    "agent-user": {
      "models": [{"name": "LLM_model"}],
      "max_tokens_per_request": 50000,
      "rate_limit_per_minute": 60
    }
  },
  "models": {
    "LLM_model": {
      "provider": "openai",
      "location": "/openai",
      "routing": {
        "strategy": "smart",
        "options": {
          "cheap": "gpt-4o-mini",
          "medium": "gpt-4o-mini",
          "expensive": "gpt-4o"
        }
      }
    }
  }
}
```

## Testing

Test smart routing:
```bash
./test_smart_routing.sh
```

Test all features:
```bash
./test_ai_proxy_features.sh
```

## Monitoring

View routing decisions and costs:
```bash
docker logs pocket_printer-nginx-1 | grep "AI Proxy"
```

Example output:
```
[AI Proxy] Smart routing: LLM_model -> gpt-4o-mini (tokens: 25)
[AI Proxy] User: agent-user | Model: gpt-4o-mini | Routing: LLM_model->gpt-4o-mini | Tokens: 30 (10+20) | Cost: $0.000018
```
