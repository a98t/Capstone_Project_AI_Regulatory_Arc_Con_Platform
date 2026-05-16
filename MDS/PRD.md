# Product Requirements Document (PRD)
## DEREK-AI: AI-Powered Regulatory Intelligence System for Kazakhstan Construction Industry

**Version:** 1.0  
**Date:** May 5, 2026  
**Author:** Capstone Project  
**Status:** Approved for Implementation  
**Deadline:** May 18, 2026 (14 days)

---

## 1. Executive Summary

DEREK-AI transforms the legacy DEREK-INFO regulatory directory platform into an AI-first compliance assistant for Kazakhstan's construction and engineering industry. Instead of manual keyword search through 30,000+ documents, professionals describe their building project in natural language and receive a structured compliance analysis with source citations, violation flags, and real-time norm freshness verification — all within seconds.

The system uses Retrieval-Augmented Generation (RAG) over a local vector database of Kazakhstan construction norms (СНиП, СП, ҚНжЕ, СТ РК, and others), a LangGraph-orchestrated multi-agent pipeline, and a Tavily MCP server for live regulatory update checks.

---

## 2. Problem Statement

### Current State (Legacy DEREK-INFO)
- Users log in to a web directory and search by keyword, document index, or title
- Search returns a list of documents — the user must open, read, and manually cross-reference each one
- A compliance check for a 9-floor residential building requires reading 5–15 documents (fire safety, seismic, accessibility, energy efficiency, structural norms)
- Time cost per project: **2–6 hours** of manual regulatory research
- Risk: missed norms, outdated references, human interpretation errors

### Target State (DEREK-AI)
- User describes building parameters in a form (type, floors, city, material, purpose)
- System automatically retrieves, analyzes, and cross-references all applicable norms
- Output is a structured compliance report: applicable articles, compliance status, violations, and plain-language explanations
- Time cost per project: **2–5 minutes**

---

## 3. Product Vision

> **"One query. All applicable norms. Instant compliance analysis."**

DEREK-AI serves as an AI co-pilot for architects, engineers, and construction professionals in Kazakhstan — reducing regulatory research from hours to minutes while maintaining full traceability to source documents.

---

## 4. User Personas

### Persona 1: Project Architect (Primary)
- **Name:** Aigerim, 34, Senior Architect at a Almaty design bureau
- **Problem:** Spends hours per project verifying compliance with fire safety, seismic, and accessibility norms
- **Goal:** Get an instant checklist of applicable regulations when starting a new project
- **Tech comfort:** Medium — uses web tools daily, comfortable with forms

### Persona 2: Junior Engineer (Secondary)
- **Name:** Damir, 26, structural engineer
- **Problem:** Unsure which norms apply to specific building types; often consults seniors for regulatory interpretation
- **Goal:** Understand regulatory requirements in plain language without legal expertise
- **Tech comfort:** High

### Persona 3: Compliance Reviewer (Tertiary)
- **Name:** Nurgul, 45, state construction oversight inspector
- **Problem:** Needs to verify that submitted designs reference correct and current norm versions
- **Goal:** Quickly check if the norms cited in a design package are current and complete
- **Tech comfort:** Low-Medium

---

## 5. User Stories

### Core Flow
| ID | As a... | I want to... | So that... | Priority |
|---|---|---|---|---|
| US-01 | Architect | Enter building parameters and get applicable regulations | I don't have to search manually | P0 |
| US-02 | Engineer | See which specific articles apply to my building | I know exactly what to check | P0 |
| US-03 | User | See a compliance status (compliant / requires action / advisory) | I can prioritize what to address | P0 |
| US-04 | User | See if the retrieved norms are current | I don't rely on outdated regulations | P0 |
| US-05 | User | Read a plain-language explanation of each requirement | I understand complex legal language | P0 |
| US-06 | User | See the source document name and article number for each finding | I can verify and cite the source | P0 |
| US-07 | User | Rate the quality of a response | The system can improve over time | P1 |
| US-08 | User | Search the document corpus by keyword (legacy mode) | I can still do traditional search if needed | P1 |
| US-09 | Admin | View agent interaction traces and token usage | I can monitor system performance | P1 |
| US-10 | User | See a warning when norm currency could not be verified | I know when to double-check externally | P0 |

