# AI CSF Profiler

NIST CSF 2.0 profile builder and gap evaluator for AI systems, with live integration
into the Meridian Risk Scoring API for evidence-backed subcategory assessment.

## What it does

Three capabilities in one tool:

**1. Profile Builder** — walks through CSF 2.0 subcategories (Govern, Identify, Protect)
with AI-specific context, informative references (NIST AI RMF, ISO/IEC 42001,
MITRE ATLAS, OWASP LLM Top 10), and live Meridian suggestions.

**2. Gap Evaluator** — compares Current vs. Target Profile, computes priority scores
(gap × AI relevance × asset risk), and generates a ranked remediation roadmap.

**3. Report Generator** — produces both a structured JSON report and a formatted PDF
with executive summary, per-function maturity breakdown, gap analysis table,
and prioritized remediation steps.

## Portfolio context

| Project | Description |
|---------|-------------|
| [OCSF Transformer](https://github.com/Lamurrz/ocsf-transformer) | Normalize raw vendor logs → OCSF |
| [CyberGraph-AD](https://github.com/Lamurrz/cybergraph-ad) | Detect behavioral anomalies via graph fusion |
| [Meridian + Risk API](https://github.com/Lamurrz/meridian-api) | Assess threat exposure via MITRE ATLAS/ATT&CK |
| **AI CSF Profiler** | Evaluate framework compliance via NIST CSF 2.0 (this project) |

The narrative: **normalize → detect → assess threat exposure → evaluate compliance.**

## Meridian integration

When the Meridian Risk Scoring API is running, the profiler automatically pulls:

- Asset inventory → suggests maturity score for **ID.AM-02**
- Risk scoring status → suggests maturity score for **ID.RA-01**, **ID.RA-05**, **GV.RM-06**
- Control gap count → informs overall Protect function assessment

This means subcategories backed by live graph data are evidence-based rather than
self-assessed — a meaningful differentiator in regulated environments.

## Quick start

```bash
git clone https://github.com/Lamurrz/ai-csf-profiler.git
cd ai-csf-profiler

python -m venv .venv
source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Demo mode (non-interactive, generates sample report)
python run.py --mode demo --org "My Organization" --target 3

# Interactive assessment
python run.py --mode assess

# Generate report from existing profile
python run.py --mode report

# Full pipeline: assess + report
python run.py --mode full
```

## Modes

| Mode | Description |
|------|-------------|
| `demo` | Non-interactive, auto-populates realistic mixed scores |
| `assess` | Interactive CLI walkthrough per subcategory |
| `report` | Generate JSON + PDF from most recent profile |
| `full` | Interactive assess + report in one run |

## CSF 2.0 subcategories covered

**Govern (GV)** — Organizational Context, Risk Management Strategy, Policy, Roles & Responsibilities

**Identify (ID)** — Asset Management, Risk Assessment

**Protect (PR)** — Identity & Access Control, Data Security, Platform Security, Infrastructure Resilience

Each subcategory includes AI-specific context, informative references, and remediation guidance.

## Informative references per subcategory

| Framework | Coverage |
|-----------|---------|
| NIST AI RMF | Govern, Map, Measure, Manage functions |
| ISO/IEC 42001 | AI management system clauses |
| MITRE ATLAS | Adversarial ML techniques |
| OWASP LLM Top 10 | LLM-specific risks |

## Output

Reports are saved to the `output/` directory:

- `csf-profile-{timestamp}.json` — raw assessment scores
- `csf_gap_report_{org}_{timestamp}.json` — evaluated gap report
- `csf_gap_report_{org}_{timestamp}.pdf` — formatted PDF report

## Project structure

```
ai-csf-profiler/
├── data/
│   └── csf_subcategories.json   # CSF 2.0 subcategory definitions + AI references
├── profiler/
│   ├── profile_builder.py       # CLI assessment walkthrough
│   ├── gap_evaluator.py         # Current vs Target gap analysis
│   └── meridian_client.py       # Meridian Risk API integration
├── report/
│   ├── json_reporter.py         # JSON gap report
│   └── pdf_reporter.py          # PDF gap report
├── config.py
├── run.py
└── requirements.txt
```

## Roadmap

- [ ] Web UI (React + FastAPI) — interactive subcategory form with live gap visualization
- [ ] Respond + Recover functions (complete all 6 CSF 2.0 functions)
- [ ] CyberGraph-AD integration — anomaly counts as Detect subcategory evidence
- [ ] Target profile templates — preconfigured targets for healthcare, finance, defense
- [ ] OSCAL export — machine-readable compliance artifact
