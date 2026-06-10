"""
BTAA Procurement Search API
FastAPI wrapper around the ask_procurement() pipeline from BTAA_RAG_v1.ipynb.

Run:
    cd <notebook directory>
    uvicorn btaa_api.main:app --reload --port 8080

Or from this file's directory:
    uvicorn main:app --reload --port 8080

Prereqs: unified.parquet, rag_index/catalog.index, rag_index/catalog_meta.parquet
must all exist (built by BTAA_RAG_v1.ipynb Stages 11-12).
"""

import sys, time, json, hashlib, gc, warnings
from pathlib import Path
from contextlib import asynccontextmanager
from typing import Optional

import numpy as np
import pandas as pd
import requests as http_requests
import faiss
from sentence_transformers import SentenceTransformer
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

warnings.filterwarnings("ignore")

# ---------------------------------------------------------------------------
# Paths - adjust if api/ is not a sibling of parquet/ and rag_index/
# ---------------------------------------------------------------------------
BASE_DIR   = Path(__file__).parent.parent   # one level up from btaa_api/
PARQUET_DIR = BASE_DIR / "parquet"
INDEX_DIR   = BASE_DIR / "rag_index"
OUTPUT_DIR  = BASE_DIR / "analysis_output"
OUTPUT_DIR.mkdir(exist_ok=True)

INDEX_PATH = INDEX_DIR / "catalog.index"
META_PATH  = INDEX_DIR / "catalog_meta.parquet"

# ---------------------------------------------------------------------------
# LLM config (same as notebook)
# ---------------------------------------------------------------------------
OLLAMA_URL   = "http://localhost:11434/v1"
OLLAMA_MODEL = "qwen2.5:7b"
NIM_URL      = "http://your-nim-server:8000/v1"  # Replace with your NIM endpoint
NIM_MODEL    = "nvidia/nemotron-3-nano"

EMB_MODEL_NAME   = "BAAI/bge-small-en-v1.5"
BGE_QUERY_PREFIX = "Represent this sentence for searching relevant passages: "
COSINE_THRESHOLD = 0.85

SYSTEM_PROMPT = """\
You are a procurement assistant for a university research lab.
You receive a list of candidate products from a catalog database.
Your job:
1. Identify which candidates are equivalent (same physical product or interchangeable).
2. For equivalent products, find the cheapest price across distributors.
3. Return your answer as JSON only - no preamble, no explanation, just the JSON object.

Output schema (strict):
{
  "best": {
    "distributor": str,
    "manufacturer": str,
    "description": str,
    "price": float,
    "catalog_num": str
  },
  "alternatives": [
    {"distributor": str, "price": float, "description": str}
  ],
  "savings_vs_worst": float,
  "n_equivalent": int,
  "reasoning": str
}

Equivalence rules - a candidate is ONLY equivalent if ALL of these are true:
- PRODUCT TYPE matches the query exactly. If the query asks for a vial, return vials only.
  A cap, lid, adapter, or accessory is NOT equivalent to the product it fits.
  A pipette tip is NOT equivalent to a pipette. A flask is NOT equivalent to a plate.
- VOLUME / SIZE matches. A 5 mL pipette is not equivalent to a 10 mL pipette.
  A 1000 uL tip is not equivalent to a 200 uL tip.
- PACK SIZE: do NOT list different pack sizes as alternatives to each other.
  If comparing prices across pack sizes, normalize to per-unit price first.
  Only compare products at the same pack size as alternatives.
- MATERIAL matches when specified. Polystyrene and glass are not interchangeable.

If fewer than 2 genuinely equivalent products are found after applying these rules,
set alternatives to [] and savings_vs_worst to 0.
Price values must be numeric (no dollar signs).
"""

LLM_CACHE_PATH = OUTPUT_DIR / "llm_cache_api.json"

# ---------------------------------------------------------------------------
# App state (loaded once at startup)
# ---------------------------------------------------------------------------
state = {}


def _to_float(v):
    if pd.isna(v): return float("nan")
    if isinstance(v, (int, float)): return float(v)
    s = str(v).replace("$", "").replace(",", "").strip()
    try: return float(s)
    except: return float("nan")


def _to_qty(v):
    try: return float(str(v).replace(",", "").strip())
    except: return np.nan