### Edge Cases
| ID | Scenario | Expected Behavior |
|---|---|---|
| US-11 | Empty or invalid input | Validation error with user-friendly message, no crash |
| US-12 | Unknown/fictional location ("Mars") | Agent acknowledges out-of-scope, no fabricated regulations |
| US-13 | Prompt injection attempt | Guardrail intercepts, system stays on compliance task |
| US-14 | Regulation not in knowledge base | Search Agent returns "not found" with confidence score |
| US-15 | MCP server unavailable | Update Agent falls back, flags "currency unverified" |
| US-16 | Query in Kazakh language | System processes and responds correctly |

---

## 6. Functional Requirements

### 6.1 Input Form
- Fields: Building Type (dropdown), Number of Floors (integer), City (dropdown + free text), Primary Material (dropdown), Building Purpose (dropdown + free text), Additional Notes (textarea)
- All fields validated on submit; Building Type, Floors, and City are required
- Character limit: 1000 chars on Additional Notes

### 6.2 Agent Pipeline
- **Orchestrator:** Routes user input through the agent pipeline; manages shared state via LangGraph StateGraph
- **Search Agent:** Queries Qdrant vector store with user parameters; returns top-k (configurable, default 8) chunks with similarity scores; applies confidence threshold (score < 0.60 → flagged as low confidence)
- **Compliance Agent:** Analyzes retrieved chunks against building parameters; produces structured JSON report with: applicable articles, compliance status per item, detected violations, and risk level (HIGH/MEDIUM/LOW/ADVISORY)
- **Update Agent:** For each distinct norm document found by Compliance Agent, calls Tavily MCP to search for recent amendments; returns freshness verdict per document; gracefully falls back if MCP unavailable
- **Explanation Agent:** Rewrites the compliance report in plain professional Russian/English; preserves all source citations; adds the standard disclaimer

### 6.3 Output Report
Structured compliance report including:
- Summary card: total norms checked, violations count, items requiring action
- Per-item detail: article reference, compliance status, plain-language description, source citation, freshness status
- Overall risk level
- Standard disclaimer: "Данный анализ выполнен с помощью ИИ. Верифицируйте результаты с лицензированным инженером перед подачей документации."

### 6.4 Document Search (Legacy Mode)
- Full-text keyword search across the document corpus
- Returns matching document titles with metadata (type, year, status)
- Links to full document text

### 6.5 User Feedback
- Star rating (1–5) on each compliance report
- Optional freeform comment
- Data stored locally in SQLite

### 6.6 Observability Dashboard
- Accessible at `/admin` (basic auth protected)
- Shows: recent queries, token usage, agent latency per step, error count
- Powered by Langfuse integration

---

## 7. Non-Functional Requirements

### 7.1 Performance
| Metric | Target |
|---|---|
| Compliance analysis response time (P95) | < 30 seconds |
| Document search response time (P95) | < 2 seconds |
| RAG retrieval latency | < 1 second |
| Concurrent users supported | ≥ 5 simultaneous |

### 7.2 Security
| Requirement | Implementation |
|---|---|
| Input sanitization | Pydantic v2 strict models on all FastAPI endpoints |
| Prompt injection detection | Guardrail layer: regex + LLM-based topic classifier before Orchestrator |
| Rate limiting | `slowapi`: 20 requests/min per IP on `/analyze` endpoint |
| No credential commits | `.env` in `.gitignore`; `.env.example` with placeholder values only |
| HTTPS in production | Nginx reverse proxy (optional for demo) |

### 7.3 RAG Quality
| Requirement | Implementation |
|---|---|
| Multilingual retrieval | `BAAI/bge-m3` embeddings (Russian/Kazakh/English support) |
| Confidence threshold | Score < 0.60 → "low confidence" flag on chunk |
| Source attribution | Every response includes document name + article number |
| Hallucination mitigation | System prompt requires agents to cite only retrieved context; "I don't know" fallback when context is insufficient |
| RAGAS evaluation | Automated test suite measures context_recall and faithfulness |

