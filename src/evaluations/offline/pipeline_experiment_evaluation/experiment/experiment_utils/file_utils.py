"""
File Utilities
==============
Helper functions for file management in inference pipelines.
"""
import logging
import os
from pathlib import Path

from src.evaluations.offline.utils.file_operations import append_to_jsonl

logger = logging.getLogger(__name__)


# =============================================================================
# FILE MANAGEMENT HELPERS
# =============================================================================
def get_file_paths(config: dict) -> tuple[Path, Path]:
    """
    Build input and output file paths from config.
    
    Args:
        config: Dictionary with input_path, input_file, output_path, output_file
        
    Returns:
        Tuple of (input_file_path, output_file_path)
    """
    base_dir = Path(os.getcwd())
    
    input_file_path = base_dir / config.get('input_path', 'datasets/') / config.get('input_file', 'input.jsonl')
    output_file_path = base_dir / config.get('output_path', 'datasets/') / config.get('output_file', 'output.jsonl')
    
    return input_file_path, output_file_path


def prepare_output_file(output_path: Path) -> None:
    """
    Prepare output file - create directory and clear existing file.
    
    Args:
        output_path: Path to the output file
    """
    # Create output directory if needed
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Clear existing file to start fresh
    if output_path.exists():
        output_path.unlink()
        logger.info("[INFERENCE] Cleared existing output file")


def save_result(output_path: Path, query: str, session_id: str, response: str) -> None:
    """
    Save a single inference result to the output file.
    
    Args:
        output_path: Path to output JSONL file
        query: Original query
        session_id: Session identifier
        response: Agent response
    """
    result = {
        'query': query,
        'session_id': session_id,
        'response': response
    }
    append_to_jsonl(str(output_path), result)
