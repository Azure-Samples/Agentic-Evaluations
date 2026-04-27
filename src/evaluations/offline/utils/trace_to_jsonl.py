"""
Enrich Agent Responses with Application Insights Data
======================================================
Shared pipeline module that enriches agent responses with
tool_definitions and tool_calls from Application Insights.

This module:
1. Loads query/response/trace_id from agent_responses.jsonl
2. Fetches tool_definitions and tool_calls from Application Insights
3. Outputs enriched JSONL for evaluation

Used by both pipeline_multi_agent_evaluation and
pipeline_multi_tool_agent_evaluation.
"""
import os
import json
import logging
import time
from pathlib import Path
from typing import Dict, List, Any
from datetime import timedelta
from azure.monitor.query import LogsQueryClient, LogsQueryStatus
from azure.identity import DefaultAzureCredential
from azure.core.exceptions import HttpResponseError
from dotenv import load_dotenv

load_dotenv()


# =============================================================================
# LOGGING SETUP
# =============================================================================
def get_logger(name: str):
    level = os.environ.get("LOG_LEVEL", "INFO").upper()
    logging.basicConfig(level=getattr(logging, level, logging.INFO))

    logging.getLogger("azure").setLevel(logging.WARNING)
    logging.getLogger("opentelemetry").setLevel(logging.WARNING)

    return logging.getLogger(name)

logger = get_logger(__name__)


