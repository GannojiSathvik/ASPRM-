# ASPM Backend (FastAPI + Neo4j)
## Case Study Title

AI-Powered Application Security Posture Management (ASPM) Using Risk Graphs and Large Language Models

This backend supports a demo where multiple security tool alerts (SAST/DAST/secrets) are unified into a risk graph and explained in developer-friendly language using an LLM. The goal is fewer unactioned alerts and faster remediation.

A minimal backend for an AI-powered ASPM demo. It ingests scanner findings (Semgrep-like),
stores them in Neo4j, lists/updates risks, and can return an AI-style explanation (stubbed by default).

## Endpoints

- `POST /webhook/semgrep` — ingest findings
- `GET /risks` — list risks
- `POST /risks/{fp}/status` — update a finding's status (`open|triaged|ignored|fixed`)
- `POST /risks/{fp}/explain` — return an explanation for a finding (stub or via LLM)
- `GET /` and `GET /healthz` — simple health checks

## Quick start

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

export NEO4J_URI=bolt://localhost:7687
export NEO4J_USER=neo4j
export NEO4J_PASS=<your-password>
# Optional if your DB is named differently (Neo4j 5+ default is 'neo4j'):
export NEO4J_DB=neo4j

# LLM provider options
# For OpenAI:
#   export LLM_PROVIDER=openai
#   export OPENAI_API_KEY=sk-...
# For Ollama (local):
#   export LLM_PROVIDER=ollama
#   export OLLAMA_MODEL=llama3-aspm

uvicorn app.main:api --reload --port 8040 --log-level debug
```

Open docs: http://127.0.0.1:8040/docs

### Sample ingest

```bash
curl -X POST http://127.0.0.1:8040/webhook/semgrep   -H "Content-Type: application/json"   -d '{
    "repo": "web-portal",
    "repo_url": "https://github.com/acme/web-portal",
    "commit": "abc123",
    "findings": [{
      "check_id": "javascript.lang.security.audit.eval",
      "path": "src/auth/login.js",
      "start": 42,
      "end": 42,
      "severity": "HIGH",
      "message": "Use of eval() may lead to RCE",
      "fingerprint": "web-portal:src/auth/login.js:eval:42",
      "cwe": "CWE-95"
    }]
  }'
```

List risks:
```bash
curl http://127.0.0.1:8040/risks
```

Update status:
```bash
curl -X POST http://127.0.0.1:8040/risks/web-portal:src/auth/login.js:eval:42/status   -H "Content-Type: application/json"   -d '{"status":"triaged"}'
```

Explain finding (stub or Ollama/OpenAI):
```bash
curl -X POST http://127.0.0.1:8040/risks/web-portal:src/auth/login.js:eval:42/explain
```

## Notes

- By default, `/risks/{fp}/explain` uses a **deterministic template** for predictable demos.
- To enable **OpenAI** explanations, set `LLM_PROVIDER=openai` and `OPENAI_API_KEY`,
  and install `openai` python package (uncomment in `requirements.txt` if you want it).

## Ollama Finetune (Llama 3)

You can fine-tune a local Llama-3 model using Ollama for security alert explanations.

### 1) Prepare dataset (JSONL)

Each line is a chat-style record used for SFT:

```json
{"messages": [
  {"role": "system", "content": "You are an AppSec assistant that writes concise, actionable explanations for developers."},
  {"role": "user", "content": "Fingerprint: web-portal:src/auth/login.js:eval:42\nSeverity: HIGH\nPath: src/auth/login.js\nRule: javascript.lang.security.audit.eval\nMessage: Use of eval() may lead to RCE\nCWE: CWE-95\nInclude: what it means, why it matters, and the exact fix to apply."},
  {"role": "assistant", "content": "The code invokes eval() on user-controlled input, enabling arbitrary code execution... [concise, actionable fix here]."}
]}
```

See `data/aspm_security_explanations.jsonl` for a small seed.

### 2) Start Ollama and pull base model

```bash
brew install ollama # macOS
ollama serve &
ollama pull llama3
```

### 3) Train via API

```bash
export LLM_PROVIDER=ollama
export




 OLLAMA_MODEL=llama3-aspm

curl -X POST http://127.0.0.1:8040/train/ollama \
  -H "Content-Type: application/json" \
  -d '{
    "dataset_path": "/absolute/path/to/data/aspm_security_explanations.jsonl",
    "base_model": "llama3",
    "finetune_name": "llama3-aspm",
    "epochs": 1,
    "batch_size": 2,
    "learning_rate": 0.00002,
    "quantize": "q4_K_M"
  }'
```

### 4) Use in inference

Ensure envs:

```bash
export LLM_PROVIDER=ollama
export OLLAMA_MODEL=llama3-aspm
```

Then call explanation endpoint as usual:

```bash
curl -X POST http://127.0.0.1:8040/risks/web-portal:src/auth/login.js:eval:42/explain
```

### 5) Model info

```bash
curl http://127.0.0.1:8040/
model/info
```
