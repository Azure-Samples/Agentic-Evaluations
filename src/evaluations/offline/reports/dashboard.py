"""Streamlit dashboard for Agentic Evaluation Reports."""

import json
import re
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

REPORTS_DIR = Path(__file__).parent
_REPORT_PATTERN = re.compile(r"^(\d+)_(.+)\.json$")

SCORE_COLORS = {"pass": "#28a745", "fail": "#dc3545"}

# Output columns to hide from all dashboard views
_HIDDEN_SUFFIXES = {
    "gpt_relevance",
    "gpt_tool_call_accuracy",
    "tool_call_accuracy_prompt_tokens",
    "tool_call_accuracy_completion_tokens",
    "tool_call_accuracy_total_tokens",
}


def _is_hidden(key: str) -> bool:
    """Return True if this output key should be hidden from the UI."""
    suffix = key.rsplit(".", 1)[-1] if "." in key else key
    return suffix in _HIDDEN_SUFFIXES


def pretty_name(eval_name: str) -> str:
    """Convert snake_case eval name to Title Case."""
    return eval_name.replace("_", " ").title()


_METRIC_DISPLAY_NAMES: dict[str, str] = {
    "custom_agents_invoked_accuracy_eval.agents_invoke_accuracy": "Agent Routing Accuracy",
    "custom_agents_invoked_accuracy_eval.agents_invoke_match_percentage": "Agent Match %",
    "custom_agents_invoked_accuracy_eval.agents_invoke_exact_match": "Agent Exact Match",
}


def friendly_name(key: str) -> str:
    """Convert a metric/output key to a clean display name.

    Examples:
        'relevance_score.relevance' -> 'Relevance Score'
        'task_adherence_score.task_adherence' -> 'Task Adherence Score'
        'relevance_score.binary_aggregate' -> 'Relevance Binary Aggregate'
        'relevance_score.relevance_reason' -> 'Relevance Reason'
        'relevance_score.relevance_threshold' -> 'Relevance Threshold'
    """
    # Strip prefixes like 'outputs.'
    key = key.removeprefix("outputs.")

    # Check explicit overrides first
    if key in _METRIC_DISPLAY_NAMES:
        return _METRIC_DISPLAY_NAMES[key]

    parts = key.split(".")
    if len(parts) == 2:
        group, field = parts
        # Remove '_score' suffix from group for cleaner base name
        base = group.removesuffix("_score")
        # If field equals the base (e.g. relevance_score.relevance), just show "<Base> Score"
        if field == base:
            return base.replace("_", " ").title() + " Score"
        # If field starts with the base (e.g. relevance_score.relevance_reason), strip base prefix
        if field.startswith(base + "_"):
            remainder = field[len(base) + 1:]
            return (base + " " + remainder).replace("_", " ").title()
        # Otherwise combine group base + field (e.g. relevance_score.binary_aggregate)
        return (base + " " + field).replace("_", " ").title()

    # Single part — just title-case it
    return key.replace("_", " ").title()


def discover_reports() -> dict[str, list[dict]]:
    """Scan reports dir for {run_id}_{eval_name}.json and group by eval name."""
    groups: dict[str, list[dict]] = {}
    for f in sorted(REPORTS_DIR.iterdir()):
        m = _REPORT_PATTERN.match(f.name)
        if not m:
            continue
        run_id = int(m.group(1))
        eval_name = m.group(2)
        groups.setdefault(eval_name, []).append(
            {"run_id": run_id, "file": f.name}
        )
    for entries in groups.values():
        entries.sort(key=lambda e: e["run_id"])
    return groups


def load_report(file_name: str) -> dict:
    path = REPORTS_DIR / file_name
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def extract_metric_columns(row: dict, prefix: str) -> dict:
    """Pull numeric score columns matching a given prefix from a row."""
    return {
        k.split(".")[-1]: v
        for k, v in row.items()
        if k.startswith(prefix) and isinstance(v, (int, float))
    }


def get_score_columns(rows: list[dict]) -> list[str]:
    """Discover all numeric output score columns across rows."""
    cols = set()
    for row in rows:
        for k, v in row.items():
            if k.startswith("outputs.") and isinstance(v, (int, float)) and not _is_hidden(k):
                cols.add(k)
    return sorted(cols)