### 7.4 Cost Management
| Component | Cost | Strategy |
|---|---|---|
| LLM inference | $0–$5 total | Ollama (Mistral-7B / Llama 3.1 8B) as primary; OpenAI GPT-4o-mini as optional upgrade |
| Embeddings | $0 | `bge-m3` runs locally via `sentence-transformers` |
| Vector database | $0 | Qdrant local via Docker |
| MCP / Search | $0 | Tavily free tier (1,000 searches/month) |
| Observability | $0 | Langfuse cloud free tier (50K events/month) or self-hosted |
| Hosting | $0 | Runs entirely locally; no cloud infrastructure |
| **Total budget** | **< $5** | LLM API calls for optional demo polish only |

### 7.5 Reliability
- Graceful degradation: MCP unavailable → continue without freshness check, flag in output
- Graceful degradation: LLM API unavailable → surface error message, suggest Ollama fallback
- All external calls wrapped in try/except with structured error logging

---

## 8. Technical Architecture

### 8.1 Component Diagram

```
┌──────────────────────────────────────────────────────────────┐
│                     REACT FRONTEND                            │
│  Vite + React 18 + TailwindCSS + shadcn/ui                   │
│                                                              │
│  ┌───────────────┐  ┌──────────────────┐  ┌──────────────┐  │
│  │  Input Form   │  │ Agent Status     │  │  Report      │  │
│  │  (US-01)      │  │ Live Panel       │  │  Viewer      │  │
│  └───────┬───────┘  └──────────────────┘  └──────────────┘  │
└──────────┼───────────────────────────────────────────────────┘
           │ REST + SSE (Server-Sent Events for streaming)
┌──────────▼───────────────────────────────────────────────────┐
│                    FASTAPI BACKEND                            │
│  Python 3.11+                                                │
│                                                              │
│  POST /api/analyze     GET /api/search                       │
│  POST /api/feedback    GET /api/health                       │
│  GET  /api/stream/{id} (SSE agent progress)                  │
│                                                              │
│  Guardrail Layer → Pydantic Validation → Rate Limiter        │
└──────────┬───────────────────────────────────────────────────┘
           │
┌──────────▼───────────────────────────────────────────────────┐
│              LANGGRAPH ORCHESTRATOR                           │
│                                                              │
│  State: AgentState (TypedDict)                               │
│                                                              │
│  [INPUT] ──► [Search Agent] ──► [Compliance Agent]           │
│                                        │                     │
│                               [Update Agent / MCP]           │
│                                        │                     │
│                             [Explanation Agent]              │
│                                        │                     │
│                                   [OUTPUT]                   │
└──────────┬───────────────────────────────────────────────────┘
           │
┌──────────▼───────────────────────────────────────────────────┐
│                     DATA LAYER                                │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────┐  │
│  │ Qdrant       │  │ SQLite       │  │ diskcache          │  │
│  │ (vectors)    │  │ (feedback,   │  │ (embedding cache,  │  │
│  │ Docker local │  │  audit log)  │  │  MCP result cache) │  │
│  └──────────────┘  └──────────────┘  └────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
           │
┌──────────▼───────────────────────────────────────────────────┐
│               EXTERNAL INTEGRATIONS                          │
│                                                              │
│  Tavily Search MCP Server  │  Ollama (local LLM)             │
│  Langfuse (tracing)        │  OpenAI API (optional)          │
└──────────────────────────────────────────────────────────────┘
```

### 8.2 LangGraph State Machine

```python
# AgentState — shared across all agents
class AgentState(TypedDict):
    # Input
    building_type: str
    floors: int
    city: str
    material: str
    purpose: str
    raw_query: str
    
    # Search Agent output
    retrieved_chunks: List[RetrievedChunk]
    search_confidence: float
    
    # Compliance Agent output
    compliance_report: ComplianceReport
    norm_identifiers: List[str]
    
    # Update Agent output
    freshness_verdicts: Dict[str, FreshnessVerdict]
    mcp_available: bool
    
    # Explanation Agent output
    final_response: FinalResponse
    
    # Metadata
    session_id: str
    agent_trace: List[AgentStep]
    errors: List[str]
```

