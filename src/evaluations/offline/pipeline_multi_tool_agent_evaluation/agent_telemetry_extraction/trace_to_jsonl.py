
"""
Trace enrichment for multi-tool agent evaluation pipeline.

Delegates to the shared trace_to_jsonl module in utils/.
"""
from src.evaluations.offline.utils.trace_to_jsonl import get_trace_main  # noqa: F401

if __name__ == "__main__":
    import yaml
    from pathlib import Path

    script_dir = Path(__file__).parent
    config_path = script_dir.parent / "experiment.yaml"

    if config_path.exists():
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        enrich_config = config.get('enrich', {})

        if not enrich_config:
            exp_config = config.get('experiment', {})
            enrich_config = {
                'input_path': exp_config.get('output_path', 'src/evaluations/offline/pipeline_multi_tool_agent_evaluation/datasets/'),
                'input_file': exp_config.get('output_file', 'agent_responses.jsonl'),
                'output_path': exp_config.get('output_path', 'src/evaluations/offline/pipeline_multi_tool_agent_evaluation/datasets/'),
                'output_file': 'agent_responses_enriched.jsonl'
            }
    else:
        enrich_config = {
            'input_path': 'src/evaluations/offline/pipeline_multi_tool_agent_evaluation/datasets/',
            'input_file': 'agent_responses.jsonl',
            'output_path': 'src/evaluations/offline/pipeline_multi_tool_agent_evaluation/datasets/',
            'output_file': 'agent_responses_enriched.jsonl'
        }

    get_trace_main(enrich_config)
