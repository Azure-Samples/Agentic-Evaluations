"""
Agent Inference Module
======================
Template module for running inference on queries from a dataset.

HOW TO USE:
1. Replace `simulate_agent_response()` with your actual agent/model logic
2. Configure input/output paths in experiment.yaml
3. Run via the pipeline or standalone

FLOW:
    Load Queries → Run Inference → Save Responses
"""
import logging
import os
import random
from pathlib import Path

from src.evaluations.offline.utils.file_operations import \
    load_queries_from_jsonl

from .experiment_utils import get_file_paths, prepare_output_file, save_result


# =============================================================================
# LOGGING SETUP
# =============================================================================
def get_logger(name: str):
    level = os.environ.get("LOG_LEVEL", "INFO").upper()
    logging.basicConfig(level=getattr(logging, level, logging.INFO))
    return logging.getLogger(name)

logger = get_logger(__name__)


# =============================================================================
# AGENT INFERENCE - CUSTOMIZE THIS FUNCTION
# this is a placeholder function to simulate agent responses. 
# Replace it with your actual inference logic. 
# Can be an API call, local model inference, or any other processing.
# =============================================================================
def simulate_agent_response(query: str) -> str:
    """
    Simulate agent response (PLACEHOLDER).
    
    ⚠️  TODO: Replace this with your actual inference logic:
        - Call your LLM API
        - Invoke your agent service  
        - Run your local model
    
    Args:
        query: The user query to process
        
    Returns:
        The agent's response string
    """
    sample_responses = [
        "The weather forecast shows cloudy skies with a temperature of 58°F.",
        "The air conditioner has been turned on.",
        "The air conditioner temperature has been set to 24 degrees Celsius.",
        "The device has been turned off.",
        "Your request has been completed successfully.",
    ]
    return random.choice(sample_responses)


# =============================================================================
# MAIN INFERENCE FUNCTION
# =============================================================================
def inference_main(config: dict, args=None) -> None:
    """
    Main entry point - processes queries and generates responses.
    
    Args:
        config: Configuration dictionary from experiment.yaml
        args: Optional additional arguments
    """
    # Step 1: Setup file paths
    input_path, output_path = get_file_paths(config)
    
    # Step 2: Prepare output file
    prepare_output_file(output_path)
    
    # Step 3: Load queries from dataset
    queries = load_queries_from_jsonl(str(input_path))
    
    # Step 4: Process each query
    for query_data in queries:
        query = query_data.get('query', '')
        session_id = query_data.get('session_id', '')
        
        # =============================================================================
        # To Do: Replace simulate_agent_response() with your agent logic
        # This can be an API call, a local model inference, or any other processing you need to do
        # =============================================================================

        response = simulate_agent_response(query)
        
        # Save result
        save_result(output_path, query, session_id, response)
    
    logger.info("[INFERENCE] Processed %d queries.", len(queries))

if __name__ == "__main__":
    # For standalone execution, load config from experiment.yaml
    import yaml

    # Get project root (go up 5 levels from this file)
    current_file = Path(__file__)  # .../experiment/agent_inference.py
    project_root = current_file.parent.parent.parent.parent.parent.parent  # Go up to project root
    config_path = project_root / "src/evaluations/offline/experiment_evaluation_pipeline/experiment.yaml"
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    experiment_config = config.get('experiment', {})
    inference_main(experiment_config)
