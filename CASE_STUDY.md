# From Messy Purchasing Data to Actionable Procurement Intelligence
## A Practitioner's Playbook

*Case study: end-to-end AI system design for multi-vendor procurement data · 2025*

---

## The Problem

Every large organization that purchases from multiple vendors faces the same structural problem: **the data is not clean, not consistent, and not comparable.**

Vendor A describes a product one way. Vendor B describes the same product differently. The quantities are in different units. The pack sizes are buried in product codes. One vendor has full purchase history; another has catalog data only. None of it lines up neatly in a spreadsheet, and nobody has been systematically comparing prices across sources.

The instinct when confronted with this is to reach for a visualization tool or drop everything into an AI assistant and ask it to find patterns. Both approaches fail for the same reason: **the data isn't ready.** You cannot virtualize your way out of a data quality problem. Garbage in, garbage out — at enterprise scale.

This case study documents the end-to-end methodology I developed to solve this problem for a multi-vendor procurement dataset spanning six million catalog rows across four major distributors. The approach is generalizable. If your organization buys from multiple vendors and you suspect you're overpaying on some products, this is the playbook.

---

## The Data Reality

The dataset in this project was representative of what you find in any large procurement environment:

- **Six million catalog rows** across four distributors, loaded from system exports
- **Inconsistent description formats** — one vendor uses verbose natural language ("[Manufacturer] 50mL Polypropylene Centrifuge Tubes, Sterile, Case of 500"), another uses terse abbreviations ("TUBE CENTRIFUGE PP 50ML CS500"), a third uses a hybrid
- **Missing fields** — some vendors had full prior-year purchase quantities; others had catalog data only
- **Pack size buried in codes** — the most important normalization variable (how many units per purchase) was sometimes in a dedicated field, sometimes encoded in the product description, sometimes inferrable only from the manufacturer's own product numbering system
- **No common identifier** — no single field you could join on. Manufacturer part numbers existed in some sources, not others. Catalog numbers were vendor-specific. Descriptions were too messy to match directly.

The question was: **which products are the same item sold at different prices by different vendors?** And once you know that: **what is the cheapest source, per unit, for each product?**

---

## The Core Methodology: Lead With What Is Deterministic

The most important architectural decision in this entire project is also the simplest one:

> **Do everything you can without AI before you use AI.**

This sounds obvious. In practice, almost nobody follows it. The instinct when you have an AI budget is to throw data at a model and let it reason. The problem is that large language models are slow, expensive per query, non-deterministic, and prone to confident mistakes on numerical comparisons. You should never use AI for something a lookup table can do in two milliseconds.

The methodology has three tiers, executed in strict order:

### Tier 1: Deterministic — Exact Part Number Matching

If two vendors both carry a product from the same manufacturer with the same part number, you do not need AI to tell you they are the same product. They are, by definition, identical. The only question is price.

Build a lookup dictionary keyed on `(manufacturer, part_number)`. For every key that appears in two or more vendor catalogs, compare prices. This comparison is 100% reliable, requires zero AI inference, and produces the most defensible savings estimates because there is no ambiguity in the match.

In this project, this approach identified **42,052 matched product pairs** across four distributors — products confirmed identical by manufacturer code, available at different prices from different sources. This was the foundation of the entire business case.

**This tier alone justifies the cost of building the system.** Before you write a single line of AI code, you have a verifiable list of products you are potentially overpaying for, with exact dollar figures.

### Tier 2: Semantic — Embedding-Based Similarity Search

The majority of the catalog cannot be matched by part number. Descriptions are too inconsistent, part numbers too sparsely populated. This is where AI enters — but carefully.

The approach: convert every product description into a dense vector embedding using a sentence transformer model (bge-small-en-v1.5 in this implementation), build a FAISS index over all six million vectors, and at query time retrieve the top candidates by cosine similarity above a calibrated threshold (0.85 in this project, tuned to return a median of 44 candidates with a max of 137).

