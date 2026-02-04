import asyncio
import json
import os
from datetime import datetime
from pathlib import Path
from agent_framework import ChatAgent
from agent_framework.observability import enable_instrumentation, get_tracer
from azure.monitor.opentelemetry import configure_azure_monitor
from opentelemetry import trace, context
from opentelemetry.trace import SpanKind
from opentelemetry.trace.span import format_trace_id
from agent_framework.azure import AzureOpenAIChatClient
from azure.identity import AzureCliCredential
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

from dotenv import load_dotenv
load_dotenv()

# Path to the dataset and output files
SCRIPT_DIR = Path(__file__).parent
DATASET_PATH = SCRIPT_DIR.parent / "datasets" / "agent_queries.json"
OUTPUT_PATH = SCRIPT_DIR.parent / "report" / "trace_results.json"

"""
This sample shows how you can observe an agent in Agent Framework by using 
Azure Monitor for Application Insights integration.
"""


def load_dataset() -> dict:
    """Load the agent queries dataset."""
    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_trace_results(results: dict) -> None:
    """Save trace results to a JSON file."""
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"\nTrace results saved to: {OUTPUT_PATH}")


async def run_single_intent_queries(agent: ChatAgent, queries: list, trace_results: dict) -> None:
    """Run single intent queries and collect trace IDs."""
    print("\n" + "="*60)
    print("SINGLE INTENT QUERIES")
    print("="*60)
    
    for item in queries:
        query_id = item["id"]
        query = item["query"]
        expected_tools = item["expected_tools"]
        
        # Create a new root span with empty context to get a unique trace ID
        with trace.use_span(trace.NonRecordingSpan(trace.SpanContext(
            trace_id=0,
            span_id=0,
            is_remote=False,
            trace_flags=trace.TraceFlags(0)
        )), end_on_exit=False):
            with get_tracer().start_as_current_span(f"Query: {query_id}", kind=SpanKind.CLIENT) as span:
                trace_id = format_trace_id(span.get_span_context().trace_id)
                print(f"\n[{query_id}] Trace ID: {trace_id}")
                print(f"Q: {query}")
                
                response = await agent.run(query)
                print(f"A: {response}")
                
                trace_results["single_intent"].append({
                    "id": query_id,
                    "query": query,
                    "expected_tools": expected_tools,
                    "response": str(response),
                    "trace_id": trace_id
                })


async def run_multi_intent_queries(agent: ChatAgent, queries: list, trace_results: dict) -> None:
    """Run multi-intent queries and collect trace IDs."""
    print("\n" + "="*60)
    print("MULTI-INTENT QUERIES")
    print("="*60)
    
    for item in queries:
        query_id = item["id"]
        query = item["query"]
        expected_tools = item["expected_tools"]
        
        # Create a new root span with empty context to get a unique trace ID
        with trace.use_span(trace.NonRecordingSpan(trace.SpanContext(
            trace_id=0,
            span_id=0,
            is_remote=False,
            trace_flags=trace.TraceFlags(0)
        )), end_on_exit=False):
            with get_tracer().start_as_current_span(f"Query: {query_id}", kind=SpanKind.CLIENT) as span:
                trace_id = format_trace_id(span.get_span_context().trace_id)
                print(f"\n[{query_id}] Trace ID: {trace_id}")
                print(f"Q: {query}")
                
                response = await agent.run(query)
                print(f"A: {response}")
                
                trace_results["multi_intent"].append({
                    "id": query_id,
                    "query": query,
                    "expected_tools": expected_tools,
                    "response": str(response),
                    "trace_id": trace_id
                })


async def run_multi_turn_conversations(agent: ChatAgent, conversations: list, trace_results: dict) -> None:
    """Run multi-turn conversations and collect trace IDs."""
    print("\n" + "="*60)
    print("MULTI-TURN CONVERSATIONS")
    print("="*60)
    
    for conv in conversations:
        conv_id = conv["id"]
        description = conv["description"]
        turns = conv["conversation"]
        
        print(f"\n--- Conversation: {conv_id} ({description}) ---")
        
        conversation_traces = {
            "id": conv_id,
            "description": description,
            "turns": []
        }
        
        # Create a new root span with empty context to get a unique trace ID for each conversation
        with trace.use_span(trace.NonRecordingSpan(trace.SpanContext(
            trace_id=0,
            span_id=0,
            is_remote=False,
            trace_flags=trace.TraceFlags(0)
        )), end_on_exit=False):
            with get_tracer().start_as_current_span(f"Conversation: {conv_id}", kind=SpanKind.CLIENT) as conv_span:
                conv_trace_id = format_trace_id(conv_span.get_span_context().trace_id)
                conversation_traces["conversation_trace_id"] = conv_trace_id
                print(f"Conversation Trace ID: {conv_trace_id}")

                # Reset agent thread for new conversation
                thread = agent.get_new_thread(service_thread_id=conv_trace_id)    
                for turn in turns:
                    turn_num = turn["turn"]
                    content = turn["content"]
                    expected_tools = turn["expected_tools"]
                    
                    with get_tracer().start_as_current_span(f"Turn {turn_num}", kind=SpanKind.CLIENT) as turn_span:
                        turn_trace_id = format_trace_id(turn_span.get_span_context().trace_id)
                        print(f"\n  Turn {turn_num} - Trace ID: {turn_trace_id}")
                        print(f"  User: {content}")
                        
                        response = await agent.run(content, thread=thread)
                        print(f"  Agent: {response}")
                        
                        conversation_traces["turns"].append({
                        "turn": turn_num,
                        "query": content,
                        "expected_tools": expected_tools,
                        "response": str(response),
                        "trace_id": turn_trace_id
                    })
        
        trace_results["multi_turn"].append(conversation_traces)


async def main():
    # Step 1: Configure Azure Monitor with your Application Insights connection string
    connection_string = os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")
    if not connection_string:
        print("WARNING: APPLICATIONINSIGHTS_CONNECTION_STRING not set!")
    else:
        configure_azure_monitor(connection_string=connection_string)
    
    # Step 2: Enable Agent Framework instrumentation (after Azure Monitor is configured)
    enable_instrumentation()
    
    # Load the dataset
    print("Loading dataset from:", DATASET_PATH)
    dataset = load_dataset()
    
    # Initialize trace results
    trace_results = {
        "metadata": {
            "run_timestamp": datetime.now().isoformat(),
            "dataset_path": str(DATASET_PATH)
        },
        "single_intent": [],
        "multi_intent": [],
        "multi_turn": []
    }

    # Create the agent
    client = AzureOpenAIChatClient(credential=AzureCliCredential())
    agent = ChatAgent(
        name="MultiToolAgent",
        instructions="You are a helpful assistant. Use available tools to help the user. Always be friendly and concise in your responses.",
        chat_client=client,
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
        tool_choice="auto", 
    )
    
    # Run all query types - each query will get its own unique trace ID
    await run_single_intent_queries(agent, dataset["single_intent"], trace_results)
    await run_multi_intent_queries(agent, dataset["multi_intent"], trace_results)
    # await run_multi_turn_conversations(agent, dataset["multi_turn"], trace_results)
    
    # Save trace results
    save_trace_results(trace_results)
    
    print("\n" + "="*60)
    print("EVALUATION COMPLETE")
    print(f"Total single-intent queries: {len(trace_results['single_intent'])}")
    print(f"Total multi-intent queries: {len(trace_results['multi_intent'])}")
    print(f"Total multi-turn conversations: {len(trace_results['multi_turn'])}")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())