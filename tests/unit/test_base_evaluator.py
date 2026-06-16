"""Unit tests for the BaseCustomEvaluator (src/agent_evaluation/agentic_ops/base_evaluator.py)."""

import os
from unittest.mock import MagicMock, patch

import pytest

from src.agent_evaluation.agentic_ops.base_evaluator import BaseCustomEvaluator

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

class ConcreteEvaluator(BaseCustomEvaluator):
    """Concrete test subclass of BaseCustomEvaluator."""

    def __init__(self, model_config=None):
        super().__init__(
            prompty_file_name="test.prompty",
            result_key="test_score",
            model_config=model_config,
        )

    def __call__(self, query: str, response: str, **kwargs):
        return self.evaluate(query=query, response=response, **kwargs)


# ---------------------------------------------------------------------------
# _extract_score
# ---------------------------------------------------------------------------

class TestExtractScore:
    @pytest.fixture
    def evaluator(self):
        with patch.object(BaseCustomEvaluator, "__init__", lambda self, *a, **kw: None):
            e = BaseCustomEvaluator.__new__(BaseCustomEvaluator)
            e.result_key = "test_score"
            e.prompty_file_name = "test.prompty"
            return e

    def test_extracts_structured_s2_tag(self, evaluator):
        """Should extract score from <S2>4</S2> format."""
        assert evaluator._extract_score("<S2>4</S2>") == 4

    def test_extracts_score_colon_format(self, evaluator):
        """Should extract from 'Score: 5' format."""
        assert evaluator._extract_score("The evaluation is complete. Score: 5") == 5

    def test_extracts_rating_format(self, evaluator):
        """Should extract from 'Rating: 3' format."""
        assert evaluator._extract_score("Rating: 3 - The response is adequate") == 3

    def test_returns_default_on_no_match(self, evaluator):
        """Should return default when no score is found."""
        assert evaluator._extract_score("No numeric content here at all") == 3

    def test_custom_default(self, evaluator):
        """Should use custom default score."""
        assert evaluator._extract_score("no score", default_score=1) == 1

    def test_ignores_out_of_range_scores(self, evaluator):
        """Scores outside 1-5 from pattern matching should fall through."""
        # The S2 tag extraction doesn't validate range, but pattern matching does
        result = evaluator._extract_score("Score: 9")
        # 9 is out of range for pattern matching fallback, should use default
        assert result == 3

    def test_s2_tag_any_value(self, evaluator):
        """S2 tag should accept any digit value."""
        assert evaluator._extract_score("<S2>1</S2>") == 1
        assert evaluator._extract_score("<S2>5</S2>") == 5


# ---------------------------------------------------------------------------
# _create_user_prompt
# ---------------------------------------------------------------------------

class TestCreateUserPrompt:
    @pytest.fixture
    def evaluator(self):
        with patch.object(BaseCustomEvaluator, "__init__", lambda self, *a, **kw: None):
            e = BaseCustomEvaluator.__new__(BaseCustomEvaluator)
            e.result_key = "test_score"
            e.prompty_file_name = "test.prompty"
            return e

    def test_replaces_single_placeholder(self, evaluator):
        """Should replace {{query}} with value."""
        template = "Evaluate: {{query}}"
        result = evaluator._create_user_prompt(template, query="What is AI?")
        assert result == "Evaluate: What is AI?"

    def test_replaces_multiple_placeholders(self, evaluator):
        """Should replace multiple placeholders."""
        template = "Query: {{query}}\nResponse: {{response}}"
        result = evaluator._create_user_prompt(template, query="Q", response="A")
        assert result == "Query: Q\nResponse: A"

    def test_leaves_unknown_placeholders(self, evaluator):
        """Unresolved placeholders should remain."""
        template = "Query: {{query}} Context: {{context}}"
        result = evaluator._create_user_prompt(template, query="Q")
        assert "{{context}}" in result

    def test_no_placeholders(self, evaluator):
        """Template without placeholders should remain unchanged."""
        template = "Plain text with no placeholders"
        result = evaluator._create_user_prompt(template, query="Q")
        assert result == template


# ---------------------------------------------------------------------------
# _load_prompt_content
# ---------------------------------------------------------------------------

