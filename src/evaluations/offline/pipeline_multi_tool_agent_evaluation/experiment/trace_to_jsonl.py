
"""
Convert Application Insights trace data from CSV to JSONL format for evaluation.
"""
import os
import json
import re
from pathlib import Path
from typing import Dict, List, Any
from datetime import timedelta
from azure.monitor.query import LogsQueryClient, LogsQueryStatus
from azure.identity import DefaultAzureCredential
from azure.core.exceptions import HttpResponseError
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


def extract_user_query(custom_dimensions: Dict[str, Any]) -> str:
    """Extract user query from gen_ai.input.messages."""
    messages_str = custom_dimensions.get("gen_ai.input.messages", "")
    if not messages_str:
        return ""
    
    try:
        messages = json.loads(messages_str)
        if messages and isinstance(messages, list) and len(messages) > 0:
            parts = messages[0].get("parts", [])
            if parts and len(parts) > 0:
                return parts[0].get("content", "")
    except json.JSONDecodeError:
        pass
    
    return ""


def extract_assistant_response(custom_dimensions: Dict[str, Any]) -> str:
    """Extract assistant response from gen_ai.output.messages."""
    messages_str = custom_dimensions.get("gen_ai.output.messages", "")
    if not messages_str:
        return ""
    
    try:
        messages = json.loads(messages_str)
        # Find the last assistant message with text content
        for message in reversed(messages):
            if message.get("role") == "assistant":
                parts = message.get("parts", [])
                for part in parts:
                    if part.get("type") == "text":
                        return part.get("content", "")
    except json.JSONDecodeError:
        pass
    
    return ""


def extract_strategy_name(operation_name: str) -> str:
    """Extract strategy name from operation name like 'Dispatch Request - StrategyName.SINGLE_CHAT'."""
    match = re.search(r'StrategyName\.(\w+)', operation_name)
    if match:
        return match.group(1)
    return ""


def extract_agent_name(operation_name: str) -> str:
    """Extract agent name from operation name like 'Invoke Agent - MultiToolAgent'."""
    match = re.search(r'Invoke Agent - (.+)', operation_name)
    if match:
        return match.group(1)
    return ""


def extract_tool_call_from_execute_tool(trace: Dict[str, Any]) -> Dict[str, Any]:
    """Extract tool call information from execute_tool operation span."""
    custom_dims = trace.get('custom_dimensions', {})
    
    tool_call_id = custom_dims.get('gen_ai.tool.call.id', '')
    # Handle both string and list formats for tool_call_id
    if isinstance(tool_call_id, str):
        try:
            parsed_id = json.loads(tool_call_id)
            if isinstance(parsed_id, list):
                tool_call_id = parsed_id[-1] if parsed_id else ''
        except (json.JSONDecodeError, TypeError):
            pass
    elif isinstance(tool_call_id, list):
        tool_call_id = tool_call_id[-1] if tool_call_id else ''
    
    arguments_str = custom_dims.get('gen_ai.tool.call.arguments', '{}')
    arguments = {}
    if isinstance(arguments_str, str):
        try:
            arguments = json.loads(arguments_str)
        except json.JSONDecodeError:
            arguments = {}
    elif isinstance(arguments_str, dict):
        arguments = arguments_str
    
    return {
        "type": "tool_call",
        "tool_call_id": tool_call_id,
        "name": custom_dims.get('gen_ai.tool.name', ''),
        "arguments": arguments
    }


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
            # Handle different tool definition formats
            if tool_def.get("type") == "function" and "function" in tool_def:
                func_def = tool_def["function"]
                tool_definitions.append({
                    "id": func_def.get("name", ""),
                    "name": func_def.get("name", ""),
                    "description": func_def.get("description", ""),
                    "parameters": func_def.get("parameters", {})
                })
            elif tool_def.get("type") == "hosted_web_search_tool":
                tool_definitions.append({
                    "id": tool_def.get("name", ""),
                    "name": tool_def.get("name", ""),
                    "description": tool_def.get("description", ""),
                    "parameters": {}
                })
    except json.JSONDecodeError:
        pass
    
    return tool_definitions