### 8.3 Agent Specifications

#### Search Agent
- **Input:** `building_type`, `floors`, `city`, `material`, `purpose`
- **Process:** Constructs semantic query → queries Qdrant (top-8 chunks) → filters by confidence threshold (≥ 0.60) → returns chunks with metadata
- **Output:** `retrieved_chunks[]` with fields: `text`, `score`, `doc_name`, `article_ref`, `doc_type`, `year`
- **Failure mode:** Returns empty list with `search_confidence=0.0`; pipeline continues with "insufficient context" flag

#### Compliance Agent
- **Input:** `retrieved_chunks[]`, building parameters
- **Process:** LLM analyzes each chunk against stated parameters → produces per-item assessment
- **Output:** `ComplianceReport` with items: `{article_ref, status: COMPLIANT|VIOLATION|REQUIRES_ACTION|ADVISORY, description, source}`
- **Constraint:** System prompt strictly forbids inventing articles not present in retrieved_chunks

#### Update Agent
- **Input:** `norm_identifiers[]` (list of distinct document names from compliance report)
- **Process:** For each norm, calls Tavily MCP with query `"{norm_name} amendment {year} Kazakhstan"` → parses search results → classifies as CURRENT / AMENDED / UNKNOWN
- **Output:** `freshness_verdicts: {norm_id: {verdict, source_url, checked_at}}`
- **Failure mode:** If MCP call fails → `{verdict: UNVERIFIED, mcp_available: false}` for all norms

#### Explanation Agent
- **Input:** Full `AgentState` (compliance report + freshness verdicts)
- **Process:** Rewrites findings in plain language; structures output as user-facing report; adds disclaimer
- **Output:** `FinalResponse` with sections: summary, findings[], disclaimer
- **Language:** Responds in the same language the user queried in (Russian or English)

### 8.4 RAG Pipeline

```
PDF Files (30K docs)
       │
       ▼
[PyMuPDF Parser]
  - Extract text, preserve structure
  - Detect document header (title, number, year, type)
  - Flag tables and figures
       │
       ▼
[Article-Aware Chunker]
  - Split on regex: р\.|п\.|раздел|section|статья
  - Chunk size: 800 tokens, overlap: 100 tokens at section boundary
  - Preserve article number in chunk metadata
       │
       ▼
[bge-m3 Embedder]
  - Model: BAAI/bge-m3 (1024-dim, multilingual)
  - Batch size: 32 docs
  - Cache: diskcache keyed by (doc_hash, chunk_index)
  - Skip if hash already in Qdrant
       │
       ▼
[Qdrant Indexer]
  - Collection: "regulations"
  - Payload: {doc_name, doc_type, year, article_ref, chunk_index, language}
  - Index: HNSW (ef=128, m=16) for fast approximate search
```

### 8.5 API Design

```
POST   /api/analyze           Trigger full agent pipeline
GET    /api/stream/{session_id}  SSE stream for agent progress updates
POST   /api/feedback          Submit star rating + comment
GET    /api/search            Keyword search in document metadata
GET    /api/health            Health check (Qdrant, LLM, MCP connectivity)
GET    /api/docs              FastAPI auto-generated OpenAPI docs
```

**POST /api/analyze — Request:**
```json
{
  "building_type": "residential",
  "floors": 9,
  "city": "Almaty",
  "material": "reinforced_concrete",
  "purpose": "apartments",
  "notes": "Underground parking, 2 levels"
}
```

