"""Unit tests for the CLI module (src/agent_evaluation/cli.py)."""

import argparse
from unittest.mock import MagicMock, mock_open, patch

import pytest
import yaml

from src.agent_evaluation.cli import (EXCLUDE_DIRS, SAMPLES_DIR, cmd_info,
                                      cmd_list, cmd_run, cmd_run_all,
                                      discover_samples, interactive_select,
                                      main, print_samples_table, run_sample)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

SAMPLE_YAML_CONTENT = {
    "app_name": "TestApp",
    "experiment_name": "test_experiment",
    "version": "1.0",
    "pipeline": [
        {"config_key": "evaluation", "base_path": "evaluator", "module": "eval_main.eval_main"},
    ],
    "evaluation": {
        "input_path": "datasets/",
        "input_file": "sample.jsonl",
        "output_path": "reports/",
        "evaluators": {"score": "relevance_evaluator"},
    },
}


@pytest.fixture
def mock_samples():
    return [
        {
            "name": "agentic_evaluation",
            "app_name": "TestApp",
            "experiment_name": "test_experiment",
            "version": "1.0",
            "config_path": "src/evaluations/offline/agentic_evaluation/experiment.yaml",
            "stages": ["evaluation"],
        },
        {
            "name": "rag_evaluation_foundry",
            "app_name": "RAGApp",
            "experiment_name": "rag_experiment",
            "version": "2.0",
            "config_path": "src/evaluations/offline/rag_evaluation_foundry/experiment.yaml",
            "stages": ["evaluation"],
        },
    ]


# ---------------------------------------------------------------------------
# discover_samples
# ---------------------------------------------------------------------------

class TestDiscoverSamples:
    def test_returns_list(self, tmp_path, monkeypatch):
        """discover_samples should return a list."""
        monkeypatch.setattr("src.agent_evaluation.cli.SAMPLES_DIR", tmp_path)
        result = discover_samples()
        assert isinstance(result, list)

    def test_skips_excluded_dirs(self, tmp_path, monkeypatch):
        """Directories in EXCLUDE_DIRS should be skipped."""
        monkeypatch.setattr("src.agent_evaluation.cli.SAMPLES_DIR", tmp_path)
        for excluded in EXCLUDE_DIRS:
            d = tmp_path / excluded
            d.mkdir()
            (d / "experiment.yaml").write_text(yaml.dump(SAMPLE_YAML_CONTENT))

        result = discover_samples()
        assert result == []

    def test_skips_dirs_without_experiment_yaml(self, tmp_path, monkeypatch):
        """Directories without experiment.yaml should be skipped."""
        monkeypatch.setattr("src.agent_evaluation.cli.SAMPLES_DIR", tmp_path)
        (tmp_path / "some_dir").mkdir()
        result = discover_samples()
        assert result == []

    def test_discovers_valid_sample(self, tmp_path, monkeypatch):
        """A valid sample directory with experiment.yaml should be discovered."""
        monkeypatch.setattr("src.agent_evaluation.cli.SAMPLES_DIR", tmp_path)
        monkeypatch.setattr("src.agent_evaluation.cli.ROOT_DIR", tmp_path.parent)

        sample_dir = tmp_path / "my_sample"
        sample_dir.mkdir()
        (sample_dir / "experiment.yaml").write_text(yaml.dump(SAMPLE_YAML_CONTENT))

        result = discover_samples()
        assert len(result) == 1
        assert result[0]["name"] == "my_sample"
        assert result[0]["app_name"] == "TestApp"
        assert result[0]["experiment_name"] == "test_experiment"
        assert result[0]["version"] == "1.0"
        assert result[0]["stages"] == ["evaluation"]

    def test_discovers_multiple_samples_sorted(self, tmp_path, monkeypatch):
        """Multiple samples should be returned in sorted order."""
        monkeypatch.setattr("src.agent_evaluation.cli.SAMPLES_DIR", tmp_path)
        monkeypatch.setattr("src.agent_evaluation.cli.ROOT_DIR", tmp_path.parent)

        for name in ["z_sample", "a_sample", "m_sample"]:
            d = tmp_path / name
            d.mkdir()
            (d / "experiment.yaml").write_text(yaml.dump(SAMPLE_YAML_CONTENT))

        result = discover_samples()
        assert [s["name"] for s in result] == ["a_sample", "m_sample", "z_sample"]

    def test_uses_defaults_for_missing_yaml_fields(self, tmp_path, monkeypatch):
        """Missing fields in experiment.yaml should use directory name as default."""
        monkeypatch.setattr("src.agent_evaluation.cli.SAMPLES_DIR", tmp_path)
        monkeypatch.setattr("src.agent_evaluation.cli.ROOT_DIR", tmp_path.parent)

        sample_dir = tmp_path / "bare_sample"
        sample_dir.mkdir()
        (sample_dir / "experiment.yaml").write_text(yaml.dump({"pipeline": []}))

        result = discover_samples()
        assert len(result) == 1
        assert result[0]["name"] == "bare_sample"
        assert result[0]["app_name"] == "bare_sample"
        assert result[0]["experiment_name"] == "bare_sample"
        assert result[0]["version"] == ""
        assert result[0]["stages"] == []


