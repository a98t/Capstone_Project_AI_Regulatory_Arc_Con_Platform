# DEREK-AI — AI-Powered Regulatory Intelligence System

> Capstone Project · EPAM AI/ML Course 2026  
> Kazakhstan Construction Norm Compliance Assistant
> Anet Tatygulov

## Overview

DEREK-AI platform transforms keyword search over 27 000 documents into an AI-first compliance assistant. Given a building description it runs a multi-agent LangGraph pipeline that:

1. **Searches** ~450 000 vector chunks (bge-m3 embeddings, Qdrant)  
2. **Analyses** compliance against СНиП / СП / ҚНжЕ / СТ РК norms  
3. **Verifies** norm freshness via Tavily MCP tool  
4. **Explains** findings in plain professional Russian/English  

---

## Quick Start

### Prerequisites
- Python 3.12+
- Docker + Docker Compose
- Node.js 18+ (for frontend)
- OpenAI API key (`LLM_PROVIDER=openai` — default)
- Optional: Tavily API key for MCP norm freshness verification

### 1. Clone & configure

```bash
git clone https://github.com/a98t/Capstone_Project_AI_Regulatory_Arc_Con_Platform
cd Capstone_Project_AI_Regulatory_Arc_Con_Platform
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
# Place PDF, DOCX, or TXT files in data/regulations/
python scripts/ingest.py --dir data/regulations

# Check index status
python scripts/check_index.py
```

### 5. Start the backend

```bash
# Windows (PowerShell)
$env:PYTHONPATH = "."; uvicorn src.api.main:app --host 0.0.0.0 --port 8001 --reload

# Linux / macOS
PYTHONPATH=. uvicorn src.api.main:app --host 0.0.0.0 --port 8001 --reload
```

API docs: http://localhost:8001/docs

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
FastAPI (port 8001)
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

---

## Regulatory Documents

The current knowledge base contains **13 official Kazakhstan construction regulations** indexed from `data/regulations/`. All documents are sourced in **Russian language only**.

> **Language note:** Each regulation is officially published in both Kazakh (Қазақша) and Russian (Русский). For this version of DEREK-AI, only the Russian-language text was used for ingestion and retrieval. Adding the Kazakh-language variant is planned as a future expansion of the platform.

### СП РК — Свод правил (Building Codes)

| Document ID | Title |
|---|---|
| СП РК 2.02-101-2022 | Пожарная безопасность зданий и сооружений *(Fire Safety of Buildings and Structures)* |
| СП РК 2.03-30-2017 | Строительство в сейсмических зонах *(Construction in Seismic Zones)* |
| СП РК 3.02-101-2012 | Здания жилые многоквартирные *(Multi-Apartment Residential Buildings)* |
| СП РК 3.02-107-2014 | Общественные здания и сооружения *(Public Buildings and Structures)* |
| СП РК 3.06-101-2012 | Проектирование зданий и сооружений с учётом доступности для маломобильных групп населения *(Accessibility Design for Persons with Reduced Mobility)* |
| СП РК 4.01-101-2012 | Внутренний водопровод и канализация зданий и сооружений *(Internal Water Supply and Drainage)* |
| СП РК 4.01-103-2013 | Наружные сети и сооружения водоснабжения и канализации *(External Water Supply and Sewerage Networks)* |
| СП РК 4.02-101-2012 | Отопление, вентиляция и кондиционирование воздуха *(Heating, Ventilation and Air Conditioning)* |
| СП РК 4.04-106-2013 | Электрооборудование жилых и общественных зданий. Правила проектирования *(Electrical Equipment of Residential and Public Buildings)* |

### СН РК — Строительные нормы (Construction Standards)

| Document ID | Title |
|---|---|
| СН РК 3.01-01-2013 | Градостроительство. Планировка и застройка городских и сельских населённых пунктов *(Urban Planning. Layout and Development of Urban and Rural Settlements)* |
| СН РК 3.01-02-2012 | Планировка и застройка районов индивидуального жилищного строительства *(Planning and Development of Individual Housing Construction Areas)* |
| СН РК 3.01-03-2011 | Генеральные планы промышленных предприятий *(General Plans of Industrial Enterprises)* |
| СН РК 3.01-05-2013 | Благоустройство территорий населённых пунктов *(Landscaping and Improvement of Settlement Territories)* |