**POST /api/analyze — Response:**
```json
{
  "session_id": "uuid",
  "summary": {"total_norms": 8, "violations": 1, "requires_action": 2, "advisory": 3, "risk_level": "MEDIUM"},
  "findings": [
    {
      "article_ref": "СП РК 2.02-101-2015, п. 8.4",
      "doc_name": "СП РК 2.02-101-2015",
      "status": "VIOLATION",
      "description": "...",
      "plain_language": "...",
      "freshness": {"verdict": "CURRENT", "source_url": "..."}
    }
  ],
  "disclaimer": "...",
  "processing_time_ms": 12400
}
```

---

## 9. Technology Stack (Final)

| Layer | Technology | Version | Justification |
|---|---|---|---|
| **Agent Framework** | LangGraph | 0.2.x | State machine with conditional routing; checkpointing; streaming support |
| **LLM (Primary)** | Ollama + `mistral:7b-instruct` | latest | Zero cost; runs locally; acceptable Russian language quality |
| **LLM (Optional)** | OpenAI `gpt-4o-mini` | latest | Better reasoning for compliance analysis; ~$2-3 total for demo |
| **Embeddings** | `BAAI/bge-m3` via `sentence-transformers` | latest | Multilingual (Russian/Kazakh/English); 1024-dim; local; SOTA for non-English retrieval |
| **Vector DB** | Qdrant | 1.9.x | Handles 450K+ vectors; rich metadata filtering; free Docker mode; far more scalable than ChromaDB |
| **PDF Processing** | PyMuPDF (`fitz`) | 1.24.x | Fast Cyrillic PDF extraction; preserves structure |
| **Text Chunking** | Custom + LangChain RecursiveCharacterTextSplitter | — | Article-aware boundaries for regulatory documents |
| **Backend** | FastAPI + uvicorn | 0.111.x | Async; Pydantic v2 validation; SSE support; auto OpenAPI docs |
| **Frontend** | React 18 + Vite | 5.x | Fast dev; tree-shaking; HMR |
| **UI Components** | shadcn/ui + TailwindCSS | latest | Pre-built accessible components; professional look for +10 UX bonus |
| **State (FE)** | Zustand | 4.x | Minimal boilerplate for agent status tracking |
| **Data Fetching (FE)** | TanStack Query (React Query) | 5.x | Caching, loading states, SSE consumption |
| **MCP Server** | Tavily Search MCP | latest | Free tier (1K/month); production MCP protocol |
| **Caching** | `diskcache` | 5.x | Persistent embedding cache; MCP result TTL cache |
| **Observability** | Langfuse | 2.x | LLM tracing; token usage; agent latency (free cloud tier) |
| **RAG Evaluation** | RAGAS | 0.1.x | Automated faithfulness + recall measurement |
| **Testing** | pytest + pytest-asyncio | latest | Async agent test support |
| **DB (feedback/logs)** | SQLite via `aiosqlite` | — | Zero infrastructure; sufficient for capstone |
| **Containerization** | Docker Compose | — | One command spins up Qdrant + optional Langfuse |
| **Security** | slowapi + Pydantic v2 | — | Rate limiting + strict input validation |

---

## 10. Project Structure

