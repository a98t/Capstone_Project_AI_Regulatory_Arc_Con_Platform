# Executive Summary

## DEREK-AI: AI-Powered Regulatory Intelligence System for Kazakhstan's Construction Industry

**Student:** Anet Tatygulov  
**Course:** EPAM Generative AI for Software Development  
**Submission Date:** 18 May 2026  
**Repository:** https://github.com/a98t/Capstone_Project_AI_Regulatory_Arc_Con_Platform

---

## The Problem

Kazakhstan's construction industry requires professionals to manually cross-reference 5–15 regulatory documents (СНиП, СП РК, ҚНжЕ, СТ РК) for every project compliance check. This process takes **2–6 hours per project**, introduces human interpretation errors, and relies on static keyword search portals that cannot determine whether referenced norms are still in force.

A missed or outdated norm in construction documentation leads to project rejections, redesigns, and in the worst case — structural safety risks.

---

## The Solution: DEREK-AI

DEREK-AI transforms a natural-language building description into a structured compliance report in under 30 seconds. The system combines:

- **Semantic RAG retrieval** over Kazakhstan construction norms embedded with a multilingual model (`BAAI/bge-m3`) that handles Russian, Kazakh, and English
- **4-agent LangGraph pipeline** that searches, analyses, verifies, and explains in sequence
- **Live norm freshness verification** via Tavily MCP — checks official Kazakhstan government portals (`adilet.zan.kz`, `online.zakon.kz`) to flag amended or superseded documents
- **Polished React frontend** for architects and engineers to use without any technical setup

---

## Architecture Highlights

```
User: "9-floor residential building, Almaty, reinforced concrete"
                       │
              ┌────────▼─────────┐
              │  FastAPI Backend  │  (guardrails, rate limiting)
              └────────┬─────────┘
                       │
         ┌─────────────▼──────────────┐
         │   LangGraph StateGraph     │
         │                            │
         │  SearchAgent               │  ← Qdrant RAG, bge-m3 embeddings
         │      ↓                     │
         │  ComplianceAgent           │  ← GPT-4o-mini / Mistral-7B
         │      ↓                     │
         │  UpdateAgent               │  ← Tavily MCP tool server
         │      ↓                     │
         │  ExplanationAgent          │  ← Plain Russian/English output
         └────────────────────────────┘
                       │
              ┌────────▼─────────┐
              │   React 18 UI    │  (TailwindCSS, live agent status)
              └──────────────────┘
```

**Key technology decisions with rationale are documented in [`MDS/DECISIONS.md`](../MDS/DECISIONS.md) (7 Architecture Decision Records).**

---

## Results and Validation

| Metric | Result |
|---|---|
| Test suite | **33 tests pass** — positive, negative, adversarial, edge cases |
| Injection detection | **100%** of adversarial prompts blocked by guardrail layer |
| RAG retrieval | Semantic search with bge-m3 (1024-dim, multilingual), confidence threshold 0.60 |
| Compliance report generation | Structured JSON with article citations, risk level, violation flags |
| Norm freshness | MCP-verified via Tavily when key configured; graceful fallback to UNVERIFIED |
| Frontend build | Production build: 152 modules, zero errors |
| Document ingestion | Supports PDF, DOCX, and TXT; article-aware chunking preserves regulatory structure |

---

## Business Value

**For architects and engineers:**  
A compliance check that took 2–6 hours now takes 30 seconds, with full source citations and plain-language explanations of complex regulatory requirements.

**For construction companies:**  
Reduced risk of project rejection due to missed or outdated norm references. The system flags when a cited norm has been amended, which is not possible with any current Kazakhstan regulatory portal.

**For regulatory bodies:**  
A reference implementation showing how Kazakhstan's 30,000+ normative document corpus can be made AI-searchable with full traceability and source attribution.

---

## Scope and Constraints

- **Data:** Production corpus requires the full set of Kazakhstan construction norms (the system is designed and tested; document ingestion is operational for PDF, DOCX, and TXT formats)
- **LLM cost:** System runs entirely locally via Ollama (Mistral-7B); OpenAI GPT-4o-mini is an optional upgrade for higher-quality outputs
- **MCP:** Requires a free Tavily API key (1,000 searches/month on free tier)
- **Deployment:** Currently localhost; production deployment would add Nginx reverse proxy and Docker Compose orchestration

---

## What Was Built

| Component | Status |
|---|---|
| 4-agent LangGraph pipeline | ✅ Complete |
| RAG pipeline (Qdrant + bge-m3) | ✅ Complete |
| MCP integration (Tavily) | ✅ Complete (graceful fallback when key not set) |
| React frontend with live agent status | ✅ Complete |
| FastAPI backend with guardrails | ✅ Complete |
| Ingestion pipeline (PDF, DOCX, TXT) | ✅ Complete |
| Test suite (33 tests) | ✅ Complete |
| Architecture Decision Records (7 ADRs) | ✅ Complete |
| User feedback system | ✅ Complete |
| Observability (Langfuse tracing) | ✅ Complete |

---

*"Regulatory intelligence that took hours now takes seconds — with full traceability to the original norm."*
