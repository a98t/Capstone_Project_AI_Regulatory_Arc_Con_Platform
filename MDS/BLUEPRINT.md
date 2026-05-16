# Architecture Blueprint — DEREK-AI
## AI-Powered Regulatory Intelligence System for Kazakhstan's Construction Industry

**Student:** Anet Tatygulov  
**Version:** 2.0 — May 2026  
**Status:** Production  

---

## 1. System Overview

DEREK-AI transforms a natural-language building description into a structured compliance report in under 30 seconds. A user enters parameters (building type, number of floors, city, structural material, purpose) and the system automatically retrieves, cross-references, and explains all applicable Kazakhstan construction norms.

**Before DEREK-AI:** A compliance check for a 9-floor residential building required an engineer to open 5–15 regulatory documents and manually cross-reference applicable articles — 2–6 hours per project.

**After DEREK-AI:** Same query takes 15–30 seconds. Every finding is cited to an exact article and document. The system flags norms that may have been amended since publication.

---

## 2. High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USER (Browser)                              │
│              React 18 + Vite + TailwindCSS (port 5173)             │
│    BuildingForm → AgentStatusPanel → ComplianceReport              │
└──────────────────────────────┬──────────────────────────────────────┘
                               │ HTTP / SSE (EventSource)
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     FastAPI Backend  (port 8001)                    │
│   /api/analyze  /api/search  /api/feedback  /api/prompt  /health   │
│   Rate limiting: slowapi (20 req/min)                               │
│   CORS: localhost:5173, localhost:3000                              │
│   Guardrails: regex injection filter → validated before LLM call   │
└──────────┬────────────────────────────────────────┬────────────────┘
           │                                        │
           ▼                                        ▼
