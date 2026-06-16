"""Unit tests for the LLM Client (src/agent_evaluation/agentic_ops/client.py)."""

import json
from unittest.mock import MagicMock, patch

import pytest

from src.agent_evaluation.agentic_ops.client import LLMClient

# ---------------------------------------------------------------------------
# LLMClient._validate_messages
# ---------------------------------------------------------------------------

class TestValidateMessages:
    @pytest.fixture
    def client(self):
        with patch("src.agent_evaluation.agentic_ops.client.get_llm_client_instance"):
            return LLMClient(temperature=0.0)

    def test_valid_messages(self, client):
        """Valid messages should not raise."""
        messages = [
            {"role": "system", "content": "You are helpful."},
            {"role": "user", "content": "Hello"},
        ]
        client._validate_messages(messages)  # Should not raise

    def test_not_a_list_raises(self, client):
        """Non-list messages should raise ValueError."""
        with pytest.raises(ValueError, match="must be a list"):
            client._validate_messages("not a list")

    def test_non_dict_message_raises(self, client):
        """Non-dict message items should raise ValueError."""
        with pytest.raises(ValueError, match="must be a dictionary"):
            client._validate_messages(["not a dict"])

    def test_missing_role_raises(self, client):
        """Message without 'role' should raise ValueError."""
        with pytest.raises(ValueError, match="must have 'role' and 'content'"):
            client._validate_messages([{"content": "hello"}])

    def test_missing_content_raises(self, client):
        """Message without 'content' should raise ValueError."""
        with pytest.raises(ValueError, match="must have 'role' and 'content'"):
            client._validate_messages([{"role": "user"}])

    def test_invalid_role_raises(self, client):
        """Invalid role value should raise ValueError."""
        with pytest.raises(ValueError, match="invalid role"):
            client._validate_messages([{"role": "invalid", "content": "hi"}])

    def test_valid_roles(self, client):
        """All valid roles should pass."""
        messages = [
            {"role": "system", "content": "sys"},
            {"role": "user", "content": "usr"},
            {"role": "assistant", "content": "asst"},
        ]
        client._validate_messages(messages)  # Should not raise


# ---------------------------------------------------------------------------
# LLMClient._parse_json_response
# ---------------------------------------------------------------------------

class TestParseJsonResponse:
    @pytest.fixture
    def client(self):
        with patch("src.agent_evaluation.agentic_ops.client.get_llm_client_instance"):
            return LLMClient(temperature=0.0)

    def test_valid_json(self, client):
        """Valid JSON string should be parsed."""
        result = client._parse_json_response('{"key": "value"}')
        assert result == {"key": "value"}

    def test_json_with_markdown_fencing(self, client):
        """JSON wrapped in ```json ... ``` should be parsed."""
        raw = '```json\n{"key": "value"}\n```'
        result = client._parse_json_response(raw)
        assert result == {"key": "value"}

    def test_invalid_json_raises(self, client):
        """Invalid JSON should raise ValueError."""
        with pytest.raises(ValueError, match="Invalid JSON"):
            client._parse_json_response("not valid json {")

    def test_json_array(self, client):
        """JSON arrays should be parsed."""
        result = client._parse_json_response('[1, 2, 3]')
        assert result == [1, 2, 3]

    def test_whitespace_handling(self, client):
        """Extra whitespace should be handled."""
        result = client._parse_json_response('  \n {"a": 1} \n  ')
        assert result == {"a": 1}


# ---------------------------------------------------------------------------
# LLMClient.get_llm_raw_response
# ---------------------------------------------------------------------------

class TestGetLlmRawResponse:
    @patch("src.agent_evaluation.agentic_ops.client.get_llm_response")
    def test_builds_messages_correctly(self, mock_get_response):
        """Should construct messages with system and user roles."""
        mock_get_response.return_value = "response text"

        with patch("src.agent_evaluation.agentic_ops.client.get_llm_client_instance"):
            client = LLMClient(temperature=0.5)

        result = client.get_llm_raw_response("system prompt", "user input")
        assert result == "response text"

        call_args = mock_get_response.call_args
        messages = call_args[0][0]
        assert messages[0] == {"role": "system", "content": "system prompt"}
        assert messages[1] == {"role": "user", "content": "user input"}


# ---------------------------------------------------------------------------
# LLMClient.get_llm_response_json
# ---------------------------------------------------------------------------

class TestGetLlmResponseJson:
    @patch("src.agent_evaluation.agentic_ops.client.get_llm_response")
    def test_returns_parsed_json(self, mock_get_response):
        """Should return parsed JSON from LLM response."""
        mock_get_response.return_value = '{"score": 4}'

        with patch("src.agent_evaluation.agentic_ops.client.get_llm_client_instance"):
            client = LLMClient()

        result = client.get_llm_response_json("sys", "usr")
        assert result == {"score": 4}


# ---------------------------------------------------------------------------
# get_llm_response (module-level)
# ---------------------------------------------------------------------------

class TestGetLlmResponse:
    @patch("src.agent_evaluation.agentic_ops.client.DEPLOYMENT_NAME", "test-model")
    @patch("src.agent_evaluation.agentic_ops.client.get_llm_client_instance")
    def test_successful_response(self, mock_get_client):
        from src.agent_evaluation.agentic_ops.client import get_llm_response

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Hello!"
        mock_client.chat.completions.create.return_value = mock_response
        mock_get_client.return_value = mock_client

        messages = [{"role": "user", "content": "Hi"}]
        result = get_llm_response(messages)
        assert result == "Hello!"

    @patch("src.agent_evaluation.agentic_ops.client.DEPLOYMENT_NAME", None)
    def test_raises_on_missing_deployment(self):
        from src.agent_evaluation.agentic_ops.client import get_llm_response

        with pytest.raises(ValueError, match="EVAL_AZURE_OPENAI_MODEL"):
            get_llm_response([{"role": "user", "content": "test"}])

    @patch("src.agent_evaluation.agentic_ops.client.DEFAULT_RETRY_DELAY", 0)
    @patch("src.agent_evaluation.agentic_ops.client.DEPLOYMENT_NAME", "test-model")
    @patch("src.agent_evaluation.agentic_ops.client.get_llm_client_instance")
    def test_retries_on_failure(self, mock_get_client):
        from src.agent_evaluation.agentic_ops.client import get_llm_response

        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = [
            Exception("transient error"),
            Exception("transient error"),
            MagicMock(choices=[MagicMock(message=MagicMock(content="success"))]),
        ]
        mock_get_client.return_value = mock_client

        messages = [{"role": "user", "content": "Hi"}]
        result = get_llm_response(messages, max_retries=3)
        assert result == "success"

    @patch("src.agent_evaluation.agentic_ops.client.DEFAULT_RETRY_DELAY", 0)
    @patch("src.agent_evaluation.agentic_ops.client.DEPLOYMENT_NAME", "test-model")
    @patch("src.agent_evaluation.agentic_ops.client.get_llm_client_instance")
    def test_raises_after_max_retries(self, mock_get_client):
        from src.agent_evaluation.agentic_ops.client import get_llm_response

        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = Exception("permanent error")
        mock_get_client.return_value = mock_client

        messages = [{"role": "user", "content": "Hi"}]
        with pytest.raises(Exception, match="Maximum retries"):
            get_llm_response(messages, max_retries=2)
