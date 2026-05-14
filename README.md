# DEREK-AI — AI-Powered Regulatory Intelligence System

> Capstone Project · EPAM AI/ML Course 2026  
> Kazakhstan Construction Norm Compliance Assistant

## Overview

DEREK-AI modernises the legacy [derek-info.kz](https://derek-info.kz) platform from keyword search over 27 000 documents into an AI-first compliance assistant. Given a building description it runs a multi-agent LangGraph pipeline that:

1. **Searches** ~450 000 vector chunks (bge-m3 embeddings, Qdrant)  
2. **Analyses** compliance against СНиП / СП / ҚНжЕ / СТ РК norms  
3. **Verifies** norm freshness via Tavily MCP tool  
4. **Explains** findings in plain professional Russian/English  

---

## Quick Start

### Prerequisites
- Python 3.11+
- Docker + Docker Compose
- Node.js 18+ (for frontend)
- Ollama installed locally (`ollama pull mistral:7b-instruct`)

### 1. Clone & configure

```bash
git clone <repo>
cd Capstone_Project
cp .env.example .env
# Edit .env — set LANGFUSE keys if desired, TAVILY_API_KEY if available
```

### 2. Start Qdrant

```bash
docker compose up -d
```

### 3. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 4. Ingest regulatory documents

```bash
# Place PDFs in data/regulations/
python scripts/ingest.py --dir data/regulations

# Check index status
python scripts/check_index.py
```

### 5. Start the backend

```bash
uvicorn src.api.main:app --reload --port 8000
```

API docs: http://localhost:8000/docs

### 6. Start the frontend

```bash
cd frontend
npm install
npm run dev
```

UI: http://localhost:5173

---

## Architecture

```
User Query
    │
    ▼
FastAPI (port 8000)
    │  Guardrail: input_filter.py
    │
    ▼
LangGraph StateGraph
    ├─ SearchAgent      → Qdrant (bge-m3 embeddings)
    ├─ ComplianceAgent  → Ollama / OpenAI (JSON report)
    ├─ UpdateAgent      → Tavily MCP (norm freshness)
    └─ ExplanationAgent → Ollama / OpenAI (plain language)
    │
    ▼
FastAPI SSE response → React frontend
```

---

## Project Structure

```
Capstone_Project/
├── src/
│   ├── config.py              # Settings via pydantic-settings
│   ├── ingestion/             # PDF parser, chunker, embedder, indexer
│   ├── rag/                   # Retriever, quality scoring
│   ├── agents/                # LangGraph nodes + orchestrator
│   ├── mcp/                   # Tavily MCP client
│   ├── guardrails/            # Input validation + injection detection
│   ├── api/                   # FastAPI app, models, routers
│   └── monitoring/            # Langfuse tracer
├── frontend/                  # React 18 + Vite + TailwindCSS
├── scripts/                   # ingest.py, check_index.py
├── tests/                     # pytest test suite
├── data/regulations/          # Place PDF documents here
├── docker-compose.yml         # Qdrant service
├── requirements.txt
└── .env.example
```

---

## Configuration

Key `.env` variables:

| Variable | Default | Description |
|---|---|---|
| `LLM_PROVIDER` | `ollama` | `ollama` or `openai` |
| `OLLAMA_MODEL` | `mistral:7b-instruct` | Ollama model name |
| `OPENAI_API_KEY` | — | Required if `LLM_PROVIDER=openai` |
| `EMBEDDING_MODEL` | `BAAI/bge-m3` | Must be multilingual for Cyrillic |
| `QDRANT_HOST` | `localhost` | Qdrant vector DB host |
| `TAVILY_API_KEY` | — | Optional — enables MCP freshness check |
| `LANGFUSE_PUBLIC_KEY` | — | Optional — LLM observability |

---

## Running Tests

```bash
# Fast tests (no Qdrant required)
pytest tests/ -v -k "not slow"

# All tests including RAGAS evaluation
pytest tests/ -v --timeout=120
```

---

## Evaluation Metrics

| Metric | Target | Measurement |
|---|---|---|
| Context Precision | ≥ 0.60 | RAGAS |
| Answer Faithfulness | ≥ 0.70 | RAGAS |
| Injection Detection | 100% | Adversarial tests |
| API Response Time | < 30s | Timing logs |
| Guardrail Accuracy | 100% | Unit tests |
