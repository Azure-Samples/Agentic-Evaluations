import logging
import os

from azure.ai.evaluation import CoherenceEvaluator, RelevanceEvaluator

from .evaluator.evaluator_repo.coherence import CoherenceEvaluatorCustom
from .evaluator.evaluator_repo.fluency import FluencyEvaluatorCustom
from .evaluator.evaluator_repo.relevance import RelevanceEvaluatorCustom
from .evaluator.evaluator_repo.similarity import SimilarityEvaluatorCustom


def get_logger(name: str):
    level = os.environ.get("LOG_LEVEL", "INFO").upper()
    logging.basicConfig(level=getattr(logging, level, logging.INFO))
    return logging.getLogger(name)
logger = get_logger(__name__)

class EvaluatorFactory:
    """Configuration for available evaluators."""

    EVALUATOR_FACTORIES = {
        # Azure built-in evaluators
        "relevance_evaluator": RelevanceEvaluator,
        "coherence_evaluator": CoherenceEvaluator,
        
        # Custom evaluators
        "custom_coherence_evaluator": CoherenceEvaluatorCustom,
        "custom_relevance_evaluator": RelevanceEvaluatorCustom,
        "custom_fluency_evaluator": FluencyEvaluatorCustom,
        "custom_similarity_evaluator": SimilarityEvaluatorCustom,
    }

    @staticmethod
    def get_evaluator_factory(name: str):
        if name not in EvaluatorFactory.EVALUATOR_FACTORIES:
            logger.error(f"[EVALUATOR][CONFIG] Evaluator '{name}' not found in available factories.")
            raise ValueError(f"Evaluator '{name}' not found in EVALUATOR_FACTORIES.")

        evaluator_class = EvaluatorFactory.EVALUATOR_FACTORIES[name]
        logger.info(f"[EVALUATOR][CONFIG] Successfully retrieved evaluator factory: '{name}' -> {evaluator_class.__name__}")
        return evaluator_class
