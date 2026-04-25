"""
Utility functions for file operations (JSONL read/write)
"""
import json
import os
import re


def load_queries_from_jsonl(file_path: str) -> list:
    """Load queries from JSONL file"""
    queries = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                data = json.loads(line)
                queries.append(data)
    return queries


def save_to_jsonl(file_path: str, data: list):
    """Save data to JSONL file"""
    with open(file_path, 'w', encoding='utf-8') as f:
        for item in data:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')


def append_to_jsonl(file_path: str, data: dict):
    """Append a single record to JSONL file"""
    with open(file_path, 'a', encoding='utf-8') as f:
        f.write(json.dumps(data, ensure_ascii=False) + '\n')


def get_next_run_id(output_dir: str) -> int:
    """Return the next sequential run_id based on existing files in the output directory."""
    max_id = 0
    if os.path.isdir(output_dir):
        for filename in os.listdir(output_dir):
            match = re.match(r'^(\d+)_.*\.json$', filename)
            if match:
                max_id = max(max_id, int(match.group(1)))
    return max_id + 1