The key insight: **you are not asking the AI to search six million rows.** You are asking a mathematical index to narrow six million rows down to ~50 candidates in under 110ms. The AI only sees those 50.

This is the funnel architecture. The embedding model handles scale; the language model handles reasoning. Never invert this.

### Tier 3: LLM Reasoning — Equivalence Judgment on a Narrow Candidate Set

With 50 candidates in hand, you now face the genuine hard problem: are these actually the same product? A 5mL pipette and a 10mL pipette have similar descriptions. PBS with calcium and PBS without calcium look nearly identical in text. A case of 500 tubes and a case of 50 tubes from the same manufacturer are priced very differently but are not interchangeable for procurement purposes.

This is where a large language model earns its place. The prompt is structured to:
1. Extract the baseline unit from the query product (what is the per-unit price?)
2. Check equivalence against strict rules: same product type, same physical size, same key specifications (concentration, sterility, thread type, etc.)
3. Normalize pack sizes before price comparison — a $14 box of 50 vs a $434 case of 500 is the same per-unit price and not a savings opportunity
4. Reject accessories, components, or related-but-not-equivalent items
5. Return only items that are genuinely cheaper per unit than the baseline

The LLM operates on a structured candidate table, not raw text. It returns structured JSON. The savings calculation runs deterministically on the LLM's output — the model identifies equivalence, the code calculates the number.

---

## The Unit Normalization Problem (And Its Solution)

The single biggest data quality challenge in this project — and in almost every multi-vendor procurement dataset — was **pack size inconsistency**.

A product listed at $317 from Vendor A and $14 from Vendor B looks like a massive savings opportunity. In reality, Vendor A's listing is for a case of 500 and Vendor B's is for a pack of 50. The per-unit price is nearly identical. Acting on the raw comparison would be wrong.

The naive fix is to parse pack sizes from descriptions using regex — looking for patterns like "CS500", "PK50", "100/BX". This works for well-formatted descriptions but fails on terse vendor abbreviations.

The real fix came from the source data itself. The procurement platform's export contained a field called `qsu` ("quantity sold as") with values like 1, 50, 100, 500, 1000 — populated for **99.9% of rows** (6,068,599 of 6,068,888). Dividing the catalog price by the qsu value produces the true per-unit price for each row.

The impact was significant:
- **23% of rows** (1,395,917) had qsu > 1, meaning they required normalization
- The raw cross-distributor savings estimate was $317,583
- After unit-price normalization: **$161,564** — a 49.1% reduction
- The $156,019 difference was entirely pack-size inflation, not real savings

**The lesson:** before building any comparison logic, find out if your data source has a quantity/pack-size field. It is often there, just not used. In this case, that single field transformed the entire analysis from unreliable to defensible.

---

## System Architecture

The production system has five layers:

```
Data sources → Preprocessing pipeline → Search index → API layer → Client interfaces
```

**Preprocessing pipeline** runs in a Jupyter notebook environment:
- Ingest and normalize raw vendor exports
- Apply unit-price normalization using the qsu field
- Build the FAISS vector index (one-time, ~48 minutes, then reused)
- Build the exact-match lookup dictionary (~90 seconds per session)
- Compute and save the unit-normalized savings table

**Search index** — two independent structures:
- A FAISS IVFFlat index (5.19M vectors, 8GB on disk) for semantic retrieval
- An in-memory Python dictionary for O(1) exact part-number lookup

**API layer** — FastAPI service exposing:
- `/candidates` — retrieval only, no AI
- `/compare` — full three-tier pipeline
- `/browse/taxonomy` and `/browse/products` — category navigation with pre-built index
- `/manufacturer/{name}` — manufacturer-level drill-down
- `/trends` — spending analysis from pre-computed parquet

**Client interfaces** — two standalone HTML files:
- Price comparison tool: three search modes (natural language, browse by category, browse by manufacturer), selection-first flow, three-tier results, downloadable CSV
- Spending dashboard: leadership-level charts, savings opportunities with filter and download, embedded spend analysis figures

