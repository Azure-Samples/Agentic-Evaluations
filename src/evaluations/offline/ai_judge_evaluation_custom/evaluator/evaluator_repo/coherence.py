from typing import Dict, Union

from ......agent_evaluation.agentic_ops.base_evaluator import \
    BaseCustomEvaluator


class CoherenceEvaluatorCustom(BaseCustomEvaluator):
    """
    Custom coherence evaluator that evaluates coherence score for a given query and response.

    The coherence measure assesses the ability of the language model to generate text that reads naturally,
    flows smoothly, and resembles human-like language in its responses. Use it when assessing the readability
    and user-friendliness of a model's generated responses in real-world applications.
    
    Example:
        evaluator = CoherenceEvaluatorCustom()
        result = evaluator(query="What is AI?", response="AI is artificial intelligence...")
        # Returns: {"coherence_score_custom": 4}
    """

    def __init__(self, model_config=None):
        """
        Initialize the coherence evaluator.
        
        :param model_config: Optional model configuration (for compatibility)
        """
        super().__init__(
            prompty_file_name="coherence.prompty",
            result_key="coherence_score_custom",
            model_config=model_config
        )

    def __call__(self, query: str, response: str, **kwargs) -> Dict[str, Union[str, float]]:
        """
        Evaluate coherence for given input of query and response.

        :param query: The query to be evaluated.
        :type query: str
        :param response: The response to be evaluated.
        :type response: str
        :param kwargs: Additional parameters (if any)
        :return: The coherence score.
        :rtype: Dict[str, Union[str, float]]
        """
        return self.evaluate(query=query, response=response, **kwargs)