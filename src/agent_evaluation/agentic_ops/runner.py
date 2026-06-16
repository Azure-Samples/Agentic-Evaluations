import argparse
import importlib
import logging
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, Optional

import yaml


def get_logger(name: str):
    level = os.environ.get("LOG_LEVEL", "INFO").upper()
    logging.basicConfig(level=getattr(logging, level, logging.INFO))
    return logging.getLogger(name)

logger = get_logger(__name__)

def load_config(config_path: Path) -> Dict[str, Any]:
    if not config_path.exists():
        logger.error(f"[MAIN] [CONFIG] Config file not found: {config_path}")
        raise FileNotFoundError(f"Config file not found: {config_path}")
    with open(config_path, "r") as f:
        return yaml.safe_load(f)

def run_pipeline(config_file: Optional[str] = None, args: Optional[argparse.Namespace] = None) -> None:
    pipeline_start_time = time.time()
    step_times = []
    
    try:
        agent_eval_dir = Path(__file__).resolve().parents[2]  # src/agent_evaluation
        root_path = agent_eval_dir.parent

        config_file_path = Path(config_file)
        eval_dir = root_path / config_file_path.parent
        config_file = root_path / config_file_path
        config = load_config(config_file)

        pipeline_steps = config.get("pipeline", [])
        if not pipeline_steps:
            logger.error("No pipeline steps found in config.")
            sys.exit(1)

        for step in pipeline_steps:
            step_start_time = time.time()
            
            base_path = step.get("base_path")
            module_entry = step.get("module")

            if not (base_path and module_entry):
                logger.error(f"[MAIN] Invalid pipeline step definition: {step}")
                sys.exit(1)

            module_parts = module_entry.split(".")
            full_folder_path = eval_dir / base_path
            relative_folder_path = full_folder_path.relative_to(root_path)
            module_import_path = ".".join(relative_folder_path.parts + tuple(module_parts[:-1]))
            function_name = module_parts[-1]

            logger.info(f"[MAIN] Running step → {module_import_path}.{function_name}")

            try:
                imported = importlib.import_module(module_import_path)
                target = getattr(imported, function_name)

                config_key = step.get("config_key")
                if not config_key:
                    logger.error(f"[MAIN] Missing 'config_key' in pipeline step: {step}")
                    sys.exit(1)

                if config_key not in config:
                    logger.error(f"[MAIN] Config key '{config_key}' not found in experiment config.")
                    sys.exit(1)

                step_config = config[config_key]
                experiment_name = config.get("experiment_name", "default_experiment")
                step_config['experiment_name'] = experiment_name
                step_config['_eval_dir_name'] = eval_dir.name
                logger.debug(f"STEP config: {step_config}")

                if isinstance(target, type):
                    logger.info(f"Instantiating class {target.__name__} with args")
                    instance = target(config=step_config, args=args)
                    if not hasattr(instance, "run") or not callable(instance.run):
                        raise AttributeError(f"Class {target.__name__} must implement a callable 'run()' method.")

                    run_method = instance.run
                    run_method()

                elif callable(target):
                    logger.info(f"Calling function {target.__name__} with args")
                    target(config=step_config, args=args)

                else:
                    raise TypeError(f"{function_name} is not a class or a callable function")

                logger.info(f"[MAIN] Step '{function_name}' completed successfully.")
                
                step_end_time = time.time()
                step_duration = step_end_time - step_start_time
                step_times.append((function_name, step_duration))
                logger.info(f"[MAIN] Step '{function_name}' took {step_duration:.2f} seconds")

            except Exception as e:
                step_end_time = time.time()
                step_duration = step_end_time - step_start_time
                step_times.append((function_name, step_duration))
                logger.error(f"[MAIN] Step '{function_name}' failed after {step_duration:.2f} seconds: {e}")
                logger.exception(f"[MAIN] Step '{function_name}' failed: {e}")
                sys.exit(1)

        # Log timing summary
        pipeline_end_time = time.time()
        total_duration = pipeline_end_time - pipeline_start_time
        
        logger.info("=" * 60)
        logger.info("[MAIN] PIPELINE EXECUTION SUMMARY")
        logger.info("=" * 60)
        logger.info("Step-by-step timing breakdown:")
        for step_name, duration in step_times:
            logger.info(f"  • {step_name}: {duration:.2f} seconds")
        logger.info("-" * 60)
        logger.info(f"Total pipeline execution time: {total_duration:.2f} seconds")
        logger.info("=" * 60)

    except Exception as e:
        pipeline_end_time = time.time()
        total_duration = pipeline_end_time - pipeline_start_time
        logger.error(f"[MAIN] Pipeline execution failed after {total_duration:.2f} seconds: {e}")
        logger.exception(f"[MAIN] Pipeline execution failed: {e}")
        sys.exit(1)

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run modular evaluation pipeline.")
    parser.add_argument(
        "--config_file",
        type=str,
        default="experiment.yaml",
        help="YAML config file name (default: experiment.yaml)"
    )
    parser.add_argument(
        "--index_fname",
        type=str,
        default=None,
        help="To select specific index for re-run"
    )
    parser.add_argument(
        "--sample",
        type=int,
        default=0,
        help="To test # of sample, 0 means test all"
    )    
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    run_pipeline(args.config_file, args)