def _norm_key(s):
    if pd.isna(s): return None
    return str(s).strip().upper()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load all heavy assets once at startup."""
    print("=" * 60)
    print("BTAA Procurement API - starting up")
    print("=" * 60)

    # --- check index exists ---
    if not INDEX_PATH.exists() or not META_PATH.exists():
        print("ERROR: FAISS index not found.")
        print(f"  Expected: {INDEX_PATH}")
        print("  Run BTAA_RAG_v1.ipynb Stage 11 first to build the index.")
        state["ready"] = False
        yield
        return

    # --- load parquet ---
    print("Loading unified.parquet...")
    t0 = time.time()
    df = pd.read_parquet(PARQUET_DIR / "unified.parquet")
    df["price_num"] = df["price"].apply(_to_float)
    df["qty_num"]   = df["quantity"].apply(_to_qty)
    print(f"  {len(df):,} rows in {time.time()-t0:.1f}s")
    state["df"] = df

    # --- build exact-match table ---
    print("Building exact-match table...")
    keyed = df[
        df["manufacturer"].notna() &
        df["mfr_part_num"].notna() &
        (df["price_num"] > 0) &
        (df["price_num"] < 10_000_000)
    ].copy()
    keyed["mfr_key"]  = keyed["manufacturer"].apply(_norm_key)
    keyed["part_key"] = keyed["mfr_part_num"].apply(_norm_key)
    keyed = keyed[keyed["mfr_key"].notna() & keyed["part_key"].notna()]
    exact_table = (
        keyed
        .groupby(["mfr_key", "part_key", "distributor"], as_index=False)
        .agg(price=("price_num", "min"),
             description=("description", "first"),
             manufacturer=("manufacturer", "first"),
             dist_catalog_num=("dist_catalog_num", "first"),
             qty=("qty_num", "max"))
    )
    span = exact_table.groupby(["mfr_key", "part_key"])["distributor"].nunique()
    state["exact_table"] = exact_table
    state["multi_keys"]  = set(span[span >= 2].index.tolist())

    # Build O(1) dict using itertuples - avoids slow groupby loop (~2 min vs 45 min)
    print("  Building exact_dict (fast)...")
    t_dict = time.time()
    cols = ["mfr_key","part_key","distributor","price","description","manufacturer","dist_catalog_num","qty"]
    sorted_table = exact_table.sort_values(["mfr_key","part_key","price"])
    exact_dict = {}
    for row in sorted_table[cols].itertuples(index=False):
        key = (row.mfr_key, row.part_key)
        rec = {
            "mfr_key": row.mfr_key, "part_key": row.part_key,
            "distributor": row.distributor, "price": row.price,
            "description": row.description, "manufacturer": row.manufacturer,
            "dist_catalog_num": row.dist_catalog_num, "qty": row.qty,
        }
        if key not in exact_dict:
            exact_dict[key] = []
        exact_dict[key].append(rec)
    state["exact_dict"] = exact_dict
    print(f"  {len(state['multi_keys']):,} cross-distributor matches | dict built in {time.time()-t_dict:.1f}s")

    # --- load FAISS index ---
    print("Loading FAISS index...")
    t0 = time.time()
    index = faiss.read_index(str(INDEX_PATH))
    index.nprobe = 64
    state["index"] = index
    state["meta"]  = pd.read_parquet(META_PATH)
    print(f"  {index.ntotal:,} vectors in {time.time()-t0:.1f}s")

    # --- load embedding model ---
    import torch
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Loading embedding model on {device}...")
    state["emb_model"] = SentenceTransformer(EMB_MODEL_NAME, device=device)
    state["device"]    = device

    # --- check LLM endpoints ---
    active = _find_active_endpoint()
    state["active_endpoint"] = active
    if active:
        print(f"LLM endpoint: {active[2]} ONLINE")
    else:
        print("WARNING: No LLM endpoint online. Semantic tier will return candidates only.")

    # Pre-index browse categories for instant lookup
    print("Pre-indexing browse categories...")
    t_browse = time.time()
    import re as _re
    browse_index = {}
    df_desc = state["df"]["description"].fillna("").str.lower()
    df_dist = state["df"]["distributor"]
    df_mfr  = state["df"]["manufacturer"].fillna("")
    df_prc  = state["df"]["price_num"].fillna(0)
    df_cat  = state["df"].get("category_desc", pd.Series([""] * len(state["df"]))).fillna("")
    df_cnum = state["df"]["dist_catalog_num"].fillna("")

    for cat, subs in TAXONOMY.items():
        browse_index[cat] = {}
        for sub, terms in subs.items():
            pattern = "|".join(_re.escape(t) for t in terms)
            mask = df_desc.str.contains(pattern, na=False) & (df_prc > 0)
            idx_rows = state["df"][mask].copy()
            # Sort by price, keep top 200 per subcategory
            idx_rows = idx_rows.sort_values("price_num").head(200)
            browse_index[cat][sub] = idx_rows.index.tolist()

    state["browse_index"] = browse_index
    state["df_full"] = state["df"]  # keep reference
    print(f"  Browse index built in {time.time()-t_browse:.1f}s")

    # Pre-index manufacturer list for autocomplete
    print("Pre-indexing manufacturers...")
    mfr_counts = state["df"]["manufacturer"].dropna().value_counts()
    state["mfr_list"] = [(str(m), int(c)) for m, c in mfr_counts.head(5000).items()]
    print(f"  {len(state['mfr_list'])} manufacturers indexed")

    state["ready"] = True
    print("Startup complete. Ready to serve requests.\n")
    yield

    # --- shutdown ---
    print("Shutting down.")
    state.clear()
    gc.collect()


def _find_active_endpoint():
    for url, model, name in [
        (OLLAMA_URL, OLLAMA_MODEL, "Ollama/qwen2.5:7b"),
        (NIM_URL,    NIM_MODEL,    "NIM/nemotron-3-nano"),
    ]:
        try:
            r = http_requests.post(
                url.rstrip("/") + "/chat/completions",
                json={"model": model,
                      "messages": [{"role": "user", "content": "ping"}],
                      "max_tokens": 5},
                timeout=5
            )
            if r.status_code == 200:
                return (url, model, name)
        except Exception:
            continue
    return None


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------
app = FastAPI(
    title="BTAA Procurement Search",
    description="Cross-distributor price comparison for UIUC lab supplies",
    version="1.0.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Core pipeline helpers (mirrors notebook functions exactly)
# ---------------------------------------------------------------------------

def _embed_query(text: str) -> np.ndarray:
    v = state["emb_model"].encode(
        [BGE_QUERY_PREFIX + text], normalize_embeddings=True
    )
    return np.asarray(v, dtype="float32")


def _search_exact(mfr: str, part_num: str) -> pd.DataFrame:
    if not mfr or not part_num:
        return pd.DataFrame()
    mk = _norm_key(mfr)
    pk = _norm_key(part_num)
    rows = state.get("exact_dict", {}).get((mk, pk), [])
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows)  # already sorted by price at build time


def _search_semantic(query: str, max_candidates: int = 150) -> pd.DataFrame:
    qv = _embed_query(query)
    lims, sims_flat, ids_flat = state["index"].range_search(qv, COSINE_THRESHOLD)
    n_hits = int(lims[1] - lims[0])
    if n_hits == 0:
        return pd.DataFrame()
    sims = sims_flat[lims[0]:lims[1]]
    ids  = ids_flat[lims[0]:lims[1]]
    order = np.argsort(-sims)
    sims  = sims[order][:max_candidates]
    ids   = ids[order][:max_candidates]
    result = state["meta"].iloc[ids].copy()
    result.insert(0, "cosine", sims)
    return result.reset_index(drop=True)


def _prompt_hash(sys_p, usr_p):
    return hashlib.sha256(f"{sys_p}|||{usr_p}".encode()).hexdigest()[:16]


def _call_llm(user_prompt: str) -> dict:
    ep = state.get("active_endpoint")
    if not ep:
        return {"content": None, "elapsed": 0, "error": "No LLM endpoint"}
    url, model, _ = ep
    cache = {}
    if LLM_CACHE_PATH.exists():
        try: cache = json.load(open(LLM_CACHE_PATH, encoding="utf-8"))
        except: pass
    key = _prompt_hash(SYSTEM_PROMPT, user_prompt)
    if key in cache:
        return {"content": cache[key], "elapsed": 0, "cached": True, "error": None}
    t0 = time.time()
    try:
        resp = http_requests.post(
            url.rstrip("/") + "/chat/completions",
            json={"model": model,
                  "messages": [{"role": "system", "content": SYSTEM_PROMPT},
                                {"role": "user",   "content": user_prompt}],
                  "max_tokens": 800, "temperature": 0.1},
            timeout=90
        )
        resp.raise_for_status()
        content = resp.json()["choices"][0]["message"]["content"]
        elapsed = time.time() - t0
        if content and content.strip():
            cache[key] = content
            json.dump(cache, open(LLM_CACHE_PATH, "w", encoding="utf-8"), indent=2)
        return {"content": content, "elapsed": elapsed, "cached": False, "error": None}
    except Exception as e:
        return {"content": None, "elapsed": time.time()-t0, "cached": False, "error": str(e)}


def _parse_llm_json(content: str):
    if not content: return None
    clean = content.strip()
    if "```" in clean:
        for p in clean.split("```"):
            p = p.strip().lstrip("json").strip()
            if p.startswith("{"): clean = p; break
    start, end = clean.find("{"), clean.rfind("}")
    if start == -1 or end == -1: return None
    try: return json.loads(clean[start:end+1])
    except: return None


def _format_candidates(candidates: pd.DataFrame, query: str) -> str:
    lines = [f"USER QUERY: {query}\n", "CANDIDATE PRODUCTS:"]
    for i, (_, r) in enumerate(candidates.head(100).iterrows(), 1):
        price = r.get("price_num", r.get("price", 0))
        cat_num = r.get("dist_catalog_num", "")
        lines.append(
            f"{i:3d}. [{r['distributor']:5s}] "
            f"${float(price) if price else 0:<10.2f} "
            f"MFR:{str(r['manufacturer'])[:30]:<32} "
            f"CAT:{str(cat_num)[:20]:<22} "
            f"{str(r['description'])[:90]}"
        )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class SearchRequest(BaseModel):
    query: str
    manufacturer: Optional[str] = None
    part_number: Optional[str] = None


class ProductResult(BaseModel):
    distributor: str
    manufacturer: str
    description: str
    price: float
    catalog_num: str = ""


class SearchResponse(BaseModel):
    query: str
    tier: str                        # "exact" | "semantic" | "no_results"
    best: Optional[ProductResult]
    alternatives: list
    savings_vs_worst: float
    candidates_returned: int
    llm_endpoint: Optional[str]
    elapsed_ms: int
    reasoning: str = ""


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/health")
def health():
    ep = state.get("active_endpoint")
    return {
        "status": "ok" if state.get("ready") else "not_ready",
        "index_vectors": state["index"].ntotal if state.get("index") else 0,
        "exact_match_keys": len(state.get("multi_keys", [])),
        "llm_endpoint": ep[2] if ep else None,
        "embedding_device": state.get("device", "unknown"),
    }


@app.get("/trends")
def trends():
    """
    Returns live ROI and spending trend data for the dashboard.
    Uses unit_normalized_savings.parquet when available (unit prices),
    falls back to live computation from df if not found.
    """
    if not state.get("ready"):
        raise HTTPException(503, "Server not ready")

    import numpy as np

    df      = state["df"]
    NORM_PATH = Path("analysis_output/unit_normalized_savings.parquet")

    # ── Try to load pre-computed unit-normalized savings ──────────────────────
    if NORM_PATH.exists():
        try:
            agg_u = pd.read_parquet(NORM_PATH)
            # Validate expected columns
            needed = ["unit_spread_pct","est_savings_unit","min_unit","max_unit",
                      "max_qty_sold","desc","manufacturer"]
            if all(c in agg_u.columns for c in needed):
                source = "unit_normalized"
            else:
                agg_u  = None
                source = "live_raw"
        except Exception:
            agg_u  = None
            source = "live_raw"
    else:
        agg_u  = None
        source = "live_raw"

    # ── Fall back: compute live from df (raw prices) ──────────────────────────
    if agg_u is None:
        exact_table = state["exact_table"]
        multi_keys  = state["multi_keys"]
        span = exact_table.groupby(["mfr_key","part_key"])["distributor"].nunique()
        multi_idx = span[span >= 2].index
        m = exact_table.set_index(["mfr_key","part_key"]).loc[multi_idx].reset_index()
        agg_u = (
            m.groupby(["mfr_key","part_key"])
             .agg(n_dist=("distributor","nunique"),
                  min_unit=("price","min"),
                  max_unit=("price","max"),
                  max_qty_sold=("qty","max"),
                  desc=("description","first"),
                  manufacturer=("manufacturer","first"))
             .reset_index()
        )
        agg_u["unit_spread"]     = agg_u["max_unit"] - agg_u["min_unit"]
        agg_u["unit_spread_pct"] = (100*(agg_u["unit_spread"]/agg_u["max_unit"])).round(2)
        agg_u["est_savings_unit"]= agg_u["unit_spread"] * agg_u["max_qty_sold"].fillna(0)
        source = "live_raw"

    # ── Build response ────────────────────────────────────────────────────────
    dist_counts = df["distributor"].value_counts().to_dict()
    has_sales   = {"DOT": True, "Neta": True, "Fisher": False, "VWR": False}
    has_parts   = {"DOT": True, "Neta": True, "Fisher": False, "VWR": True}
    distributors = [
        {"name": d, "rows": int(dist_counts.get(d,0)),
         "has_sales": has_sales.get(d,False),
         "has_parts": has_parts.get(d,False)}
        for d in ["Neta","VWR","Fisher","DOT"]
    ]

    spread_data = agg_u[agg_u["unit_spread_pct"] > 0]["unit_spread_pct"]
    total_savings = float(agg_u["est_savings_unit"].sum())

    # Top 25 by unit savings
    top25 = agg_u[agg_u["est_savings_unit"] > 0].nlargest(25,"est_savings_unit")
    top25_list = []
    for _, r in top25.iterrows():
        top25_list.append({
            "desc":        str(r["desc"])[:120],
            "manufacturer":str(r.get("manufacturer",""))[:40],
            "spread_pct":  round(float(r["unit_spread_pct"]),1),
            "min_price":   round(float(r["min_unit"]),2),
            "max_price":   round(float(r["max_unit"]),2),
            "qty":         int(r["max_qty_sold"]) if not np.isnan(r.get("max_qty_sold",float("nan"))) else None,
            "est_savings": round(float(r["est_savings_unit"]),0),
        })

    # Top 10 high spread no qty
    no_qty = agg_u[agg_u["max_qty_sold"].isna() | (agg_u["max_qty_sold"]==0)]
    top_spread_list = []
    for _, r in no_qty.nlargest(10,"unit_spread").iterrows():
        top_spread_list.append({
            "desc":      str(r["desc"])[:120],
            "spread":    round(float(r["unit_spread"]),2),
            "spread_pct":round(float(r["unit_spread_pct"]),1),
            "min_price": round(float(r["min_unit"]),2),
            "max_price": round(float(r["max_unit"]),2),
        })

    # Histogram
    buckets = [0,10,20,30,40,50,60,75,90,100]
    bucket_labels = [f"{buckets[i]}-{buckets[i+1]}%" for i in range(len(buckets)-1)]
    bucket_counts = [
        int(((spread_data>=buckets[i])&(spread_data<buckets[i+1])).sum())
        for i in range(len(buckets)-1)
    ]

    return {
        "total_rows":        int(len(df)),
        "matched_keys":      int(len(state.get("multi_keys",[]))),
        "est_savings":       round(total_savings,0),
        "median_spread_pct": round(float(spread_data.median()),1),
        "mean_spread_pct":   round(float(spread_data.mean()),1),
        "no_qty_keys":       int(len(agg_u[agg_u["max_qty_sold"].isna()])),
        "unit_normalized":   source == "unit_normalized",
        "distributors":      distributors,
        "top25":             top25_list,
        "high_spread_no_qty":top_spread_list,
        "spread_histogram":  {"labels":bucket_labels,"counts":bucket_counts},
    }


@app.post("/search", response_model=SearchResponse)
def search(req: SearchRequest):
    if not state.get("ready"):
        raise HTTPException(503, "Server not ready - index may still be building")

    t_start = time.time()
    q       = req.query.strip()
    if not q:
        raise HTTPException(400, "Query cannot be empty")

    # --- Tier 1: exact match ---
    tier = "semantic"
    candidates = pd.DataFrame()
    if req.manufacturer and req.part_number:
        exact = _search_exact(req.manufacturer, req.part_number)
        if len(exact) >= 2:
            tier       = "exact"
            candidates = exact

    # --- Tier 2: semantic ---
    if tier == "semantic":
        candidates = _search_semantic(q)

    if len(candidates) == 0:
        return SearchResponse(
            query=q, tier="no_results", best=None,
            alternatives=[], savings_vs_worst=0,
            candidates_returned=0, llm_endpoint=None,
            elapsed_ms=int((time.time()-t_start)*1000)
        )

    ep      = state.get("active_endpoint")
    ep_name = ep[2] if ep else None

    # --- exact: no LLM needed ---
    if tier == "exact":
        best_row = candidates.iloc[0]
        savings  = float(candidates["price"].max() - best_row["price"])
        alts = [
            {"distributor": r["distributor"],
             "price": float(r["price"]),
             "description": str(r["description"])[:80]}
            for _, r in candidates.iloc[1:4].iterrows()
        ]
        return SearchResponse(
            query=q, tier="exact",
            best=ProductResult(
                distributor=str(best_row["distributor"]),
                manufacturer=str(best_row["manufacturer"]),
                description=str(best_row["description"]),
                price=float(best_row["price"]),
                catalog_num=str(best_row.get("dist_catalog_num", "")),
            ),
            alternatives=alts,
            savings_vs_worst=savings,
            candidates_returned=len(candidates),
            llm_endpoint="exact-match (no LLM)",
            elapsed_ms=int((time.time()-t_start)*1000),
        )

    # --- semantic: LLM reasoning ---
    user_prompt = _format_candidates(candidates, q)
    llm         = _call_llm(user_prompt)
    parsed      = _parse_llm_json(llm["content"]) if llm["content"] else None

    if not parsed:
        # fallback: return cheapest candidate without LLM
        best_row = candidates.sort_values("price_num").iloc[0] if "price_num" in candidates.columns else candidates.iloc[0]
        return SearchResponse(
            query=q, tier="semantic_no_llm",
            best=ProductResult(
                distributor=str(best_row.get("distributor","")),
                manufacturer=str(best_row.get("manufacturer","")),
                description=str(best_row.get("description","")),
                price=float(best_row.get("price_num", 0) or 0),
                catalog_num=str(best_row.get("dist_catalog_num","")),
            ),
            alternatives=[],
            savings_vs_worst=0,
            candidates_returned=len(candidates),
            llm_endpoint=ep_name,
            elapsed_ms=int((time.time()-t_start)*1000),
            reasoning="LLM parse failed - showing cheapest candidate"
        )

    best_d = parsed.get("best", {})
    return SearchResponse(
        query=q, tier="semantic",
        best=ProductResult(
            distributor=str(best_d.get("distributor","")),
            manufacturer=str(best_d.get("manufacturer","")),
            description=str(best_d.get("description","")),
            price=float(best_d.get("price", 0) or 0),
            catalog_num=str(best_d.get("catalog_num","")),
        ),
        alternatives=parsed.get("alternatives", []),
        savings_vs_worst=float(parsed.get("savings_vs_worst", 0) or 0),
        candidates_returned=len(candidates),
        llm_endpoint=ep_name,
        elapsed_ms=int((time.time()-t_start)*1000),
        reasoning=str(parsed.get("reasoning",""))[:300],
    )





class BaselineProduct(BaseModel):
    distributor: str
    manufacturer: str = ""
    description: str
    price: float
    catalog_num: str = ""


class CompareRequest(BaseModel):
    baseline: BaselineProduct
    query: str


COMPARE_PROMPT = """\
You are a procurement assistant for a university research lab.
The researcher is CURRENTLY BUYING a specific product at a known price.
Your job is to find cheaper alternatives from other distributors.

