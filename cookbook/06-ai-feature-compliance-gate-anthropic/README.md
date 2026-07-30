# 🛡️ Demo 06: AI Feature Launch Compliance Gate (Anthropic / Claude)

This demo runs a **parallel-isolated regulatory review** of a proposed product
feature using the **Octochains** framework, powered by **Anthropic's Claude**.

Four official compliance presets each read the *same* feature dossier from a
different regulatory angle — with **zero awareness of one another** — and a
`Synthesizer` merges their isolated findings into a single go / no-go
compliance memo.

## The Council

| Preset | Angle |
| :--- | :--- |
| `data_sovereignty_auditor` | GDPR Art. 5/17 — cross-border transfers, retention limits |
| `ai_risk_assessor` | EU AI Act regulatory tiering |
| `phi_sanitizer` | Special Category (health) data handling & anonymization |
| `licensing_reviewer` | Copyleft (GPL/AGPL) contamination risk |

Because the specialists run in isolated threads, the licensing reviewer never
"anchors" on the GDPR auditor's framing and vice-versa — each verdict is
independent, then reconciled by the aggregator.

## Provider

The `llm_callable` is wired to the **Anthropic Claude API** via the official
[`anthropic`](https://pypi.org/project/anthropic/) SDK (`claude-opus-4-8`, with
adaptive thinking). Swap `MODEL_NAME` in `run_demo.py` for `claude-sonnet-5` or
`claude-haiku-4-5` for a cheaper/faster run.

## Getting Started

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Set your Anthropic API key
```bash
export ANTHROPIC_API_KEY=sk-ant-...      # Windows PowerShell: $env:ANTHROPIC_API_KEY="sk-ant-..."
```

### 3. Run
```bash
python run_demo.py
```

## Input

The scenario under review lives in `sample_input/feature_dossier.txt` — a
telehealth "AI triage assistant" that raises data-residency, EU AI Act,
health-data, and AGPL-licensing questions all at once. Edit that file (or point
`dossier_path` elsewhere) to review your own feature.

## Output

The engine broadcasts the dossier to all four specialists in parallel, collects
their reports, and prints the synthesized compliance memo — narrative, key
takeaways, and a confidence score.