def get_input_columns(rows: list[dict]) -> list[str]:
    cols = set()
    for row in rows:
        for k in row:
            if k.startswith("inputs."):
                cols.add(k)
    return sorted(cols)


def short_col(col: str) -> str:
    """Shorten an output column name for display."""
    return friendly_name(col)


def build_summary_df(rows: list[dict], score_cols: list[str]) -> pd.DataFrame:
    records = []
    for row in rows:
        rec = {}
        query = row.get("inputs.query", row.get("inputs.id", ""))
        rec["query"] = query[:80] + "..." if len(str(query)) > 80 else query
        for col in score_cols:
            rec[short_col(col)] = row.get(col)
        records.append(rec)
    return pd.DataFrame(records)


def _score_color(value: float, max_val: float) -> str:
    """Return a color from red to green based on value relative to max."""
    ratio = value / max_val if max_val else 0
    if ratio >= 0.8:
        return "#22c55e"  # green
    if ratio >= 0.6:
        return "#84cc16"  # lime
    if ratio >= 0.4:
        return "#eab308"  # yellow
    if ratio >= 0.2:
        return "#f97316"  # orange
    return "#ef4444"  # red


def _make_gauge(label: str, value: float, max_val: float, suffix: str = "") -> go.Figure:
    """Create a compact Plotly gauge chart."""
    color = _score_color(value, max_val)
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        number={"suffix": suffix, "font": {"size": 28, "color": "white"}},
        title={"text": label, "font": {"size": 13, "color": "#9ca3af"}},
        gauge={
            "axis": {"range": [0, max_val], "tickfont": {"size": 10, "color": "#6b7280"}},
            "bar": {"color": color, "thickness": 0.7},
            "bgcolor": "#1f2937",
            "borderwidth": 0,
            "steps": [
                {"range": [0, max_val * 0.4], "color": "rgba(239,68,68,0.1)"},
                {"range": [max_val * 0.4, max_val * 0.7], "color": "rgba(234,179,8,0.1)"},
                {"range": [max_val * 0.7, max_val], "color": "rgba(34,197,94,0.1)"},
            ],
            "threshold": {
                "line": {"color": "white", "width": 2},
                "thickness": 0.75,
                "value": value,
            },
        },
    ))
    fig.update_layout(
        height=180,
        margin={"t": 40, "b": 10, "l": 20, "r": 20},
        paper_bgcolor="rgba(0,0,0,0)",
        font={"color": "white"},
    )
    return fig


def render_aggregate_metrics(report: dict, key_prefix: str = "agg") -> None:
    metrics = report.get("metrics", {})
    if not metrics:
        st.info("No aggregate metrics found for this report.")
        return

    display_metrics = {
        k: v for k, v in metrics.items()
        if isinstance(v, (int, float)) and not _is_hidden(k)
    }
    if not display_metrics:
        return

    cols = st.columns(min(len(display_metrics), 4))
    for i, (name, value) in enumerate(display_metrics.items()):
        col = cols[i % len(cols)]
        label = friendly_name(name)

        # Some aggregate metrics are ratios in [0, 1] and should be displayed as percentages.
        is_ratio_metric = (
            isinstance(value, (int, float))
            and 0.0 <= float(value) <= 1.0
            and (
                "binary" in name
                or name.startswith("custom_agents_invoked_accuracy_eval.")
            )
        )

        if is_ratio_metric:
            fig = _make_gauge(label, value * 100, 100, "%")
        else:
            max_val = 5.0 if value <= 5.0 else (value * 1.5)
            fig = _make_gauge(label, value, max_val)
        col.plotly_chart(fig, use_container_width=True, key=f"{key_prefix}_{name}_{i}")


def render_score_distributions(df: pd.DataFrame, score_cols: list[str]) -> None:
    numeric_cols = [short_col(c) for c in score_cols if short_col(c) in df.columns]
    if not numeric_cols:
        return
    st.subheader("Score Distributions")
    chart_df = df[numeric_cols].apply(pd.to_numeric, errors="coerce")
    tabs = st.tabs(numeric_cols)
    for tab, col in zip(tabs, numeric_cols):
        with tab:
            series = chart_df[col].dropna()
            if series.empty:
                st.write("No data")
                continue
            hist_data = series.value_counts().sort_index()
            st.bar_chart(hist_data, x_label="Score", y_label="Count")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Mean", f"{series.mean():.2f}")
            c2.metric("Median", f"{series.median():.2f}")
            c3.metric("Min", f"{series.min():.2f}")
            c4.metric("Max", f"{series.max():.2f}")


