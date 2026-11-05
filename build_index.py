import json
import os

with open('public/initial_data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

p2_json = json.dumps(data['p2'])
p3_json = json.dumps(data['p3'])

template = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>LLM Engineering Portfolio — Production Systems & Evaluation</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg: #f8fafc;
      --card-bg: #ffffff;
      --border: #e2e8f0;
      --border-focus: #3b82f6;
      --primary: #2563eb;
      --primary-hover: #1d4ed8;
      --text-main: #0f172a;
      --text-muted: #64748b;
      --success-bg: #ecfdf5;
      --success-text: #065f46;
      --success-border: #a7f3d0;
      --warning-bg: #fffbeb;
      --warning-text: #92400e;
      --warning-border: #fde68a;
      --danger-bg: #fef2f2;
      --danger-text: #991b1b;
      --danger-border: #fecaca;
    }

    * {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }

    body {
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
      background-color: var(--bg);
      color: var(--text-main);
      line-height: 1.5;
      -webkit-font-smoothing: antialiased;
    }

    .hidden {
      display: none !important;
    }

    /* Header */
    header {
      background: #0f172a;
      color: #fff;
      padding: 1.25rem 2rem;
      border-bottom: 1px solid #1e293b;
    }
    .header-inner {
      max-width: 1200px;
      margin: 0 auto;
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 1rem;
    }
    .brand {
      display: flex;
      align-items: center;
      gap: 0.75rem;
    }
    .brand-icon {
      width: 36px;
      height: 36px;
      background: #2563eb;
      border-radius: 8px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 1.25rem;
    }
    .brand-title {
      font-size: 1.15rem;
      font-weight: 700;
      letter-spacing: -0.02em;
    }
    .brand-subtitle {
      font-size: 0.8rem;
      color: #94a3b8;
    }
    .gh-link {
      color: #e2e8f0;
      text-decoration: none;
      font-size: 0.85rem;
      font-weight: 600;
      display: inline-flex;
      align-items: center;
      gap: 0.5rem;
      background: #1e293b;
      padding: 0.45rem 0.85rem;
      border-radius: 6px;
      border: 1px solid #334155;
      transition: background 0.15s, border-color 0.15s;
    }
    .gh-link:hover {
      background: #334155;
      border-color: #475569;
    }

    /* Metric Banner */
    .banner {
      background: #1e293b;
      color: #fff;
      padding: 1.25rem 2rem;
      border-bottom: 1px solid #334155;
    }
    .banner-grid {
      max-width: 1200px;
      margin: 0 auto;
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
      gap: 1.25rem;
    }
    .banner-card {
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid rgba(255, 255, 255, 0.1);
      border-radius: 8px;
      padding: 1rem 1.25rem;
    }
    .banner-tag {
      font-size: 0.72rem;
      text-transform: uppercase;
      font-weight: 700;
      letter-spacing: 0.05em;
      color: #60a5fa;
      margin-bottom: 0.25rem;
    }
    .banner-val {
      font-size: 1.4rem;
      font-weight: 800;
      letter-spacing: -0.02em;
    }
    .banner-val span {
      font-size: 0.85rem;
      font-weight: 500;
      color: #94a3b8;
    }
    .banner-desc {
      font-size: 0.78rem;
      color: #cbd5e1;
      margin-top: 0.35rem;
    }

    /* Main Container */
    .container {
      max-width: 1200px;
      margin: 2rem auto;
      padding: 0 1.5rem;
    }

    /* Tabs Navigation */
    .tabs-nav {
      display: flex;
      gap: 0.5rem;
      border-bottom: 2px solid #e2e8f0;
      margin-bottom: 1.75rem;
      overflow-x: auto;
      padding-bottom: 2px;
    }
    .tab-btn {
      background: transparent;
      border: none;
      font-size: 0.92rem;
      font-weight: 600;
      color: #64748b;
      padding: 0.75rem 1.25rem;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 0.5rem;
      border-bottom: 2px solid transparent;
      margin-bottom: -4px;
      transition: color 0.15s, border-color 0.15s;
      white-space: nowrap;
    }
    .tab-btn:hover {
      color: #1e293b;
    }
    .tab-btn.active {
      color: #2563eb;
      border-bottom-color: #2563eb;
    }

    /* Cards & Layout */
    .card {
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 1.5rem;
      box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
      margin-bottom: 1.5rem;
    }
    .grid-2-1 {
      display: grid;
      grid-template-columns: 2fr 1fr;
      gap: 1.5rem;
    }
    .grid-2 {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 1.5rem;
    }
    @media (max-width: 900px) {
      .grid-2-1, .grid-2 {
        grid-template-columns: 1fr;
      }
    }

    /* Form Controls & Inputs */
    label {
      display: block;
      margin-bottom: 0.35rem;
    }
    select, input[type="text"] {
      width: 100% !important;
      display: block;
      min-height: 42px;
      padding: 0.6rem 0.85rem;
      border: 1px solid var(--border);
      border-radius: 8px;
      font-size: 0.9rem;
      color: var(--text-main);
      background: #fff;
      outline: none;
      transition: border-color 0.15s, box-shadow 0.15s;
    }
    select:focus, input[type="text"]:focus, textarea:focus {
      border-color: var(--primary);
      box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.12);
    }
    select {
      cursor: pointer;
      font-weight: 500;
    }

    .input-row {
      display: flex;
      gap: 0.75rem;
      margin-top: 1rem;
    }
    .input-row input {
      flex: 1;
    }

    .btn-primary {
      background: var(--primary);
      color: #fff;
      border: none;
      padding: 0.65rem 1.35rem;
      border-radius: 8px;
      font-weight: 600;
      font-size: 0.9rem;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 0.4rem;
      white-space: nowrap;
      transition: background 0.15s;
    }
    .btn-primary:hover { background: var(--primary-hover); }
    .btn-primary:disabled {
      opacity: 0.6;
      cursor: not-allowed;
    }
    .btn-emerald { background: #059669; }
    .btn-emerald:hover { background: #047857; }
    .btn-indigo { background: #4f46e5; }
    .btn-indigo:hover { background: #4338ca; }

    /* Preset Pills */
    .presets {
      display: flex;
      flex-wrap: wrap;
      gap: 0.5rem;
      align-items: center;
      margin-top: 0.75rem;
    }
    .preset-pill {
      background: #f1f5f9;
      color: #334155;
      border: 1px solid #cbd5e1;
      border-radius: 9999px;
      padding: 0.3rem 0.75rem;
      font-size: 0.75rem;
      font-weight: 600;
      cursor: pointer;
      transition: background 0.15s, border-color 0.15s;
    }
    .preset-pill:hover {
      background: #e2e8f0;
      border-color: #94a3b8;
    }

    /* Checkbox list */
    .checkbox-label {
      display: flex;
      align-items: flex-start;
      gap: 0.6rem;
      margin-bottom: 0.85rem;
      cursor: pointer;
      font-size: 0.85rem;
    }
    .checkbox-label input[type="checkbox"] {
      margin-top: 0.2rem;
      width: 16px;
      height: 16px;
      accent-color: var(--primary);
      cursor: pointer;
    }
    .setting-desc {
      font-size: 0.74rem;
      color: var(--text-muted);
      margin-top: 0.15rem;
    }

    /* Result Box & Badges */
    .result-box {
      margin-top: 1.25rem;
      border-top: 1px solid var(--border);
      padding-top: 1.25rem;
    }
    .result-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 0.75rem;
      margin-bottom: 0.75rem;
    }
    .badge {
      display: inline-flex;
      align-items: center;
      gap: 0.35rem;
      padding: 0.3rem 0.75rem;
      border-radius: 9999px;
      font-size: 0.75rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }
    .badge-hit { background: var(--success-bg); color: var(--success-text); border: 1px solid var(--success-border); }
    .badge-miss { background: var(--warning-bg); color: var(--warning-text); border: 1px solid var(--warning-border); }
    .badge-danger { background: var(--danger-bg); color: var(--danger-text); border: 1px solid var(--danger-border); }
    .badge-info { background: #eff6ff; color: #1e40af; border: 1px solid #bfdbfe; }

    .result-stats {
      font-size: 0.76rem;
      color: var(--text-muted);
      display: flex;
      gap: 1rem;
      font-family: 'JetBrains Mono', monospace;
    }
    .result-content {
      background: #fff;
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 1rem;
      font-size: 0.88rem;
      color: var(--text-main);
      line-height: 1.6;
    }

    /* Candidate Textareas for P2 */
    .candidate-textarea {
      width: 100% !important;
      min-height: 160px;
      padding: 0.85rem;
      border: 1px solid var(--border);
      border-radius: 8px;
      font-size: 0.85rem;
      line-height: 1.6;
      color: var(--text-main);
      background: #f8fafc;
      resize: vertical;
      font-family: inherit;
      outline: none;
      transition: border-color 0.15s, background 0.15s;
    }
    .candidate-textarea:focus {
      background: #fff;
      border-color: var(--primary);
      box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
    }
    .edit-hint {
      font-size: 0.72rem;
      color: var(--text-muted);
      font-style: italic;
      margin-top: 0.25rem;
    }
  </style>
</head>
<body>

  <!-- Header -->
  <header>
    <div class="header-inner">
      <div class="brand">
        <div class="brand-icon">⚙️</div>
        <div>
          <div class="brand-title">Production LLM Systems & Evaluation Suite</div>
          <div class="brand-subtitle">Designed by Shivam Jaiswal — Real Empirical Benchmarks</div>
        </div>
      </div>
      <a href="https://github.com/Shivam9621/llm-portfolio" target="_blank" class="gh-link">
        <svg width="16" height="16" fill="currentColor" viewBox="0 0 16 16"><path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.012 8.012 0 0 0 16 8c0-4.42-3.58-8-8-8z"/></svg>
        GitHub Repository
      </a>
    </div>
  </header>

  <!-- Metric Banner -->
  <div class="banner">
    <div class="banner-grid">
      <div class="banner-card">
        <div class="banner-tag">Project 1: Semantic Cache</div>
        <div class="banner-val">14.0% Hit Rate <span>| 0 False Hits</span></div>
        <div class="banner-desc">FAISS vector cosine lookup drops latency from 1,144 ms to 0.11 ms (98.2% faster).</div>
      </div>
      <div class="banner-card">
        <div class="banner-tag">Project 2: LLM Judge Audit</div>
        <div class="banner-val">36.7% Agreement <span>| 25 Flips Solved</span></div>
        <div class="banner-desc">Bidirectional order checks + length-neutral rules eliminate position & verbosity bias.</div>
      </div>
      <div class="banner-card">
        <div class="banner-tag">Project 3: RAG Injection Defense</div>
        <div class="banner-val">0% ASR <span>(Down from 100%)</span></div>
        <div class="banner-desc">10/10 poisoned documents stopped; 0 false blocks across 20 normal queries.</div>
      </div>
    </div>
  </div>

  <!-- Main Container -->
  <div class="container">
    <!-- Tabs Nav -->
    <div class="tabs-nav">
      <button class="tab-btn active" id="tab-btn-p1" onclick="showTab('p1')">
        ⚡ Project 1: Semantic Cache Playground
      </button>
      <button class="tab-btn" id="tab-btn-p2" onclick="showTab('p2')">
        ⚖️ Project 2: LLM-as-a-Judge Arena
      </button>
      <button class="tab-btn" id="tab-btn-p3" onclick="showTab('p3')">
        🛡️ Project 3: RAG Injection Sandbox
      </button>
    </div>

    <!-- ================================================================= -->
    <!-- TAB 1: SEMANTIC CACHE -->
    <!-- ================================================================= -->
    <div id="tab-p1">
      <div class="grid-2-1">
        <div class="card">
          <h2 style="font-size: 1.15rem; font-weight: 800;">Query the Vector Semantic Cache</h2>
          <p style="font-size: 0.8rem; color: var(--text-muted); margin-top: 0.2rem;">
            Test exact queries, multilingual paraphrases, negation guardrails, and real-time latency savings.
          </p>

          <div class="presets">
            <span style="font-size: 0.75rem; color: var(--text-muted);">Quick Presets:</span>
            <button class="preset-pill" onclick="setPreset('What is your return policy?')">Exact FAQ</button>
            <button class="preset-pill" onclick="setPreset('can i get a refund on an item i bought?')">Semantic Paraphrase</button>
            <button class="preset-pill" onclick="setPreset('Why is international shipping not available?')">Adversarial Negation</button>
            <button class="preset-pill" onclick="setPreset('What is the capital of Australia?')">Out of Scope</button>
          </div>

          <div class="input-row">
            <input type="text" id="p1-input" value="What is your return policy?" placeholder="Ask any e-commerce question...">
            <button class="btn-primary" id="p1-btn" onclick="submitP1()">Ask Bot</button>
          </div>

          <div id="p1-result" class="result-box hidden">
            <div class="result-header">
              <span id="p1-badge" class="badge"></span>
              <div class="result-stats">
                <span>Sim: <strong id="p1-sim" style="color: var(--text-main);"></strong></span>
                <span>Latency: <strong id="p1-lat" style="color: var(--text-main);"></strong></span>
                <span>Tokens: <strong id="p1-tok" style="color: var(--text-main);"></strong></span>
              </div>
            </div>
            <div style="font-size: 0.72rem; font-weight: 700; color: var(--text-muted); text-transform: uppercase; margin-bottom: 0.25rem;">Bot Answer:</div>
            <div id="p1-answer" class="result-content"></div>
          </div>
        </div>

        <!-- P1 Settings -->
        <div class="card">
          <h3 style="font-size: 0.9rem; font-weight: 800; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 1rem;">⚙️ Cache Configuration</h3>

          <div style="margin-bottom: 1rem;">
            <div style="display: flex; justify-content: space-between; font-size: 0.8rem; font-weight: 700;">
              <span>Similarity Threshold (T)</span>
              <span id="p1-thresh-val" style="color: var(--primary);">0.75</span>
            </div>
            <input type="range" id="p1-threshold" min="0.50" max="0.95" step="0.05" value="0.75" style="width: 100%; margin-top: 0.5rem;" oninput="document.getElementById('p1-thresh-val').innerText = this.value;">
            <div class="setting-desc">Calibrated at 0.75 for 14.0% hit rate with 0.0% false hits.</div>
          </div>

          <label class="checkbox-label">
            <input type="checkbox" id="p1-neg" checked>
            <div>
              <strong>Negation Polarity Guard</strong>
              <div class="setting-desc">Prevents semantic collisions across positive/negative requests.</div>
            </div>
          </label>

          <label class="checkbox-label">
            <input type="checkbox" id="p1-pii" checked>
            <div>
              <strong>PII & Order-ID Sanitizer</strong>
              <div class="setting-desc">Refuses caching answers containing order IDs or names.</div>
            </div>
          </label>
        </div>
      </div>
    </div>

    <!-- ================================================================= -->
    <!-- TAB 2: LLM JUDGE -->
    <!-- ================================================================= -->
    <div id="tab-p2" class="hidden">
      <div class="card" style="margin-bottom: 1.5rem;">
        <h2 style="font-size: 1.15rem; font-weight: 800;">LLM-as-a-Judge Bias Arena</h2>
        <p style="font-size: 0.8rem; color: var(--text-muted); margin-top: 0.2rem;">
          Compare Candidate A (Concise Engineer) vs Candidate B (Verbose Academic) across 30 technical backend engineering questions. You can pick any question or edit the answers directly below!
        </p>

        <div style="margin-top: 1rem; display: flex; gap: 1rem; flex-wrap: wrap; align-items: flex-end;">
          <div style="flex: 1; min-width: 300px;">
            <label style="font-size: 0.75rem; font-weight: 700; text-transform: uppercase;">Select Benchmark Question:</label>
            <select id="p2-select" onchange="renderP2Selected()"></select>
          </div>
          <label class="checkbox-label" style="margin: 0; padding-bottom: 0.6rem;">
            <input type="checkbox" id="p2-swap">
            <span>Swap Order (B then A)</span>
          </label>
          <label class="checkbox-label" style="margin: 0; padding-bottom: 0.6rem;">
            <input type="checkbox" id="p2-length-neutral">
            <span>'Length Does Not Matter' Rule</span>
          </label>
          <button class="btn-primary btn-indigo" id="p2-btn" onclick="submitP2()">Evaluate with Judge</button>
        </div>
      </div>

      <div class="grid-2">
        <div class="card">
          <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
            <strong style="color: #2563eb; font-size: 0.85rem; text-transform: uppercase;">Candidate A: Concise Engineer</strong>
            <span id="p2-words-a" style="font-size: 0.75rem; color: var(--text-muted);"></span>
          </div>
          <textarea id="p2-text-a" class="candidate-textarea" oninput="updateP2WordCounts()" placeholder="Type or edit Candidate A response..."></textarea>
          <div class="edit-hint">✎ You can click and edit Candidate A's answer directly to test judge responses.</div>
        </div>

        <div class="card">
          <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
            <strong style="color: #7c3aed; font-size: 0.85rem; text-transform: uppercase;">Candidate B: Verbose Academic</strong>
            <span id="p2-words-b" style="font-size: 0.75rem; color: var(--text-muted);"></span>
          </div>
          <textarea id="p2-text-b" class="candidate-textarea" oninput="updateP2WordCounts()" placeholder="Type or edit Candidate B response..."></textarea>
          <div class="edit-hint">✎ You can click and edit Candidate B's answer directly to test judge responses.</div>
        </div>
      </div>

      <div id="p2-result" class="result-box hidden">
        <div class="result-header">
          <span id="p2-badge" class="badge"></span>
          <span id="p2-pres" style="font-size: 0.75rem; color: var(--text-muted);"></span>
        </div>
        <div style="font-size: 0.72rem; font-weight: 700; color: var(--text-muted); text-transform: uppercase; margin-bottom: 0.25rem;">Judge Reasoning & Scorecard:</div>
        <div id="p2-reason" class="result-content"></div>
      </div>
    </div>

    <!-- ================================================================= -->
    <!-- TAB 3: PROMPT INJECTION -->
    <!-- ================================================================= -->
    <div id="tab-p3" class="hidden">
      <div class="grid-2-1">
        <div class="card">
          <h2 style="font-size: 1.15rem; font-weight: 800;">RAG Indirect Prompt-Injection Simulator</h2>
          <p style="font-size: 0.8rem; color: var(--text-muted); margin-top: 0.2rem;">
            Launch real poisoned documents into retrieval to test if target secret (<code>TIGER-42</code>) leaks.
          </p>

          <div style="margin-top: 1rem;">
            <label style="font-size: 0.75rem; font-weight: 700; text-transform: uppercase;">Select Attack Scenario:</label>
            <select id="p3-select" onchange="renderP3Selected()"></select>
          </div>

          <div style="margin-top: 1rem; background: #f8fafc; border: 1px solid var(--border); border-radius: 8px; padding: 1rem;">
            <div>
              <label style="font-size: 0.75rem; font-weight: 700; text-transform: uppercase;">Trigger Query (Editable):</label>
              <input type="text" id="p3-query-input" style="font-family: 'JetBrains Mono', monospace; font-size: 0.85rem; margin-top: 0.25rem;">
            </div>
            <div style="margin-top: 0.65rem; font-size: 0.82rem;">
              <strong>Target Secret:</strong> <span id="p3-target" style="color: #dc2626; font-family: 'JetBrains Mono', monospace;"></span>
            </div>
            <div id="p3-desc" style="color: var(--text-muted); margin-top: 0.4rem; font-size: 0.8rem;"></div>
          </div>

          <div style="margin-top: 1rem;">
            <button class="btn-primary btn-emerald" id="p3-btn" onclick="submitP3()">Launch Query to RAG Bot</button>
          </div>

          <div id="p3-result" class="result-box hidden">
            <div class="result-header">
              <span id="p3-badge" class="badge"></span>
              <span id="p3-poison-info" style="font-size: 0.75rem; color: var(--text-muted); font-family: 'JetBrains Mono', monospace;"></span>
            </div>
            <div style="font-size: 0.72rem; font-weight: 700; color: var(--text-muted); text-transform: uppercase; margin-bottom: 0.25rem;">Bot Output:</div>
            <div id="p3-response" class="result-content" style="font-family: 'JetBrains Mono', monospace; font-size: 0.82rem;"></div>
          </div>
        </div>

        <!-- P3 Defense Layers -->
        <div class="card">
          <h3 style="font-size: 0.9rem; font-weight: 800; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.5rem;">🛡️ Defense in Depth Layers</h3>
          <p style="font-size: 0.75rem; color: var(--text-muted); margin-bottom: 1rem;">Toggle layers to see how defense combinations neutralize injections.</p>

          <label class="checkbox-label">
            <input type="checkbox" id="p3-l1" checked>
            <div>
              <strong>Layer 1: Spotlighting</strong>
              <div class="setting-desc">Wraps documents in &lt;document&gt; tags with passive-data prompt constraint.</div>
            </div>
          </label>

          <label class="checkbox-label">
            <input type="checkbox" id="p3-l2" checked>
            <div>
              <strong>Layer 2: Input Quarantine</strong>
              <div class="setting-desc">Scans retrieved chunks for regex jailbreaks and exfiltration syntax.</div>
            </div>
          </label>

          <label class="checkbox-label">
            <input type="checkbox" id="p3-l3" checked>
            <div>
              <strong>Layer 3: Output Redaction</strong>
              <div class="setting-desc">Masks leaked passwords (TIGER-42) and blocks unauthorized links.</div>
            </div>
          </label>

          <label class="checkbox-label">
            <input type="checkbox" id="p3-l4" checked>
            <div>
              <strong>Layer 4: Least Privilege</strong>
              <div class="setting-desc">Removes internal administrative credentials from the system instructions.</div>
            </div>
          </label>
        </div>
      </div>
    </div>
  </div>

  <script>
    // Embedded Initial Data for 100% Instant Zero-Network Rendering
    let p2Questions = __P2_JSON__;
    let p3Attacks = __P3_JSON__;

    function showTab(id) {
      ['p1', 'p2', 'p3'].forEach(t => {
        document.getElementById(`tab-${t}`).classList.add('hidden');
        document.getElementById(`tab-btn-${t}`).classList.remove('active');
      });
      document.getElementById(`tab-${id}`).classList.remove('hidden');
      document.getElementById(`tab-btn-${id}`).classList.add('active');

      if (id === 'p2') renderP2Selected();
      if (id === 'p3') renderP3Selected();
    }

    function setPreset(val) {
      document.getElementById('p1-input').value = val;
      submitP1();
    }

    async function submitP1() {
      const q = document.getElementById('p1-input').value.trim();
      const t = parseFloat(document.getElementById('p1-threshold').value);
      const neg = document.getElementById('p1-neg').checked;
      const pii = document.getElementById('p1-pii').checked;
      const btn = document.getElementById('p1-btn');

      btn.innerText = 'Searching...';
      btn.disabled = true;

      try {
        const res = await fetch('/api/p1/query', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({ question: q, threshold: t, enable_neg_guard: neg, enable_pii_filter: pii })
        }).then(r => r.json());

        const box = document.getElementById('p1-result');
        const badge = document.getElementById('p1-badge');
        box.classList.remove('hidden');

        if (res.hit) {
          badge.className = 'badge badge-hit';
          badge.innerText = `CACHE HIT (${res.matched_faq_id})`;
        } else {
          badge.className = 'badge badge-miss';
          badge.innerText = res.audit?.negation_blocked ? 'LLM (NEGATION GUARD BLOCKED)' : 'LLM FALLBACK (MISS)';
        }

        document.getElementById('p1-sim').innerText = res.similarity;
        document.getElementById('p1-lat').innerText = res.latency_ms + ' ms';
        document.getElementById('p1-tok').innerText = res.tokens;
        document.getElementById('p1-answer').innerText = res.answer;
      } catch (err) {
        alert('API query failed: ' + err.message);
      } finally {
        btn.innerText = 'Ask Bot';
        btn.disabled = false;
      }
    }

    function updateP2WordCounts() {
      const textA = (document.getElementById('p2-text-a').value || '').trim();
      const textB = (document.getElementById('p2-text-b').value || '').trim();
      document.getElementById('p2-words-a').innerText = (textA ? textA.split(/\\s+/).length : 0) + ' words';
      document.getElementById('p2-words-b').innerText = (textB ? textB.split(/\\s+/).length : 0) + ' words';
    }

    function renderP2Selected() {
      const sel = document.getElementById('p2-select');
      const id = sel.value || (p2Questions[0] ? p2Questions[0].id : 'q01');
      const item = p2Questions.find(q => q.id === id);
      if (item) {
        document.getElementById('p2-text-a').value = item.answer_a;
        document.getElementById('p2-text-b').value = item.answer_b;
        updateP2WordCounts();
      }
    }

    async function submitP2() {
      const sel = document.getElementById('p2-select');
      const id = sel.value || 'q01';
      const item = p2Questions.find(q => q.id === id);
      const questionText = item ? item.question : '';
      const textA = document.getElementById('p2-text-a').value;
      const textB = document.getElementById('p2-text-b').value;
      const swap = document.getElementById('p2-swap').checked;
      const len = document.getElementById('p2-length-neutral').checked;
      const btn = document.getElementById('p2-btn');

      btn.innerText = 'Evaluating with Judge...';
      btn.disabled = true;

      try {
        const res = await fetch('/api/p2/judge', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({
            question_id: id,
            question: questionText,
            answer_a: textA,
            answer_b: textB,
            swap_order: swap,
            length_neutral: len
          })
        }).then(r => r.json());

        const box = document.getElementById('p2-result');
        const badge = document.getElementById('p2-badge');
        box.classList.remove('hidden');

        if (res.winner === 'A') {
          badge.className = 'badge badge-info';
          badge.innerText = 'WINNER: MODEL A (CONCISE)';
        } else if (res.winner === 'B') {
          badge.className = 'badge badge-info';
          badge.innerText = 'WINNER: MODEL B (VERBOSE)';
        } else {
          badge.className = 'badge badge-miss';
          badge.innerText = 'OUTCOME: TIE';
        }

        document.getElementById('p2-pres').innerText = res.presentation || '';
        document.getElementById('p2-reason').innerText = res.reason || '';
      } catch (err) {
        alert('Judge API failed: ' + err.message);
      } finally {
        btn.innerText = 'Evaluate with Judge';
        btn.disabled = false;
      }
    }

    function renderP3Selected() {
      const sel = document.getElementById('p3-select');
      const id = sel.value || (p3Attacks[0] ? p3Attacks[0].id : 'atk_01');
      const atk = p3Attacks.find(a => a.id === id);
      if (atk) {
        document.getElementById('p3-query-input').value = atk.trigger_query;
        document.getElementById('p3-target').innerText = atk.target_pattern;
        document.getElementById('p3-desc').innerText = atk.description;
      }
    }

    async function submitP3() {
      const sel = document.getElementById('p3-select');
      const id = sel.value || 'atk_01';
      const customQuery = document.getElementById('p3-query-input').value.trim();
      const l1 = document.getElementById('p3-l1').checked;
      const l2 = document.getElementById('p3-l2').checked;
      const l3 = document.getElementById('p3-l3').checked;
      const l4 = document.getElementById('p3-l4').checked;
      const btn = document.getElementById('p3-btn');

      btn.innerText = 'Running RAG Security Pipeline...';
      btn.disabled = true;

      try {
        const res = await fetch('/api/p3/query', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({
            attack_id: id,
            custom_query: customQuery,
            layer_spotlighting: l1,
            layer_input_filter: l2,
            layer_output_filter: l3,
            layer_least_privilege: l4
          })
        }).then(r => r.json());

        const box = document.getElementById('p3-result');
        const badge = document.getElementById('p3-badge');
        box.classList.remove('hidden');

        if (res.attack_succeeded) {
          badge.className = 'badge badge-danger';
          badge.innerText = '🚨 PWNED: SECRET EXFILTRATED';
        } else {
          badge.className = 'badge badge-hit';
          badge.innerText = '✅ DEFENDED: ATTACK BLOCKED';
        }

        document.getElementById('p3-poison-info').innerText = `Poison in Top-3: ${res.poison_in_top3}`;
        document.getElementById('p3-response').innerText = res.response;
      } catch (err) {
        alert('RAG API failed: ' + err.message);
      } finally {
        btn.innerText = 'Launch Query to RAG Bot';
        btn.disabled = false;
      }
    }

    // Populate Select Options immediately
    function initApp() {
      const p2Sel = document.getElementById('p2-select');
      if (p2Sel && p2Questions.length > 0) {
        p2Sel.innerHTML = p2Questions.map(q => `<option value="${q.id}">${q.id}: ${q.question.slice(0, 80)}...</option>`).join('');
        renderP2Selected();
      }

      const p3Sel = document.getElementById('p3-select');
      if (p3Sel && p3Attacks.length > 0) {
        p3Sel.innerHTML = p3Attacks.map((a, i) => `<option value="${a.id}">Attack #${i+1}: ${a.name}</option>`).join('');
        renderP3Selected();
      }
    }

    document.addEventListener('DOMContentLoaded', initApp);
    initApp();
  </script>
</body>
</html>"""

html = template.replace('__P2_JSON__', p2_json).replace('__P3_JSON__', p3_json)

with open('public/index.html', 'w', encoding='utf-8') as f:
    f.write(html)

print('Successfully generated public/index.html!')
print('File size:', len(html.encode('utf-8')), 'bytes')
