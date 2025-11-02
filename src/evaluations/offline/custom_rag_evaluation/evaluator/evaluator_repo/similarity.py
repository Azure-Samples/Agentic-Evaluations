# ---------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# ---------------------------------------------------------
from typing import Dict, Union
from ......agent_evaluation.agentic_ops.base_evaluator import BaseCustomEvaluator


class SimilarityEvaluatorCustom(BaseCustomEvaluator):
    """
    Custom similarity evaluator that evaluates similarity score between response and ground truth.

    The similarity measure assesses how closely the response matches the expected
    ground truth answer in terms of semantic meaning and content. It evaluates whether
    the response provides equivalent information to the ground truth, even if expressed
    differently.
    
    Example:
        evaluator = SimilarityEvaluatorCustom()
        result = evaluator(
            query="What is AI?", 
            response="AI is artificial intelligence", 
            ground_truth="Artificial intelligence (AI) is intelligence demonstrated by machines"
        )
        # Returns: {"similarity_score_custom": 4}
    """

    def __init__(self, model_config=None):
        """
        Initialize the similarity evaluator.
        
        :param model_config: Optional model configuration (for compatibility)
        """
        super().__init__(
            prompty_file_name="similarity.prompty",
            result_key="similarity_score_custom",
            model_config=model_config
        )

    def __call__(self, query: str, response: str, ground_truth: str, **kwargs) -> Dict[str, Union[str, float]]:
        """
        Evaluate similarity between response and ground truth.

        :param query: The original query for context.
        :type query: str
        :param response: The response to be evaluated.
        :type response: str
        :param ground_truth: The expected correct answer to compare against.
        :type ground_truth: str
        :param kwargs: Additional parameters (if any)
        :return: The similarity score in the range of 1-5.
        :rtype: Dict[str, Union[str, float]]
        """
        return self.evaluate(query=query, response=response, ground_truth=ground_truth, **kwargs)