════════════════════════════════════════════════════════════
THE RESEARCHER'S CURRENT PRODUCT (BASELINE)
════════════════════════════════════════════════════════════
  Distributor:   {distributor}
  Manufacturer:  {manufacturer}
  Description:   {description}
  Current price: ${price:.2f}
  Catalog #:     {catalog_num}

════════════════════════════════════════════════════════════
CANDIDATE PRODUCTS TO EVALUATE
════════════════════════════════════════════════════════════
{candidates}

════════════════════════════════════════════════════════════
EQUIVALENCE RULES — READ CAREFULLY
════════════════════════════════════════════════════════════

STEP 1 — EXTRACT BASELINE UNIT
Before comparing anything, determine the baseline product's unit:
  - Pack quantity: look for CS500, PK50, 100/BX, 20/PK, "per case", "per bag" etc.
  - Volume: look for mL, L, uL
  - Weight: look for g, kg, mg
  - Count: individual items vs multi-packs
  Baseline unit price = ${price:.2f} ÷ baseline quantity

STEP 2 — EQUIVALENCE CHECK (ALL must be true to call equivalent)
  ✓ SAME product type (a tube is not a cap, a pipette is not a tip)
  ✓ SAME physical size/capacity (5mL ≠ 10mL, 25cm² ≠ 75cm², 500mL ≠ 1L)
  ✓ SAME key specifications:
      - "with calcium" ≠ "without calcium"
      - "sterile" ≠ "non-sterile" (if spec matters for the product type)
      - "1x" ≠ "10x" concentration
      - "external thread" ≠ "internal thread" (for vials/cryovials)
      - filter pore size must match (0.2μm ≠ 0.45μm)
  ✓ SAME or compatible material when critical (polypropylene vs glass = NOT equivalent)