---

## Example Prompts

The system accepts natural language queries in English, Russian, and Kazakh. Below are 10 realistic professional examples:

### English

1. **Mixed-use high-rise, Almaty**
   > "We are designing a 22-storey mixed-use tower in Almaty with retail on floors 1–3, offices on floors 4–15, and residential apartments on floors 16–22. The structural system is reinforced concrete with a curtain-wall façade. Please assess compliance with fire safety, seismic, accessibility, and MEP requirements."

2. **Industrial warehouse, Karaganda**
   > "A single-storey prefabricated steel warehouse of 8 500 m² net area is planned in the Karaganda industrial zone. The facility will store non-hazardous dry goods. Provide a compliance review covering fire safety compartmentation, natural ventilation requirements, and site drainage standards."

3. **Public school extension, Astana**
   > "An existing 3-storey public school in Astana requires a new 2-storey classroom wing of approximately 1 200 m². Structural material is brick masonry. Identify all applicable СП РК and СН РК requirements for educational facilities, including accessibility, fire evacuation routes, and HVAC."

### Russian

4. **Жилой многоквартирный дом, Алматы**
   > «Планируется строительство 9-этажного жилого дома в Алматы из монолитного железобетона общей площадью 12 000 м². Здание расположено в сейсмической зоне 8 баллов. Проведите анализ соответствия нормативным требованиям по сейсмостойкости, пожарной безопасности, доступности для маломобильных групп и инженерным системам.»

5. **Торговый центр, Астана**
   > «Проектируется трёхэтажный торгово-развлекательный центр площадью 35 000 м² в Астане. Конструктивная схема — стальной каркас с навесным фасадом. Требуется оценка соответствия СП РК по пожарной безопасности, эвакуационным выходам, вентиляции и электрооборудованию.»

6. **Офисное здание, Шымкент**
   > «Пятиэтажное офисное здание класса B+ из сборного железобетона, общая площадь 6 500 м², г. Шымкент. Здание предназначено для размещения 400 рабочих мест. Проверьте соответствие нормам по водоснабжению, канализации, отоплению и вентиляции, а также требованиям доступности.»

7. **Индивидуальный жилой дом, Актобе**
   > «Проектирование двухэтажного индивидуального жилого дома из кирпича площадью 280 м² в г. Актобе. Участок находится в зоне умеренной сейсмичности. Необходим анализ требований СН РК по планировке территории, СП РК по пожарной безопасности и инженерным коммуникациям.»

8. **Спортивный комплекс, Атырау**
   > «Одноэтажный крытый спортивный комплекс площадью 4 200 м² с плавательным бассейном в г. Атырау. Конструкция — металлические фермы с сэндвич-панелями. Оцените требования по пожарной безопасности, вентиляции бассейна, водоснабжению и обеспечению доступности.»

### Kazakh

9. **Тұрғын үй кешені, Алматы**
   > «Алматы қаласында 14 қабатты тұрғын үй кешені жоспарлануда, жалпы ауданы 18 000 м², монолитті темірбетон конструкциясы. Ғимарат 8 балдық сейсмикалық аймақта орналасқан. Өрт қауіпсіздігі, сейсмикалық тұрақтылық, қолжетімділік және инженерлік жүйелер бойынша СП РК және СН РК нормаларының сақталуын тексеріңіз.»

10. **Әкімшілік ғимарат, Астана**
    > «Астана қаласында болат каркасты 6 қабатты әкімшілік ғимарат салу жоспарлануда, жалпы ауданы 9 000 м². Ғимаратта 600 жұмысшы орналасады. Су жабдықтау, кәріз, жылыту, желдету және электр жабдықтары бойынша СП РК нормаларының талаптарын, сондай-ақ мүмкіндігі шектеулі адамдарға арналған қолжетімділік талаптарын бағалаңыз.»
