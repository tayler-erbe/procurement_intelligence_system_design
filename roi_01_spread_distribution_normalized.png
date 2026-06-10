# Procurement Intelligence System Design

**End-to-end AI system for identifying cost-saving opportunities across multi-vendor purchasing catalogs.**

A three-tier pipeline that processes millions of catalog rows from multiple distributors using deterministic exact matching, FAISS semantic retrieval, and LLM equivalence reasoning with pack-size normalization. Includes a live price comparison tool and a leadership-facing spending intelligence dashboard.

**Portfolio case study:** [taylererbe.com/procurement-intelligence](https://terbe2022.github.io/tayler-portfolio/procurement-intelligence.html)  
**Medium article:** [Stop Throwing AI at Your Messy Data](https://medium.com/@tayler.erbe)

---

## What this repository contains

This is a **system design reference implementation** — the architecture, pipeline logic, API, and client interfaces. The data (6M+ catalog rows, FAISS index, parquet files) is not included and cannot be shared.

| File | Description |
|---|---|
| `BTAA_RAG_v1.ipynb` | Main RAG notebook — data loading, FAISS index, exact-match dict, LLM pipeline (Stages 11–19) |
| `btaa_api/main.py` | FastAPI service — 10 endpoints including three-tier compare, browse by category/manufacturer, trends |
| `btaa_api/requirements.txt` | Python dependencies |
| `demo.html` | Price comparison UI — search, browse by category, browse by manufacturer, auto-compare |
| `trends_dashboard.html` | Spending intelligence dashboard — 10 embedded spend analysis charts, savings filter, CSV export |
| `system_architecture.html` | Standalone system architecture diagram |
| `eval_set.json` | 30 hand-curated test queries with expected tier, price range, and alternatives |
| `eval_runner.py` | Evaluation grading script — runs against live API, produces pass rate report |
| `roi_0*.png` | Unit-normalized ROI charts |

---

## Core architecture

```
Multi-vendor catalog data (millions of rows)
           │
           ▼
┌─────────────────────────────┐
│  Preprocessing               │
│  - Unit normalization (qsu)  │
│  - Exact-match dict build    │
│  - FAISS vector index        │
└─────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────┐
│  Three-Tier Comparison Pipeline                          │
│                                                          │
│  Tier 1: Exact match (mfr + part#)  →  2ms, no AI       │
│  Tier 2: FAISS semantic retrieval   →  75–110ms          │
│  Tier 3: LLM equivalence reasoning  →  5–8s              │
│                                                          │
│  Degrades gracefully — Tier 1 always runs offline        │
└─────────────────────────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────┐
│  FastAPI service (10 endpoints) │
│  + HTML client interfaces    │
└─────────────────────────────┘
```

**The design principle:** lead with what is deterministic. Exact part-number matching requires no AI and produces the most defensible savings estimates. Semantic retrieval narrows millions of rows to ~20–40 candidates. The LLM only sees that small pre-screened set — it reasons, it does not search.

---

## Key metrics (reference implementation)

| Metric | Value |
|---|---|
| Catalog rows processed | 6,068,888 |
| Exact-matched product pairs | 42,052 |
| Defensible savings (unit-normalized) | $161,564 |
| Pack-size inflation removed from raw figure | 49.1% |
| Median unit-price spread | 20.7% |
| FAISS index size | 5.19M vectors, 8GB |
| Tier 1 latency | < 2ms |
| Tier 2 latency | 75–110ms |
| Tier 3 latency | 5–8s |

---

## Running the system

### Prerequisites

```bash
conda create -n procurement python=3.11
conda activate procurement
pip install -r btaa_api/requirements.txt
```

You will need:
- `parquet/unified.parquet` — your catalog data (build from source exports)
- `rag_index/catalog.index` — FAISS index (built by notebook Stage 11)
- `rag_index/catalog_meta.parquet` — vector metadata
- Ollama running locally with qwen2.5:7b

### Start Ollama (keep open)
```bash
ollama run qwen2.5:7b
# Wait for >>> prompt
```

### Start the API
```bash
uvicorn btaa_api.main:app --reload --port 8080
# Startup: ~5 min (loads data, builds browse index, indexes manufacturers)
# Watch for: Startup complete. Ready to serve requests.
```

### Open the tools
Double-click `demo.html` and `trends_dashboard.html` in any browser.

### Run the eval suite
```bash
python eval_runner.py
# Options:
# --category exact        (exact-match queries only)
# --category semantic     (semantic queries only)
# --out results.txt       (custom output path)
```

---

## Adapting to your data

The system expects a unified parquet file with these columns:

| Column | Description |
|---|---|
| `distributor` | Vendor name |
| `manufacturer` | Manufacturer name |
| `description` | Product description text |
| `price_num` | Numeric price |
| `dist_catalog_num` | Vendor catalog number |
| `manufacturer_part_num` | Manufacturer part number (enables exact matching) |
| `qsu` | Quantity sold as — used for unit price normalization |
| `qty` | Prior-year purchase quantity (enables savings estimates) |
| `category_desc` | UNSPSC or equivalent category label |

To build from your own vendor exports, adapt the EDA notebook (`Jaggaer_Data_EDA_v2.ipynb` equivalent) to normalize and merge your sources into this schema.

---

## LLM configuration

The system supports two LLM backends. Configure in `btaa_api/main.py`:

```python
# Local inference (Ollama)
OLLAMA_URL   = "http://localhost:11434/v1"
OLLAMA_MODEL = "qwen2.5:7b"

# Remote inference (NIM or any OpenAI-compatible endpoint)
NIM_URL   = "http://your-nim-server:8000/v1"
NIM_MODEL = "nvidia/nemotron-3-nano"
```

The API health-checks both at startup and uses whichever is online. Falls back gracefully to exact-match-only when no LLM is available.

For Azure deployment, replace with Azure OpenAI:
```python
OLLAMA_URL   = "https://your-resource.openai.azure.com/openai/deployments/gpt-4o-mini/v1"
OLLAMA_MODEL = "gpt-4o-mini"
```

---

## Production deployment (Azure)

| Component | Service | Est. cost/month |
|---|---|---|
| FastAPI app | App Service B3 (8GB RAM min) | ~$75 |
| FAISS index + parquet | Blob Storage 10GB | ~$0.20 |
| LLM | Azure OpenAI gpt-4o-mini | ~$2 |
| **Total** | | **~$77/month** |

---

## Technical decisions

| Decision | Chosen | Rationale |
|---|---|---|
| Embedding model | bge-small-en-v1.5 (384-dim) | 8GB index vs 32GB for large variant; quality comparable |
| FAISS threshold | cos ≥ 0.85 | Median 44 candidates, max 137 — safe LLM context budget |
| LLM | qwen2.5:7b | 4/4 correctness, 4/4 consistency on domain eval set |
| Savings baseline | User-selected product | Anchors to real price, eliminates pack-size ambiguity |
| Unit price | price / qsu | 99.9% field coverage; removes pack-size inflation |
| Browse pre-indexing | Startup-time (adds ~30s) | Makes all browse operations instant |

---

## Author

**Tayler Erbe** — Data Scientist  
[taylererbe.com](https://terbe2022.github.io/tayler-portfolio/) · [LinkedIn](https://linkedin.com/in/tayler-erbe-194374141) · [Medium](https://medium.com/@tayler.erbe)