STEP 3 — PACK SIZE NORMALIZATION (only for confirmed equivalent products)
  If the candidate has a DIFFERENT pack size than the baseline:
    candidate_unit_price = candidate_price ÷ candidate_quantity
    savings_vs_baseline  = baseline_unit_price - candidate_unit_price
    Only include if savings_vs_baseline > 0 (cheaper per unit)
  
  Report the UNIT PRICE in the price field, not the pack price.
  Add a note in reasoning explaining the normalization.

STEP 4 — REJECT if any of these are true
  ✗ Different physical size or capacity
  ✗ Different key specification (concentration, sterility, thread type, etc.)
  ✗ Accessory or component for the product (e.g. a cap for a vial ≠ the vial)
  ✗ Rack, holder, or storage for the product ≠ the product itself
  ✗ Candidate is more expensive per unit than baseline (no savings)

════════════════════════════════════════════════════════════
OUTPUT FORMAT
════════════════════════════════════════════════════════════
Return JSON only — no preamble, no markdown, no explanation outside the JSON:
{{
  "baseline_unit": "description of baseline unit (e.g. per tube, per mL, per gram)",
  "baseline_unit_price": float,
  "equivalents": [
    {{
      "distributor": str,
      "manufacturer": str,
      "description": str,
      "pack_price": float,
      "pack_qty": int_or_float,
      "price": float,
      "catalog_num": str,
      "savings_vs_baseline": float,
      "savings_pct": float,
      "normalization_note": str
    }}
  ],
  "cheapest": {{same fields as above}},
  "n_equivalent": int,
  "reasoning": str
}}

