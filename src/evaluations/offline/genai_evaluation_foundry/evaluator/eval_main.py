import os
from pathlib import Path
from src.agent_evaluation.agentic_ops.run_eval import execute_eval
import logging
from src.evaluations.offline.utils.constants import *
from ..eval_factory import EvaluatorFactory
from src.evaluations.offline.utils.blobFileUpload import upload_file_to_blob


def get_logger(name: str):
    level = os.environ.get("LOG_LEVEL", "INFO").upper()
    logging.basicConfig(level=getattr(logging, level, logging.INFO))
    return logging.getLogger(name)

logger = get_logger(__name__)

def eval_main(config, args=None):
    """
    Main function for evaluation logic.
    """
    try:
        eval_config = config
        parent_dir = Path(os.getcwd())
        output_path = os.path.join(parent_dir, eval_config["output_path"])
        # Create the output directory if it doesn't exist
        os.makedirs(output_path, exist_ok=True)
        eval_name = eval_config[EVAL_NAME]
        input_file_path = os.path.join(parent_dir, eval_config["input_path"], eval_config["input_file"])
        results_file_path = os.path.join(parent_dir, eval_config["output_path"], f"{eval_config[EVAL_NAME]}.json")
        logger.info("[EVALUATION][EVAL MAIN] - Evaluation begin: input_file_path=%s, results_file_path=%s, eval_name=%s", input_file_path, results_file_path, eval_name)
        execute_eval(eval_name, input_file_path, results_file_path, eval_config, EvaluatorFactory)
        logger.info("[EVALUATION][EVAL MAIN] - Evaluation completed successfully.")
    except Exception as e:
        logger.error("[EVALUATION][EVAL MAIN] - Error in eval_main: %s", e, exc_info=True)

if __name__ == "__main__":
    eval_main()
