<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>BTAA Procurement — Live Demo</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');

/* ── Tokens ─────────────────────────────────────────────────────────── */
:root {
  --navy:   #1F4E79;
  --mid:    #2E75B6;
  --steel:  #4A90C4;
  --light:  #D6E4F0;
  --frost:  #EBF3FA;
  --green:  #548235;
  --red:    #C00000;
  --amber:  #B8860B;
  --body:   #3D3D3D;
  --muted:  #7A8999;
  --border: #D0DCE9;
  --bg:     #F4F7FB;
  --white:  #FFFFFF;
  --mono:   'JetBrains Mono', monospace;
  --sans:   'Inter', system-ui, sans-serif;
  --radius: 10px;
  --shadow: 0 2px 12px rgba(31,78,121,0.09);
}

* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: var(--sans); background: var(--bg); color: var(--body); min-height: 100vh; }

/* ── Layout ─────────────────────────────────────────────────────────── */
.app { max-width: 1100px; margin: 0 auto; padding: 0 20px 80px; }

/* ── Header ─────────────────────────────────────────────────────────── */
.header {
  background: var(--navy);
  margin: 0 -20px;
  padding: 0 40px;
  display: flex; align-items: center; gap: 14px;
  position: sticky; top: 0; z-index: 100;
  box-shadow: 0 2px 16px rgba(31,78,121,0.35);
  height: 56px;
}
.header-mark {
  font-family: var(--mono); font-size: 12px; font-weight: 500;
  background: var(--mid); color: white;
  padding: 4px 9px; border-radius: 6px; letter-spacing: 0.5px;
}
.header h1 { font-size: 15px; font-weight: 500; color: white; letter-spacing: 0.2px; }
.header-sub { font-size: 12px; color: rgba(255,255,255,0.45); font-weight: 300; margin-left: 4px; }
.header-right { margin-left: auto; display: flex; gap: 16px; align-items: center; }
.ep-status { display: flex; align-items: center; gap: 6px; font-size: 12px; font-family: var(--mono); color: rgba(255,255,255,0.6); }
.dot { width: 7px; height: 7px; border-radius: 50%; background: #555; flex-shrink: 0; }
.dot.on  { background: #6BCB77; box-shadow: 0 0 5px #6BCB77; }
.dot.off { background: var(--red); }

/* ── Search card ─────────────────────────────────────────────────────── */
.search-wrap { padding: 32px 0 0; }
.search-card {
  background: white; border-radius: var(--radius);
  border: 1px solid var(--border); box-shadow: var(--shadow);
  padding: 28px 32px 24px;
}
.search-card h2 { font-size: 20px; font-weight: 600; color: var(--navy); margin-bottom: 4px; }
.search-card p  { font-size: 13px; color: var(--muted); font-weight: 300; margin-bottom: 22px; line-height: 1.5; }

.search-row { display: flex; gap: 10px; margin-bottom: 12px; }
.field { display: flex; flex-direction: column; gap: 5px; }
.field.grow { flex: 1; }
.field label { font-size: 11px; font-weight: 600; color: var(--navy); text-transform: uppercase; letter-spacing: 0.7px; font-family: var(--mono); }
.field input {
  padding: 10px 14px; border: 1.5px solid var(--border); border-radius: 8px;
  font-family: var(--sans); font-size: 14px; color: var(--body); background: var(--frost);
  transition: border-color .15s, box-shadow .15s; outline: none;
}
.field input:focus { border-color: var(--mid); box-shadow: 0 0 0 3px rgba(46,117,182,.12); background: white; }
.field input::placeholder { color: #b5c0cc; }

.btn-row { display: flex; gap: 10px; align-items: center; margin-top: 4px; }
.btn { padding: 10px 24px; border: none; border-radius: 8px; font-family: var(--sans); font-size: 14px; font-weight: 500; cursor: pointer; transition: all .15s; }
.btn-primary { background: var(--navy); color: white; }
.btn-primary:hover { background: #174069; }
.btn-primary:active { transform: scale(.98); }
.btn-primary:disabled { background: #8aaec8; cursor: not-allowed; transform: none; }
.btn-ghost { background: transparent; color: var(--muted); border: 1.5px solid var(--border); padding: 9px 16px; }
.btn-ghost:hover { border-color: var(--mid); color: var(--mid); }

.pills { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 16px; }
.pill-label { font-size: 11px; color: var(--muted); align-self: center; margin-right: 2px; }
.pill {
  background: var(--frost); border: 1px solid var(--border); border-radius: 20px;
  padding: 4px 12px; font-size: 12px; color: var(--navy); cursor: pointer;
  font-family: var(--sans); transition: all .12s;
}
.pill:hover { background: var(--light); border-color: var(--mid); }

/* ── Pipeline steps ──────────────────────────────────────────────────── */
.pipeline { margin-top: 28px; display: flex; flex-direction: column; gap: 20px; }

.step {
  background: white; border-radius: var(--radius);
  border: 1px solid var(--border); box-shadow: var(--shadow);
  overflow: hidden; display: none;
  animation: fadeUp .25s ease;
}
.step.visible { display: block; }
@keyframes fadeUp { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: translateY(0); } }

.step-header {
  display: flex; align-items: center; gap: 12px;
  padding: 14px 20px; border-bottom: 1px solid var(--border);
  background: var(--frost);
}
.step-num {
  width: 26px; height: 26px; border-radius: 50%;
  background: var(--navy); color: white;
  display: flex; align-items: center; justify-content: center;
  font-size: 12px; font-weight: 600; font-family: var(--mono);
  flex-shrink: 0;
}
.step-title { font-size: 13px; font-weight: 600; color: var(--navy); }
.step-meta  { margin-left: auto; font-size: 12px; font-family: var(--mono); color: var(--muted); }
.step-body  { padding: 20px; }


/* ── Browse mode ─────────────────────────────────────────────────────────── */
.mode-tabs {
  display: flex; gap: 0; margin-bottom: 20px;
  border: 1.5px solid var(--border); border-radius: 8px; overflow: hidden;
  width: fit-content;
}
.mode-tab {
  padding: 8px 20px; font-size: 13px; font-weight: 500;
  cursor: pointer; border: none; background: white; color: var(--muted);
  transition: all .15s; font-family: var(--sans);
}
.mode-tab.active { background: var(--navy); color: white; }
.mode-tab:hover:not(.active) { background: var(--frost); color: var(--navy); }

.browse-dropdowns {
  display: none; flex-direction: column; gap: 12px;
}
.browse-dropdowns.visible { display: flex; }
.browse-row { display: flex; gap: 10px; align-items: flex-end; flex-wrap: wrap; }
.browse-group { display: flex; flex-direction: column; gap: 5px; min-width: 200px; flex: 1; }
.browse-group label { font-size: 11px; font-weight: 600; color: var(--navy); text-transform: uppercase; letter-spacing: 0.7px; font-family: var(--mono); }
.browse-select {
  padding: 10px 14px; border: 1.5px solid var(--border); border-radius: 8px;
  font-family: var(--sans); font-size: 14px; color: var(--body);
  background: var(--frost); cursor: pointer; outline: none;
  transition: border-color .15s; appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='8' viewBox='0 0 12 8'%3E%3Cpath fill='%237A8999' d='M6 8L0 0h12z'/%3E%3C/svg%3E");
  background-repeat: no-repeat; background-position: right 12px center;
  padding-right: 32px;
}
.browse-select:focus { border-color: var(--mid); box-shadow: 0 0 0 3px rgba(46,117,182,.12); background-color: white; }
.browse-select:disabled { opacity: 0.5; cursor: not-allowed; }

/* Browse results table */
.browse-results { margin-top: 8px; }
.browse-results-header {
  display: flex; justify-content: space-between; align-items: center;
  margin-bottom: 12px; padding: 10px 0;
  border-bottom: 2px solid var(--light);
}
.browse-results-title { font-size: 14px; font-weight: 600; color: var(--navy); }
.browse-results-meta { font-size: 12px; color: var(--muted); font-family: var(--mono); }
.browse-table-wrap { overflow-x: auto; }
.browse-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.browse-table thead th {
  background: var(--navy); color: white; padding: 9px 12px;
  text-align: left; font-size: 11px; font-weight: 600;
  text-transform: uppercase; letter-spacing: 0.6px; white-space: nowrap;
}
.browse-table tbody tr { cursor: pointer; transition: background .1s; }
.browse-table tbody tr:nth-child(even) { background: var(--frost); }
.browse-table tbody tr:hover { background: var(--light); }
.browse-table td { padding: 9px 12px; border-bottom: 1px solid var(--border); vertical-align: middle; }
.browse-table td.bnum { font-family: var(--mono); text-align: right; white-space: nowrap; font-size: 12px; }
.click-hint { font-size: 11px; color: var(--muted); font-style: italic; margin-top: 8px; }

/* ── Loading bar ─────────────────────────────────────────────────────── */
.loading-bar {
  height: 3px; background: var(--light); border-radius: 2px; overflow: hidden; margin-bottom: 14px;
}
.loading-bar-fill {
  height: 100%; background: linear-gradient(90deg, var(--mid), var(--steel));
  border-radius: 2px; width: 0; transition: width 0.4s ease;
  animation: indeterminate 1.4s ease infinite;
}
@keyframes indeterminate {
  0%   { transform: translateX(-100%) scaleX(0.5); }
  50%  { transform: translateX(0%)    scaleX(0.8); }
  100% { transform: translateX(100%)  scaleX(0.5); }
}
.loading-bar.done .loading-bar-fill { animation: none; width: 100%; background: var(--green); }

/* ── Candidates table ────────────────────────────────────────────────── */
.table-wrap { overflow-x: auto; }
table { width: 100%; border-collapse: collapse; font-size: 13px; }
thead th {
  background: var(--navy); color: white; padding: 9px 12px;
  text-align: left; font-weight: 600; font-size: 11px;
  text-transform: uppercase; letter-spacing: 0.6px; white-space: nowrap;
}
tbody tr:nth-child(even) { background: var(--frost); }
tbody tr:hover { background: var(--light); }
td { padding: 8px 12px; border-bottom: 1px solid var(--border); vertical-align: top; }
td.num { font-family: var(--mono); font-size: 12px; text-align: right; white-space: nowrap; }
td.cos { font-family: var(--mono); font-size: 11px; color: var(--muted); }
.dist-badge {
  background: var(--navy); color: white; padding: 2px 7px;
  border-radius: 4px; font-size: 10px; font-family: var(--mono); font-weight: 500;
}
.dist-Neta   { background: #2E75B6; }
.dist-VWR    { background: #1F4E79; }
.dist-Fisher { background: #548235; }
.dist-DOT    { background: #7B4E2D; }

/* ── LLM columns ─────────────────────────────────────────────────────── */
.llm-cols { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
@media (max-width: 700px) { .llm-cols { grid-template-columns: 1fr; } }

.llm-card {
  border: 1.5px solid var(--border); border-radius: 8px; overflow: hidden;
}
.llm-card-header {
  padding: 10px 16px; display: flex; align-items: center; gap: 8px;
  border-bottom: 1px solid var(--border); background: var(--frost);
}
.llm-card-header .dot { width: 8px; height: 8px; }
.llm-name { font-size: 12px; font-weight: 600; font-family: var(--mono); color: var(--navy); }
.llm-latency { margin-left: auto; font-size: 11px; font-family: var(--mono); color: var(--muted); }
.llm-card-body { padding: 16px; }

.thinking {
  display: flex; align-items: center; gap: 10px;
  color: var(--muted); font-size: 13px; font-style: italic;
}
.spinner {
  width: 18px; height: 18px; border: 2px solid var(--light);
  border-top-color: var(--mid); border-radius: 50%;
  animation: spin .7s linear infinite; flex-shrink: 0;
}
@keyframes spin { to { transform: rotate(360deg); } }

.result-price {
  font-size: 28px; font-weight: 600; color: var(--navy);
  font-family: var(--mono); letter-spacing: -1px;
  margin-bottom: 2px;
}
.result-from { font-size: 12px; color: var(--muted); margin-bottom: 10px; }
.result-desc { font-size: 13px; color: var(--body); line-height: 1.5; margin-bottom: 10px; }

.savings-tag {
  display: inline-flex; align-items: center; gap: 5px;
  background: rgba(84,130,53,.12); border: 1px solid rgba(84,130,53,.35);
  color: var(--green); padding: 4px 10px; border-radius: 20px;
  font-size: 12px; font-weight: 600; font-family: var(--mono);
  margin-bottom: 12px;
}

.alts-label { font-size: 11px; font-weight: 600; color: var(--muted); text-transform: uppercase; letter-spacing: 0.6px; margin-bottom: 6px; }
.alt-row { display: flex; align-items: center; gap: 8px; padding: 6px 0; border-top: 1px solid var(--border); font-size: 12px; }
.alt-price { font-family: var(--mono); font-weight: 500; color: var(--navy); min-width: 60px; }
.alt-desc  { color: var(--muted); flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

.reasoning-box {
  margin-top: 12px; padding: 10px 14px;
  background: var(--frost); border-left: 3px solid var(--mid);
  border-radius: 0 6px 6px 0; font-size: 12px; color: var(--muted);
  font-style: italic; line-height: 1.6;
}

.err-box {
  background: #fff5f5; border: 1px solid #f5c6c6; border-radius: 6px;
  padding: 12px 14px; color: var(--red); font-size: 13px; line-height: 1.5;
}
.no-equiv {
  color: var(--muted); font-size: 13px; font-style: italic; padding: 8px 0;
}

/* ── Offline warning ─────────────────────────────────────────────────── */
.offline-warn {
  background: #fffbf0; border: 1px solid #f0d080; border-radius: 8px;
  padding: 12px 16px; font-size: 13px; color: var(--amber);
  margin-bottom: 16px; display: none;
}
</style>
</head>
<body>

<div class="header">
  <span class="header-mark">BTAA</span>
  <h1>Procurement Search <span class="header-sub">/ Live Demo</span></h1>
  <div class="header-right">
    <div class="ep-status"><span class="dot" id="ollamaDot"></span><span id="ollamaLabel">Ollama…</span></div>
    <div class="ep-status"><span class="dot" id="nimDot"></span><span id="nimLabel">NIM…</span></div>
  </div>
</div>

<div class="app">
<div class="search-wrap">
<div class="search-card">
  <h2>Cross-distributor price comparison</h2>
  <p>Searches 5.19 million catalog entries across DOT Scientific, Fisher, Neta Scientific, and VWR. Type any product description to see the full pipeline live.</p>

  <div class="search-row">
    <div class="field grow">
      <label>Product description</label>
      <input id="queryInput" type="text" placeholder="e.g.  5 mL sterile serological pipette polystyrene" autocomplete="off">
    </div>
  </div>
  <div class="search-row">
    <div class="field" style="flex:1">
      <label>Manufacturer <span style="font-weight:300;text-transform:none;letter-spacing:0;font-family:var(--sans)">(optional)</span></label>
      <input id="mfrInput" type="text" placeholder="e.g. Corning">
    </div>
    <div class="field" style="flex:1">
      <label>Part # <span style="font-weight:300;text-transform:none;letter-spacing:0;font-family:var(--sans)">(optional — enables instant match)</span></label>
      <input id="partInput" type="text" placeholder="e.g. 430829">
    </div>
  </div>

  <div class="offline-warn" id="offlineWarn">
    ⚠ Both LLM endpoints appear offline. The candidates table will still show, but the AI reasoning step will be skipped.
    Make sure Ollama is running: <code>ollama serve</code>
  </div>

  <div class="btn-row">
    <button class="btn btn-primary" id="searchBtn" onclick="runSearch()">Search</button>
    <button class="btn btn-ghost" onclick="clearAll()">Clear</button>
  </div>

  <div class="pills">
    <span class="pill-label">Try:</span>
    <button class="pill" onclick="q('5 mL sterile serological pipette polystyrene')">5 mL serological pipette</button>
    <button class="pill" onclick="q('50 mL centrifuge tubes Corning', 'CORNING', '430829')">50 mL Corning centrifuge tube</button>
    <button class="pill" onclick="q('1000 uL filter pipette tips sterile')">1000 uL filter tips</button>
    <button class="pill" onclick="q('cryogenic vials 2 mL external thread polypropylene')">2 mL cryogenic vials</button>
    <button class="pill" onclick="q('6 well plate tissue culture treated')">6-well plate TC</button>
    <button class="pill" onclick="q('Cytiva Hyclone PBS phosphate buffered saline 1x')">Hyclone PBS</button>
    <button class="pill" onclick="q('75 cm2 tissue culture flask T-75')">T-75 flask</button>
  </div>
</div>
</div>

<!-- Pipeline steps rendered here -->
<div class="pipeline" id="pipeline">

  <!-- Step 1: Retrieval -->
  <div class="step" id="stepRetrieval">
    <div class="step-header">
      <div class="step-num">1</div>
      <div class="step-title">FAISS Semantic Retrieval</div>
      <div class="step-meta" id="retrievalMeta">searching…</div>
    </div>
    <div class="step-body">
      <div class="loading-bar" id="retrievalBar"><div class="loading-bar-fill"></div></div>
      <div id="retrievalContent"></div>
    </div>
  </div>

  <!-- Step 2: LLM reasoning -->
  <div class="step" id="stepLLM">
    <div class="step-header">
      <div class="step-num">2</div>
      <div class="step-title">LLM Equivalence Reasoning</div>
      <div class="step-meta" id="llmMeta">sending to both models…</div>
    </div>
    <div class="step-body">
      <div class="llm-cols">
        <div class="llm-card" id="cardOllama">
          <div class="llm-card-header">
            <span class="dot" id="ollamaCardDot"></span>
            <span class="llm-name">Ollama / qwen2.5:7b</span>
            <span class="llm-latency" id="ollamaLatency"></span>
          </div>
          <div class="llm-card-body" id="ollamaResult">
            <div class="thinking"><div class="spinner"></div>Reasoning…</div>
          </div>
        </div>
        <div class="llm-card" id="cardNim">
          <div class="llm-card-header">
            <span class="dot" id="nimCardDot"></span>
            <span class="llm-name">NIM / nemotron-3-nano</span>
            <span class="llm-latency" id="nimLatency"></span>
          </div>
          <div class="llm-card-body" id="nimResult">
            <div class="thinking"><div class="spinner"></div>Reasoning…</div>
          </div>
        </div>
      </div>
    </div>
  </div>

</div><!-- /pipeline -->
</div><!-- /app -->

<script>
// ── Config ───────────────────────────────────────────────────────────────────
const API_BASE = 'http://localhost:8080';

// ── State ─────────────────────────────────────────────────────────────────────
let currentCandidates = [];
let currentQuery      = '';

// ── Health check ─────────────────────────────────────────────────────────────
async function checkEndpoints() {
  try {
    const r = await fetch(API_BASE + '/health', { signal: AbortSignal.timeout(3000) });
    const d = await r.json();
    const isReady = d.status === 'ok';
    setDot('ollamaDot', !!d.llm_endpoint);
    document.getElementById('ollamaLabel').textContent = d.llm_endpoint || 'No LLM';
    setDot('nimDot', false);
    document.getElementById('nimLabel').textContent = d.index_vectors
      ? `${(d.index_vectors/1e6).toFixed(1)}M vectors` : 'index not loaded';
    document.getElementById('offlineWarn').style.display =
      !d.llm_endpoint ? 'block' : 'none';
  } catch(e) {
    setDot('ollamaDot', false);
    document.getElementById('ollamaLabel').textContent = 'API offline';
    document.getElementById('offlineWarn').style.display = 'block';
  }
}

function setDot(id, on) {
  const el = document.getElementById(id);
  el.classList.remove('on', 'off');
  el.classList.add(on ? 'on' : 'off');
}

// ── Quick pill ────────────────────────────────────────────────────────────────
function q(query, mfr='', part='') {
  document.getElementById('queryInput').value = query;
  document.getElementById('mfrInput').value   = mfr;
  document.getElementById('partInput').value  = part;
  runSearch();
}

function clearAll() {
  ['queryInput','mfrInput','partInput'].forEach(id => document.getElementById(id).value = '');
  ['stepRetrieval','stepLLM'].forEach(id => {
    document.getElementById(id).classList.remove('visible');
  });
  currentCandidates = [];
}

document.addEventListener('keydown', e => {
  if (e.key === 'Enter' && ['queryInput','mfrInput','partInput'].includes(e.target.id)) runSearch();
});

function fmt(n) {
  return '$' + Number(n || 0).toLocaleString('en-US', {minimumFractionDigits:2, maximumFractionDigits:2});
}
function distBadge(d) {
  const cls = ['Neta','VWR','Fisher','DOT'].includes(d) ? `dist-${d}` : '';
  return `<span class="dist-badge ${cls}">${d || '?'}</span>`;
}

// ── Main search ───────────────────────────────────────────────────────────────
async function runSearch() {
  const query = document.getElementById('queryInput').value.trim();
  if (!query) { document.getElementById('queryInput').focus(); return; }
  currentQuery = query;
  const mfr  = document.getElementById('mfrInput').value.trim() || null;
  const part = document.getElementById('partInput').value.trim() || null;

  document.getElementById('stepRetrieval').classList.add('visible');
  document.getElementById('stepLLM').classList.remove('visible');
  setBarLoading('retrievalBar', true);
  document.getElementById('retrievalMeta').textContent = 'searching…';
  document.getElementById('retrievalContent').innerHTML = '';
  document.getElementById('searchBtn').disabled = true;

  const t0 = Date.now();

  try {
    // Step 1: Get candidates from /candidates endpoint (fast, no LLM)
    const params = new URLSearchParams({ query });
    if (mfr)  params.append('manufacturer', mfr);
    if (part) params.append('part_number', part);

    const candResp = await fetch(API_BASE + '/candidates?' + params.toString());
    if (!candResp.ok) throw new Error(`API ${candResp.status}`);
    const candData = await candResp.json();

    const elapsed = Date.now() - t0;
    setBarLoading('retrievalBar', false);
    setBarDone('retrievalBar');

    const tier = candData.tier;
    const candidates = candData.candidates || [];
    currentCandidates = candidates;

    const tierLabel = tier === 'exact' ? 'exact part-number match' : `semantic  cos ≥ 0.85`;
    document.getElementById('retrievalMeta').textContent =
      `${candidates.length} candidates  ·  ${tierLabel}  ·  ${elapsed}ms`;

    renderCandidates(candidates, tier);

    if (candidates.length === 0) {
      document.getElementById('searchBtn').disabled = false;
      return;
    }

    // Step 2: LLM reasoning via /search_both
    showStep('stepLLM');
    document.getElementById('llmMeta').textContent = 'reasoning…';

    // Show spinners
    document.getElementById('ollamaResult').innerHTML = '<div class="thinking"><div class="spinner"></div>Reasoning…</div>';
    document.getElementById('nimResult').innerHTML    = '<div class="thinking"><div class="spinner"></div>Reasoning…</div>';

    const llmResp = await fetch(API_BASE + '/search_both', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, manufacturer: mfr, part_number: part }),
      signal: AbortSignal.timeout(90000)
    });

    if (!llmResp.ok) throw new Error(`LLM API ${llmResp.status}`);
    const llmData = await llmResp.json();

    // Display results in both cards
    const activeEp = llmData.active_endpoint || '';
    const isOllama = activeEp.includes('Ollama') || activeEp.includes('qwen');

    // Ollama card
    if (llmData.ollama || isOllama) {
      const r = llmData.ollama || (isOllama ? { parsed: llmData.ollama, elapsed: 0 } : null);
      renderAPIResult('ollamaResult', 'ollamaLatency', 'ollamaCardDot', r || llmData.nim, true);
    } else {
      renderAPIResult('ollamaResult', 'ollamaLatency', 'ollamaCardDot', null, false);
    }

    // NIM card - show same result or offline
    if (llmData.nim) {
      renderAPIResult('nimResult', 'nimLatency', 'nimCardDot', llmData.nim, true);
    } else {
      // Show the active endpoint result in NIM card too so both show something
      if (llmData.ollama || isOllama) {
        const r = llmData.ollama;
        if (r) {
          document.getElementById('nimCardDot').className = 'dot on';
          document.getElementById('nimLatency').textContent = `via ${activeEp}`;
          renderAPIResult('nimResult', 'nimLatency', 'nimCardDot', r, true);
        } else {
          document.getElementById('nimResult').innerHTML = '<div class="err-box">NIM server offline</div>';
          document.getElementById('nimCardDot').className = 'dot off';
        }
      } else {
        document.getElementById('nimResult').innerHTML = '<div class="err-box">NIM server offline</div>';
        document.getElementById('nimCardDot').className = 'dot off';
      }
    }

    document.getElementById('llmMeta').textContent = `complete · via ${activeEp || 'API'}`;

  } catch(err) {
    setBarLoading('retrievalBar', false);
    document.getElementById('retrievalContent').innerHTML =
      `<div class="err-box">Error: ${err.message.substring(0,200)}<br>
       Make sure the API is running: <code>uvicorn btaa_api.main:app --port 8080</code></div>`;
    document.getElementById('retrievalMeta').textContent = 'error';
  }

  document.getElementById('searchBtn').disabled = false;
}

function renderAPIResult(resultId, latencyId, dotId, result, isOnline) {
  const el  = document.getElementById(resultId);
  const lat = document.getElementById(latencyId);
  const dot = document.getElementById(dotId);

  if (!isOnline || !result) {
    dot.className = 'dot off';
    el.innerHTML = '<div class="err-box">Endpoint offline</div>';
    return;
  }

  dot.className = 'dot on';
  if (result.elapsed) lat.textContent = `${result.elapsed.toFixed(1)}s`;

  const d = result.parsed;
  if (!d || !d.best || !d.best.price) {
    el.innerHTML = '<p class="no-equiv">No equivalent products identified.</p>';
    return;
  }

  const best = d.best;
  const savingsHtml = d.savings_vs_worst > 0
    ? `<div class="savings-tag">↓ Save ${fmt(d.savings_vs_worst)} vs highest</div>` : '';
  const alts = (d.alternatives || []).slice(0,4);
  const altsHtml = alts.length ? `
    <div class="alts-label">Other equivalent prices</div>
    ${alts.map(a => `<div class="alt-row">
      ${distBadge(a.distributor)}
      <span class="alt-price">${fmt(a.price)}</span>
      <span class="alt-desc">${(a.description||'').substring(0,60)}</span>
    </div>`).join('')}` : '';
  const reasonHtml = d.reasoning
    ? `<div class="reasoning-box">${d.reasoning}</div>` : '';

  el.innerHTML = `
    <div class="result-price">${fmt(best.price)}</div>
    <div class="result-from">${distBadge(best.distributor)} &nbsp;${best.manufacturer||''}</div>
    ${savingsHtml}
    <div class="result-desc">${(best.description||'').substring(0,100)}</div>
    ${altsHtml}
    ${reasonHtml}`;
}

function renderCandidates(candidates, tier) {
  if (!candidates.length) {
    document.getElementById('retrievalContent').innerHTML =
      '<p style="color:var(--muted);font-style:italic;font-size:13px">No candidates found. Try a broader description.</p>';
    return;
  }
  const rows = candidates.map((c, i) => {
    const cos = c.cosine != null ? `<span style="color:var(--mid);font-weight:500">${Number(c.cosine).toFixed(3)}</span>` : '—';
    const isBest = i === 0 && tier === 'exact';
    const tag = isBest ? '<span style="background:var(--green);color:white;padding:1px 6px;border-radius:3px;font-size:10px;font-family:var(--mono)">BEST</span>' : '';
    return `<tr>
      <td class="cos">${cos}</td>
      <td>${distBadge(c.distributor)}</td>
      <td class="num">${fmt(c.price)}</td>
      <td style="font-size:12px;color:var(--muted)">${(c.manufacturer||'').substring(0,25)}</td>
      <td style="font-size:13px">${(c.description||'').substring(0,90)} ${tag}</td>
      <td style="font-size:11px;font-family:var(--mono);color:var(--muted)">${c.catalog_num||''}</td>
    </tr>`;
  }).join('');

  document.getElementById('retrievalContent').innerHTML = `
    <div class="table-wrap">
      <table>
        <thead><tr>
          <th>cos</th><th>Distributor</th><th>Price</th>
          <th>Manufacturer</th><th>Description</th><th>Catalog #</th>
        </tr></thead>
        <tbody>${rows}</tbody>
      </table>
    </div>`;
}

// ── UI helpers ────────────────────────────────────────────────────────────────
function showStep(id) {
  document.getElementById(id).classList.add('visible');
  document.getElementById(id).scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}
function setBarLoading(id, on) {
  const el = document.getElementById(id);
  el.classList.remove('done');
  el.querySelector('.loading-bar-fill').style.animation = on ? 'indeterminate 1.4s ease infinite' : 'none';
}
function setBarDone(id) {
  document.getElementById(id).classList.add('done');
}

// ── Browse mode ──────────────────────────────────────────────────────────────
let taxonomyData = {};

function setMode(mode) {
  const isSearch = mode === 'search';
  document.getElementById('tabSearch').classList.toggle('active', isSearch);
  document.getElementById('tabBrowse').classList.toggle('active', !isSearch);
  document.getElementById('searchMode').style.display = isSearch ? 'block' : 'none';
  document.getElementById('browseMode').classList.toggle('visible', !isSearch);
  // Hide pipeline steps when switching modes
  if (!isSearch) {
    document.getElementById('stepRetrieval').classList.remove('visible');
    document.getElementById('stepLLM').classList.remove('visible');
  }
}

async function loadTaxonomy() {
  try {
    const r = await fetch(API_BASE + '/browse/taxonomy');
    if (!r.ok) return;
    taxonomyData = await r.json();
    const sel = document.getElementById('browseCategory');
    sel.innerHTML = '<option value="">Select a category…</option>';
    Object.keys(taxonomyData).forEach(cat => {
      const opt = document.createElement('option');
      opt.value = cat;
      opt.textContent = cat;
      sel.appendChild(opt);
    });
  } catch(e) {
    console.warn('Taxonomy load failed:', e);
  }
}

function onCategoryChange() {
  const cat = document.getElementById('browseCategory').value;
  const subSel = document.getElementById('browseSubcategory');
  const btn = document.getElementById('browseBtn');
  subSel.innerHTML = '<option value="">Select product type…</option>';
  subSel.disabled = !cat;
  btn.disabled = true;
  document.getElementById('browseResults').innerHTML = '';
  if (!cat || !taxonomyData[cat]) return;
  taxonomyData[cat].forEach(sub => {
    const opt = document.createElement('option');
    opt.value = sub;
    opt.textContent = sub;
    subSel.appendChild(opt);
  });
}

function onSubcategoryChange() {
  const sub = document.getElementById('browseSubcategory').value;
  document.getElementById('browseBtn').disabled = !sub;
  document.getElementById('browseResults').innerHTML = '';
}

async function runBrowse() {
  const cat = document.getElementById('browseCategory').value;
  const sub = document.getElementById('browseSubcategory').value;
  if (!cat || !sub) return;

  const btn = document.getElementById('browseBtn');
  const resultsEl = document.getElementById('browseResults');
  btn.disabled = true;
  btn.textContent = 'Loading…';
  resultsEl.innerHTML = '<p style="color:var(--muted);font-size:13px;padding:12px 0">Searching catalog…</p>';

  try {
    const params = new URLSearchParams({ category: cat, subcategory: sub, limit: 60 });
    const r = await fetch(API_BASE + '/browse/products?' + params.toString());
    if (!r.ok) throw new Error(`API ${r.status}`);
    const data = await r.json();

    if (!data.products || data.products.length === 0) {
      resultsEl.innerHTML = '<p style="color:var(--muted);font-size:13px;padding:12px 0;font-style:italic">No products found in this category. Try a different subcategory.</p>';
      return;
    }

    const rows = data.products.map((p, i) => `
      <tr onclick="searchFromBrowse('${p.description.replace(/'/g, "\'")}')">
        <td>${distBadge(p.distributor)}</td>
        <td class="bnum">${fmt(p.price)}</td>
        <td style="font-size:12px;color:var(--muted)">${(p.manufacturer||'').substring(0,22)}</td>
        <td style="font-size:13px">${p.description.substring(0,90)}</td>
        <td style="font-size:11px;font-family:var(--mono);color:var(--muted)">${p.catalog_num||''}</td>
      </tr>`).join('');

    resultsEl.innerHTML = `
      <div class="browse-results">
        <div class="browse-results-header">
          <span class="browse-results-title">${sub}</span>
          <span class="browse-results-meta">${data.showing} of ${data.total.toLocaleString()} products · sorted by price</span>
        </div>
        <div class="browse-table-wrap">
          <table class="browse-table">
            <thead><tr>
              <th>Distributor</th><th>Price</th><th>Manufacturer</th>
              <th>Description</th><th>Catalog #</th>
            </tr></thead>
            <tbody>${rows}</tbody>
          </table>
        </div>
        <p class="click-hint">💡 Click any row to search for that product across all distributors and find the best price</p>
      </div>`;

  } catch(e) {
    resultsEl.innerHTML = `<p style="color:var(--red);font-size:13px;padding:12px 0">Error: ${e.message}</p>`;
  } finally {
    btn.disabled = false;
    btn.textContent = 'Show Products';
  }
}

function searchFromBrowse(description) {
  // Switch to search mode and run the query
  setMode('search');
  document.getElementById('queryInput').value = description.substring(0, 80);
  document.getElementById('mfrInput').value = '';
  document.getElementById('partInput').value = '';
  runSearch();
}

// ── Init ──────────────────────────────────────────────────────────────────────
checkEndpoints();
loadTaxonomy();
setInterval(checkEndpoints, 15000);
</script>
</body>
</html>
