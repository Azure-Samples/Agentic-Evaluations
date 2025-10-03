# from azure.ai.evaluation import GroundednessEvaluator, FluencyEvaluator, RelevanceEvaluator, CoherenceEvaluator, SimilarityEvaluator, BleuScoreEvaluator
from azure.ai.evaluation import RelevanceEvaluator
# from src.evaluations.offline.bill_item_eval.evaluator.evaluator_repo.evaluate_bill_items import EvaluateBillItemsMatch
from src.evaluations.offline.agentic_evaluation.evaluator.evaluator_repo.evaluate_agent_invoked import EvaluateAgentsInvoked
# from src.evaluations.offline.bill_item_eval.evaluator.evaluator_repo.evaluate_bill_items import EvaluateBillItemsMatch
# from src.evaluations.offline.e2e_eval.evaluator.evaluator_repo.coherence import CoherenceEvaluatorCustom

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
        # "fluency_evaluator": FluencyEvaluator,
        # "coherance_evaluator": CoherenceEvaluator,
        # "groundedness_evaluator": GroundednessEvaluator,
        # "similarity_evaluator": SimilarityEvaluator,
        # "bleu_score_evaluator": BleuScoreEvaluator,
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