# ---------------------------------------------------------------------------
# print_samples_table
# ---------------------------------------------------------------------------

class TestPrintSamplesTable:
    def test_empty_samples(self, capsys):
        """Empty list should print 'No evaluation samples found.'"""
        print_samples_table([])
        captured = capsys.readouterr()
        assert "No evaluation samples found." in captured.out

    def test_prints_sample_names(self, capsys, mock_samples):
        """Should print sample names in the table."""
        print_samples_table(mock_samples)
        captured = capsys.readouterr()
        assert "agentic_evaluation" in captured.out
        assert "rag_evaluation_foundry" in captured.out

    def test_prints_stages(self, capsys, mock_samples):
        """Should print stage info in the table."""
        print_samples_table(mock_samples)
        captured = capsys.readouterr()
        assert "evaluation" in captured.out


# ---------------------------------------------------------------------------
# run_sample
# ---------------------------------------------------------------------------

class TestRunSample:
    @patch("src.agent_evaluation.agentic_ops.runner.run_pipeline")
    @patch("src.agent_evaluation.agentic_ops.runner.parse_args")
    def test_run_sample_success(self, mock_parse, mock_run, mock_samples):
        """Successful run should return 0."""
        mock_args = MagicMock()
        mock_parse.return_value = mock_args
        mock_run.return_value = None

        result = run_sample(mock_samples[0])
        assert result == 0

    @patch("src.agent_evaluation.agentic_ops.runner.run_pipeline")
    @patch("src.agent_evaluation.agentic_ops.runner.parse_args")
    def test_run_sample_system_exit(self, mock_parse, mock_run, mock_samples):
        """SystemExit with code should be returned."""
        mock_args = MagicMock()
        mock_parse.return_value = mock_args
        mock_run.side_effect = SystemExit(2)

        result = run_sample(mock_samples[0])
        assert result == 2

    @patch("src.agent_evaluation.agentic_ops.runner.run_pipeline")
    @patch("src.agent_evaluation.agentic_ops.runner.parse_args")
    def test_run_sample_with_extra_args(self, mock_parse, mock_run, mock_samples):
        """Extra args should be passed to sys.argv."""
        mock_args = MagicMock()
        mock_parse.return_value = mock_args
        mock_run.return_value = None

        result = run_sample(mock_samples[0], extra_args=["--sample", "5"])
        assert result == 0


# ---------------------------------------------------------------------------
# interactive_select
# ---------------------------------------------------------------------------

class TestInteractiveSelect:
    @patch("builtins.input", return_value="1")
    def test_select_by_number(self, mock_input, mock_samples):
        """Selecting by number should return the correct sample."""
        result = interactive_select(mock_samples)
        assert result == mock_samples[0]

    @patch("builtins.input", return_value="2")
    def test_select_by_second_number(self, mock_input, mock_samples):
        """Selecting second item returns second sample."""
        result = interactive_select(mock_samples)
        assert result == mock_samples[1]

    @patch("builtins.input", return_value="q")
    def test_quit(self, mock_input, mock_samples):
        """Typing 'q' should return None."""
        result = interactive_select(mock_samples)
        assert result is None

    @patch("builtins.input", return_value="exit")
    def test_exit(self, mock_input, mock_samples):
        """Typing 'exit' should return None."""
        result = interactive_select(mock_samples)
        assert result is None

    @patch("builtins.input", return_value="agentic")
    def test_select_by_partial_name(self, mock_input, mock_samples):
        """Partial name matching should work for unique matches."""
        result = interactive_select(mock_samples)
        assert result == mock_samples[0]

    @patch("builtins.input", side_effect=EOFError)
    def test_eof_returns_none(self, mock_input, mock_samples):
        """EOFError should return None."""
        result = interactive_select(mock_samples)
        assert result is None

    @patch("builtins.input", side_effect=KeyboardInterrupt)
    def test_keyboard_interrupt_returns_none(self, mock_input, mock_samples):
        """KeyboardInterrupt should return None."""
        result = interactive_select(mock_samples)
        assert result is None


# ---------------------------------------------------------------------------
# cmd_list
# ---------------------------------------------------------------------------

class TestCmdList:
    @patch("src.agent_evaluation.cli.discover_samples")
    def test_cmd_list_returns_zero(self, mock_discover, mock_samples):
        """cmd_list should always return 0."""
        mock_discover.return_value = mock_samples
        args = argparse.Namespace()
        result = cmd_list(args)
        assert result == 0

    @patch("src.agent_evaluation.cli.discover_samples")
    def test_cmd_list_empty(self, mock_discover):
        """cmd_list with no samples should still return 0."""
        mock_discover.return_value = []
        args = argparse.Namespace()
        result = cmd_list(args)
        assert result == 0


# ---------------------------------------------------------------------------
# cmd_run
# ---------------------------------------------------------------------------

