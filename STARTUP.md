# DEREK-AI — Project Startup Guide

All commands are run from the project root: `Capstone_Project/`

---

## Prerequisites

| Tool | Version | Install |
|---|---|---|
| Python | 3.11+ | https://python.org |
| Docker Desktop | latest | https://docker.com |
| Node.js | 18+ | https://nodejs.org |
| Ollama | latest | https://ollama.com |

Verify with:
```powershell
python --version
docker --version
node --version
ollama --version
```

---

## Step 1 — Configure environment

```powershell
cd C:\Users\anet.tatygulov\Desktop\EPAM_Course\Capstone_Project
Copy-Item .env.example .env
```

Open `.env` and set at minimum:
- `TAVILY_API_KEY` — free at https://tavily.com (1 000 searches/month)
- `LANGFUSE_PUBLIC_KEY` / `LANGFUSE_SECRET_KEY` — free at https://cloud.langfuse.com  
  (leave as placeholders if you don't want observability — the app still runs)

Everything else works with defaults (`LLM_PROVIDER=ollama`).

---

## Step 2 — Start Qdrant (vector database)

```powershell
docker compose up -d
```

Verify it's healthy:
```powershell
docker compose ps
# qdrant should show "healthy"
```

Web UI available at: http://localhost:6333/dashboard

---

## Step 3 — Pull the LLM (Ollama)

```powershell
ollama pull mistral:7b-instruct
```

This downloads ~4 GB once. To confirm:
```powershell
ollama list
```

---

## Step 4 — Install Python dependencies

```powershell
pip install -r requirements.txt
```

> First run downloads the `BAAI/bge-m3` embedding model (~1 GB). Subsequent starts use the disk cache.

---

## Step 5 — Ingest regulatory documents  *(skip if no PDFs yet)*

Place PDF files (СНиП / СП / ҚНжЕ / СТ РК) in `data/regulations/`:

```powershell
python scripts/ingest.py --dir data/regulations
```

Check index status:
```powershell
python scripts/check_index.py
```

---

## Step 6 — Start the backend (FastAPI)

```powershell
# From project root, with PYTHONPATH set
$env:PYTHONPATH = "."
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
```

API will be live at:
- http://localhost:8000/health
- http://localhost:8000/docs  ← Swagger UI

---

## Step 7 — Start the frontend (React)

Open a **second terminal**:

```powershell
cd C:\Users\anet.tatygulov\Desktop\EPAM_Course\Capstone_Project\frontend
npm install        # first time only
npm run dev
```

App is available at: **http://localhost:5173**

---

## All services at a glance

| Service | URL | Command |
|---|---|---|
| Qdrant (vector DB) | http://localhost:6333/dashboard | `docker compose up -d` |
| Backend (FastAPI) | http://localhost:8000/docs | `uvicorn src.api.main:app --reload` |
| Frontend (React) | http://localhost:5173 | `npm run dev` (in `frontend/`) |
| Ollama (LLM) | http://localhost:11434 | starts automatically with `ollama serve` |

---

## Stopping the project

```powershell
# Stop frontend — Ctrl+C in its terminal

# Stop backend — Ctrl+C in its terminal

# Stop Qdrant
docker compose down
```

---

## Quick health check

```powershell
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "ok",
  "qdrant": "ok",
  "llm": "ok",
  "mcp": "ok"
}
```

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `ModuleNotFoundError: src` | Set `$env:PYTHONPATH = "."` before uvicorn |
| Qdrant unhealthy | `docker compose logs qdrant` — check port 6333 is free |
| Ollama not responding | Run `ollama serve` in a separate terminal |
| bge-m3 download hangs | Check internet connection; model is ~1 GB |
| Frontend can't reach API | Confirm backend is on port 8000; Vite proxy is pre-configured |
| `TAVILY_API_KEY` missing | App still works — norm freshness shows `UNVERIFIED` |

---

## Run tests

```powershell
# From project root
$env:PYTHONPATH = "."
pytest tests/ -v                        # unit tests (fast)
pytest tests/ -v -m slow               # includes RAGAS eval (slow, needs Qdrant)
```