**LLM integration** — two configurable LLM endpoints, health-checked at startup, graceful degradation to exact-match-only when offline

---

## What the AI Can and Cannot Do

This is the section most AI projects skip, and the omission is usually why they fail.

**The AI can:**
- Read messy, inconsistent product descriptions and identify whether two products are functionally equivalent
- Reason about specifications (calcium vs no calcium, sterile vs non-sterile, thread type, concentration) from natural language
- Normalize pack sizes when the calculation is expressed in the description
- Return structured, parseable JSON reliably at the 7b parameter scale with the right prompt

**The AI cannot:**
- Be trusted with raw numerical price comparisons without explicit unit normalization upstream
- Search six million rows at query time — this is a scaling problem, not an intelligence problem
- Be the first line of defense for data quality problems — preprocessing must happen before the AI sees any data
- Replace deterministic exact matching for identical products — this is both slower and less reliable

**The design principle:** every AI call in this system has a maximum of ~60 candidates as input. The funnel is never wider than that. If the funnel is wider, you haven't done enough preprocessing.

---

## The Results

Across the full dataset:

| Metric | Value |
|---|---|
| Catalog rows processed | 6,068,888 |
| Exact-matched product pairs | 42,052 |
| Rows with unit normalization applied | 1,395,917 (23%) |
| Raw savings estimate (before normalization) | $317,583 |
| **Defensible savings estimate (unit-normalized)** | **$161,564** |
| Pack-size inflation removed | $156,019 (49.1%) |
| Median unit-price spread on matched products | 20.7% |
| 90th percentile spread | 95.0% |
| Query latency — exact match | ~2ms |
| Query latency — semantic retrieval | 75–110ms |
| Query latency — full AI pipeline | 5–8s |
| LLM parse rate | 4/4 correctness, 4/4 consistency |

The $161,564 figure covers only the products where prior-year purchase quantities were available from two of the four vendors. An additional 37,535 matched product pairs have confirmed price gaps but unknown purchase volume — the true savings potential is larger.

---

## Generalizing the Playbook

If you are facing a similar problem — multi-vendor purchasing data, inconsistent descriptions, no common identifier — here is the sequence:

**Phase 1: Understand your data sources**
- Which vendors have purchase history (quantities)? Which are catalog-only?
- Which vendors have manufacturer part numbers? Which don't?
- Is there a quantity/pack-size field in any source? Find it before writing a single line of code.
- What is the completeness of each field across each source? Run value counts on every column.

**Phase 2: Extract the deterministic signal**
- Build the exact-match lookup on manufacturer + part number
- Apply unit normalization using the pack-size field
- Count how many matches exist across vendors
- Calculate savings estimates on matched pairs with known quantities
- This is your business case. Present it before building anything else.

**Phase 3: Build the semantic layer**
- Choose an embedding model calibrated for your domain (scientific products, office supplies, industrial parts — the vocabulary matters)
- Build the FAISS index offline, once, and reuse it
- Calibrate the cosine similarity threshold empirically — you want enough candidates to find alternatives, not so many the LLM gets confused
- Test retrieval quality on 20–30 hand-picked queries before building the API

**Phase 4: Design the LLM prompt for your domain**
- The prompt must be explicit about what makes two products equivalent in your context
- Unit normalization logic belongs in the prompt: extract pack size, compute unit price, compare unit prices
- List explicit rejection criteria: accessories ≠ products, different sizes ≠ equivalent, different concentrations ≠ equivalent
- Always ask for structured JSON output; parse it deterministically
- Cache LLM responses by prompt hash — repeat queries are free

**Phase 5: Build the user interface around selection, not search**
- The hardest UX problem in procurement tools is that users don't always know what they're looking for
- Provide three paths: natural language search, category browse, manufacturer browse
- The critical design decision: **make the user select their current product as the baseline before running AI**. This anchors the savings calculation to a real number, eliminates pack-size ambiguity, and produces results the user can defend to their organization.
- Every result should be downloadable as a CSV. The user needs to verify the AI's suggestion independently before acting on it.

