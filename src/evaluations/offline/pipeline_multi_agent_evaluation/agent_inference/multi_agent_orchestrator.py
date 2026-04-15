"""
Multi-Agent Orchestrator Inference Module
==========================================
Pipeline module that runs a multi-agent orchestrator on queries from a dataset.

This module creates an orchestrator agent that routes user requests to
specialized device agents (AC, TV, Dishwasher). The orchestrator decides
which agent(s) to invoke via delegation tool functions, gathers responses
from sub-agents, and combines them into a single coherent reply.

Architecture:
    - Device agents (ACAgent, TVAgent, DishwasherAgent) each own their
      device-specific tools.
    - Delegation tools (delegate_to_ac_agent, etc.) wrap sub-agent calls
      and are registered as tools on the OrchestratorAgent.
    - The orchestrator uses the delegation tools to route requests to the
      appropriate device agent(s) based on user queries.

This module is designed to work with the evaluation pipeline runner.
It reads queries from a JSON file, runs them through the orchestrator,
and outputs responses to a JSONL file for evaluation.
"""
import asyncio
import json
import os
import logging
from typing import Annotated
from pathlib import Path
from agent_framework import Agent, tool
from agent_framework.observability import enable_instrumentation, get_tracer
from azure.monitor.opentelemetry import configure_azure_monitor
from opentelemetry import trace
from opentelemetry.trace import SpanKind
from opentelemetry.trace.span import format_trace_id
from agent_framework.openai import OpenAIChatClient
from azure.identity import AzureCliCredential
from pydantic import Field

# Handle both standalone and package execution
try:
    # When run as part of pipeline (package import)
    from .agent_tools import (
        # AC tools
        set_ac_temperature,
        turn_ac_on,
        turn_ac_off,
        set_ac_mode,
        get_ac_status,
        # TV tools
        turn_tv_on,
        turn_tv_off,
        set_tv_channel,
        set_tv_volume,
        get_tv_status,
        # Dishwasher tools
        start_dishwasher,
        stop_dishwasher,
        get_dishwasher_status,
        set_dishwasher_delay,
    )