def _has_agent_data(rows: list[dict]) -> bool:
    return any(r.get("inputs.expected_agents") for r in rows)


def render_agent_routing(rows: list[dict]) -> None:
    """Render agent routing analysis for multi-agent evaluations."""
    agent_rows = [r for r in rows if r.get("inputs.expected_agents")]
    if not agent_rows:
        return

    st.subheader("Agent Routing Analysis")

    # Compute per-row match
    matches = 0
    records = []
    for r in agent_rows:
        expected = set(r.get("inputs.expected_agents", []))
        invoked = set(r.get("inputs.agents_invoked", []))
        # Match if all expected agents were invoked (ignore orchestrator)
        matched = expected.issubset(invoked)
        if matched:
            matches += 1
        records.append({
            "ID": r.get("inputs.id", ""),
            "Query": str(r.get("inputs.query", ""))[:60],
            "Category": r.get("inputs.category", ""),
            "Expected Agents": ", ".join(sorted(expected)),
            "Agents Invoked": ", ".join(sorted(invoked)),
            "Routed Correctly": "\u2705" if matched else "\u274c",
        })

    total = len(agent_rows)
    accuracy = matches / total if total else 0

    # Summary metrics
    m1, m2, m3 = st.columns(3)
    m1.metric("Routing Accuracy", f"{accuracy:.0%}")
    m2.metric("Correct", f"{matches}/{total}")
    categories = {r.get("inputs.category", "unknown") for r in agent_rows}
    m3.metric("Categories", ", ".join(sorted(categories)))

    # Per-category breakdown
    if len(categories) > 1:
        st.markdown("**Per-Category Routing Accuracy:**")
        cat_cols = st.columns(min(len(categories), 4))
        for i, cat in enumerate(sorted(categories)):
            cat_rows = [r for r in agent_rows if r.get("inputs.category") == cat]
            cat_match = sum(
                1 for r in cat_rows
                if set(r.get("inputs.expected_agents", [])).issubset(
                    set(r.get("inputs.agents_invoked", []))
                )
            )
            cat_cols[i % len(cat_cols)].metric(
                cat.replace("_", " ").title(),
                f"{cat_match}/{len(cat_rows)} ({cat_match / len(cat_rows):.0%})",
            )

    # Routing table
    routing_df = pd.DataFrame(records)
    st.dataframe(routing_df, width="stretch", hide_index=True)


def render_pass_fail(rows: list[dict], score_cols: list[str], key_prefix: str = "pf") -> None:
    result_cols = []
    for row in rows:
        for k, v in row.items():
            if k.startswith("outputs.") and k.endswith("_result") and isinstance(v, str):
                if k not in result_cols:
                    result_cols.append(k)
    if not result_cols:
        return

    st.subheader("Pass / Fail Rates")
    cols = st.columns(min(len(result_cols), 3))
    for i, rc in enumerate(result_cols):
        vals = [r.get(rc) for r in rows if r.get(rc) in ("pass", "fail")]
        if not vals:
            continue
        total = len(vals)
        passes = vals.count("pass")
        fails = vals.count("fail")
        col = cols[i % len(cols)]
        label = friendly_name(rc.removeprefix("outputs.").removesuffix("_result"))

        pass_color = "#22c55e" if passes / total >= 0.7 else ("#eab308" if passes / total >= 0.4 else "#ef4444")
        fig = go.Figure(go.Pie(
            values=[passes, fails],
            labels=["Pass", "Fail"],
            marker={"colors": [pass_color, "#374151"]},
            hole=0.65,
            textinfo="none",
            hovertemplate="%{label}: %{value}<extra></extra>",
        ))
        fig.add_annotation(
            text=f"<b>{passes}/{total}</b><br><span style='font-size:11px'>{passes/total:.0%}</span>",
            x=0.5, y=0.5, showarrow=False,
            font={"size": 18, "color": "white"},
        )
        fig.update_layout(
            title={"text": label, "font": {"size": 13, "color": "#9ca3af"}, "x": 0.5},
            height=200,
            margin={"t": 35, "b": 10, "l": 10, "r": 10},
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            showlegend=False,
        )
        col.plotly_chart(fig, use_container_width=True, key=f"{key_prefix}_{rc}_{i}")