```
derek-regulatory-ai/
│
├── docker-compose.yml           # Qdrant + optional Langfuse
├── requirements.txt             # Python dependencies
├── requirements-dev.txt         # Dev/test dependencies
├── .env.example                 # Template — no real credentials
├── .gitignore
├── README.md
├── BLUEPRINT.md                 # Architecture blueprint + trade-offs
│
├── data/
│   └── regulations/             # Source PDFs (not committed to git)
│
├── scripts/
│   ├── ingest.py                # CLI: python scripts/ingest.py --dir data/regulations
│   └── check_index.py           # CLI: verify Qdrant collection stats
│
├── src/
│   ├── __init__.py
│   │
│   ├── config.py                # Settings via pydantic-settings (.env loading)
│   │
│   ├── ingestion/
│   │   ├── __init__.py
│   │   ├── parser.py            # PyMuPDF PDF → structured text
│   │   ├── chunker.py           # Article-aware chunker
│   │   ├── embedder.py          # bge-m3 embedder with diskcache
│   │   └── indexer.py           # Qdrant ingestion pipeline
│   │
│   ├── rag/
│   │   ├── __init__.py
│   │   ├── retriever.py         # Qdrant semantic search interface
│   │   └── quality.py           # Confidence scoring, RAGAS eval helpers
│   │
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── state.py             # AgentState TypedDict definition
│   │   ├── orchestrator.py      # LangGraph StateGraph definition
│   │   ├── search_agent.py      # RAG retrieval node
│   │   ├── compliance_agent.py  # Norm analysis node
│   │   ├── update_agent.py      # MCP freshness check node
│   │   └── explanation_agent.py # Plain-language rewriting node
│   │
│   ├── mcp/
│   │   ├── __init__.py
│   │   └── tavily_client.py     # Tavily MCP server connection + fallback
│   │
│   ├── guardrails/
│   │   ├── __init__.py
│   │   └── input_filter.py      # Injection detection + topic classifier
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI app factory
│   │   ├── routers/
│   │   │   ├── analyze.py       # POST /api/analyze + SSE stream
│   │   │   ├── search.py        # GET /api/search
│   │   │   └── feedback.py      # POST /api/feedback
│   │   ├── models.py            # Pydantic request/response schemas
│   │   └── middleware.py        # Rate limiting, CORS, logging
│   │
│   └── monitoring/
│       ├── __init__.py
│       └── tracer.py            # Langfuse integration wrapper
│
├── frontend/
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.ts
│   ├── src/
│   │   ├── main.tsx
│   │   ├── App.tsx
│   │   ├── components/
│   │   │   ├── AnalysisForm.tsx      # Building parameter input form
│   │   │   ├── AgentStatusPanel.tsx  # Real-time agent progress display
│   │   │   ├── ComplianceReport.tsx  # Structured findings output
│   │   │   ├── FindingCard.tsx       # Individual finding with citation
│   │   │   ├── Freshnessbadge.tsx    # CURRENT / AMENDED / UNVERIFIED badge
│   │   │   ├── FeedbackWidget.tsx    # Star rating + comment
│   │   │   └── SearchPanel.tsx       # Legacy keyword search
│   │   ├── store/
│   │   │   └── analysisStore.ts      # Zustand store
│   │   ├── hooks/
│   │   │   ├── useAnalysis.ts        # React Query mutation + SSE hook
│   │   │   └── useAgentStream.ts     # SSE agent progress stream
│   │   └── lib/
│   │       └── api.ts                # Typed API client
│   └── public/
│
└── tests/
    ├── conftest.py
    ├── test_positive.py          # Happy path scenarios
    ├── test_negative.py          # Edge cases, empty input, unknown location
    ├── test_adversarial.py       # Prompt injection, off-topic
    └── test_ragas_eval.py        # RAG quality evaluation
```

---

## 11. Risk Register & Mitigations

### R1 — Ingestion Time for 30K Documents
| | |
|---|---|
| **Risk** | Embedding 30K PDFs locally could take 8–24 hours and block development |
| **Probability** | HIGH |
| **Impact** | HIGH |
| **Mitigation** | **Phase ingestion:** Ingest a curated subset of 200–500 high-priority documents (fire safety, seismic, residential, structural) for demo. Full ingestion runs overnight in background. System is functional with partial index from Day 3. |
| **Fallback** | Demo uses 200 docs; note in presentation that full 30K corpus is being indexed |

### R2 — Poor Russian/Kazakh Retrieval Quality
| | |
|---|---|
| **Risk** | Wrong embedding model produces irrelevant search results for Cyrillic text |
| **Probability** | HIGH if wrong model chosen |
| **Impact** | CRITICAL — entire RAG pipeline fails |
| **Mitigation** | Use `BAAI/bge-m3` from Day 1. Do NOT use `all-MiniLM-L6-v2` (English-only). Validate retrieval quality on 10 known queries before full ingestion. |
| **Fallback** | `intfloat/multilingual-e5-large` as backup (also multilingual, slightly smaller) |

