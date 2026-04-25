## Overview

The Agentic Evaluation Dashboard is a [Streamlit](https://streamlit.io) app that reads the JSON evaluation reports produced by the offline evaluation pipelines and renders them as interactive visualizations. It provides three views: a high-level overview, per-run detail drill-downs, and cross-run metric comparisons.

## Prerequisites

- Python 3.10+
- Streamlit and Plotly installed (included in the project's `pyproject.toml`)
- One or more report JSON files present in this directory, named using the pattern `{run_id}_{eval_name}.json` (e.g., `1_pipeline_multi_agent_evaluation.json`)

## Running the Dashboard

From the repository root, run:

```bash
python -m streamlit run src/evaluations/offline/reports/dashboard.py
```

The dashboard opens automatically in your default browser at `http://localhost:8501`.

## Report File Convention

The dashboard auto-discovers reports from the same directory as `dashboard.py`. Files must follow the naming pattern:

```
{run_id}_{eval_name}.json
```

| Part | Description |
|------|-------------|
| `run_id` | A positive integer that determines ordering (e.g., `1`, `2`, `16`) |
| `eval_name` | Snake-case pipeline name (e.g., `pipeline_multi_agent_evaluation`) |

Reports that do not match this pattern are silently ignored.

## Dashboard Views

### Overview Page

The default landing page. For each evaluation type discovered in the reports directory, it shows:

- **Aggregate metric gauges** — color-coded from red (low) to green (high)
- **Multi-run summary table** — side-by-side metric values for all runs of the same evaluation type when multiple runs exist

Click **View Run** in the sidebar to drill into a specific run.

### Run Detail Page

A full breakdown of a single evaluation run, organized into the following sections:

| Section | Description |
|---------|-------------|
| **Aggregate Metrics** | Gauge charts for every top-level metric in the `metrics` block |
| **Pass / Fail Rates** | Donut charts for each `*_result` column (pass/fail percentages) |
| **Agent Routing Analysis** | Available for multi-agent pipelines; shows per-row routing correctness, per-category accuracy, and a routing table with expected vs. invoked agents |
| **Results Table** | Flat summary of all rows with score columns |
| **Detailed Row Explorer** | Expandable row cards with **Inputs**, **Outputs**, and (for multi-agent reports) **Agent Routing** tabs |

### Run Comparison Page

Select two or more runs of the same evaluation type from the sidebar to compare metric trends. The page renders:

- A data table with all numeric metrics side by side
- A line chart of primary score metrics (relevance, adherence, accuracy, …)
- A separate line chart of binary pass-rate metrics

## Metric Display

### Scale Conventions

| Metric type | Scale | Display |
|-------------|-------|---------|
| Relevance, Task Adherence (1–5) | 0–5 | Raw value gauge |
| Binary aggregate pass rates (`*binary_aggregate`) | 0–1 | Percentage gauge (0–100%) |
| Custom agent-invoked accuracy metrics | 0–1 | Percentage gauge (0–100%) |

### Custom Metric Display Names

Long evaluator-prefixed keys are mapped to short, human-readable labels:

| Metric key | Display name |
|------------|--------------|
| `custom_agents_invoked_accuracy_eval.agents_invoke_accuracy` | Agent Routing Accuracy |
| `custom_agents_invoked_accuracy_eval.agents_invoke_match_percentage` | Agent Match % |
| `custom_agents_invoked_accuracy_eval.agents_invoke_exact_match` | Agent Exact Match |

To add display names for new custom evaluators, extend the `_METRIC_DISPLAY_NAMES` dict near the top of `dashboard.py`.

## Folder Structure

```
reports/
├── dashboard.py                          # Streamlit dashboard app
├── README.md                             # This file
├── 1_pipeline_multi_agent_evaluation.json   # Sample report (tracked)
└── {run_id}_{eval_name}.json             # Additional reports (git-ignored)
```

> [!NOTE]
> Only `1_pipeline_multi_agent_evaluation.json` is tracked in source control as a sample.
> All other report JSON files are git-ignored to avoid committing potentially sensitive
> Azure resource information.