def render_row_detail(row: dict, idx: int) -> None:
    with st.expander(f"Row {idx + 1}: {str(row.get('inputs.query', row.get('inputs.id', '')))[:100]}"):
        # Determine if this is a multi-agent row
        expected = row.get("inputs.expected_agents")
        invoked = row.get("inputs.agents_invoked")
        has_agents = bool(expected)

        if has_agents:
            tab_names = ["Inputs", "Outputs", "Agent Routing"]
        else:
            tab_names = ["Inputs", "Outputs"]
        tabs = st.tabs(tab_names)
        input_tab = tabs[0]
        output_tab = tabs[1]

        if has_agents:
            agent_tab = tabs[2]
            with agent_tab:
                expected_set = set(expected)
                invoked_set = set(invoked or [])
                matched = expected_set.issubset(invoked_set)

                badge = "\u2705 Routed Correctly" if matched else "\u274c Routing Mismatch"
                st.markdown(f"### {badge}")

                c1, c2 = st.columns(2)
                c1.markdown(f"**Category:** {row.get('inputs.category', 'N/A')}")
                c2.markdown(f"**Primary Agent:** {row.get('inputs.agent_name', 'N/A')}")

                c3, c4 = st.columns(2)
                c3.markdown("**Expected Agents:**")
                for agent in sorted(expected_set):
                    icon = "\u2705" if agent in invoked_set else "\u274c"
                    c3.markdown(f"- {icon} {agent}")
                c4.markdown("**Agents Invoked:**")
                for agent in sorted(invoked_set):
                    icon = "\u2705" if agent in expected_set else "\u26a0\ufe0f"
                    c4.markdown(f"- {icon} {agent}")

                missing = expected_set - invoked_set
                extra = invoked_set - expected_set
                if missing:
                    st.error(f"**Missing Agents:** {', '.join(sorted(missing))}")
                if extra:
                    st.warning(f"**Unexpected Agents:** {', '.join(sorted(extra))}")
                if not missing and not extra:
                    st.success("All expected agents were invoked with no unexpected agents.")

                # Tool calls summary
                tool_calls = row.get("inputs.tool_calls")
                if tool_calls:
                    st.markdown("**Tool Calls:**")
                    for tc in tool_calls:
                        st.markdown(f"- `{tc.get('name', 'unknown')}`")

        with input_tab:
            for k, v in row.items():
                if k.startswith("inputs."):
                    label = k.replace("inputs.", "")
                    if isinstance(v, str) and len(v) > 200:
                        st.text_area(label, v, height=120, disabled=True, key=f"in_{idx}_{k}")
                    elif isinstance(v, (list, dict)):
                        st.json(v, expanded=False)
                    else:
                        st.write(f"**{label}:** {v}")

        with output_tab:
            scores = {}
            reasons = {}
            for k, v in row.items():
                if not k.startswith("outputs.") or _is_hidden(k):
                    continue
                short = k.replace("outputs.", "")
                if isinstance(v, (int, float)):
                    scores[short] = v
                elif isinstance(v, str) and ("reason" in k or "details" in k):
                    reasons[short] = v
                elif isinstance(v, dict):
                    reasons[short] = v

            if scores:
                score_cols = st.columns(min(len(scores), 4))
                for j, (name, val) in enumerate(scores.items()):
                    c = score_cols[j % len(score_cols)]
                    display_name = friendly_name(name)
                    c.metric(display_name, f"{val}")

            for name, val in reasons.items():
                display_name = friendly_name(name)
                if isinstance(val, dict):
                    st.write(f"**{display_name}:**")
                    st.json(val, expanded=False)
                elif val:
                    st.write(f"**{display_name}:**")
                    st.caption(val)


def _nav_to(**params: str) -> None:
    """Navigate by updating URL query params and triggering a rerun."""
    st.query_params.clear()
    st.query_params.update(params)
    st.rerun()