# =============================================================================
# APP INSIGHTS DATA EXTRACTION
# =============================================================================
def extract_tool_definitions(custom_dimensions: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract tool definitions from gen_ai.tool.definitions."""
    tool_defs_str = custom_dimensions.get("gen_ai.tool.definitions", "")
    if not tool_defs_str:
        return []

    tool_definitions = []
    try:
        tool_defs = json.loads(tool_defs_str)
        if not isinstance(tool_defs, list):
            return []

        for tool_def in tool_defs:
            if tool_def.get("type") == "function" and "function" in tool_def:
                func_def = tool_def["function"]
                tool_definitions.append({
                    "id": func_def.get("name", ""),
                    "name": func_def.get("name", ""),
                    "description": func_def.get("description", ""),
                    "parameters": func_def.get("parameters", {})
                })
    except json.JSONDecodeError:
        pass

    return tool_definitions


def merge_tool_definitions(existing: List[Dict[str, Any]], new: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Merge tool definitions, de-duplicating by tool name/id.

    If a tool with the same name already exists, the new definition is skipped
    (keeping the first encountered definition).

    Args:
        existing: Current list of tool definitions
        new: New tool definitions to merge in

    Returns:
        Merged list with duplicates removed by name
    """
    if not new:
        return existing

    # Create a dict keyed by tool name for quick lookup
    by_name = {tool.get("name"): tool for tool in existing}

    # Add new tools if name doesn't already exist
    for tool in new:
        tool_name = tool.get("name")
        if tool_name and tool_name not in by_name:
            by_name[tool_name] = tool

    return list(by_name.values())


def extract_tool_call_from_span(custom_dims: Dict[str, Any], operation_name: str) -> Dict[str, Any]:
    """Extract tool call info from execute_tool span."""
    tool_name = operation_name.replace("execute_tool ", "") if operation_name.startswith("execute_tool ") else ""

    return {
        "type": "tool_call",
        "name": tool_name or custom_dims.get('gen_ai.tool.name', ''),
    }



def fetch_tool_data_from_app_insights(trace_ids: List[str]) -> Dict[str, Dict[str, Any]]:
    """
    Fetch tool_definitions, tool_calls from Application Insights.

    Returns:
        Dict mapping trace_id to {tool_definitions: [...], tool_calls: [...], agent_name: "...", agents_invoked: [...]}
    """
    tool_data_by_trace = {}

    workspace_id = os.getenv("APPLICATION_INSIGHTS_WORKSPACE_ID")
    if not workspace_id:
        logger.error("APPLICATION_INSIGHTS_WORKSPACE_ID environment variable is not set")
        return tool_data_by_trace

    logger.info("Fetching tool data from App Insights for %d traces", len(trace_ids))

    trace_ids_str = "', '".join(trace_ids)
    query = f"""
    union AppDependencies
    | where OperationId in ('{trace_ids_str}')
    | project
        operation_id=OperationId,
        name=Name,
        custom_dimensions=Properties,
        timestamp=TimeGenerated
    | order by operation_id asc, timestamp asc
    """

    try:
        credential = DefaultAzureCredential()
        client = LogsQueryClient(credential)

        response = client.query_workspace(
            workspace_id=workspace_id,
            query=query,
            timespan=timedelta(days=7),
        )

        if response.status == LogsQueryStatus.SUCCESS:
            table = response.tables[0]
            logger.info("App Insights returned %d rows", len(table.rows))

            column_names = [column.name for column in table.columns]

            for row in table.rows:
                # azure-monitor-query rows are commonly sequence-like (aligned with table.columns)
                # but may also be dict-like depending on client version/shape.
                row_data = dict(zip(column_names, row)) if not isinstance(row, dict) else row

                operation_id = row_data.get("operation_id")
                operation_name = row_data.get("name", "")

                if not operation_id:
                    continue

                if operation_id not in tool_data_by_trace:
                    tool_data_by_trace[operation_id] = {
                        "tool_definitions": [],
                        "tool_calls": [],
                        "agent_name": "",
                        "agents_invoked": []
                    }

                custom_dims = {}
                custom_dimensions = row_data.get("custom_dimensions")
                if isinstance(custom_dimensions, dict):
                    custom_dims = custom_dimensions
                elif isinstance(custom_dimensions, str):
                    try:
                        custom_dims = json.loads(custom_dimensions)
                    except (json.JSONDecodeError, TypeError):
                        pass

                # Extract tool_definitions from invoke_agent spans
                if operation_name.startswith("invoke_agent"):
                    tool_defs = extract_tool_definitions(custom_dims)
                    if tool_defs:
                        # Accumulate and de-duplicate tool definitions across all agents
                        tool_data_by_trace[operation_id]["tool_definitions"] = merge_tool_definitions(
                            tool_data_by_trace[operation_id]["tool_definitions"],
                            tool_defs
                        )

                    agent_name = custom_dims.get("gen_ai.agent.name", "")
                    if agent_name:
                        if not tool_data_by_trace[operation_id]["agent_name"]:
                            tool_data_by_trace[operation_id]["agent_name"] = agent_name
                        if agent_name not in tool_data_by_trace[operation_id]["agents_invoked"]:
                            tool_data_by_trace[operation_id]["agents_invoked"].append(agent_name)

                # Extract tool_calls from execute_tool spans
                if operation_name.startswith("execute_tool "):
                    tool_call = extract_tool_call_from_span(custom_dims, operation_name)
                    if tool_call["name"]:
                        tool_data_by_trace[operation_id]["tool_calls"].append(tool_call)
        else:
            logger.warning("Partial App Insights query error: %s", response.partial_error)

    except HttpResponseError as err:
        logger.error("HTTP error while querying App Insights: %s", err)

    return tool_data_by_trace


# =============================================================================
# LOCAL DATA LOADING
# =============================================================================
def load_agent_responses_jsonl(input_path: str) -> List[Dict[str, Any]]:
    """
    Load records from agent_responses.jsonl.

    Returns:
        List of records with id, query, response, trace_id, and evaluation-specific fields
    """
    records = []
    with open(input_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                record = json.loads(line)
                records.append(record)
    return records


# =============================================================================
# MERGE AND OUTPUT
# =============================================================================
def merge_and_save_to_jsonl(
    local_records: List[Dict[str, Any]],
    app_insights_data: Dict[str, Dict[str, Any]],
    output_path: str
) -> int:
    """
    Merge local query/response with App Insights tool data and save to JSONL and JSON.

    All fields from the original record are preserved. Enrichment fields
    (tool_calls, agent_name, tool_definitions, agents_invoked) are added
    from Application Insights data.

    Args:
        local_records: Records from agent_responses.jsonl (query, response, trace_id, etc.)
        app_insights_data: Tool data from App Insights (tool_definitions, tool_calls, agents_invoked)
        output_path: Output JSONL file path

    Returns:
        Number of records written
    """
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    all_records = []
    count = 0

    with open(output_path, 'w', encoding='utf-8') as f:
        for record in local_records:
            trace_id = record.get("trace_id", "")

            ai_data = app_insights_data.get(trace_id, {})

            tool_calls = ai_data.get("tool_calls", [])
            tool_names = [tc["name"] for tc in tool_calls if isinstance(tc, dict) and tc.get("name")]
            all_tool_defs = ai_data.get("tool_definitions", [])
            tool_definitions = [td for td in all_tool_defs if td.get("name") in tool_names]

            # Preserve all original record fields and add enrichment
            merged = dict(record)
            merged.update({
                "agents_invoked": ai_data.get("agents_invoked", []),
                "tool_calls": tool_calls,
                "agent_name": ai_data.get("agent_name", ""),
                "tool_definitions": tool_definitions,
            })

            f.write(json.dumps(merged, ensure_ascii=False) + '\n')
            all_records.append(merged)
            count += 1

    json_output_path = output_path.replace('.jsonl', '.json')
    with open(json_output_path, 'w', encoding='utf-8') as f:
        json.dump(all_records, f, indent=2, ensure_ascii=False)

    logger.info("[ENRICH] Also saved JSON format: %s", json_output_path)

    return count


# =============================================================================
# PIPELINE ENTRY POINT
# =============================================================================
def get_trace_main(config: dict, args=None) -> None:
    """
    Main entry point for the pipeline runner.

    Reads agent_responses.jsonl, enriches with App Insights data,
    outputs to enriched JSONL file.

    Args:
        config: Configuration dictionary from experiment.yaml
        args: Optional additional arguments
    """
    logger.info("[ENRICH] Starting trace enrichment...")

    delay_seconds = config.get('delay_seconds', 60)
    logger.info("[ENRICH] Waiting %d seconds for App Insights data ingestion...", delay_seconds)
    time.sleep(delay_seconds)

    base_dir = Path(os.getcwd())
    input_path = config.get('input_path', 'datasets/')
    input_file = config.get('input_file', 'agent_responses.jsonl')
    output_path = config.get('output_path', 'datasets/')
    output_file = config.get('output_file', 'agent_responses_enriched.jsonl')

    input_file_path = base_dir / input_path / input_file
    output_file_path = base_dir / output_path / output_file

    logger.info("[ENRICH] Loading responses from: %s", input_file_path)
    try:
        local_records = load_agent_responses_jsonl(str(input_file_path))
    except FileNotFoundError:
        logger.error("[ENRICH] Input file not found: %s", input_file_path)
        raise

    logger.info("[ENRICH] Loaded %d records", len(local_records))

    trace_ids = list(set(r["trace_id"] for r in local_records if r.get("trace_id")))

    if not trace_ids:
        logger.warning("[ENRICH] No trace IDs found, skipping App Insights fetch")
        app_insights_data = {}
    else:
        logger.info("[ENRICH] Fetching tool data for %d traces from App Insights...", len(trace_ids))
        app_insights_data = fetch_tool_data_from_app_insights(trace_ids)
        logger.info("[ENRICH] Fetched data for %d traces", len(app_insights_data))

    count = merge_and_save_to_jsonl(local_records, app_insights_data, str(output_file_path))

    records_with_tools = sum(1 for r in local_records if app_insights_data.get(r.get("trace_id", ""), {}).get("tool_definitions"))
    logger.info("[ENRICH] Output: %s", output_file_path)
    logger.info("[ENRICH] Total records: %d, with tool_definitions: %d", count, records_with_tools)
    logger.info("[ENRICH] Enrichment complete.")