### R3 — LLM API Cost Overrun
| | |
|---|---|
| **Risk** | OpenAI API costs exceed budget during development and testing |
| **Probability** | MEDIUM |
| **Impact** | LOW-MEDIUM |
| **Mitigation** | **Use Ollama as default during development.** Switch to GPT-4o-mini only for final demo recording. Implement max_tokens limit (1500 per agent call). Estimated total cost for demo: < $3. |
| **Fallback** | 100% Ollama (Mistral-7B) mode — zero API cost |

### R4 — LangGraph Learning Curve
| | |
|---|---|
| **Risk** | LangGraph's StateGraph API is not trivial; debugging agent routing issues can consume 2–3 days |
| **Probability** | MEDIUM |
| **Impact** | HIGH |
| **Mitigation** | Use LangGraph's built-in visualization (`graph.get_graph().draw_mermaid_png()`). Start with a linear pipeline (no conditional routing) and add branching only after all agents work end-to-end. Use LangGraph's checkpoint API for debugging intermediate states. |
| **Fallback** | Simple sequential Python function calls (not true LangGraph) as emergency fallback — still demonstrates multi-agent concept |

### R5 — MCP Protocol Complexity
| | |
|---|---|
| **Risk** | MCP integration takes longer than expected; Tavily MCP server setup is non-trivial |
| **Probability** | MEDIUM |
| **Impact** | MEDIUM |
| **Mitigation** | Use Tavily's REST API as a simpler first implementation, then wrap it with an MCP client. The MCP "wrapper" approach still satisfies the protocol requirement while reducing implementation risk. Allocate Day 7 for this. |
| **Fallback** | Direct Tavily REST API call wrapped in an `MCPCompatibleClient` class that implements the MCP tool-calling interface |

### R6 — React Frontend Scope Creep
| | |
|---|---|
| **Risk** | Frontend development expands beyond budget; backend blocked by UI work |
| **Probability** | MEDIUM |
| **Impact** | MEDIUM |
| **Mitigation** | Use shadcn/ui pre-built components exclusively — no custom CSS components. Timebox frontend to Days 10–11 (2 days max). Backend must be fully functional and tested before frontend work begins. |
| **Fallback** | Use a minimal Streamlit UI for demo if React is not ready by Day 11 |

### R7 — PDF Parsing Quality
| | |
|---|---|
| **Risk** | Some regulatory PDFs are scanned images (no text layer), causing empty extraction |
| **Probability** | MEDIUM (regulatory docs vary in quality) |
| **Impact** | MEDIUM |
| **Mitigation** | Add OCR fallback using `pytesseract` for PDFs where PyMuPDF returns < 100 characters. Log all failed extractions for manual review. |
| **Fallback** | Skip unextractable files; log them in `data/failed_ingestion.txt` for transparency |

### R8 — 2-Week Timeline Compression
| | |
|---|---|
| **Risk** | Full system cannot be delivered in 14 days |
| **Probability** | MEDIUM |
| **Impact** | HIGH |
| **Mitigation** | Strict MVP scope: implement P0 features only in Week 1. P1 features and polish in Week 2. Use the phased plan below. Cut scope before cutting quality. |
| **Fallback** | Submit with partial frontend (Streamlit) and complete backend — backend quality counts more for the scoring rubric |

---

## 12. Out of Scope (This Version)

- BIM integration
- Drawing auto-check
- User authentication system (demo uses no-auth mode)
- Multi-tenancy
- Cloud deployment
- Real-time regulatory update subscriptions
- Mobile application
- Integration with derek-info.kz directly
- Support for non-Kazakhstan jurisdictions

---

## 13. Implementation Roadmap — 14-Day Sprint

### Week 1: Foundation (Days 1–7)

