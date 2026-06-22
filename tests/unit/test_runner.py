"""Unit tests for the pipeline runner (src/agent_evaluation/agentic_ops/runner.py)."""

import argparse
from unittest.mock import MagicMock, mock_open, patch

import pytest
import yaml

from src.agent_evaluation.agentic_ops.runner import load_config, parse_args

# ---------------------------------------------------------------------------
# load_config
# ---------------------------------------------------------------------------

class TestLoadConfig:
    def test_loads_valid_yaml(self, tmp_path):
        """Should load and return config dict from valid YAML."""
        config_data = {"app_name": "TestApp", "pipeline": []}
        config_file = tmp_path / "experiment.yaml"
        config_file.write_text(yaml.dump(config_data))

        result = load_config(config_file)
        assert result == config_data

    def test_raises_on_missing_file(self, tmp_path):
        """Should raise FileNotFoundError for missing config."""
        missing = tmp_path / "missing.yaml"
        with pytest.raises(FileNotFoundError):
            load_config(missing)

    def test_returns_none_for_empty_yaml(self, tmp_path):
        """Empty YAML file should return None."""
        config_file = tmp_path / "empty.yaml"
        config_file.write_text("")
        result = load_config(config_file)
        assert result is None


# ---------------------------------------------------------------------------
# parse_args
# ---------------------------------------------------------------------------

class TestParseArgs:
    def test_defaults(self):
        """Default args should have expected values."""
        with patch("sys.argv", ["runner"]):
            args = parse_args()
        assert args.config_file == "experiment.yaml"
        assert args.index_fname is None
        assert args.sample == 0

    def test_custom_config_file(self):
        """Should accept --config_file argument."""
        with patch("sys.argv", ["runner", "--config_file", "custom.yaml"]):
            args = parse_args()
        assert args.config_file == "custom.yaml"

    def test_sample_arg(self):
        """Should accept --sample argument."""
        with patch("sys.argv", ["runner", "--sample", "10"]):
            args = parse_args()
        assert args.sample == 10

    def test_index_fname_arg(self):
        """Should accept --index_fname argument."""
        with patch("sys.argv", ["runner", "--index_fname", "file_001"]):
            args = parse_args()
        assert args.index_fname == "file_001"


# ---------------------------------------------------------------------------
# run_pipeline
# ---------------------------------------------------------------------------

class TestRunPipeline:
    @patch("src.agent_evaluation.agentic_ops.runner.importlib.import_module")
    @patch("src.agent_evaluation.agentic_ops.runner.load_config")
    def test_run_pipeline_exits_on_invalid_step(self, mock_load_config, mock_import, tmp_path):
        """Pipeline with an invalid step (missing base_path/module) should exit."""
        from src.agent_evaluation.agentic_ops.runner import run_pipeline

        mock_load_config.return_value = {
            "experiment_name": "test",
            "pipeline": [{"config_key": "evaluation"}],  # missing base_path and module
            "evaluation": {},
        }

        with pytest.raises(SystemExit):
            run_pipeline("test/experiment.yaml", argparse.Namespace(sample=0, index_fname=None))

    @patch("src.agent_evaluation.agentic_ops.runner.load_config")
    def test_run_pipeline_exits_on_empty_pipeline(self, mock_load_config, tmp_path):
        """Pipeline with no steps should exit."""
        from src.agent_evaluation.agentic_ops.runner import run_pipeline

        mock_load_config.return_value = {"pipeline": []}

        with pytest.raises(SystemExit):
            run_pipeline("test/experiment.yaml", argparse.Namespace(sample=0, index_fname=None))