def render_overview(
    report_groups: dict[str, list[dict]],
) -> None:
    """Render the overview page with per-eval-type run summaries."""
    st.header("Evaluation Overview")

    for eval_name, runs in report_groups.items():
        display_name = pretty_name(eval_name)
        run_count = len(runs)
        latest = runs[-1]
        report = load_report(latest["file"])
        rows = report.get("rows", [])

        with st.container(border=True):
            st.subheader(display_name)
            st.caption(
                f"{run_count} run{'s' if run_count != 1 else ''} "
                f"\u00b7 Latest: Run {latest['run_id']} "
                f"({len(rows)} rows)"
            )

            # Latest-run aggregate metrics
            render_aggregate_metrics(report, key_prefix=f"ov_{eval_name}")

            # Per-run summary table when multiple runs exist
            if run_count > 1:
                records = []
                for entry in runs:
                    r = load_report(entry["file"])
                    m = r.get("metrics", {})
                    row_data = {"Run": entry["run_id"], "Rows": len(r.get("rows", []))}
                    for mk, mv in m.items():
                        if isinstance(mv, (int, float)):
                            row_data[mk.replace("_", " ").title()] = mv
                    records.append(row_data)
                run_df = pd.DataFrame(records).set_index("Run")
                st.dataframe(
                    run_df.style.format(
                        "{:.2f}",
                        subset=[c for c in run_df.columns if c != "Rows"],
                    ),
                    width="stretch",
                    hide_index=False,
                )


def render_run_comparison(eval_name: str, runs: list[dict]) -> None:
    """Show metric trends across selected runs of the same eval type."""
    st.header(f"Run Comparison: {pretty_name(eval_name)}")
    st.write(f"Comparing {len(runs)} run(s).")

    if len(runs) < 2:
        st.info("Select at least 2 runs to compare.")
        return

    records = []
    for entry in runs:
        report = load_report(entry["file"])
        metrics = report.get("metrics", {})
        row_data = {"Run": f"Run {entry['run_id']}"}
        for mk, mv in metrics.items():
            if isinstance(mv, (int, float)):
                row_data[friendly_name(mk)] = mv
        records.append(row_data)

    if not records:
        st.info("No metrics to compare across runs.")
        return

    run_df = pd.DataFrame(records).set_index("Run")
    st.dataframe(run_df.style.format("{:.2f}"), width="stretch")

    score_metric_cols = [
        c for c in run_df.columns
        if any(
            kw in c.lower()
            for kw in ["relevance", "coherence", "adherence", "accuracy", "fluency", "similarity"]
        )
        and "binary" not in c.lower()
        and "token" not in c.lower()
        and "prompt" not in c.lower()
        and "completion" not in c.lower()
    ]
    if score_metric_cols:
        st.subheader("Metric Trends Across Runs")
        st.line_chart(run_df[score_metric_cols])

    binary_cols = [c for c in run_df.columns if "binary" in c.lower()]
    if binary_cols:
        st.subheader("Binary Pass Rate Trends")
        st.line_chart(run_df[binary_cols])


def render_single_report(name: str, report: dict) -> None:
    rows = report.get("rows", [])
    if not rows:
        st.warning("No evaluation rows found.")
        return

    score_cols = get_score_columns(rows)

    st.subheader("Aggregate Metrics")
    render_aggregate_metrics(report)

    st.divider()
    render_pass_fail(rows, score_cols)

    if _has_agent_data(rows):
        st.divider()
        render_agent_routing(rows)

    st.divider()
    summary_df = build_summary_df(rows, score_cols)
    st.subheader("Results Table")
    st.dataframe(summary_df, width="stretch", hide_index=True)

    st.divider()
    st.subheader("Detailed Row Explorer")
    st.write(f"Showing {len(rows)} evaluation rows. Expand any row for full details.")
    for idx, row in enumerate(rows):
        render_row_detail(row, idx)


def render_detail_page(
    eval_name: str,
    runs: list[dict],
    selected_run_id: int,
) -> None:
    """Render a single-run detail page with a run selector."""
    st.header(pretty_name(eval_name))

    # Run selector row
    sel_col, back_col = st.columns([3, 1])
    with sel_col:
        run_labels = [f"Run {r['run_id']}" for r in runs]
        current_label = f"Run {selected_run_id}"
        default_idx = (
            run_labels.index(current_label)
            if current_label in run_labels
            else len(run_labels) - 1
        )
        chosen = st.selectbox("Select run", run_labels, index=default_idx)
        chosen_run_id = int(chosen.split()[-1])
        if chosen_run_id != selected_run_id:
            _nav_to(
                page="detail",
                eval=eval_name,
                run=str(chosen_run_id),
            )
    with back_col:
        st.write("")  # spacing
        if st.button("\u2190 Back to Overview"):
            _nav_to(page="overview")

    # Find the matching run entry and render
    entry = next(
        (r for r in runs if r["run_id"] == selected_run_id), runs[-1]
    )
    report = load_report(entry["file"])
    st.caption(f"Showing Run {entry['run_id']} — {entry['file']}")
    render_single_report(eval_name, report)