| Day | Focus | Deliverables | Hours |
|---|---|---|---|
| **Day 1** | Project setup | Repo, Docker Compose (Qdrant), venv, `requirements.txt`, `.env.example`, project structure created | 3h |
| **Day 2** | RAG ingestion pipeline | `parser.py`, `chunker.py`, `embedder.py`, `indexer.py`; demo corpus of 200 docs ingested and searchable | 6h |
| **Day 3** | Qdrant retriever + quality | `retriever.py`, `quality.py`; validate retrieval on 10 test queries; confidence threshold working | 4h |
| **Day 4** | Search Agent + LangGraph base | `state.py`, `orchestrator.py` skeleton, `search_agent.py`; end-to-end: query → RAG chunks | 5h |
| **Day 5** | Compliance Agent | `compliance_agent.py`; produces structured `ComplianceReport` from retrieved chunks | 5h |
| **Day 6** | Update Agent (MCP) | `tavily_client.py`, `update_agent.py`; freshness verdict for norm documents; fallback logic | 4h |
| **Day 7** | Explanation Agent + full pipeline | `explanation_agent.py`; full pipeline test end-to-end; Langfuse tracing connected | 4h |

**Week 1 Exit Criteria:** Full agent pipeline works end-to-end via Python REPL. All 4 agents functional with Langfuse traces visible.

### Week 2: Integration & Polish (Days 8–14)

| Day | Focus | Deliverables | Hours |
|---|---|---|---|
| **Day 8** | FastAPI backend | `main.py`, routers, Pydantic models, middleware, SSE endpoint; all API endpoints functional | 5h |
| **Day 9** | Guardrails + testing skeleton | `input_filter.py`; `test_positive.py`, `test_negative.py`, `test_adversarial.py` with first 4 test cases each | 4h |
| **Day 10** | React frontend — core | Vite scaffold, AnalysisForm, AgentStatusPanel (SSE), ComplianceReport components | 6h |
| **Day 11** | React frontend — polish | FindingCard, FreshnessBadge, FeedbackWidget, SearchPanel; TailwindCSS styling; responsive layout | 5h |
| **Day 12** | Full integration + bug fixes | Frontend ↔ Backend integration; end-to-end manual testing; bug fixes; complete test suite | 5h |
| **Day 13** | Documentation + RAGAS eval | README, BLUEPRINT.md, `.env.example`; RAGAS eval run; executive summary draft | 4h |
| **Day 14** | Demo recording + final polish | Demo script rehearsal; screen recording; 2–5 min demo video; final README review | 4h |

**Week 2 Exit Criteria:** Full system running locally; 8+ automated tests passing; demo video recorded; all deliverables complete.

---

## 14. Definition of Done

A feature is complete when:
1. Code is written and works end-to-end
2. At least one positive test case passes
3. At least one edge case is handled gracefully
4. Langfuse trace is visible for any LLM call
5. No credentials committed to git

---

## 15. Deliverables Checklist

| # | Deliverable | Criteria | Due |
|---|---|---|---|
| 1 | Architecture Blueprint | System diagram + tech stack table + data flow | Day 1 |
| 2 | Working Application | All 4 agents functional; demo-ready | Day 12 |
| 3 | Code Repository | GitHub repo; clean structure; README; BLUEPRINT.md | Day 13 |
| 4 | Test Suite | ≥ 8 test cases covering positive, negative, adversarial | Day 12 |
| 5 | Video Demo | 2–5 min; input → agents → report → test → code commentary | Day 14 |
| 6 | Executive Summary | 1–2 page PDF; problem, architecture, business value | Day 13 |

---

## 16. Scoring Strategy

| Category | Points | Strategy |
|---|---|---|
| Working Application | Base | MVP working by Day 7 (backend); full integration Day 12 |
| Code Delivery | Base | Clean structure from Day 1 using this PRD's project layout |
| LLM Behavior Tests | Base | 8 test cases defined; implemented Day 9 |
| Video Demo | Base | Recorded Day 14 using prepared demo script |
| **UX & Presentation** | **+10** | React + shadcn/ui; animated agent status panel; professional compliance report layout |
| **Data Quality** | **+10** | RAGAS evaluation output; curated 200-doc demo corpus with metadata validation; ingestion statistics |
| **Code Excellence** | **+10** | LangGraph state machine; Pydantic v2 models; proper separation of concerns; BLUEPRINT.md with trade-off justification |

---

*This PRD is the single source of truth for implementation. All development decisions should be validated against the requirements defined here.*
