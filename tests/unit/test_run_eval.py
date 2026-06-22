"""Unit tests for run_eval module (src/agent_evaluation/agentic_ops/run_eval.py)."""

from unittest.mock import MagicMock, patch

import pytest

from src.agent_evaluation.agentic_ops.run_eval import (setup_evaluation,
                                                       should_pass_config)

# ---------------------------------------------------------------------------
# should_pass_config
# ---------------------------------------------------------------------------

class TestShouldPassConfig:
    def test_function_with_required_arg(self):
        """Function with required arg should return True."""
        def func(config):
            pass
        assert should_pass_config(func) is True

    def test_function_no_args(self):
        """Function with no args should return False."""
        def func():
            pass
        assert should_pass_config(func) is False

    def test_function_only_defaults(self):
        """Function with only default args should return False."""
        def func(x=10, y=20):
            pass
        assert should_pass_config(func) is False

    def test_function_with_kwargs_only(self):
        """Function with **kwargs only should return False."""
        def func(**kwargs):
            pass
        assert should_pass_config(func) is False

    def test_function_keyword_only_required(self):
        """Function with keyword-only required param should return True."""
        def func(*, config):
            pass
        assert should_pass_config(func) is True


# ---------------------------------------------------------------------------
# setup_evaluation
# ---------------------------------------------------------------------------

class TestSetupEvaluation:
    def test_setup_with_model_config_param(self):
        """Evaluator factory accepting model_config should get it passed."""
        mock_factory_cls = MagicMock()
        mock_evaluator = MagicMock()
        mock_factory_cls.return_value = mock_evaluator

        # Create a factory class with model_config parameter
        def factory_func(model_config=None):
            return mock_evaluator

        mock_eval_factory = MagicMock()
        mock_eval_factory.get_evaluator_factory.return_value = factory_func

        config = {
            "evaluators": {"test_eval": "test_factory"},
            "evaluator_config": {},
        }

        with patch.dict("os.environ", {
            "EVAL_AZURE_OPENAI_ENDPOINT": "https://test.openai.azure.com",
            "EVAL_AZURE_OPENAI_MODEL": "gpt-4",
            "EVAL_AZURE_OPENAI_VERSION": "2024-01-01",
        }):
            evaluators, evaluator_config = setup_evaluation(config, mock_eval_factory)

        assert "test_eval" in evaluators
        assert evaluators["test_eval"] == mock_evaluator

    def test_setup_with_no_params_factory(self):
        """Evaluator factory accepting no params should be called without args."""
        mock_evaluator = MagicMock()

        def factory_func():
            return mock_evaluator

        mock_eval_factory = MagicMock()
        mock_eval_factory.get_evaluator_factory.return_value = factory_func

        config = {
            "evaluators": {"simple_eval": "simple_factory"},
            "evaluator_config": {},
        }

        with patch.dict("os.environ", {
            "EVAL_AZURE_OPENAI_ENDPOINT": "https://test.openai.azure.com",
            "EVAL_AZURE_OPENAI_MODEL": "gpt-4",
            "EVAL_AZURE_OPENAI_VERSION": "2024-01-01",
        }):
            evaluators, evaluator_config = setup_evaluation(config, mock_eval_factory)

        assert "simple_eval" in evaluators
        assert evaluators["simple_eval"] == mock_evaluator

    def test_setup_with_azure_ai_project_param(self):
        """Factory accepting azure_ai_project should get it."""
        mock_evaluator = MagicMock()

        def factory_func(azure_ai_project=None):
            return mock_evaluator

        mock_eval_factory = MagicMock()
        mock_eval_factory.get_evaluator_factory.return_value = factory_func

        config = {
            "evaluators": {"proj_eval": "proj_factory"},
            "evaluator_config": {},
        }

        mock_project = MagicMock()
        with patch.dict("os.environ", {
            "EVAL_AZURE_OPENAI_ENDPOINT": "https://test.openai.azure.com",
            "EVAL_AZURE_OPENAI_MODEL": "gpt-4",
            "EVAL_AZURE_OPENAI_VERSION": "2024-01-01",
        }):
            evaluators, _ = setup_evaluation(config, mock_eval_factory, azure_ai_project=mock_project)

        assert "proj_eval" in evaluators

    def test_setup_resolves_column_mapping_placeholder(self):
        """evaluator_config with 'use_column_mapping' should resolve."""
        mock_evaluator = MagicMock()

        def factory_func():
            return mock_evaluator

        mock_eval_factory = MagicMock()
        mock_eval_factory.get_evaluator_factory.return_value = factory_func

        config = {
            "evaluators": {"test_eval": "test_factory"},
            "column_mapping": {"query": "${data.query}"},
            "evaluator_config": {
                "test_eval": {"column_mapping": "use_column_mapping"},
            },
        }

        with patch.dict("os.environ", {
            "EVAL_AZURE_OPENAI_ENDPOINT": "https://test.openai.azure.com",
            "EVAL_AZURE_OPENAI_MODEL": "gpt-4",
            "EVAL_AZURE_OPENAI_VERSION": "2024-01-01",
        }):
            _, evaluator_config = setup_evaluation(config, mock_eval_factory)

        assert evaluator_config["test_eval"]["column_mapping"] == {"query": "${data.query}"}
