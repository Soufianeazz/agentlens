# llm-evaltrack

> Drop-in observability for LLM applications — automatic quality scoring, hallucination detection, and cost tracking.

## Why

Most LLM apps run blind. You don't know which prompts fail, which models waste money, or when quality drops. llm-evaltrack fixes that with **2 lines of code**.

## Quick Start

```bash
pip install llm-evaltrack
```

```python
import llm_observe

llm_observe.init(api_url="https://your-server.com/ingest")
llm_observe.patch_openai()    # auto-track all OpenAI calls
llm_observe.patch_anthropic() # auto-track all Anthropic calls
```

That's it. Your existing code is unchanged. Every API call is now automatically tracked.

## What You Get

**Dashboard** (self-hosted)
- Real-time quality trend charts
- Bad response categorization
- Root-cause analysis: which prompts fail most
- Cost vs. quality per model
- Regression alerts when quality drops

**Auto-tracked per call**

| Field | Source |
|---|---|
| Input / Output | Message content |
| Model | `response.model` |
| Tokens | `response.usage` |
| Cost (USD) | Calculated from token counts |
| Quality Score | Automatic evaluation (heuristics or LLM judge) |
| Hallucination flags | Automatic detection |

## Manual Tracking

```python
llm_observe.track_llm_call(
    input="What is the capital of France?",
    output="Paris.",
    prompt="You are a helpful assistant.",
    model="gpt-4o",
    metadata={"feature": "qa", "user_id": "u_123"},
)
```

## Self-Host the Dashboard

```bash
git clone https://github.com/Soufianeazz/llm-evaltrack
cd llm-evaltrack
pip install -r requirements.txt
uvicorn api.main:app --reload
```

Open `http://localhost:8000` — dashboard is live.

Optional: add an Anthropic API key to enable the LLM judge for higher-quality scoring:
```bash
export ANTHROPIC_API_KEY=sk-ant-...
```

## Stack

- Python 3.10+, FastAPI, SQLite
- Dashboard: HTML + Chart.js (no frontend build step)
- SDK: zero dependencies beyond `httpx`

## License

MIT