class TestLoadPromptContent:
    def test_returns_fallback_on_missing_file(self):
        """Missing prompty file should return fallback prompt."""
        with patch.object(BaseCustomEvaluator, "__init__", lambda self, *a, **kw: None):
            e = BaseCustomEvaluator.__new__(BaseCustomEvaluator)
            e.prompty_path = "/nonexistent/path/test.prompty"
            e.result_key = "test_score"
            e.prompty_file_name = "test.prompty"

        system, user = e._load_prompt_content()
        assert "test" in user.lower() or "evaluate" in user.lower()

    def test_parses_prompty_with_system_and_user(self, tmp_path):
        """Should parse system/user sections from prompty file."""
        # Prompty files have: ---\nmetadata\n---\nprompt content
        # The parser splits on '---' and expects at least 3 parts
        prompty_content = "---\nname: test\nmodel: gpt-4\n---\nsystem:\nYou are an evaluator.\nuser:\nEvaluate this: {{query}}\n---\n"
        prompty_file = tmp_path / "test.prompty"
        prompty_file.write_text(prompty_content, encoding="utf-8")

        with patch.object(BaseCustomEvaluator, "__init__", lambda self, *a, **kw: None):
            e = BaseCustomEvaluator.__new__(BaseCustomEvaluator)
            e.prompty_path = str(prompty_file)
            e.result_key = "test_score"
            e.prompty_file_name = "test.prompty"

        system, user = e._load_prompt_content()
        # The parser should extract content from the prompty file
        combined = system + user
        assert len(combined) > 0


# ---------------------------------------------------------------------------
# evaluate
# ---------------------------------------------------------------------------

class TestEvaluate:
    @patch("src.agent_evaluation.agentic_ops.base_evaluator.LLMClient")
    def test_evaluate_returns_score(self, mock_client_cls):
        """evaluate() should return dict with result_key and score."""
        mock_client = MagicMock()
        mock_client.get_llm_response_with_prompty.return_value = "<S2>4</S2>"
        mock_client_cls.return_value = mock_client

        with patch.object(BaseCustomEvaluator, "_load_prompt_content", return_value=("system", "{{query}}")):
            with patch.object(BaseCustomEvaluator, "__init__", lambda self, *a, **kw: None):
                e = BaseCustomEvaluator.__new__(BaseCustomEvaluator)
                e.prompty_path = "test.prompty"
                e.result_key = "test_score"
                e.prompty_file_name = "test.prompty"

            result = e.evaluate(query="What is AI?")
        assert result == {"test_score": 4}

    @patch("src.agent_evaluation.agentic_ops.base_evaluator.LLMClient")
    def test_evaluate_returns_default_on_error(self, mock_client_cls):
        """evaluate() should return default score on LLM error."""
        mock_client = MagicMock()
        mock_client.get_llm_response_with_prompty.side_effect = Exception("API error")
        mock_client_cls.return_value = mock_client

        with patch.object(BaseCustomEvaluator, "_load_prompt_content", return_value=("system", "{{query}}")):
            with patch.object(BaseCustomEvaluator, "__init__", lambda self, *a, **kw: None):
                e = BaseCustomEvaluator.__new__(BaseCustomEvaluator)
                e.prompty_path = "test.prompty"
                e.result_key = "test_score"
                e.prompty_file_name = "test.prompty"

            result = e.evaluate(query="What is AI?")
        assert result == {"test_score": 3}


# ---------------------------------------------------------------------------
# __call__
# ---------------------------------------------------------------------------

class TestCall:
    @patch("src.agent_evaluation.agentic_ops.base_evaluator.LLMClient")
    def test_call_delegates_to_evaluate(self, mock_client_cls):
        """__call__ should delegate to evaluate."""
        mock_client = MagicMock()
        mock_client.get_llm_response_with_prompty.return_value = "<S2>5</S2>"
        mock_client_cls.return_value = mock_client

        with patch.object(BaseCustomEvaluator, "_load_prompt_content", return_value=("sys", "{{query}}")):
            with patch.object(BaseCustomEvaluator, "__init__", lambda self, *a, **kw: None):
                e = BaseCustomEvaluator.__new__(BaseCustomEvaluator)
                e.prompty_path = "test.prompty"
                e.result_key = "test_score"
                e.prompty_file_name = "test.prompty"

            result = e(query="test")
        assert result == {"test_score": 5}
