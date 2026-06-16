"""
LLM Client for Custom Evaluators

This module provides a simplified client for interacting with Azure OpenAI
for custom evaluation purposes. It handles authentication, retry logic,
and response parsing.
"""

import json
import logging
import os
import time

from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from dotenv import load_dotenv
from openai import AzureOpenAI

load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# Azure OpenAI Configuration
AZURE_ENDPOINT = os.getenv("EVAL_AZURE_OPENAI_ENDPOINT")
API_VERSION = os.getenv("EVAL_AZURE_OPENAI_VERSION")
DEPLOYMENT_NAME = os.getenv("EVAL_AZURE_OPENAI_MODEL")

# Default configuration
DEFAULT_MAX_TOKENS = 800
DEFAULT_TEMPERATURE = 0.0
DEFAULT_MAX_RETRIES = 3
DEFAULT_RETRY_DELAY = 5


def get_llm_client_instance():
    """Get an instance of the Azure OpenAI client using DefaultAzureCredential."""
    if not all([AZURE_ENDPOINT, API_VERSION]):
        raise ValueError(
            "Missing required Azure OpenAI configuration. "
            "Please check EVAL_AZURE_OPENAI_ENDPOINT "
            "and EVAL_AZURE_OPENAI_VERSION environment variables."
        )

    credential = DefaultAzureCredential()
    token_provider = get_bearer_token_provider(
        credential, "https://cognitiveservices.azure.com/.default"
    )

    return AzureOpenAI(
        azure_endpoint=AZURE_ENDPOINT,
        azure_ad_token_provider=token_provider,
        api_version=API_VERSION,
    )


def get_llm_response(messages, temperature=DEFAULT_TEMPERATURE, max_retries=DEFAULT_MAX_RETRIES):
    """
    Get response from Azure OpenAI with retry logic.
    
    :param messages: List of message dictionaries for the conversation
    :param temperature: Sampling temperature (0.0 to 1.0)
    :param max_retries: Maximum number of retry attempts
    :return: Response content as string
    """
    if not DEPLOYMENT_NAME:
        raise ValueError("EVAL_AZURE_OPENAI_MODEL environment variable is not set.")
        
    client = get_llm_client_instance()
    
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model=DEPLOYMENT_NAME,
                messages=messages,
                temperature=temperature,
                max_tokens=DEFAULT_MAX_TOKENS,
            )
            
            response_content = response.choices[0].message.content
            if response_content:
                return response_content
            else:
                raise ValueError("Empty response received from Azure OpenAI")

        except Exception as e:
            logger.warning(f"Attempt {attempt + 1}/{max_retries} failed: {e}")
            if attempt < max_retries - 1:
                logger.info(f"Retrying in {DEFAULT_RETRY_DELAY} seconds...")
                time.sleep(DEFAULT_RETRY_DELAY)
            else:
                raise Exception(f"Maximum retries ({max_retries}) exceeded: {e}")


class LLMClient:
    """
    Simplified client for interacting with Azure OpenAI for evaluation purposes.
    
    This client is designed to work with custom evaluators and provides
    methods for both raw text and JSON responses.
    """

    def __init__(self, temperature=DEFAULT_TEMPERATURE):
        """
        Initialize the LLM client.
        
        :param temperature: Sampling temperature for responses (0.0 to 1.0)
        """
        self.temperature = temperature
        logger.info(f"Initialized LLMClient with temperature: {temperature}")

    def get_llm_response_with_prompty(self, messages):
        """
        Get response from LLM using a list of messages.
        
        This is the main method used by custom evaluators.
        
        :param messages: List of message dictionaries with 'role' and 'content' keys
        :return: Response content as string
        """
        self._validate_messages(messages)
        return get_llm_response(messages, temperature=self.temperature)

    def get_llm_raw_response(self, system_prompt, user_input):
        """
        Get raw response from LLM with separate system prompt and user input.
        
        :param system_prompt: System prompt content
        :param user_input: User input content
        :return: Response content as string
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input},
        ]
        return self.get_llm_response_with_prompty(messages)
    
    def get_llm_response_json_with_prompty(self, messages):
        """
        Get JSON response from LLM using a list of messages.
        
        :param messages: List of message dictionaries
        :return: Parsed JSON response
        """
        response = self.get_llm_response_with_prompty(messages)
        return self._parse_json_response(response)

    def get_llm_response_json(self, system_prompt, user_input):
        """
        Get JSON response from LLM with separate prompts.
        
        :param system_prompt: System prompt content
        :param user_input: User input content
        :return: Parsed JSON response
        """
        response = self.get_llm_raw_response(system_prompt, user_input)
        return self._parse_json_response(response)

    def _validate_messages(self, messages):
        """Validate message format."""
        if not isinstance(messages, list):
            raise ValueError("Messages must be a list")
        
        for i, msg in enumerate(messages):
            if not isinstance(msg, dict):
                raise ValueError(f"Message {i} must be a dictionary")
            if 'role' not in msg or 'content' not in msg:
                raise ValueError(f"Message {i} must have 'role' and 'content' keys")
            if msg['role'] not in ['system', 'user', 'assistant']:
                raise ValueError(f"Message {i} has invalid role: {msg['role']}")

    def _parse_json_response(self, response):
        """Parse JSON response with error handling."""
        response = response.strip()
        
        # Remove common markdown artifacts
        if response.startswith("```json"):
            response = response[7:]
        if response.endswith("```"):
            response = response[:-3]
        
        response = response.strip()
        
        try:
            return json.loads(response)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.error(f"Raw response: {response}")
            raise ValueError(f"Invalid JSON response from LLM: {e}")