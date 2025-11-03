# ---------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# ---------------------------------------------------------
import os
import re
import logging
from typing import Dict, Union

from .client import LLMClient


class BaseCustomEvaluator:
    """
    Base class for custom evaluators that use prompty files.
    
    This class provides common functionality for loading prompty files and extracting scores
    from LLM responses. Inherit from this class to create custom evaluators.
    
    Example:
        class MyCustomEvaluator(BaseCustomEvaluator):
            def __init__(self, model_config=None):
                super().__init__(
                    prompty_file_name="my_custom.prompty",
                    result_key="my_custom_score",
                    model_config=model_config
                )
            
            def __call__(self, query: str, response: str, **kwargs):
                return self.evaluate(query=query, response=response, **kwargs)
    """

    def __init__(self, prompty_file_name: str, result_key: str, model_config=None):
        """
        Initialize the base evaluator.
        
        :param prompty_file_name: Name of the prompty file (e.g., "coherence.prompty")
        :param result_key: Key to use in the return dictionary (e.g., "coherence_score_custom")
        :param model_config: Optional model configuration
        """
        # Look for prompts in the evaluator_repo/prompts directory
        # Navigate from agentic_ops back to the evaluation-specific prompts
        agentic_ops_dir = os.path.dirname(__file__)
        evaluations_dir = os.path.join(agentic_ops_dir, "..", "..", "evaluations", "offline", "custom_rag_evaluation")
        prompts_dir = os.path.join(evaluations_dir, "evaluator", "evaluator_repo", "prompts")
        self.prompty_path = os.path.join(prompts_dir, prompty_file_name)
        
        self.result_key = result_key
        self.model_config = model_config
        self.prompty_file_name = prompty_file_name

    def _load_prompt_content(self):
        """Load the prompt content from the prompty file."""
        try:
            with open(self.prompty_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Extract the system and user content from the prompty file
            parts = content.split('---')
            if len(parts) >= 3:
                prompt_content = parts[2].strip()
                
                # Split into system and user parts
                if 'system:' in prompt_content and 'user:' in prompt_content:
                    system_part = prompt_content.split('user:')[0].replace('system:', '').strip()
                    user_part = prompt_content.split('user:')[1].strip()
                    return system_part, user_part
                else:
                    # If no system/user split, treat all as user content
                    return "", prompt_content
            else:
                return "", content
        except Exception as e:
            logging.error(f"Error loading prompt file {self.prompty_path}: {e}")
            # Fallback prompt
            metric_name = self.result_key.replace('_score_custom', '').replace('_', ' ')
            return "", f"Evaluate the {metric_name} of the response to the query on a scale of 1-5."

    def _extract_score(self, llm_response: str, default_score: int = 3) -> int:
        """
        Extract score from LLM response.
        
        First tries to extract from structured response tags <S2>score</S2>,
        then falls back to pattern matching for numeric scores.
        
        :param llm_response: Raw response from LLM
        :param default_score: Default score if extraction fails
        :return: Extracted score as integer
        """
        # Try structured response format first
        score_match = re.search(r'<S2>(\d+)</S2>', llm_response)
        if score_match:
            return int(score_match.group(1))
        
        # Fallback to pattern matching for various score formats
        score_patterns = [
            r'(?:Score:\s*)?(\d+)',  # Score: 4 or just 4
            r'(?:Rating:\s*)?(\d+)',  # Rating: 4
            r'(?:\*\*Score\*\*:\s*)?(\d+)',  # **Score**: 4
            r'(?:Final score:\s*)?(\d+)',  # Final score: 4
        ]
        
        for pattern in score_patterns:
            score_list = re.findall(pattern, llm_response, re.IGNORECASE)
            if score_list:
                try:
                    score = int(score_list[0])
                    if 1 <= score <= 5:  # Validate score is in expected range
                        return score
                except ValueError:
                    continue
        
        # Final fallback
        logging.warning(f"Could not extract score from response for {self.result_key}. Using default: {default_score}")
        logging.debug(f"LLM Response: {llm_response[:200]}...")  # Log first 200 chars for debugging
        return default_score

    def _create_user_prompt(self, user_content: str, **kwargs) -> str:
        """
        Replace placeholders in user content with actual values.
        
        :param user_content: Template content with placeholders
        :param kwargs: Values to replace placeholders with
        :return: User prompt with placeholders replaced
        """
        user_prompt = user_content
        for key, value in kwargs.items():
            placeholder = f"{{{{{key}}}}}"
            if placeholder in user_prompt:
                user_prompt = user_prompt.replace(placeholder, str(value))
        
        # Log any unresolved placeholders for debugging
        remaining_placeholders = re.findall(r'\{\{(\w+)\}\}', user_prompt)
        if remaining_placeholders:
            logging.warning(f"Unresolved placeholders in {self.prompty_file_name}: {remaining_placeholders}")
        
        return user_prompt

    def evaluate(self, **kwargs) -> Dict[str, Union[str, float]]:
        """
        Main evaluation method.
        
        :param kwargs: Evaluation parameters (e.g., query, response, context, ground_truth, etc.)
        :return: Dictionary with evaluation results
        """
        logging.info(f"Loading prompt template from {os.path.basename(self.prompty_path)}")

        # Load prompt content from the prompty file
        system_content, user_content = self._load_prompt_content()

        # Create an instance of the LLMClient class
        llm_client = LLMClient(temperature=0.0)

        # Replace placeholders in the user content
        user_prompt = self._create_user_prompt(user_content, **kwargs)

        # Create messages for the LLM
        messages = [
            {"role": "system", "content": system_content},
            {"role": "user", "content": user_prompt}
        ]

        try:
            score_response = llm_client.get_llm_response_with_prompty(messages=messages)

            # Extract score from the response
            score = self._extract_score(score_response)

            logging.info(f"{self.result_key}: {score}")
            logging.info(f"{self.result_key} generated successfully")

            return {self.result_key: score}
            
        except Exception as e:
            logging.error(f"Error during evaluation for {self.result_key}: {e}")
            # Return default score on error
            default_score = 3
            logging.warning(f"Returning default score {default_score} for {self.result_key}")
            return {self.result_key: default_score}

    def __call__(self, **kwargs) -> Dict[str, Union[str, float]]:
        """
        Default call method - can be overridden by subclasses for specific parameter handling.
        
        :param kwargs: Evaluation parameters
        :return: Dictionary with evaluation results
        """
        return self.evaluate(**kwargs)