Rules for numeric fields:
- price = per-unit price AFTER normalization (not the pack price)
- pack_price = the actual catalog price as listed
- pack_qty = how many units in the pack (1 if sold individually)
- savings_vs_baseline = baseline_unit_price - candidate_unit_price (positive = cheaper)
- savings_pct = 100 * savings_vs_baseline / baseline_unit_price
- If no equivalent found, return equivalents: [] and cheapest: null
- All prices must be numeric (no dollar signs)
"""



# ===========================================================================
# Helper: sort by price
# ===========================================================================
def _sort_by_price(best, alternatives):
    all_items = ([best] if best else []) + (alternatives or [])
    all_items = [p for p in all_items if p and p.get('price') is not None]
    all_items.sort(key=lambda p: float(p.get('price', 9e9)))
    if not all_items:
        return None, [], 0
    cheapest = all_items[0]
    rest = all_items[1:]
    savings = round(float(all_items[-1].get('price',0)) - float(cheapest.get('price',0)), 2) if rest else 0
    return cheapest, rest, savings


# ===========================================================================
# Models
# ===========================================================================
class SearchRequest(BaseModel):
    query: str
    manufacturer: Optional[str] = None
    part_number:  Optional[str] = None

class BaselineProduct(BaseModel):
    distributor:  str
    manufacturer: str = ""
    description:  str
    price:        float
    catalog_num:  str = ""

class CompareRequest(BaseModel):
    baseline: BaselineProduct
    query:    str


# ===========================================================================
# /health
# ===========================================================================
@app.get("/health")
def health():
    ep = state.get("active_endpoint")
    return {
        "status":          "ok" if state.get("ready") else "not_ready",
        "index_vectors":   state["index"].ntotal if state.get("index") else 0,
        "exact_match_keys":len(state.get("multi_keys", [])),
        "llm_endpoint":    ep[2] if ep else None,
        "embedding_device":state.get("device", "unknown"),
    }


# ===========================================================================
# /candidates  — retrieval only, no LLM
# ===========================================================================
@app.get("/candidates")
def candidates_only(query: str, manufacturer: str = None, part_number: str = None):
    if not state.get("ready"):
        raise HTTPException(503, "Server not ready")

    # Try exact match first
    if manufacturer and part_number:
        exact = _search_exact(manufacturer, part_number)
        if len(exact) >= 2:
            rows = []
            for _, row in exact.iterrows():
                rows.append({
                    "cosine":       None,
                    "distributor":  str(row.get("distributor","")),
                    "manufacturer": str(row.get("manufacturer","")),
                    "description":  str(row.get("description","")),
                    "price":        float(row.get("price", 0) or 0),
                    "catalog_num":  str(row.get("dist_catalog_num","")),
                })
            return {"tier": "exact", "candidates": rows, "count": len(rows)}

    cands = _search_semantic(query)
    if len(cands) == 0:
        return {"tier": "semantic", "candidates": [], "count": 0}

    rows = []
    for _, row in cands.iterrows():
        rows.append({
            "cosine":       float(row.get("cosine", 0)),
            "distributor":  str(row.get("distributor","")),
            "manufacturer": str(row.get("manufacturer","")),
            "description":  str(row.get("description","")),
            "price":        float(row.get("price_num", 0) or 0),
            "catalog_num":  str(row.get("dist_catalog_num","")),
        })
    return {"tier": "semantic", "candidates": rows, "count": len(rows)}


# ===========================================================================
# /compare  — 3-tier: exact + AI + semantic
# ===========================================================================
@app.post("/compare")
def compare(req: CompareRequest):
    if not state.get("ready"):
        raise HTTPException(503, "Server not ready")

    t_start  = time.time()
    baseline = req.baseline
    query    = req.query.strip()

    # Tier 1: exact part-number matches
    exact_matches = []
    if baseline.manufacturer and baseline.catalog_num:
        mk = _norm_key(baseline.manufacturer)
        pk = _norm_key(baseline.catalog_num)
        rows = state["exact_dict"].get((mk, pk), [])
        for row in rows:
            if row.get("distributor") == baseline.distributor:
                continue
            price   = float(row.get("price", 0) or 0)
            savings = round(baseline.price - price, 2)
            savings_pct = round(100 * savings / baseline.price, 1) if baseline.price else 0
            exact_matches.append({
                "distributor":         str(row.get("distributor","")),
                "manufacturer":        str(row.get("manufacturer","")),
                "description":         str(row.get("description",""))[:120],
                "price":               price,
                "catalog_num":         str(row.get("dist_catalog_num","")),
                "savings_vs_baseline": savings,
                "savings_pct":         savings_pct,
                "match_type":          "exact",
            })
    exact_matches.sort(key=lambda x: float(x.get("price", 9e9)))

    # Tier 2: semantic candidates
    cands = _search_semantic(query)
    semantic_candidates = []
    for _, row in cands.iterrows():
        price = float(row.get("price_num", 0) or 0)
        cos   = float(row.get("cosine", 0))
        if (str(row.get("distributor","")) == baseline.distributor and
            str(row.get("dist_catalog_num","")) == baseline.catalog_num):
            continue
        savings = round(baseline.price - price, 2)
        semantic_candidates.append({
            "distributor":         str(row.get("distributor","")),
            "manufacturer":        str(row.get("manufacturer","")),
            "description":         str(row.get("description",""))[:120],
            "price":               price,
            "catalog_num":         str(row.get("dist_catalog_num","")),
            "cosine":              round(cos, 3),
            "savings_vs_baseline": round(savings, 2),
            "savings_pct":         round(100*savings/baseline.price, 1) if baseline.price else 0,
            "match_type":          "semantic",
        })

    # Tier 3: LLM equivalence
    llm_equivalents = []
    cheapest        = None
    reasoning       = ""
    llm_elapsed     = 0
    baseline_unit   = ""
    baseline_unit_price = baseline.price

    ep = state.get("active_endpoint")
    if ep and len(semantic_candidates) > 0:
        lines = ["CANDIDATE PRODUCTS:"]
        for i, c in enumerate(semantic_candidates[:60], 1):
            lines.append(
                f"{i:3d}. [{c['distributor']:<6}] ${c['price']:<10.2f} "
                f"cos:{c['cosine']:.3f}  MFR:{c['manufacturer'][:25]:<27} "
                f"CAT:{c['catalog_num'][:18]:<20} {c['description'][:80]}"
            )
        user_prompt = COMPARE_PROMPT.format(
            distributor  = baseline.distributor,
            manufacturer = baseline.manufacturer,
            description  = baseline.description,
            price        = baseline.price,
            catalog_num  = baseline.catalog_num,
            candidates   = "\n".join(lines),
        )
        llm_result  = _call_llm(user_prompt)
        parsed      = _parse_llm_json(llm_result["content"]) if llm_result["content"] else None
        llm_elapsed = llm_result.get("elapsed", 0)

        if parsed:
            baseline_unit       = str(parsed.get("baseline_unit",""))
            baseline_unit_price = float(parsed.get("baseline_unit_price") or baseline.price)
            equivs = parsed.get("equivalents", []) or []
            for e in equivs:
                price      = float(e.get("price", 0) or 0)
                pack_price = float(e.get("pack_price", price) or price)
                e["price"]               = price
                e["pack_price"]          = pack_price
                e["savings_vs_baseline"] = round(baseline_unit_price - price, 2)
                e["savings_pct"]         = round(100*(baseline_unit_price-price)/baseline_unit_price, 1) if baseline_unit_price else 0
                e["match_type"]          = "llm"
                e["normalization_note"]  = str(e.get("normalization_note",""))
            llm_equivalents = [e for e in equivs if e.get("savings_vs_baseline", 0) > 0]
            llm_equivalents.sort(key=lambda e: float(e.get("price", 9e9)))
            reasoning = str(parsed.get("reasoning",""))[:500]

    # Only include items actually cheaper than baseline
    all_cheaper = [e for e in exact_matches + llm_equivalents
                   if float(e.get("price", 9e9)) < baseline.price]
    cheapest = min(all_cheaper, key=lambda x: float(x.get("price", 9e9))) if all_cheaper else None

    return {
        "baseline":             baseline.dict(),
        "baseline_unit":        baseline_unit,
        "baseline_unit_price":  baseline_unit_price,
        "exact_matches":        exact_matches,
        "semantic_candidates":  semantic_candidates,
        "llm_equivalents":      llm_equivalents,
        "cheapest":             cheapest,
        "n_exact":              len(exact_matches),
        "n_llm":                len(llm_equivalents),
        "reasoning":            reasoning,
        "candidates_n":         len(cands),
        "llm_online":           ep is not None,
        "elapsed_ms":           int((time.time()-t_start)*1000),
        "llm_elapsed":          llm_elapsed,
    }


# ===========================================================================
# /search_both  — runs both LLM endpoints, returns side-by-side
# ===========================================================================
@app.post("/search_both")
def search_both(req: SearchRequest):
    if not state.get("ready"):
        raise HTTPException(503, "Server not ready")

    t_start = time.time()
    q = req.query.strip()
    if not q:
        raise HTTPException(400, "Query cannot be empty")

    cands_resp = candidates_only(q, req.manufacturer, req.part_number)
    tier       = cands_resp["tier"]
    raw_cands  = cands_resp["candidates"]

    if not raw_cands:
        return {"tier": "no_results", "candidates": [], "ollama": None,
                "nim": None, "elapsed_ms": int((time.time()-t_start)*1000)}

    lines = [f"USER QUERY: {q}\n", "CANDIDATE PRODUCTS:"]
    for i, c in enumerate(raw_cands[:100], 1):
        cos = f"{c['cosine']:.3f}" if c['cosine'] else "—"
        lines.append(f"{i:3d}. [{c['distributor']:5s}] ${float(c['price']):<10.2f} MFR:{c['manufacturer'][:28]:<30} cos:{cos}  {c['description'][:80]}")
    user_prompt = "\n".join(lines)

    ep = state.get("active_endpoint")
    ollama_result = None
    nim_result    = None

    if ep:
        llm_r  = _call_llm(user_prompt)
        parsed = _parse_llm_json(llm_r["content"]) if llm_r["content"] else None
        if parsed:
            best, alts, sav = _sort_by_price(parsed.get("best"), parsed.get("alternatives",[]))
            parsed["best"] = best
            parsed["alternatives"] = alts
            parsed["savings_vs_worst"] = sav
        result = {"parsed": parsed, "elapsed": llm_r.get("elapsed",0),
                  "error": llm_r.get("error"), "cached": llm_r.get("cached")}
        if ep[2] and "Ollama" in ep[2]:
            ollama_result = result
        else:
            nim_result = result

    return {
        "tier":             tier,
        "candidates":       raw_cands,
        "ollama":           ollama_result,
        "nim":              nim_result,
        "elapsed_ms":       int((time.time()-t_start)*1000),
        "active_endpoint":  ep[2] if ep else None,
    }


# ===========================================================================
# Browse taxonomy
# ===========================================================================
TAXONOMY = {
    "Pipettes & Tips": {
        "Serological Pipettes": ["serological pipet", "stripette"],
        "Pipette Tips":          ["pipette tip", "filter tip"],
        "Micropipettes & Controllers": ["pipette controller", "micropipet", "electronic pipet"],
        "Pasteur Pipettes":      ["pasteur pipet", "transfer pipet"],
    },
    "Tubes & Vials": {
        "Centrifuge Tubes":      ["centrifuge tube", "conical tube"],
        "Microcentrifuge Tubes": ["microcentrifuge", "microtube"],
        "Cryogenic Vials":       ["cryogenic vial", "cryovial", "cryo tube"],
        "Culture Tubes":         ["culture tube", "test tube"],
        "PCR Tubes & Strips":    ["pcr tube", "pcr strip"],
    },
    "Cell Culture": {
        "Well Plates":           ["well plate", "multiwell", "tissue culture plate"],
        "Flasks":                ["tissue culture flask", "t-75", "t-25"],
        "Dishes":                ["petri dish", "culture dish"],
        "Media & Reagents":      ["dmem", "rpmi", "hyclone", "fetal bovine serum"],
        "Serological Supplies":  ["cell strainer", "biosafety"],
    },
    "Filtration & Paper": {
        "Filter Paper":          ["filter paper", "qualitative filter", "quantitative filter"],
        "Syringe Filters":       ["syringe filter", "membrane filter"],
        "Bottle-Top Filters":    ["bottle top filter", "vacuum filter"],
        "Lab Wipes & Tissues":   ["kimwipe", "lab wipe", "paper towel"],
        "Membranes":             ["nitrocellulose", "pvdf membrane", "nylon membrane"],
    },
    "Bottles & Glassware": {
        "Storage Vials":         ["storage vial", "sample vial", "borosilicate vial"],
        "Media Bottles":         ["media bottle", "reagent bottle"],
        "Beakers & Flasks":      ["beaker", "erlenmeyer flask", "round bottom flask"],
        "Graduated Cylinders":   ["graduated cylinder"],
        "Burets":                ["buret", "burette"],
    },
    "Reagents & Chemicals": {
        "Antibodies":            ["antibody", "monoclonal antibody"],
        "Proteins & Enzymes":    ["protein", "enzyme", "protease"],
        "Buffers & Solutions":   ["phosphate buffer", "tris buffer", "pbs", "hepes"],
        "Stains & Dyes":         ["stain", "fluorescent dye"],
        "Solvents":              ["acetone", "ethanol", "methanol"],
    },
    "Safety & Protective": {
        "Gloves":                ["nitrile glove", "latex glove"],
        "Spill Kits":            ["spill kit", "spill cleanup"],
        "Eye Protection":        ["safety goggle", "eye protection"],
        "Lab Coats":             ["lab coat"],
    },
    "Instruments & Equipment": {
        "Hot Plates & Stirrers": ["hot plate", "magnetic stir"],
        "Vacuum Pumps":          ["vacuum pump"],
        "Pipette Controllers":   ["pipette controller", "propipette"],
        "Columns & HPLC":        ["hplc column", "lc column"],
    },
    "Syringes & Needles": {
        "Syringes":              ["syringe", "luer"],
        "Needles":               ["needle", "hypodermic"],
    },
}


@app.get("/browse/taxonomy")
def browse_taxonomy():
    return {cat: list(subs.keys()) for cat, subs in TAXONOMY.items()}


@app.get("/browse/products")
def browse_products(category: str, subcategory: str,
                    manufacturer: str = None, limit: int = 60):
    """
    Returns products in a category/subcategory using pre-built index.
    Optional manufacturer filter to narrow results.
    """
    if not state.get("ready"):
        raise HTTPException(503, "Server not ready")
    if category not in TAXONOMY or subcategory not in TAXONOMY[category]:
        raise HTTPException(404, f"Category '{category}' / '{subcategory}' not found")

    # Use pre-built index for speed
    browse_index = state.get("browse_index", {})
    df = state["df"]

    if browse_index and category in browse_index and subcategory in browse_index[category]:
        idx_rows = browse_index[category][subcategory]
        matches = df.loc[idx_rows].copy()
    else:
        # Fallback: live search
        import re
        terms   = TAXONOMY[category][subcategory]
        pattern = "|".join(re.escape(t) for t in terms)
        mask    = df["description"].str.contains(pattern, case=False, na=False) & (df["price_num"] > 0)
        matches = df[mask].copy()

    # Apply optional manufacturer filter
    if manufacturer and manufacturer.strip():
        mfr_upper = manufacturer.strip().upper()
        matches = matches[matches["manufacturer"].fillna("").str.upper().str.contains(mfr_upper, na=False)]

    if len(matches) == 0:
        return {"category": category, "subcategory": subcategory,
                "total": 0, "products": [], "manufacturers": [],
                "search_terms": TAXONOMY[category][subcategory]}

    # Get unique manufacturer list for filter dropdown
    mfr_list = sorted(matches["manufacturer"].dropna().unique().tolist())

    # Deduplicate and sort by price
    top = (
        matches[matches["price_num"] > 0]
        .sort_values("price_num")
        .drop_duplicates(subset=["distributor", "description"])
        .head(limit)
    )

    products = []
    for _, row in top.iterrows():
        products.append({
            "distributor":   str(row.get("distributor", "")),
            "manufacturer":  str(row.get("manufacturer", "")),
            "description":   str(row.get("description", ""))[:120],
            "price":         float(row.get("price_num", 0) or 0),
            "catalog_num":   str(row.get("dist_catalog_num", "")),
            "category_desc": str(row.get("category_desc", ""))[:60],
        })

    return {
        "category":    category,
        "subcategory": subcategory,
        "total":       int(len(matches.drop_duplicates(subset=["distributor", "description"]))),
        "showing":     len(products),
        "products":    products,
        "manufacturers": mfr_list[:50],
        "search_terms": TAXONOMY[category][subcategory],
    }


@app.get("/browse/manufacturers")
def browse_manufacturers_in_category(category: str, subcategory: str):
    """Returns manufacturer list for a given category/subcategory."""
    if not state.get("ready"):
        raise HTTPException(503, "Server not ready")
    browse_index = state.get("browse_index", {})
    df = state["df"]
    if browse_index and category in browse_index and subcategory in browse_index[category]:
        matches = df.loc[browse_index[category][subcategory]]
    else:
        import re
        terms   = TAXONOMY[category][subcategory]
        pattern = "|".join(re.escape(t) for t in terms)
        mask    = df["description"].str.contains(pattern, case=False, na=False)
        matches = df[mask]
    mfrs = matches["manufacturer"].dropna().value_counts().head(50)
    return [{"name": str(m), "count": int(c)} for m, c in mfrs.items()]


@app.get("/manufacturers/search")
def manufacturers_search(q: str = "", limit: int = 10):
    """Autocomplete: returns manufacturer names matching query string."""
    if not state.get("ready"):
        raise HTTPException(503, "Server not ready")
    mfr_list = state.get("mfr_list", [])
    if not q.strip():
        return [{"name": m, "count": c} for m, c in mfr_list[:limit]]
    q_upper = q.strip().upper()
    # Exact prefix matches first, then contains
    prefix  = [(m, c) for m, c in mfr_list if str(m).upper().startswith(q_upper)]
    contains= [(m, c) for m, c in mfr_list if q_upper in str(m).upper() and not str(m).upper().startswith(q_upper)]
    results = (prefix + contains)[:limit]
    return [{"name": m, "count": c} for m, c in results]



@app.get("/manufacturer/{mfr_name}")
def manufacturer_browse(mfr_name: str, category: str = None, limit: int = 100):
    """
    Returns products from a manufacturer.
    If category specified, filters to that UNSPSC category.
    Always returns the list of categories available for this manufacturer.
    """
    if not state.get("ready"):
        raise HTTPException(503, "Server not ready")

    df        = state["df"]
    mfr_upper = mfr_name.upper().strip()
    all_mfrs  = df["manufacturer"].dropna().unique()
    matching  = [m for m in all_mfrs if mfr_upper in str(m).upper()]

    if not matching:
        return {"manufacturer": mfr_name, "total": 0, "products": [],
                "distributors": [], "categories": []}

    mask    = df["manufacturer"].isin(matching) & (df["price_num"] > 0)
    matches = df[mask].copy()
    if len(matches) == 0:
        return {"manufacturer": mfr_name, "total": 0, "products": [],
                "distributors": [], "categories": []}

    canonical = matches["manufacturer"].value_counts().index[0]

    # Get category list for this manufacturer
    cat_counts = (
        matches["category_desc"].dropna()
        .value_counts().head(30)
    )
    categories = [{"name": str(c), "count": int(n)} for c, n in cat_counts.items()]

    # Apply category filter if provided
    if category and category.strip():
        matches = matches[matches["category_desc"].fillna("") == category]
        if len(matches) == 0:
            return {
                "manufacturer": canonical,
                "search_term":  mfr_name,
                "total":        0,
                "showing":      0,
                "distributors": list(df[df["manufacturer"].isin(matching)]["distributor"].unique()),
                "categories":   categories,
                "selected_category": category,
                "products":     [],
            }

    top = (
        matches
        .sort_values("price_num")
        .drop_duplicates(subset=["distributor", "description"])
        .head(limit)
    )

    products = []
    for _, row in top.iterrows():
        products.append({
            "distributor":   str(row.get("distributor", "")),
            "manufacturer":  str(row.get("manufacturer", "")),
            "description":   str(row.get("description", ""))[:120],
            "price":         float(row.get("price_num", 0) or 0),
            "catalog_num":   str(row.get("dist_catalog_num", "")),
            "category_desc": str(row.get("category_desc", ""))[:60],
        })

    total_deduped = int(len(matches.drop_duplicates(subset=["distributor","description"])))

    return {
        "manufacturer":      canonical,
        "search_term":       mfr_name,
        "total":             total_deduped,
        "showing":           len(products),
        "distributors":      list(df[df["manufacturer"].isin(matching)]["distributor"].unique()),
        "categories":        categories,
        "selected_category": category or "",
        "products":          products,
    }

