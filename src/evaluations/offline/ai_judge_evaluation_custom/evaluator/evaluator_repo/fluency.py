# ---------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# ---------------------------------------------------------
from typing import Dict, Union

from ......agent_evaluation.agentic_ops.base_evaluator import \
    BaseCustomEvaluator


class FluencyEvaluatorCustom(BaseCustomEvaluator):
    """
    Custom fluency evaluator that evaluates fluency score for a given response.

    The fluency measure assesses the linguistic quality of the response, including
    grammar, syntax, readability, and natural language flow. A fluent response reads
    naturally, follows standard language conventions, and is easy to understand
    without grammatical errors or awkward phrasing.
    
    Example:
        evaluator = FluencyEvaluatorCustom()
        result = evaluator(response="This is a well-written response with proper grammar.")
        # Returns: {"fluency_score_custom": 4}
    """

    def __init__(self, model_config=None):
        """
        Initialize the fluency evaluator.
        
        :param model_config: Optional model configuration (for compatibility)
        """
        super().__init__(
            prompty_file_name="fluency.prompty",
            result_key="fluency_score_custom",
            model_config=model_config
        )

    def __call__(self, response: str, **kwargs) -> Dict[str, Union[str, float]]:
        """
        Evaluate fluency for given response.

        :param response: The response to be evaluated for linguistic quality.
        :type response: str
        :param kwargs: Additional parameters (if any)
        :return: The fluency score in the range of 1-5.
        :rtype: Dict[str, Union[str, float]]
        """
        return self.evaluate(response=response, **kwargs)