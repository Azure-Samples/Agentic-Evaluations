# Custom Agentic Evaluation

## Overview

This evaluation framework is designed to assess **agentic systems** - AI agents that can invoke tools, make decisions, and interact with multiple services to complete tasks. Unlike traditional LLM evaluations that focus on text quality, agentic evaluations measure whether agents correctly select and invoke the right tools/plugins for a given user query.

**What makes agentic systems unique?**
- Agents are AI models with memory that communicate via messages
- They can interact with tools, functions, and other agents
- They form chat histories/threads/trajectories through multi-turn conversations
- Systems can range from single agents with tool calling to complex multi-agent architectures

This framework provides a comprehensive evaluation pipeline for agentic systems using Azure AI Foundry, with support for both built-in evaluators and custom metrics specific to agent behavior.

## Evaluation Metrics

### Built-in Metrics (Azure AI Foundry SDK)

- **Relevance**: Measures how well the agent's response addresses the user's query
  - Score range: 1-5
  - Evaluates if the response is pertinent and directly related to the question

### Custom Agentic Metrics

- **Agent Invocation Accuracy**: Measures if the agent invoked the exact set of expected tools/plugins
  - Binary score: 1.0 (correct) or 0.0 (incorrect)
  - Validates end-to-end agent decision-making

- **Recall@K**: Measures how many of the expected agents appear in the top-K predicted agents
  - Recall@1: Did the agent get the top choice correct?
  - Recall@2: Are the expected agents in the top 2 predictions?
  - Recall@3: Are the expected agents in the top 3 predictions?
  - Score range: 0.0 - 1.0

- **Agent Invocation Counts**: Diagnostic metrics
  - `num_expected`: Number of agents that should have been invoked
  - `num_predicted`: Number of agents actually invoked
  - Helps identify over-invocation or under-invocation patterns

## Dataset Format

Your evaluation dataset should be in JSONL format with the following fields:

```json
{
  "conversation_id": "unique_id",
  "user_query": "What's the weather in Seattle?",
  "gt_agent_response": "The current weather in Seattle is...",
  "expected_agents_to_invoke": ["weather_plugin", "location_service"],
  "selected_agents": ["weather_plugin", "location_service"]
}
```

## How to Add Custom Metrics

### Step 1: Create Your Custom Evaluator

Create a new evaluator file in `evaluator/evaluator_repo/`:

```python
# evaluator/evaluator_repo/your_custom_evaluator.py

class YourCustomEvaluator:
    def __init__(self):
        """Initialize your evaluator with any required setup."""
        pass

    def __call__(self, expected_field, predicted_field, **kwargs):
        """
        Implement your evaluation logic.
        
        Args:
            expected_field: Ground truth value from your dataset
            predicted_field: Model prediction from your dataset
            **kwargs: Additional fields from your dataset
            
        Returns:
            dict: Dictionary of metric names and their scores
        """
        # Your evaluation logic here
        score = self.compute_your_metric(expected_field, predicted_field)
        
        return {
            "your_metric_name": score,
            "additional_metric": another_score
        }
```

### Step 2: Register the Evaluator in `eval_factory.py`

```python
from .evaluator.evaluator_repo.your_custom_evaluator import YourCustomEvaluator

class EvaluatorFactory:
    EVALUATOR_FACTORIES = {
        "relevance_evaluator": RelevanceEvaluator,
        "custom_agents_invoked_evaluator": EvaluateAgentsInvoked,
        "your_custom_evaluator": YourCustomEvaluator,  # Add your evaluator here
    }
```

### Step 3: Configure in `experiment.yaml`

Add your evaluator to the configuration:

```yaml
evaluation:
  evaluators:
    relevance_score: "relevance_evaluator"
    agents_invoked_eval: "custom_agents_invoked_evaluator"
    your_metric: "your_custom_evaluator"  # Add your evaluator
  
  evaluator_config:
    your_metric:
      column_mapping:
        expected_field: "${data.ground_truth_column}"
        predicted_field: "${data.prediction_column}"
```

## How to Run

### Prerequisites

1. Azure AI Foundry project configured
2. Environment variables set (see main README)
3. Dataset prepared in JSONL format

### Run the Evaluation

From the repository root:

```bash
python -m src.agent_evaluation.agentic_ops.runner --config_file src/evaluations/offline/agentic_evaluation_custom/experiment.yaml
```

### Configuration Options

Edit `experiment.yaml` to customize:

```yaml
evaluation:
  run_local: False                    # Set to True for local-only evaluation
  input_path: src/evaluations/offline/agentic_evaluation_custom/datasets/
  input_file: agent_response_sample_data.jsonl
  output_path: src/evaluations/offline/agentic_evaluation_custom/report/
  
  # Map your dataset columns to evaluator parameters
  column_mapping:
    user_id: "${data.conversation_id}"
  
  # Configure which evaluators to run
  evaluators:
    relevance_score: "relevance_evaluator"
    agents_invoked_eval: "custom_agents_invoked_evaluator"
  
  # Map dataset columns to evaluator inputs
  evaluator_config:
    relevance_score:
      column_mapping:
        query: "${data.user_query}"
        response: "${data.gt_agent_response}"
    agents_invoked_eval:
      column_mapping:
        expected_agents_to_invoke: "${data.expected_agents_to_invoke}"
        predicted_agents_to_invoke: "${data.selected_agents}"
```

## Output

Results are saved to the configured output path:
- **JSON Report**: `{output_path}/{experiment_name}.json`
- **Azure AI Foundry**: Results automatically uploaded for dashboard visualization

The report includes:
- Per-sample evaluation scores
- Aggregate metrics across the dataset
- Detailed agent invocation analysis
- Recall metrics at different K values

## Example Use Cases

1. **Tool Selection Validation**: Verify your agent selects the correct tools/plugins for different query types
2. **Multi-Agent Coordination**: Evaluate if the right agents are invoked in multi-agent systems
3. **Agent Experimentation**: Compare different agent architectures or prompt strategies
4. **Single Turn Evaluation**: Assess agent performance on isolated, one-off user queries to ensure correct tool invocation and response quality in simple scenarios.
5. **Multi-Turn Conversation Evaluation**: Evaluate agent behavior across multi-step dialogues, measuring consistency, memory usage, and correct tool selection throughout the conversation history.
6. **Multi-Agent Conversation Evaluation**: Analyze scenarios involving multiple agents collaborating or interacting, focusing on coordination, correct delegation, and appropriate tool/plugin usage by each agent.
7. 
8. **Regression Testing**: Ensure agent behavior remains consistent across updates 