except ImportError:
    # When run standalone
    from agent_tools import (
        set_ac_temperature,
        turn_ac_on,
        turn_ac_off,
        set_ac_mode,
        get_ac_status,
        turn_tv_on,
        turn_tv_off,
        set_tv_channel,
        set_tv_volume,
        get_tv_status,
        start_dishwasher,
        stop_dishwasher,
        get_dishwasher_status,
        set_dishwasher_delay,
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
# MODULE-LEVEL DEVICE AGENT REFERENCES
# =============================================================================
# These are set during create_agents() and accessed by the delegation tools.
_ac_agent: Agent | None = None
_tv_agent: Agent | None = None
_dishwasher_agent: Agent | None = None


# =============================================================================
# DELEGATION TOOLS (called by the Orchestrator to route to device agents)
# =============================================================================
# NOTE: approval_mode="never_require" is for sample brevity.
# Use "always_require" in production.
@tool(approval_mode="never_require")
async def delegate_to_ac_agent(
    request: Annotated[str, Field(description="The AC-related request to send to the AC Agent. Describe what the user wants done with the air conditioner.")],
) -> str:
    """Delegate an air conditioner request to the AC Agent. Use this for any AC-related operations like turning on/off, setting temperature, changing mode, or checking status."""
    response = await _ac_agent.run(request)
    return str(response)


@tool(approval_mode="never_require")
async def delegate_to_tv_agent(
    request: Annotated[str, Field(description="The TV-related request to send to the TV Agent. Describe what the user wants done with the television.")],
) -> str:
    """Delegate a television request to the TV Agent. Use this for any TV-related operations like turning on/off, changing channels, adjusting volume, or checking status."""
    response = await _tv_agent.run(request)
    return str(response)


@tool(approval_mode="never_require")
async def delegate_to_dishwasher_agent(
    request: Annotated[str, Field(description="The Dishwasher-related request to send to the Dishwasher Agent. Describe what the user wants done with the dishwasher.")],
) -> str:
    """Delegate a dishwasher request to the Dishwasher Agent. Use this for any dishwasher operations like starting/stopping cycles, checking status, or setting delayed starts."""
    response = await _dishwasher_agent.run(request)
    return str(response)


# =============================================================================
# AGENT SETUP
# =============================================================================
def create_agents(client) -> Agent:
    """Create device agents and the orchestrator agent.

    Device agents (ACAgent, TVAgent, DishwasherAgent) each have their own
    device-specific tools. The orchestrator delegates to them via
    delegation tool functions.

    Args:
        client: The OpenAIChatClient instance.

    Returns:
        The OrchestratorAgent configured with delegation tools.
    """
    global _ac_agent, _tv_agent, _dishwasher_agent

    # Create device agents with their tools
    _ac_agent = Agent(
        client=client,
        instructions=(
            "You are the AC Agent. You control the air conditioner. "
            "Use the available tools to turn the AC on/off, set temperature, "
            "change modes, and check status. Be concise in your responses."
        ),
        name="ACAgent",
        tools=[
            set_ac_temperature,
            turn_ac_on,
            turn_ac_off,
            set_ac_mode,
            get_ac_status,
        ],
    )

    _tv_agent = Agent(
        client=client,
        instructions=(
            "You are the TV Agent. You control the television. "
            "Use the available tools to turn the TV on/off, change channels, "
            "adjust volume, and check status. Be concise in your responses."
        ),
        name="TVAgent",
        tools=[
            turn_tv_on,
            turn_tv_off,
            set_tv_channel,
            set_tv_volume,
            get_tv_status,
        ],
    )

    _dishwasher_agent = Agent(
        client=client,
        instructions=(
            "You are the Dishwasher Agent. You control the dishwasher. "
            "Use the available tools to start/stop the dishwasher, check status, "
            "and set delayed starts. Be concise in your responses."
        ),
        name="DishwasherAgent",
        tools=[
            start_dishwasher,
            stop_dishwasher,
            get_dishwasher_status,
            set_dishwasher_delay,
        ],
    )

    # Create orchestrator with delegation tools
    orchestrator = Agent(
        client=client,
        instructions=(
            "You are the Smart Home Orchestrator. You coordinate requests across "
            "multiple device agents: AC Agent, TV Agent, and Dishwasher Agent.\n\n"
            "When a user makes a request:\n"
            "1. Determine which device agent(s) need to handle the request.\n"
            "2. Delegate to the appropriate agent(s) using the delegation tools.\n"
            "3. If a request involves multiple devices, call each relevant delegation tool.\n"
            "4. Combine the responses from all agents into a single coherent reply.\n\n"
            "Available delegation tools:\n"
            "- delegate_to_ac_agent: For air conditioner requests\n"
            "- delegate_to_tv_agent: For television requests\n"
            "- delegate_to_dishwasher_agent: For dishwasher requests\n\n"
            "Always be helpful and concise."
        ),
        name="OrchestratorAgent",
        tools=[delegate_to_ac_agent, delegate_to_tv_agent, delegate_to_dishwasher_agent],
    )

    return orchestrator


# =============================================================================
# QUERY PROCESSING
# =============================================================================
async def process_query(orchestrator: Agent, query: str, query_id: str) -> tuple[str, str]:
    """
    Process a single query with the orchestrator agent and return response + trace_id.

    Args:
        orchestrator: The orchestrator Agent instance
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
            response = await orchestrator.run(query)
            return str(response), trace_id


async def run_inference_async(config: dict) -> None:
    """
    Async main function for running multi-agent inference.

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
        logger.info("[AGENT] Azure Monitor configured")

    # Enable Agent Framework instrumentation
    enable_instrumentation()

    # Load dataset
    logger.info("[AGENT] Loading queries from: %s", input_file_path)
    with open(input_file_path, 'r', encoding='utf-8') as f:
        dataset = json.load(f)

    # Create device agents and orchestrator
    client = OpenAIChatClient(credential=AzureCliCredential())
    orchestrator = create_agents(client)

    logger.info("[AGENT] Orchestrator created with device agents: ACAgent, TVAgent, DishwasherAgent")

    # Process all query categories
    total_processed = 0

    for category in ['single_agent', 'multi_agent']:
        if category not in dataset:
            continue

        queries = dataset[category]
        logger.info("[AGENT] Processing %d %s queries", len(queries), category)

        for item in queries:
            query_id = item.get('id', f'{category}_{total_processed}')
            query = item.get('query', '')
            expected_agents = item.get('expected_agents', [])

            # Run inference
            response, trace_id = await process_query(orchestrator, query, query_id)

            # Save result
            result = {
                'id': query_id,
                'query': query,
                'response': response,
                'trace_id': trace_id,
                'expected_agents': expected_agents,
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
    from the 'agent_inference' section of experiment.yaml.

    Args:
        config: Configuration dictionary from experiment.yaml
        args: Optional additional arguments
    """
    logger.info("[AGENT] Starting multi-agent orchestrator inference...")
    asyncio.run(run_inference_async(config))
    logger.info("[AGENT] Multi-agent orchestrator inference completed.")


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