def main() -> None:
    st.set_page_config(
        page_title="Agentic Evaluation Dashboard",
        page_icon="📊",
        layout="wide",
    )
    st.title("📊 Agentic Evaluation Dashboard")
    st.caption("Explore and compare evaluation results across pipeline runs.")

    report_groups = discover_reports()

    if not report_groups:
        st.error(
            "No report files found. Place JSON reports "
            "(e.g. 1_eval_name.json) in the reports/ directory."
        )
        return

    # Read navigation state from URL query params
    params = st.query_params
    page = params.get("page", "overview")
    param_eval = params.get("eval", "")
    param_run = params.get("run", "")

    eval_names = sorted(report_groups.keys(), key=lambda n: len(report_groups[n]), reverse=True)

    # Sidebar navigation
    st.sidebar.title("Navigation")
    if st.sidebar.button("🏠 Overview", use_container_width=True):
        _nav_to(page="overview")

    st.sidebar.markdown("---")
    st.sidebar.markdown("**Evaluations**")
    for name in eval_names:
        runs = report_groups[name]
        run_count = len(runs)
        suffix = "s" if run_count != 1 else ""
        is_active = param_eval == name and page in ("detail", "compare")
        label = (
            f"**{pretty_name(name)}** ({run_count} run{suffix})"
            if is_active
            else f"{pretty_name(name)} ({run_count} run{suffix})"
        )
        with st.sidebar.expander(label, expanded=is_active):
            for entry in runs:
                if run_count > 1:
                    cb_key = f"sb_sel_{name}_{entry['run_id']}"
                    if cb_key not in st.session_state:
                        st.session_state[cb_key] = True
                    cb_col, btn_col = st.columns([1, 3])
                    with cb_col:
                        st.checkbox(
                            "",
                            key=cb_key,
                            label_visibility="collapsed",
                        )
                    with btn_col:
                        if st.button(
                            f"Run {entry['run_id']}",
                            key=f"sb_{name}_{entry['run_id']}",
                            use_container_width=True,
                        ):
                            _nav_to(
                                page="detail",
                                eval=name,
                                run=str(entry["run_id"]),
                            )
                else:
                    if st.button(
                        f"Run {entry['run_id']}",
                        key=f"sb_{name}_{entry['run_id']}",
                        use_container_width=True,
                    ):
                        _nav_to(
                            page="detail",
                            eval=name,
                            run=str(entry["run_id"]),
                        )
            if run_count > 1:
                selected_ids = [
                    str(e["run_id"])
                    for e in runs
                    if st.session_state.get(f"sb_sel_{name}_{e['run_id']}", True)
                ]
                if st.button(
                    "📊 Compare Runs",
                    key=f"sb_cmp_{name}",
                    use_container_width=True,
                ):
                    _nav_to(
                        page="compare",
                        eval=name,
                        runs=",".join(selected_ids),
                    )

    # Route to the correct page
    if page == "detail" and param_eval in report_groups:
        runs = report_groups[param_eval]
        run_id = int(param_run) if param_run.isdigit() else runs[-1]["run_id"]
        render_detail_page(param_eval, runs, run_id)

    elif page == "compare" and param_eval in report_groups:
        all_runs = report_groups[param_eval]
        param_runs = params.get("runs", "")
        if param_runs:
            selected_ids = {int(x) for x in param_runs.split(",") if x.isdigit()}
            runs = [r for r in all_runs if r["run_id"] in selected_ids]
        else:
            runs = all_runs
        back_col, _ = st.columns([1, 5])
        with back_col:
            if st.button("\u2190 Back to Overview"):
                _nav_to(page="overview")
        render_run_comparison(param_eval, runs)

    else:
        render_overview(report_groups)


if __name__ == "__main__":
    main()