class TestCmdRun:
    @patch("src.agent_evaluation.cli.run_sample", return_value=0)
    @patch("src.agent_evaluation.cli.discover_samples")
    def test_run_by_exact_name(self, mock_discover, mock_run, mock_samples):
        """Running by exact name should find and run the sample."""
        mock_discover.return_value = mock_samples
        args = argparse.Namespace(name="agentic_evaluation", sample=0, index_fname=None)
        result = cmd_run(args)
        assert result == 0
        mock_run.assert_called_once()

    @patch("src.agent_evaluation.cli.run_sample", return_value=0)
    @patch("src.agent_evaluation.cli.discover_samples")
    def test_run_by_partial_name(self, mock_discover, mock_run, mock_samples):
        """Running by partial name should match the sample."""
        mock_discover.return_value = mock_samples
        args = argparse.Namespace(name="agentic", sample=0, index_fname=None)
        result = cmd_run(args)
        assert result == 0

    @patch("src.agent_evaluation.cli.discover_samples")
    def test_run_not_found(self, mock_discover, mock_samples):
        """Running with a non-matching name should return 1."""
        mock_discover.return_value = mock_samples
        args = argparse.Namespace(name="nonexistent", sample=0, index_fname=None)
        result = cmd_run(args)
        assert result == 1

    @patch("src.agent_evaluation.cli.discover_samples")
    def test_run_no_samples(self, mock_discover):
        """Running with no samples available returns 1."""
        mock_discover.return_value = []
        args = argparse.Namespace(name="anything", sample=0, index_fname=None)
        result = cmd_run(args)
        assert result == 1

    @patch("src.agent_evaluation.cli.run_sample", return_value=0)
    @patch("src.agent_evaluation.cli.discover_samples")
    def test_run_by_number(self, mock_discover, mock_run, mock_samples):
        """Running by number index should work."""
        mock_discover.return_value = mock_samples
        args = argparse.Namespace(name="1", sample=0, index_fname=None)
        result = cmd_run(args)
        assert result == 0

    @patch("src.agent_evaluation.cli.discover_samples")
    def test_run_ambiguous_name(self, mock_discover, mock_samples):
        """Ambiguous partial name should return 1."""
        mock_discover.return_value = mock_samples
        args = argparse.Namespace(name="evaluation", sample=0, index_fname=None)
        result = cmd_run(args)
        assert result == 1


# ---------------------------------------------------------------------------
# cmd_run_all
# ---------------------------------------------------------------------------

class TestCmdRunAll:
    @patch("src.agent_evaluation.cli.run_sample", return_value=0)
    @patch("src.agent_evaluation.cli.discover_samples")
    def test_all_pass(self, mock_discover, mock_run, mock_samples):
        """All samples passing should return 0."""
        mock_discover.return_value = mock_samples
        args = argparse.Namespace()
        result = cmd_run_all(args)
        assert result == 0
        assert mock_run.call_count == len(mock_samples)

    @patch("src.agent_evaluation.cli.run_sample", return_value=1)
    @patch("src.agent_evaluation.cli.discover_samples")
    def test_any_failure_returns_one(self, mock_discover, mock_run, mock_samples):
        """Any sample failing should return 1."""
        mock_discover.return_value = mock_samples
        args = argparse.Namespace()
        result = cmd_run_all(args)
        assert result == 1

    @patch("src.agent_evaluation.cli.discover_samples")
    def test_no_samples(self, mock_discover):
        """No samples available should return 1."""
        mock_discover.return_value = []
        args = argparse.Namespace()
        result = cmd_run_all(args)
        assert result == 1


# ---------------------------------------------------------------------------
# cmd_info
# ---------------------------------------------------------------------------

class TestCmdInfo:
    @patch("src.agent_evaluation.cli.discover_samples")
    def test_info_not_found(self, mock_discover, mock_samples):
        """Non-existent sample should return 1."""
        mock_discover.return_value = mock_samples
        args = argparse.Namespace(name="nonexistent")
        result = cmd_info(args)
        assert result == 1

    @patch("builtins.open", mock_open(read_data=yaml.dump(SAMPLE_YAML_CONTENT)))
    @patch("src.agent_evaluation.cli.discover_samples")
    def test_info_found(self, mock_discover, mock_samples):
        """Found sample should return 0."""
        mock_discover.return_value = mock_samples
        args = argparse.Namespace(name="agentic_evaluation")
        result = cmd_info(args)
        assert result == 0


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

class TestMain:
    @patch("src.agent_evaluation.cli.discover_samples", return_value=[])
    def test_main_no_command_no_samples(self, mock_discover):
        """No command and no samples should exit with 1."""
        with patch("sys.argv", ["agent_evals"]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1

    @patch("src.agent_evaluation.cli.cmd_list", return_value=0)
    def test_main_list_command(self, mock_cmd):
        """'list' command should dispatch to cmd_list."""
        with patch("sys.argv", ["agent_evals", "list"]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 0
        mock_cmd.assert_called_once()
