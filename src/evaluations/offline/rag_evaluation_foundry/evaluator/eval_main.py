import os
from pathlib import Path
from src.agent_evaluation.agentic_ops.run_eval import execute_eval
import logging
from src.evaluations.offline.utils.constants import EVAL_NAME
from src.evaluations.offline.utils.file_operations import get_next_run_id
from ..eval_factory import EvaluatorFactory


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
        output_filename = eval_config.get('_eval_dir_name', eval_config[EVAL_NAME])
        run_id = get_next_run_id(output_path)
        results_file_path = os.path.join(parent_dir, eval_config["output_path"], f"{run_id}_{output_filename}.json")
        logger.info("[EVALUATION][EVAL MAIN] - Evaluation begin: input_file_path=%s, results_file_path=%s, eval_name=%s", input_file_path, results_file_path, eval_name)
        execute_eval(eval_name, input_file_path, results_file_path, eval_config, EvaluatorFactory)
        logger.info("[EVALUATION][EVAL MAIN] - Evaluation completed successfully.")
    except Exception as e:
        logger.error("[EVALUATION][EVAL MAIN] - Error in eval_main: %s", e, exc_info=True)

if __name__ == "__main__":
    import yaml

    config_path = Path(__file__).resolve().parent.parent / "experiment.yaml"
    with open(config_path, "r", encoding="utf-8") as file:
        config = yaml.safe_load(file)

    eval_main(config.get("evaluation", {}))
