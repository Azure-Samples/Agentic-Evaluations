"""Unit tests for utility modules (file_operations, constants, trace_to_jsonl)."""

import json

from src.evaluations.offline.utils.constants import EVAL_NAME
from src.evaluations.offline.utils.file_operations import (
    append_to_jsonl, get_next_run_id, load_queries_from_jsonl, save_to_jsonl)

# ---------------------------------------------------------------------------
# constants
# ---------------------------------------------------------------------------

class TestConstants:
    def test_eval_name_value(self):
        """EVAL_NAME should be 'experiment_name'."""
        assert EVAL_NAME == "experiment_name"


# ---------------------------------------------------------------------------
# load_queries_from_jsonl
# ---------------------------------------------------------------------------

class TestLoadQueriesFromJsonl:
    def test_loads_valid_jsonl(self, tmp_path):
        """Should load all lines from valid JSONL file."""
        data = [{"query": "q1"}, {"query": "q2"}, {"query": "q3"}]
        f = tmp_path / "test.jsonl"
        f.write_text("\n".join(json.dumps(d) for d in data))

        result = load_queries_from_jsonl(str(f))
        assert result == data

    def test_skips_blank_lines(self, tmp_path):
        """Blank lines should be skipped."""
        f = tmp_path / "test.jsonl"
        f.write_text('{"a":1}\n\n{"b":2}\n\n')

        result = load_queries_from_jsonl(str(f))
        assert len(result) == 2

    def test_empty_file(self, tmp_path):
        """Empty file should return empty list."""
        f = tmp_path / "empty.jsonl"
        f.write_text("")

        result = load_queries_from_jsonl(str(f))
        assert result == []

    def test_preserves_unicode(self, tmp_path):
        """Unicode content should be preserved."""
        data = [{"query": "Hello world"}]
        f = tmp_path / "unicode.jsonl"
        f.write_text(json.dumps(data[0], ensure_ascii=True) + "\n")

        result = load_queries_from_jsonl(str(f))
        assert result[0]["query"] == "Hello world"


# ---------------------------------------------------------------------------
# save_to_jsonl
# ---------------------------------------------------------------------------

class TestSaveToJsonl:
    def test_saves_data(self, tmp_path):
        """Should save list of dicts to JSONL."""
        data = [{"a": 1}, {"b": 2}]
        f = tmp_path / "out.jsonl"

        save_to_jsonl(str(f), data)

        lines = f.read_text().strip().split("\n")
        assert len(lines) == 2
        assert json.loads(lines[0]) == {"a": 1}
        assert json.loads(lines[1]) == {"b": 2}

    def test_empty_list(self, tmp_path):
        """Empty list should create empty file."""
        f = tmp_path / "empty.jsonl"
        save_to_jsonl(str(f), [])
        assert f.read_text() == ""

    def test_overwrites_existing(self, tmp_path):
        """Should overwrite existing file."""
        f = tmp_path / "overwrite.jsonl"
        f.write_text("old content")

        save_to_jsonl(str(f), [{"new": True}])
        lines = f.read_text().strip().split("\n")
        assert json.loads(lines[0]) == {"new": True}


# ---------------------------------------------------------------------------
# append_to_jsonl
# ---------------------------------------------------------------------------

class TestAppendToJsonl:
    def test_appends_single_record(self, tmp_path):
        """Should append one record to file."""
        f = tmp_path / "append.jsonl"
        f.write_text('{"a":1}\n')

        append_to_jsonl(str(f), {"b": 2})

        lines = f.read_text().strip().split("\n")
        assert len(lines) == 2
        assert json.loads(lines[1]) == {"b": 2}

    def test_creates_file_if_missing(self, tmp_path):
        """Should create file if it doesn't exist."""
        f = tmp_path / "new.jsonl"
        append_to_jsonl(str(f), {"first": True})

        assert f.exists()
        assert json.loads(f.read_text().strip()) == {"first": True}


# ---------------------------------------------------------------------------
# get_next_run_id
# ---------------------------------------------------------------------------

class TestGetNextRunId:
    def test_empty_directory(self, tmp_path):
        """Empty dir should return 1."""
        assert get_next_run_id(str(tmp_path)) == 1

    def test_nonexistent_directory(self, tmp_path):
        """Non-existent dir should return 1."""
        assert get_next_run_id(str(tmp_path / "nonexistent")) == 1

    def test_sequential_numbering(self, tmp_path):
        """Should return one more than the highest existing number."""
        (tmp_path / "1_eval_result.json").write_text("{}")
        (tmp_path / "2_eval_result.json").write_text("{}")
        (tmp_path / "3_eval_result.json").write_text("{}")

        assert get_next_run_id(str(tmp_path)) == 4

    def test_ignores_non_matching_files(self, tmp_path):
        """Files not matching the pattern should be ignored."""
        (tmp_path / "2_eval_result.json").write_text("{}")
        (tmp_path / "readme.md").write_text("# Hi")
        (tmp_path / "config.yaml").write_text("")

        assert get_next_run_id(str(tmp_path)) == 3

    def test_handles_gaps(self, tmp_path):
        """Should use the max, not count."""
        (tmp_path / "1_a.json").write_text("{}")
        (tmp_path / "5_b.json").write_text("{}")

        assert get_next_run_id(str(tmp_path)) == 6
