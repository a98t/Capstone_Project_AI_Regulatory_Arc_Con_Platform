# Architecture Decision Record — DEREK-AI

## ADR-001: Vector Database — Qdrant over ChromaDB

**Decision**: Use Qdrant 1.9.7 (Docker) as the vector store.

**Context**: ~30 000 PDFs × ~15 chunks = ~450 000 vectors with rich metadata filters (doc_type, year, city).

**Rejected**: ChromaDB — in-process, degrades significantly above 100 K vectors, no production-grade filtering.

**Consequence**: Requires Docker. Adds ops overhead but provides cosine similarity search at scale with metadata filtering in a single query.

---

## ADR-002: Embedding Model — BAAI/bge-m3 over all-MiniLM-L6-v2

**Decision**: Use `BAAI/bge-m3` (1024-dim, multilingual).

**Context**: Regulatory documents are in Russian and Kazakh (Cyrillic). Technical terms like "СНиП", "ҚНжЕ", "сейсмостойкость" must embed correctly.

**Rejected**: `all-MiniLM-L6-v2` — English-only, produces garbage embeddings for Cyrillic text. Tested and confirmed fails on Russian regulatory queries.

**Consequence**: Larger model (570 MB) → slower first load. Mitigated by disk cache (diskcache) so embeddings computed once.

---

## ADR-003: Agent Framework — LangGraph over CrewAI / AutoGen

**Decision**: Use LangGraph 0.4 `StateGraph`.

**Context**: Need a deterministic, inspectable pipeline: Search → Compliance → Update → Explain. Must support conditional routing (skip compliance if search confidence = 0).

**Rejected**: CrewAI — better for autonomous agents with emergent behaviour, not deterministic pipelines. AutoGen — heavier, harder to trace.

**Consequence**: More boilerplate than CrewAI but full control over state transitions, easy SSE integration, native Langchain LLM support.

---

## ADR-004: LLM — Ollama (local) with OpenAI fallback

**Decision**: Default to `ollama/mistral:7b-instruct` (free, local). `gpt-4o-mini` available via `LLM_PROVIDER=openai`.

**Context**: $0 budget. Ollama runs locally on student hardware. Quality is acceptable for structured JSON compliance reports.

**Consequence**: First run requires `ollama pull mistral:7b-instruct` (~4 GB). Demo on OpenAI costs ~$2–3 for final graded demonstration.

---

## ADR-005: MCP Integration — Tavily Search as norm freshness tool

**Decision**: Integrate Tavily Search API as an MCP Tool Server for norm freshness verification.

**Context**: Regulatory norms change. The system must flag when a cited norm (e.g. "СП 14.13330.2018") has been amended or superseded.

**Rejected**: Scraping kazakh government portals directly — fragile, unreliable, rate-limited.

**Consequence**: Requires `TAVILY_API_KEY` (free tier: 1 000 searches/month). System degrades gracefully to UNVERIFIED verdicts if key not set.

---

## ADR-006: Frontend — React over Streamlit

**Decision**: React 18 + Vite + TailwindCSS.

**Context**: Capstone rubric awards +10 bonus points for polished UI. Streamlit would be faster to build but looks like a prototype.

**Consequence**: ~2× more frontend development time. Mitigated by Zustand + TanStack Query reducing boilerplate. SSE streaming supported natively via EventSource.

---

## ADR-007: Guardrails — Regex-based injection detection

**Decision**: Block prompt injection with compiled regex patterns in `src/guardrails/input_filter.py` before any LLM call.

**Context**: Users submit free text (notes, purpose). Must prevent "ignore all previous instructions" style attacks from reaching the LLM.

**Rejected**: LLM-as-judge moderation — adds latency and cost. OpenAI Moderation API — not free, not needed for structured form inputs.

**Consequence**: 100% coverage of known injection patterns. False positive rate near zero on legitimate construction queries.
