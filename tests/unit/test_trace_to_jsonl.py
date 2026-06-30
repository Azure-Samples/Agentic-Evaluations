"""Unit tests for trace_to_jsonl shared module."""

import json

from src.evaluations.offline.utils.trace_to_jsonl import (
    extract_tool_call_from_span, extract_tool_definitions,
    merge_tool_definitions)

# ---------------------------------------------------------------------------
# extract_tool_definitions
# ---------------------------------------------------------------------------

class TestExtractToolDefinitions:
    def test_extracts_function_tools(self):
        """Should extract function-type tool definitions."""
        tool_defs = [
            {
                "type": "function",
                "function": {
                    "name": "get_weather",
                    "description": "Get weather data",
                    "parameters": {"type": "object"},
                },
            }
        ]
        custom_dims = {"gen_ai.tool.definitions": json.dumps(tool_defs)}

        result = extract_tool_definitions(custom_dims)
        assert len(result) == 1
        assert result[0]["name"] == "get_weather"
        assert result[0]["description"] == "Get weather data"

    def test_empty_string(self):
        """Empty tool definitions string should return empty list."""
        result = extract_tool_definitions({"gen_ai.tool.definitions": ""})
        assert result == []

    def test_missing_key(self):
        """Missing key should return empty list."""
        result = extract_tool_definitions({})
        assert result == []

    def test_invalid_json(self):
        """Invalid JSON should return empty list."""
        result = extract_tool_definitions({"gen_ai.tool.definitions": "not json"})
        assert result == []

    def test_non_list_json(self):
        """Non-list JSON should return empty list."""
        result = extract_tool_definitions({"gen_ai.tool.definitions": '{"key": "value"}'})
        assert result == []

    def test_skips_non_function_type(self):
        """Non-function type tools should be skipped."""
        tool_defs = [{"type": "retrieval", "name": "search"}]
        custom_dims = {"gen_ai.tool.definitions": json.dumps(tool_defs)}

        result = extract_tool_definitions(custom_dims)
        assert result == []

    def test_multiple_tools(self):
        """Multiple function tools should all be extracted."""
        tool_defs = [
            {"type": "function", "function": {"name": "tool_a", "description": "A", "parameters": {}}},
            {"type": "function", "function": {"name": "tool_b", "description": "B", "parameters": {}}},
        ]
        custom_dims = {"gen_ai.tool.definitions": json.dumps(tool_defs)}

        result = extract_tool_definitions(custom_dims)
        assert len(result) == 2
        assert result[0]["name"] == "tool_a"
        assert result[1]["name"] == "tool_b"


# ---------------------------------------------------------------------------
# merge_tool_definitions
# ---------------------------------------------------------------------------

class TestMergeToolDefinitions:
    def test_merge_new_tools(self):
        """New tools should be added."""
        existing = [{"name": "tool_a", "id": "tool_a"}]
        new = [{"name": "tool_b", "id": "tool_b"}]

        result = merge_tool_definitions(existing, new)
        names = {t["name"] for t in result}
        assert names == {"tool_a", "tool_b"}

    def test_deduplicates_by_name(self):
        """Duplicate names should not be added."""
        existing = [{"name": "tool_a", "id": "1", "description": "first"}]
        new = [{"name": "tool_a", "id": "2", "description": "second"}]

        result = merge_tool_definitions(existing, new)
        assert len(result) == 1
        assert result[0]["description"] == "first"  # Keeps existing

    def test_empty_new(self):
        """Empty new list should return existing unchanged."""
        existing = [{"name": "tool_a"}]
        result = merge_tool_definitions(existing, [])
        assert result == existing

    def test_empty_existing(self):
        """Empty existing should return new tools."""
        new = [{"name": "tool_a"}, {"name": "tool_b"}]
        result = merge_tool_definitions([], new)
        assert len(result) == 2

    def test_both_empty(self):
        """Both empty should return empty list."""
        result = merge_tool_definitions([], [])
        assert result == []


# ---------------------------------------------------------------------------
# extract_tool_call_from_span
# ---------------------------------------------------------------------------

class TestExtractToolCallFromSpan:
    def test_extracts_from_operation_name(self):
        """Should extract tool name from 'execute_tool <name>' format."""
        result = extract_tool_call_from_span({}, "execute_tool get_weather")
        assert result["type"] == "tool_call"
        assert result["name"] == "get_weather"

    def test_falls_back_to_custom_dims(self):
        """Should fall back to gen_ai.tool.name from custom dims."""
        custom_dims = {"gen_ai.tool.name": "search_tool"}
        result = extract_tool_call_from_span(custom_dims, "some_other_operation")
        assert result["type"] == "tool_call"
        assert result["name"] == "search_tool"

    def test_empty_name(self):
        """Should handle missing tool name gracefully."""
        result = extract_tool_call_from_span({}, "other_span")
        assert result["type"] == "tool_call"
        assert result["name"] == ""
