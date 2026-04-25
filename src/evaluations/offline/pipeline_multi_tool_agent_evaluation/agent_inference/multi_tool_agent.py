"""
Multi-Tool Agent Inference Module
=================================
Pipeline module that runs a multi-tool agent on queries from a dataset.

This module is designed to work with the evaluation pipeline runner.
It reads queries from a JSON file, runs them through the agent, and
outputs responses to a JSONL file for evaluation.
"""
import asyncio
import json
import os
import logging
from datetime import datetime
from pathlib import Path
from agent_framework import Agent, ChatOptions
from agent_framework.observability import enable_instrumentation, get_tracer
from azure.monitor.opentelemetry import configure_azure_monitor
from opentelemetry import trace
from opentelemetry.trace import SpanKind
from opentelemetry.trace.span import format_trace_id
from agent_framework.openai import OpenAIChatClient
from azure.identity import AzureCliCredential

# Handle both standalone and package execution
try:
    # When run as part of pipeline (package import)
    from .agent_tools import (
        get_current_datetime,
        calculate_sum,
        calculate_product,
        convert_temperature,
        count_words,
        generate_uuid,
        format_json,
        get_weather
    )
except ImportError:
    # When run standalone
    from agent_tools import (
        get_current_datetime,
        calculate_sum,
        calculate_product,
        convert_temperature,
        count_words,
        generate_uuid,
        format_json,
        get_weather
    )

try:
    from src.evaluations.offline.utils.file_operations import append_to_jsonl
except ImportError:
    # When run standalone, add project root to path
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent.parent))
    from src.evaluations.offline.utils.file_operations import append_to_jsonl

from dotenv import load_dotenv
load_dotenv()


# =============================================================================
# LOGGING SETUP
# =============================================================================
def get_logger(name: str):
    level = os.environ.get("LOG_LEVEL", "INFO").upper()
    logging.basicConfig(level=getattr(logging, level, logging.INFO))
    
    # Suppress verbose logging from all dependencies
    logging.getLogger("azure").setLevel(logging.WARNING)
    logging.getLogger("opentelemetry").setLevel(logging.WARNING)
    logging.getLogger("agent_framework").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    
    return logging.getLogger(name)

logger = get_logger(__name__)


# =============================================================================
# AGENT SETUP
# =============================================================================
def create_agent() -> Agent:
    """Create and configure the multi-tool agent."""
    client = OpenAIChatClient(credential=AzureCliCredential())
    
    agent = Agent(
        client=client,
        instructions="You are a helpful assistant. Use available tools to help the user. Always be friendly and concise in your responses.",
        name="MultiToolAgent",
        tools=[
            get_weather,
            get_current_datetime,
            calculate_sum,
            calculate_product,
            convert_temperature,
            count_words,
            generate_uuid,
            format_json
        ],
        default_options=ChatOptions(tool_choice="auto"),
    )
    return agent


# =============================================================================
# QUERY PROCESSING
# =============================================================================
async def process_query(agent: Agent, query: str, query_id: str) -> tuple[str, str]:
    """
    Process a single query with the agent and return response + trace_id.
    
    Args:
        agent: The ChatAgent instance
        query: The query text
        query_id: Unique identifier for the query
        
    Returns:
        Tuple of (response, trace_id)
    """
    # Create a new root span to get a unique trace ID
    with trace.use_span(trace.NonRecordingSpan(trace.SpanContext(
        trace_id=0,
        span_id=0,
        is_remote=False,
        trace_flags=trace.TraceFlags(0)
    )), end_on_exit=False):
        with get_tracer().start_as_current_span(f"Query: {query_id}", kind=SpanKind.CLIENT) as span:
            trace_id = format_trace_id(span.get_span_context().trace_id)
            response = await agent.run(query)
            return str(response), trace_id


async def run_inference_async(config: dict) -> None:
    """
    Async main function for running agent inference.
    
    Args:
        config: Configuration dictionary from experiment.yaml
    """
    # Get paths from config
    base_dir = Path(os.getcwd())
    input_path = config.get('input_path', 'datasets/')
    input_file = config.get('input_file', 'agent_queries.json')
    output_path = config.get('output_path', 'datasets/')
    output_file = config.get('output_file', 'agent_responses.jsonl')
    
    input_file_path = base_dir / input_path / input_file
    output_file_path = base_dir / output_path / output_file
    
    # Create output directory if needed
    output_file_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Clear existing output file
    if output_file_path.exists():
        output_file_path.unlink()
        logger.info("[AGENT] Cleared existing output file")
    
    # Configure Azure Monitor (if connection string is set)
    connection_string = os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")
    if connection_string:
        configure_azure_monitor(connection_string=connection_string)
        enable_instrumentation()
        logger.info("[AGENT] Azure Monitor configured with instrumentation")
    else:
        logger.warning("[AGENT] APPLICATIONINSIGHTS_CONNECTION_STRING not set — telemetry disabled")
    
    # Load dataset
    logger.info("[AGENT] Loading queries from: %s", input_file_path)
    with open(input_file_path, 'r', encoding='utf-8') as f:
        dataset = json.load(f)
    
    # Create agent
    agent = create_agent()
    logger.info("[AGENT] Agent created: %s", agent.name)
    
    # Process all query categories
    total_processed = 0
    
    for category in ['single_intent', 'multi_intent']:
        if category not in dataset:
            continue
            
        queries = dataset[category]
        logger.info("[AGENT] Processing %d %s queries", len(queries), category)
        
        for item in queries:
            query_id = item.get('id', f'{category}_{total_processed}')
            query = item.get('query', '')
            expected_tools = item.get('expected_tools', [])
            
            # Run inference
            response, trace_id = await process_query(agent, query, query_id)
            
            # Save result
            result = {
                'id': query_id,
                'query': query,
                'response': response,
                'trace_id': trace_id,
                'expected_tools': expected_tools,
                'category': category
            }
            append_to_jsonl(str(output_file_path), result)
            total_processed += 1
            
            logger.info("[AGENT] [%d] %s", total_processed, query_id)
            logger.info("[AGENT] Query: %s", query[:80] + "..." if len(query) > 80 else query)
            logger.info("[AGENT] Response: %s", response[:100] + "..." if len(response) > 100 else response)
            logger.info("[AGENT] Trace ID: %s", trace_id)
            logger.info("")  # blank line for readability
    
    logger.info("[AGENT] Inference complete. Processed %d queries.", total_processed)


# =============================================================================
# PIPELINE ENTRY POINT
# =============================================================================
def inference_main(config: dict, args=None) -> None:
    """
    Main entry point for the pipeline runner.
    
    This function is called by the pipeline runner with the config
    from the 'experiment' section of experiment.yaml.
    
    Args:
        config: Configuration dictionary from experiment.yaml
        args: Optional additional arguments
    """
    logger.info("[AGENT] Starting multi-tool agent inference...")
    asyncio.run(run_inference_async(config))
    logger.info("[AGENT] Multi-tool agent inference completed.")


# =============================================================================
# STANDALONE EXECUTION
# =============================================================================
if __name__ == "__main__":
    import yaml
    
    # Get config path relative to this file
    script_dir = Path(__file__).parent
    config_path = script_dir.parent / "experiment.yaml"
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    experiment_config = config.get('agent_inference', {})
    inference_main(experiment_config)