"""
Agent inference module - invokes chat server with queries from dataset
"""
import os
import logging
from pathlib import Path
from src.evaluations.offline.utils.file_operations import load_queries_from_jsonl, append_to_jsonl
from .experiment_utils.http_client import chat_http_request


def get_logger(name: str):
    level = os.environ.get("LOG_LEVEL", "INFO").upper()
    logging.basicConfig(level=getattr(logging, level, logging.INFO))
    return logging.getLogger(name)


logger = get_logger(__name__)

def inference_main(config, args=None):
    """
    Main function for agent inference logic.
    Invokes chat server with queries from dataset and collects responses.
    """
    try:
        print('config', config)
        experiment_config = config
        parent_dir = Path(os.getcwd())
        
        # Get dataset path
        input_path = experiment_config.get('input_path', 'src/evaluations/offline/experiment_evaluation_pipeline/datasets/')
        input_file = experiment_config.get('input_file', 'agent_utterances.jsonl')
        output_path = experiment_config.get('output_path', 'src/evaluations/offline/experiment_evaluation_pipeline/datasets/')
        output_file = experiment_config.get('output_file', 'agent_responses.jsonl')
        base_url = experiment_config.get('base_url', 'http://localhost:8000')
        
        input_file_path = os.path.join(parent_dir, input_path, input_file)
        output_file_path = os.path.join(parent_dir, output_path, output_file)
        
        # Create output directory if it doesn't exist
        os.makedirs(os.path.join(parent_dir, output_path), exist_ok=True)
        
        # Clear the output file if it exists (start fresh)
        if os.path.exists(output_file_path):
            os.remove(output_file_path)
            logger.info("[AGENT INFERENCE] - Cleared existing output file: %s", output_file_path)
        
        # Load queries from JSONL file
        logger.info("[AGENT INFERENCE] - Loading queries from: %s", input_file_path)
        queries = load_queries_from_jsonl(input_file_path)
        
        logger.info("[AGENT INFERENCE] - Agent Inference begin: Dataset=%s, Total queries=%d, Base URL=%s", 
                   input_file, len(queries), base_url)
        logger.info("[AGENT INFERENCE] - Output file: %s", output_file_path)
        
        record_count = 0
        
        for i, query_data in enumerate(queries, 1):
            query_text = query_data.get('query', '')
            session_id = query_data.get('session_id')  # Read session_id from dataset
            
            if not session_id:
                raise ValueError(f"Query {i} is missing 'session_id' field in the dataset")
            
            logger.info("[AGENT INFERENCE] - [%d/%d] Query: %s, Session ID: %s", i, len(queries), query_text, session_id)
            response = chat_http_request(base_url, query_text, session_id)
            logger.info("[AGENT INFERENCE] - Response: %s", response)
            
            # Create result object with only query, session_id, and response
            result = {
                'query': query_text,
                'session_id': session_id,
                'response': response
            }
            
            # Write immediately to file
            append_to_jsonl(output_file_path, result)
            record_count += 1
            logger.info("[AGENT INFERENCE] - Record %d written to output file", record_count)
        
        logger.info("[AGENT INFERENCE] - All results saved successfully. Total records: %d", record_count)
        
        logger.info("[AGENT INFERENCE] - Agent inference completed successfully.")
    except Exception as e:
        logger.error("[AGENT INFERENCE] - Error in agent_inference: %s", e, exc_info=True)

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
