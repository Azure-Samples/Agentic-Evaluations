from azure.ai.evaluation import RelevanceEvaluator
from .evaluator.evaluator_repo.evaluate_agent_invoked import EvaluateAgentsInvoked

import os
import logging

def get_logger(name: str):
    level = os.environ.get("LOG_LEVEL", "INFO").upper()
    logging.basicConfig(level=getattr(logging, level, logging.INFO))
    return logging.getLogger(name)
logger = get_logger(__name__)

class EvaluatorFactory:
    """Configuration for available evaluators."""

    EVALUATOR_FACTORIES = {
        "relevance_evaluator": RelevanceEvaluator,
        "custom_agents_invoked_evaluator": EvaluateAgentsInvoked,    
    }

    @staticmethod
    def get_evaluator_factory(name: str):
        if name not in EvaluatorFactory.EVALUATOR_FACTORIES:
            logger.error(f"[EVALUATOR][CONFIG] Evaluator '{name}' not found in available factories.")
            raise ValueError(f"Evaluator '{name}' not found in EVALUATOR_FACTORIES.")

        evaluator_class = EvaluatorFactory.EVALUATOR_FACTORIES[name]
        logger.info(f"[EVALUATOR][CONFIG] Successfully retrieved evaluator factory: '{name}' -> {evaluator_class.__name__}")
        return evaluator_class    