def fetch_traces_from_app_insights(trace_ids: List[str]) -> Dict[str, List[Dict[str, Any]]]:
    """Fetch traces from Application Insights for the given trace IDs."""
    traces_by_operation = {}
    
    # Build the KQL query with the trace IDs
    trace_ids_str = "', '".join(trace_ids)
    query = f"""
    union AppTraces, AppDependencies, AppRequests, AppExceptions, AppEvents    
    | where OperationId in ('{trace_ids_str}')
    | project
        id=Id,
        parent_id=ParentId,
        operation_id=OperationId,
        name=Name,
        timestamp=TimeGenerated,
        duration=DurationMs,
        message=Message,
        severity_level=SeverityLevel,
        custom_dimensions=Properties    
    | order by timestamp asc
    """
    
    try:
        credential = DefaultAzureCredential()
        client = LogsQueryClient(credential)
        
        response = client.query_workspace(
            workspace_id=os.getenv("APPLICATION_INSIGHTS_WORKSPACE_ID"),
            query=query,
            timespan=timedelta(days=7),
        )
        
        if response.status == LogsQueryStatus.SUCCESS:
            table = response.tables[0]
            
            for row in table.rows:
                operation_id = row["operation_id"]
                
                if operation_id not in traces_by_operation:
                    traces_by_operation[operation_id] = []
                
                # Parse custom_dimensions JSON if present
                custom_dimensions = {}
                if row["custom_dimensions"]:
                    try:
                        custom_dimensions = json.loads(row["custom_dimensions"])
                    except json.JSONDecodeError:
                        pass
                
                trace_data = {
                    'id': row["id"],
                    'parent_id': row["parent_id"],
                    'operation_id': operation_id,
                    'name': row["name"],
                    'timestamp': row["timestamp"].strftime('%Y-%m-%d %H:%M:%S'),
                    'duration': row["duration"] if row["duration"] else None,
                    'custom_dimensions': custom_dimensions
                }
                
                traces_by_operation[operation_id].append(trace_data)
        else:
            # LogsQueryPartialResult
            error = response.partial_error
            print(f"Partial error occurred: {error}")
            
    except HttpResponseError as err:
        print(f"HTTP error occurred while fetching traces: {err}")
        raise
    
    return traces_by_operation


