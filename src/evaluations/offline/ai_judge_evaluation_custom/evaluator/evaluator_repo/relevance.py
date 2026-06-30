from typing import Dict, Union

from ......agent_evaluation.agentic_ops.base_evaluator import \
    BaseCustomEvaluator


class RelevanceEvaluatorCustom(BaseCustomEvaluator):
    """
    Custom relevance evaluator that evaluates relevance score for a given query and response.

    The relevance measure assesses how well the response addresses the specific question or request
    posed in the query. It evaluates whether the response contains information that directly
    answers the question and is pertinent to the user's needs.
    
    Example:
        evaluator = RelevanceEvaluatorCustom()
        result = evaluator(query="What is AI?", response="AI is artificial intelligence...")
        # Returns: {"relevance_score_custom": 5}
    """

    def __init__(self, model_config=None):
        """
        Initialize the relevance evaluator.
        
        :param model_config: Optional model configuration (for compatibility)
        """
        super().__init__(
            prompty_file_name="relevance.prompty",
            result_key="relevance_score_custom",
            model_config=model_config
        )

    def __call__(self, query: str, response: str, **kwargs) -> Dict[str, Union[str, float]]:
        """
        Evaluate relevance for given input of query and response.

        :param query: The query to be evaluated.
        :type query: str
        :param response: The response to be evaluated.
        :type response: str
        :param kwargs: Additional parameters (if any)
        :return: The relevance score.
        :rtype: Dict[str, Union[str, float]]
        """
        return self.evaluate(query=query, response=response, **kwargs)