**Phase 6: Build the trends layer separately**
- The comparison tool answers "is there a cheaper option for this specific product?"
- The trends dashboard answers "where should we be looking for savings across all of our purchasing?"
- These are different questions requiring different interfaces
- The trends layer uses the pre-computed unit-normalized savings table — no AI required, fully deterministic, runs in milliseconds
- Embed the insight in the dashboard: not just "here are the numbers" but "here is what you should do first and why"

---

## Key Lessons

**1. The quantity field is the most important field nobody uses.**
In every multi-vendor dataset I have worked with, there is a quantity or pack-size field with high coverage that sits unused. Find it, use it, normalize on it first. It will change your savings estimates significantly.

**2. The funnel architecture is non-negotiable at scale.**
You cannot run LLM inference on six million rows. You can run it on 50. Design your system so that by the time a record reaches the AI, it has been through at least two filtering steps. Embedding similarity is your first filter. The exact-match lookup is your second. The LLM is your final judge on a narrow, pre-screened set.

**3. Exact matching and semantic matching are not competing approaches — they are complementary tiers.**
Exact matching is fast, reliable, and requires zero AI. Use it first. Semantic matching covers what exact matching misses. Never let semantic matching replace exact matching; the false positive rate is too high for a system people will act on.

**4. Savings estimates must be unit-normalized before they are shown to anyone.**
A $300K savings figure that is actually 49% pack-size inflation is not a savings figure — it is a credibility problem. The normalization step is not optional. Find the quantity field, apply it, show the corrected number, and document the methodology.

**5. The AI's job is equivalence judgment, not price comparison.**
Price comparison is arithmetic. Do it in code after the AI runs. The AI's one job is to look at ~50 product descriptions and say: "these three are the same product as your baseline; these others are not." Keep the AI's scope narrow, give it explicit rules, and validate its output with spot checks.

**6. Build for graceful degradation.**
When the LLM is offline, the exact-match tier should still return results. When the vector index is cold, the browse-by-category path should still work from a pre-built index. A procurement tool that returns nothing when one component is unavailable will not be used.

---

## Technologies Used

| Layer | Technology | Rationale |
|---|---|---|
| Data processing | Python, pandas, numpy | Standard, well-supported, sufficient for 6M rows |
| Vector embeddings | bge-small-en-v1.5 | Domain-appropriate, 384-dim, 8× smaller index than large variants |
| Vector index | FAISS IVFFlat | Proven at scale, exact within cells, controllable precision |
| LLM | 7B parameter model via Ollama | 4/4 correctness on domain eval set, local inference, no API cost |
| API | FastAPI | Async, automatic docs, Pydantic validation |
| Serialization | Parquet (pyarrow) | Columnar, fast predicate pushdown, smaller than CSV |
| Client | Vanilla HTML/JS | No framework dependency, works as a local file, zero deployment complexity |

---

## What This Project Is Not

It is not a general-purpose AI assistant for procurement. It does not replace procurement expertise or judgment. It does not automate purchasing decisions.

It is a decision-support tool. It answers a specific, well-defined question ("is there a cheaper source for this exact product?") reliably and quickly, with a transparent methodology the user can verify. The final decision — whether to switch vendors, whether the alternative is truly equivalent, whether there are contract restrictions — remains with the human.

The CSV download is not an afterthought. It is the trust mechanism. Every AI suggestion in this system is accompanied by the full candidate list, labeled by match type, available for independent verification. The user should not have to take the AI's word for anything.

---

*This case study is based on a real implementation. Specific organizational details, spend figures, and vendor relationships have been omitted. The methodology, architecture, and technical approach are fully generalizable and have been written as a replicable playbook for any organization facing similar multi-vendor purchasing data challenges.*

---

*This case study is based on a real production implementation. A reference implementation is available at: github.com/tayler-erbe/procurement_intelligence_system_design*