def convert_traces_to_jsonl(traces: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Convert a group of traces (same operation_id) to a single JSONL record."""
    if not traces:
        return None
    
    # Initialize the output record
    record = {
        "trace_id": traces[0]['operation_id'],
        "orchestration_strategy": "",
        "query": "",
        "selected_agents": [],
        "response": "",
        "tool_calls": [],
        "tool_definitions": []
    }
    
    # Find the root invoke_agent span (the one with smallest depth/earliest in trace hierarchy)
    # This is typically the span with parent_id that matches "Invoke Agent -" operation
    invoke_agent_spans = []
    
    # Process each trace
    for trace in traces:
        operation_name = trace['name']
        custom_dims = trace['custom_dimensions']
        
        # Extract orchestration strategy
        if operation_name.startswith("Dispatch Request - StrategyName."):
            strategy = extract_strategy_name(operation_name)
            if strategy:
                record["orchestration_strategy"] = strategy
        
        # Collect invoke_agent spans for later processing
        if operation_name.startswith("invoke_agent"):
            agent_name = custom_dims.get("gen_ai.agent.name", "")
            
            # Skip IntentRouterAgent for selected_agents mapping
            if agent_name != "IntentRouterAgent":
                invoke_agent_spans.append(trace)
                # Extract agent name from custom_dimensions
                if agent_name and agent_name not in record["selected_agents"]:
                    record["selected_agents"].append(agent_name)
        
        # Extract tool calls from execute_tool operations
        if operation_name.startswith("execute_tool "):
            tool_call = extract_tool_call_from_execute_tool(trace)
            if tool_call["name"]:  # Only add if tool name is present
                record["tool_calls"].append(tool_call)
    
    # Find the root invoke_agent span (the one whose parent is "Dispatch Request")
    root_invoke_span = None
    for span in invoke_agent_spans:
        # Check if this span's parent is a "Dispatch Request" operation
        parent_id = span['parent_id']
        for trace in traces:
            if trace['id'] == parent_id and trace['name'].startswith("Dispatch Request"):
                root_invoke_span = span
                break
        if root_invoke_span:
            break
    
    # If no root found, use the first invoke_agent span
    if not root_invoke_span and invoke_agent_spans:
        root_invoke_span = invoke_agent_spans[0]
    
    # Extract query, response, and tool definitions from the root invoke_agent span
    if root_invoke_span:
        custom_dims = root_invoke_span['custom_dimensions']
        query = extract_user_query(custom_dims)
        if query:
            record["query"] = query
        
        response = extract_assistant_response(custom_dims)
        if response:
            record["response"] = response
        
        # Extract tool definitions
        tool_definitions = extract_tool_definitions(custom_dims)
        if tool_definitions:
            record["tool_definitions"] = tool_definitions
    
    return record


def convert_traces_to_jsonl_file(trace_ids: List[str], output_jsonl_path: str):
    """
    Fetch traces from Application Insights and convert to JSONL format.
    
    Args:
        trace_ids: List of operation IDs (trace IDs) to fetch
        output_jsonl_path: Path to output JSONL file
    """
    print(f"Fetching traces for {len(trace_ids)} operation IDs from Application Insights...")
    
    # Fetch traces from Application Insights
    traces_by_operation = fetch_traces_from_app_insights(trace_ids)
    print(f"Found {len(traces_by_operation)} unique operation IDs")
    
    # Convert each group to JSONL record
    records = []
    for operation_id, traces in traces_by_operation.items():
        record = convert_traces_to_jsonl(traces)
        if record and record["query"]:  # Only include records with a query
            records.append(record)
    
    # Write to JSONL file
    output_path = Path(output_jsonl_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_jsonl_path, 'w', encoding='utf-8') as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + '\n')
    
    print(f"Successfully converted {len(records)} records to: {output_jsonl_path}")


def load_trace_ids_from_results(results_path: str) -> List[str]:
    """
    Load unique trace IDs from trace_results.json file.
    
    Args:
        results_path: Path to the trace_results.json file
        
    Returns:
        List of unique trace IDs
    """
    with open(results_path, 'r', encoding='utf-8') as f:
        results = json.load(f)
    
    trace_ids = set()
    
    # Add root trace ID from metadata if present
    if "metadata" in results and "root_trace_id" in results["metadata"]:
        trace_ids.add(results["metadata"]["root_trace_id"])
    
    # Extract trace IDs from all categories (single_intent, multi_intent, multi_turn, etc.)
    for key, value in results.items():
        if key == "metadata":
            continue
        if isinstance(value, list):
            for entry in value:
                if isinstance(entry, dict) and "trace_id" in entry:
                    trace_ids.add(entry["trace_id"])
    
    return list(trace_ids)


if __name__ == "__main__":
    import sys
    
    # Get the directory where this script is located
    script_dir = Path(__file__).parent
    report_dir = script_dir.parent / "report"
    trace_results_path = report_dir / "trace_results.json"
    
    # Load trace IDs from trace_results.json
    try:
        trace_ids = load_trace_ids_from_results(str(trace_results_path))
    except FileNotFoundError:
        print(f"Trace results file not found: {trace_results_path}")
        print("Please run the agent first to generate trace_results.json")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error parsing trace results file: {e}")
        sys.exit(1)
    
    if not trace_ids:
        print("No trace IDs found in trace_results.json")
        sys.exit(1)
    
    print(f"Found {len(trace_ids)} unique trace ID(s) in trace_results.json")
    
    # Output to datasets directory
    output_path = script_dir.parent / "datasets" / "agent_responses.jsonl"
    convert_traces_to_jsonl_file(trace_ids, str(output_path))