┌──────────────────────┐              ┌─────────────────────────┐
│  LangGraph Pipeline  │              │  Qdrant Vector DB        │
│  (orchestrator.py)   │◄────────────►│  Docker · port 6333      │
│                      │  RAG search  │  Collection: regulations  │
│  START               │              │  1,004 vectors, 1024-dim  │
│    ↓                 │              │  BAAI/bge-m3 embeddings   │
│  SearchAgent         │              │  13 real Kazakhstan PDFs  │
│    ↓                 │              └─────────────────────────┘
│  ComplianceAgent     │
│    ↓                 │              ┌─────────────────────────┐
│  UpdateAgent         │◄────────────►│  Tavily MCP Tool Server  │
│    ↓                 │  freshness   │  Live web search         │
│  ExplanationAgent    │              │  adilet.zan.kz           │
│    ↓                 │              │  online.zakon.kz         │
│  END                 │              └─────────────────────────┘
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│  OpenAI gpt-4o-mini  │
│  temperature=0.0     │
│  max_tokens=1500     │
│  (via LangChain)     │
└──────────────────────┘
```

---

## 3. Component Breakdown

### 3.1 Frontend — `frontend/`

| Technology | Version | Role |
|---|---|---|
| React | 18 | UI framework |
| Vite | 5 | Build tool / dev server |
| TailwindCSS | 3 | Utility-first styling |
| Zustand | 4 | Global state management |
| TanStack Query | 5 | Server state, caching, retries |
| EventSource (native) | — | SSE streaming for agent status |

**Key components:**
- `BuildingForm` — structured form (building type, floors, city, material, purpose, notes)
- `AgentStatusPanel` — real-time updates as each of the 4 agents completes (via SSE)
- `ComplianceReport` — renders the final structured report with article citations, risk level, freshness badges
- `SearchPanel` — direct semantic search into the regulatory corpus

**Proxy config:** `vite.config.ts` proxies `/api/*` → `http://localhost:8001`

---

### 3.2 Backend — `src/api/`

**Framework:** FastAPI 0.115.12 + uvicorn (port 8001)

**Routers:**
| Route | Method | Description |
|---|---|---|
| `POST /api/analyze` | POST | Run full 4-agent pipeline, stream SSE events |
| `GET /api/search` | GET | Direct semantic search (no agents) |
| `POST /api/feedback` | POST | Store user thumbs-up/down + comment |
| `GET /api/prompt` | GET | Return current system prompt template |
| `GET /health` | GET | Liveness check — Qdrant, LLM, MCP status |

**Middleware:** CORS, structlog request logging, slowapi rate limiting (20 req/min).

---

### 3.3 LangGraph Pipeline — `src/agents/`

Implemented as a `StateGraph` with a single shared `AgentState` (Pydantic v2 model).  
Pipeline is **linear and deterministic** — no emergent behaviour, full traceability.

```
START → search_agent → compliance_agent → update_agent → explanation_agent → END
```

**AgentState fields (key):**
```python
building_type: str
floors: int
city: str
material: str
purpose: str
raw_query: str          # concatenated from inputs
retrieved_chunks: list  # output of SearchAgent
search_confidence: float
compliance_report: dict # structured output of ComplianceAgent
norm_identifiers: list  # e.g. ["СП РК 2.03-30-2017", "СН РК 3.01-01-2013"]
freshness_verdicts: dict # norm_id → CURRENT | AMENDED | UNKNOWN
mcp_available: bool
final_response: str     # plain-language report from ExplanationAgent
agent_trace: list       # timing and status of each agent
```

#### SearchAgent (`search_agent.py`)
- Embeds `raw_query` with BAAI/bge-m3 (1024-dim)
- Performs cosine similarity search against Qdrant `regulations` collection
- Returns top-K chunks (default K=8, threshold=0.60)
- Sets `search_confidence` (0.0–1.0)
- If confidence = 0: downstream agents produce "insufficient data" responses gracefully

#### ComplianceAgent (`compliance_agent.py`)
- Receives `retrieved_chunks` from SearchAgent
- Constructs a structured prompt for gpt-4o-mini: building parameters + retrieved text
- LLM returns a JSON compliance report: applicable articles, compliance status (COMPLIANT / VIOLATION / UNCLEAR), severity, explanation
- Extracts `norm_identifiers` for freshness check

#### UpdateAgent (`update_agent.py`)
- For each `norm_identifier`, calls Tavily MCP search targeting `adilet.zan.kz` and `online.zakon.kz`
- Classifies freshness: **CURRENT** (no amendments found), **AMENDED** (keyword hit), **UNKNOWN** (no results)
- Results stored in `freshness_verdicts`
- Degrades gracefully: if `TAVILY_API_KEY` is empty → all verdicts = UNVERIFIED, pipeline continues

#### ExplanationAgent (`explanation_agent.py`)
- Receives `compliance_report` + `freshness_verdicts`
- Calls gpt-4o-mini to write a professional, plain-language compliance summary in Russian
- Embeds freshness badges alongside each article citation
- Stores result in `final_response`

---

### 3.4 LLM — `src/agents/llm.py`

**Production LLM:** OpenAI `gpt-4o-mini`
- Provider: `LLM_PROVIDER=openai` in `.env`
- `OPENAI_API_KEY` set to a live key
- `temperature=0.0` — deterministic structured output
- `max_tokens=1500`
- Instantiated via LangChain `ChatOpenAI`, cached with `@lru_cache`

**Alternative (local):** Ollama `mistral:7b-instruct` — available via `LLM_PROVIDER=ollama` but **not used in the evaluated deployment**. Included for zero-cost local experimentation.

---

### 3.5 RAG Layer — `src/rag/`

**Retriever (`retriever.py`):**
- Embeds query → `embed_query()` using BAAI/bge-m3
- Calls `client.query_points()` (Qdrant client ≥ 1.7 API)
- Supports optional metadata filters: `doc_type`, `language`
- Returns `List[RetrievedChunk]`, each with: `text`, `score`, `article_ref`, `doc_name`, `doc_number`, `doc_type`, `year`, `language`, `is_low_confidence`

**Embedding model:** `BAAI/bge-m3`
- 1024-dimensional output
- Multilingual: Russian, Kazakh (Cyrillic), English
- Loaded once, cached locally (~2.27 GB model file)
- Batch size: 32 chunks per embed call

---

### 3.6 Document Ingestion Pipeline — `src/ingestion/`

```
data/regulations/*.pdf  ──►  parser.py  ──►  chunker.py  ──►  embedder.py  ──►  indexer.py  ──►  Qdrant
data/regulations/*.docx ──►     │
data/regulations/*.txt  ──►     │
```

**Parser (`parser.py`):**
- PDF: PyMuPDF (`fitz`) — text extraction, OCR fallback via pytesseract if available
- DOCX: python-docx 1.1.2 — extracts paragraphs + table cells
- TXT: plain read with encoding detection
- Outputs `ParsedDocument`: `title`, `doc_number`, `doc_type`, `year`, `language`, `full_text`
- Detects doc type by regex: СНиП, СП РК, ҚНжЕ, СТ РК, СН РК, etc.

**Chunker (`chunker.py`):**
- Article-aware chunking: splits on article markers (п. N, Раздел, §) before falling back to fixed-size
- Chunk size: 800 tokens, overlap: 100 tokens
- Each `DocumentChunk` carries: `text`, `article_ref`, `doc_number`, `doc_type`, `year`, `language`, `doc_hash`

**Indexer (`indexer.py`):**
- De-duplicates by `doc_hash` — re-ingestion is safe (already-indexed docs skipped)
- Batch upsert: 64 points per request
- Stores rich payload per vector: all chunk metadata for filtered retrieval

**Current corpus:** 13 real Kazakhstan regulatory PDFs, 1,004 chunks

| Document | Chunks |
|---|---|
| СП РК 4.02-101-2012 | 129 |
| СП РК 4.04-106-2013 | 123 |
| СП РК 3.02-107-2014 | 109 |
| СП РК 3.02-101-2012 | 92 |
| СП РК 4.01-103-2013 | 75 |
| СП РК 2.03-30-2017 | 67 |
| СП РК 2.02-101-2022 | 67 |
| СП РК 4.01-101-2012 | 66 |
| СН РК 3.01-01-2013 | 66 |
| СП РК 3.06-101-2012 | 55 |
| СН РК 3.01-05-2013 | 38 |
| СН РК 3.01-02-2012 | 29 |
| СН РК 3.01-03-2011 | 29 |
| **Total** | **1,004** |

---

### 3.7 Qdrant Vector Database

| Property | Value |
|---|---|
| Container name | `derek_qdrant` |
| Image | `qdrant/qdrant:1.9.7` |
| Port | 6333 (HTTP), gRPC 6334 |
| Collection | `regulations` |
| Vector size | 1024 |
| Distance | Cosine |
| Vectors | 1,004 |
| Status | green |

**Client factory (`src/qdrant_client_factory.py`):**  
Centralised factory with `check_compatibility=False` — prevents version mismatch errors between client 1.17.1 and server 1.9.7. All modules import `create_qdrant_client()` from this single location.

---

### 3.8 MCP Integration — `src/mcp/tavily_client.py`

**Tool:** Tavily Search API (free tier: 1,000 searches/month)  
**Role in MCP protocol:** Tavily acts as a Tool Server providing a `search` tool. The UpdateAgent calls it via HTTP.

**Workflow per norm identifier:**
1. Query: `"<norm_id> изменение поправка актуализированная site:adilet.zan.kz OR site:online.zakon.kz"`
2. Parse top-3 results for amendment keywords: `изменение`, `отменён`, `superseded`, `новая редакция`, `взамен`, etc.
3. Return `FreshnessVerdict`: `CURRENT` | `AMENDED` | `UNKNOWN`

**Caching:** `diskcache` with TTL = 24 hours (configurable via `MCP_CACHE_TTL_HOURS`)  
**Retry:** `tenacity` — 2 attempts, exponential backoff 1–4 seconds  
**Graceful degradation:** If `TAVILY_API_KEY` is empty or placeholder → `is_mcp_available()` returns `False` → all verdicts = `UNVERIFIED`. Pipeline always completes.

---

### 3.9 Guardrails — `src/guardrails/input_filter.py`

Validates all user input before it reaches the LLM or agent pipeline.

**Three-layer validation:**

1. **Prompt injection detection** — 10 compiled regex patterns:
   - `ignore all previous instructions`
   - `forget all previous`
   - `you are now a ...`
   - `act as if you are`
   - `pretend / roleplay / imagine`
   - `override safety/content/system`
   - `disregard your guidelines`
   - `say that the building is compliant`
   - `DAN` (Do Anything Now)
   - `jailbreak`

2. **Off-topic domain filter** — rejects clearly non-construction queries (recipes, stocks, movies, politics)

3. **Domain relevance check** — at least one construction keyword must appear in the combined query (building/здание, floor/этаж, norm/СНиП, city name, material, etc.)

**Rejection is fast-fail** — no LLM call is made for blocked requests.

---

### 3.10 Monitoring & Observability

- **Structured logging:** `structlog` JSON logs on every request, agent step, and embedding call
- **Request tracing:** `session_id` (UUID) generated per pipeline run, attached to all log lines
- **Agent trace:** `agent_trace` list in `AgentState` records each agent's start time, end time, and status
- **Rate limiting:** slowapi — 20 requests/min per IP, 429 response on breach
- **User feedback:** SQLite (`data/derek_ai.db`) — thumbs-up/down + free-text comment per session
- **Health endpoint:** `GET /health` — real-time Qdrant, LLM, MCP availability
- **Optional:** Langfuse integration (`LANGFUSE_PUBLIC_KEY` / `LANGFUSE_SECRET_KEY`) for LLM call tracing — disabled by default

---

## 4. Data Flow — End to End

```
1. User fills BuildingForm
   → browser sends POST /api/analyze
   → FastAPI receives request

2. Input validation
   → guardrails/input_filter.py
   → If blocked: 400 + reason returned immediately

3. AgentState initialised
   → raw_query = "Жилой дом, 9 этажей, Алматы, железобетон, жильё"
   → session_id = UUID

4. SearchAgent
   → embed_query(raw_query) via BAAI/bge-m3 → 1024-dim vector
   → client.query_points(collection="regulations", top_k=8, min_score=0.60)
   → returns list[RetrievedChunk]
   → SSE event: {"agent": "search", "status": "done", "chunks": N}

5. ComplianceAgent
   → builds prompt: system_prompt + building_params + retrieved chunks
   → calls gpt-4o-mini (temperature=0)
   → parses structured JSON: {applicable_articles, violations, risk_level}
   → SSE event: {"agent": "compliance", "status": "done"}

6. UpdateAgent
   → for each norm_identifier: Tavily search → classify freshness
   → SSE event: {"agent": "update", "status": "done", "mcp_used": true/false}

7. ExplanationAgent
   → calls gpt-4o-mini with compliance_report + freshness_verdicts
   → produces final_response (professional Russian prose)
   → SSE event: {"agent": "explanation", "status": "done"}

8. Final SSE event: {"type": "complete", "response": final_response, "trace": [...]}
   → React renders ComplianceReport component
```

---

## 5. Project Structure

```
Capstone_Project/
├── src/
│   ├── agents/
│   │   ├── orchestrator.py        # LangGraph StateGraph — pipeline definition
│   │   ├── state.py               # AgentState Pydantic v2 model
│   │   ├── search_agent.py        # RAG retrieval agent
│   │   ├── compliance_agent.py    # LLM compliance analysis agent
│   │   ├── update_agent.py        # Tavily MCP freshness agent
│   │   ├── explanation_agent.py   # LLM final report agent
│   │   └── llm.py                 # LLM factory (OpenAI / Ollama)
│   ├── api/
│   │   ├── main.py                # FastAPI app factory
│   │   ├── middleware.py          # CORS, logging, rate-limit setup
│   │   └── routers/
│   │       ├── analyze.py         # POST /api/analyze (SSE streaming)
│   │       ├── search.py          # GET /api/search
│   │       ├── feedback.py        # POST /api/feedback
│   │       └── prompt.py          # GET /api/prompt
│   ├── rag/
│   │   └── retriever.py           # Semantic search interface
│   ├── ingestion/
│   │   ├── parser.py              # PDF / DOCX / TXT parser
│   │   ├── chunker.py             # Article-aware chunker
│   │   ├── embedder.py            # BAAI/bge-m3 embedding wrapper
│   │   └── indexer.py             # Qdrant batch upserter
│   ├── mcp/
│   │   └── tavily_client.py       # Tavily Search MCP client
│   ├── guardrails/
│   │   └── input_filter.py        # Injection detection + domain validation
│   ├── monitoring/
│   │   └── feedback_store.py      # SQLite feedback persistence
│   ├── qdrant_client_factory.py   # Centralised Qdrant client (check_compatibility=False)
│   └── config.py                  # Pydantic-settings — all env vars
├── frontend/
│   ├── src/
│   │   ├── components/            # BuildingForm, AgentStatusPanel, ComplianceReport
│   │   ├── hooks/                 # useAnalysis, useSearch, useFeedback
│   │   └── stores/                # Zustand global state
│   ├── vite.config.ts             # Proxy /api → localhost:8001
│   └── package.json
├── scripts/
│   ├── ingest.py                  # CLI: python scripts/ingest.py --dir data/regulations
│   └── check_index.py             # CLI: check Qdrant collection stats
├── tests/
│   ├── test_guardrails.py         # 12 guardrail tests (injection, off-topic, valid)
│   ├── test_retriever.py          # Retriever integration tests
│   ├── test_api.py                # FastAPI endpoint tests
│   └── test_pipeline.py           # Full pipeline smoke tests
├── MDS/
│   ├── BLUEPRINT.md               # This file — architecture + all ADRs
│   ├── PRD.md                     # Full Product Requirements Document (~650 lines)
│   └── capstone_topic_proposal.md # Original approved topic proposal
├── docs/
│   └── EXECUTIVE_SUMMARY.md       # 1-page executive summary deliverable
├── data/
│   ├── regulations/               # 13 real Kazakhstan PDFs (gitignored)
│   └── qdrant_storage/            # Qdrant persistent volume (gitignored)
├── .env                           # Secrets (gitignored)
├── .env.example                   # Template — safe to commit
├── docker-compose.yml             # Qdrant container
├── requirements.txt               # Python dependencies
├── pytest.ini                     # pytest config — asyncio scope, slow marker
├── README.md                      # Setup and quick-start guide
└── Capstone_project_Anet_Tatygulov.txt  # Submission file
```

---

## 6. Architecture Decision Records (ADRs)

### ADR-001: Vector Database — Qdrant over ChromaDB

**Decision:** Use Qdrant 1.9.7 (Docker) as the vector store.

**Context:** Regulatory corpus can reach ~450,000 vectors (30,000 PDFs × ~15 chunks). Metadata filtering is critical — queries must filter by `doc_type` (СНиП vs СП vs ҚНжЕ), `year`, and `language` in a single search call.

**Rejected:** ChromaDB — in-process SQLite backend degrades significantly above 100K vectors. No production-grade filtered search. Would require a full rewrite at scale.

**Consequence:** Requires Docker. Adds operational overhead but provides cosine similarity search at scale with compound metadata filtering in a single `query_points()` call. Centralised client factory (`qdrant_client_factory.py`) handles version compatibility (`check_compatibility=False`) between client 1.17.1 and server 1.9.7.

---

### ADR-002: Embedding Model — BAAI/bge-m3 over all-MiniLM-L6-v2

**Decision:** Use `BAAI/bge-m3` (1024-dim, multilingual, ~570 MB).

**Context:** Kazakhstan regulatory documents are in Russian and Kazakh (Cyrillic). Technical terms — `СНиП`, `ҚНжЕ`, `сейсмостойкость`, `жылу оқшаулауы` — must embed correctly and retrieve accurately against mixed-language queries.

**Rejected:** `all-MiniLM-L6-v2` — English-only, produces near-random embeddings for Cyrillic text. Tested: Russian regulatory queries returned irrelevant chunks with scores < 0.3.

**Consequence:** Larger model (2.27 GB cached on disk) → slower cold start. Mitigated with `diskcache` so embeddings are computed once per document. Inference runs on CPU; embedding 1,004 chunks took ~80 minutes on student hardware. In production, GPU inference or a hosted embedding API would reduce this to minutes.

---

### ADR-003: Agent Framework — LangGraph over CrewAI / AutoGen

**Decision:** Use LangGraph 0.4 `StateGraph` with a deterministic 4-node pipeline.

**Context:** The compliance workflow is inherently sequential: you must retrieve before you can analyse, analyse before you can verify freshness, and verify before you can explain. The pipeline must be inspectable (each step's output is visible in `AgentState`) and must support real-time SSE streaming of intermediate results.

**Rejected:**
- **CrewAI** — designed for autonomous agents with emergent, non-deterministic task allocation. Cannot guarantee pipeline order; hard to stream intermediate state.
- **AutoGen** — heavier framework, complex multi-party chat model not suited to a linear compliance pipeline. Harder to integrate with FastAPI SSE.

**Consequence:** More setup boilerplate than CrewAI but complete control over state transitions and streaming. Native LangChain LLM support means the same `get_llm()` factory works across all agents.

---

### ADR-004: LLM — OpenAI gpt-4o-mini as Primary

**Decision:** Use OpenAI `gpt-4o-mini` as the production LLM (`LLM_PROVIDER=openai`).

**Context:** Compliance analysis requires structured JSON output (articles, risk levels, violation details). The LLM must follow strict output format instructions reliably. Response quality directly determines the usefulness of the report.

**Rejected:**
- **Ollama `mistral:7b-instruct` as primary** — quality insufficient for structured JSON compliance reports in Russian. Hallucinated article numbers and misclassified risk levels in testing. Still available as a `LLM_PROVIDER=ollama` fallback for zero-cost local experimentation.
- **GPT-4o** — higher quality but 6× more expensive per token. gpt-4o-mini quality is sufficient for structured extraction with `temperature=0`.

**Consequence:** Requires a live `OPENAI_API_KEY`. Demo cost ~$2–3 for full graded submission run. `temperature=0.0`, `max_tokens=1500` for deterministic structured output.

---

### ADR-005: MCP Integration — Tavily Search as Norm Freshness Tool

**Decision:** Integrate Tavily Search API as an MCP Tool Server for norm freshness verification.

**Context:** Kazakhstan regulatory norms are updated regularly. A compliance report citing an outdated or superseded norm creates legal risk for the engineer relying on it. The system must proactively flag this.

**Rejected:**
- **Scraping `adilet.zan.kz` directly** — fragile (DOM changes break scrapers), rate-limited, requires maintaining CSS selectors.
- **Static "last updated" metadata** — only as accurate as the last ingestion run; does not catch mid-cycle amendments.

**Implementation:** Tavily queries target `adilet.zan.kz` and `online.zakon.kz`. Result text is scanned for amendment keywords (Russian + English). Results cached for 24 hours with `diskcache`. Retry with exponential backoff via `tenacity`.

**Consequence:** Requires `TAVILY_API_KEY` (free tier: 1,000 searches/month). System degrades gracefully to `UNVERIFIED` verdicts if key not set. Pipeline always completes.

---

### ADR-006: Frontend — React over Streamlit

**Decision:** React 18 + Vite + TailwindCSS + Zustand + TanStack Query.

**Context:** The capstone rubric awards +10 bonus points for polished UI. More importantly, the target users are professional architects and engineers — the UI must feel like a professional tool, not a prototype.

**Rejected:** Streamlit — faster to build (~2 hours vs ~8 hours) but looks like a data science notebook. Cannot support real-time SSE streaming without hacks. Poor mobile responsiveness. Not production-deployable without significant wrapping.

**Consequence:** ~2× more frontend development time. Mitigated by TailwindCSS (no custom CSS written), TanStack Query (no manual fetch state management), Zustand (minimal boilerplate). SSE streaming via native `EventSource` — no extra library needed. Production build: 152 modules, ~350 KB gzipped.

---

### ADR-007: Guardrails — Regex-based Injection Detection

**Decision:** Block prompt injection with 10 compiled regex patterns in `src/guardrails/input_filter.py` before any LLM call.

**Context:** Users submit free-text (building notes, purpose). Must prevent `"ignore all previous instructions"` style attacks from reaching the LLM and manipulating compliance verdicts (e.g. forcing a `COMPLIANT` output for a non-compliant building).

**Rejected:**
- **LLM-as-judge moderation** — adds 300–500 ms latency and $0.002 per request cost for a check that regex handles deterministically.
- **OpenAI Moderation API** — not free, not designed for domain-specific injection patterns (e.g. `"say that the building is compliant"` would pass OpenAI moderation but is a domain-specific injection).

**Consequence:** 100% deterministic coverage of known injection patterns. Sub-millisecond check. False positive rate is near zero on legitimate construction queries (tested against 500+ real queries). New patterns can be added as a single regex line.

---

## 7. Security Considerations

| Threat | Mitigation |
|---|---|
| Prompt injection | Regex guardrails block 10 known patterns before any LLM call |
| API key leakage | `.env` gitignored, `.env.example` committed instead |
| Credential stuffing / DoS | slowapi rate limiter — 20 req/min per IP |
| Compliance verdict manipulation | Guardrails reject `"say that the building is compliant"` pattern |
| CORS abuse | Explicit allow-list: localhost:5173, localhost:3000 |
| SQL injection | SQLite ORM layer for feedback; no raw SQL string interpolation |
| Path traversal in ingestion | `Path(file).suffix.lower()` check, no user-controlled file paths |

---

## 8. Testing Strategy

**Framework:** pytest 8.3.5 + `pytest-asyncio`  
**Total tests (fast):** 33 passing  
**Marker:** `@pytest.mark.slow` for integration tests requiring live Qdrant (excluded from CI with `-k "not slow"`)

| Test file | Coverage |
|---|---|
| `test_guardrails.py` | Valid queries, injection patterns, off-topic rejection, edge cases |
| `test_retriever.py` | Semantic search correctness, low-confidence handling, filter logic |
| `test_api.py` | All FastAPI endpoints, 400/429 error responses |
| `test_pipeline.py` | Full pipeline smoke test, graceful degradation without MCP |

**Test categories:**
- **Positive:** Valid building descriptions → pipeline completes, report generated
- **Negative:** Invalid inputs, empty queries, out-of-scope cities → correct rejection
- **Adversarial:** All 10 injection patterns → all blocked, no LLM call made

---

## 9. Key Dependencies

```
# Core
fastapi==0.115.12
uvicorn[standard]==0.34.0
pydantic==2.11.4
pydantic-settings==2.9.1

# Agents
langgraph==0.4.3
langchain-core==0.3.59
langchain-openai==0.3.16
langchain-community==0.3.23  # Ollama fallback

# Embeddings & Vector DB
sentence-transformers==3.4.1  # BAAI/bge-m3
qdrant-client==1.17.1

# Document parsing
pymupdf==1.24.11             # PyMuPDF — PDF text extraction
python-docx==1.1.2           # DOCX parsing

# MCP / Tavily
tavily-python==0.5.0
diskcache==5.6.3
tenacity==9.0.0

# Observability
structlog==25.1.0
slowapi==0.1.9               # Rate limiting

# Testing
pytest==8.3.5
pytest-asyncio==0.26.0
httpx==0.28.1                # Test client
```

---

## 10. Local Deployment

**Requirements:** Python 3.12, Docker, Node.js 18+

```powershell
# 1. Clone
git clone https://github.com/a98t/Capstone_Project_AI_Regulatory_Arc_Con_Platform
cd Capstone_Project_AI_Regulatory_Arc_Con_Platform

# 2. Configure
cp .env.example .env
# Set: LLM_PROVIDER=openai, OPENAI_API_KEY=sk-...
# Optional: TAVILY_API_KEY=tvly-...

# 3. Start Qdrant
docker compose up -d

# 4. Install Python deps
pip install -r requirements.txt

# 5. Ingest regulatory documents (place PDFs in data/regulations/)
$env:PYTHONPATH = "."; python scripts/ingest.py --dir data/regulations

# 6. Start backend (port 8001)
$env:PYTHONPATH = "."; uvicorn src.api.main:app --host 0.0.0.0 --port 8001 --reload

# 7. Start frontend (port 5173)
cd frontend; npm install; npm run dev
```

---

*Last updated: May 2026 — Anet Tatygulov*
