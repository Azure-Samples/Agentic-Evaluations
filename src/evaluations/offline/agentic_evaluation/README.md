# Agentic Systems Evaluation

## Overview

This evaluation framework assesses **agentic systems** - AI agents that invoke tools, make decisions, and coordinate with other agents to complete tasks. Unlike traditional LLM evaluations focused on text quality, agentic evaluations measure whether agents correctly select and invoke the right tools/agents for a given user query.

**What makes agentic systems unique?**
- Agents are AI models with memory that communicate via messages
- They can interact with tools, functions, and other agents
- They form chat histories/threads/trajectories through multi-turn conversations
- Systems range from single agents with tool calling to complex multi-agent architectures

This evaluation measures both **agent behavior** (tool/agent selection accuracy) and **response quality** (relevance, task adherence) using Azure AI Foundry.

## What's Included

**Sample Dataset:** `datasets/agent_response_sample_data.jsonl`
- 10 sample agent responses from a home automation system
- Fields: `query`, `expected_agents_to_invoke`, `selected_agents`, `response`, `tool_calls`
- Agents: ACAgent (air conditioner), TVAgent, LightAgent, MusicAgent, SpeakerAgent

**Pre-configured Evaluators:**
- **Custom Agentic Metrics**: Invocation Accuracy, Recall@K, Agent Hallucination
- **Azure AI Foundry Metrics**: Relevance, Task Adherence

**Ready to Run:** Execute immediately with sample data or swap in your own dataset.

## Evaluation Metrics

### Custom Agentic Metrics

| Metric | Formula | Output | What It Measures |
|--------|---------|--------|------------------|
| **Agent Invocation Accuracy** | `set(expected) == set(predicted)` | True/False | Exact match - did system invoke exactly the right agents? |
| **Recall@K** | `len(set(expected) ∩ set(predicted[:k])) / len(expected)` | 0.0-1.0 | Are expected agents in top-K selections? (K=1,2,3) |
| **Agent Hallucination** | `len(predicted) > len(expected)` | "yes"/"no" | Did system call extra agents? (over-invocation detection) |
| **Agent Counts** | `len(expected)`, `len(predicted)` | Integer | Diagnostic: number of expected vs. predicted agents |

**Interpretation:**
```python
Example Result:
{
  "agents_invoke_accuracy": True,    # Perfect match
  "recall@1": 1.0,                   # All expected agents in top 1
  "recall@2": 1.0,                   # All expected agents in top 2
  "recall@3": 1.0,                   # All expected agents in top 3
  "num_expected": 2,                 # Expected 2 agents
  "num_predicted": 2                 # Invoked 2 agents
}
```

### Built-in Metrics (Azure AI Foundry SDK)

| Evaluator | Required Fields | Score Range | What It Measures |
|-----------|----------------|-------------|------------------|
| **RelevanceEvaluator** | `query`, `response` | 1-5 | Does response answer the query? |
| **TaskAdherenceEvaluator** | `query`, `response` | 1-5 | Does response follow instructions? |

## Dataset Format

Your evaluation dataset should be in JSONL format (one JSON object per line) with these fields:

**Required Fields:**
```jsonl
{"conversation_id": "001", "query": "Set AC to 24 degrees", "expected_agents_to_invoke": ["ACAgent"], "selected_agents": ["ACAgent"], "response": "Temperature set to 24 degrees."}
```

**Field Descriptions:**
- `query` or `user_query`: User's input that triggers agent selection
- `expected_agents_to_invoke`: Ground truth list of agents that should be invoked (array of strings)
- `selected_agents`: Actual agents selected/invoked by your system (array of strings)
- `response` (optional): Agent's text response - required for Relevance/Task Adherence evaluators

**Optional Fields:**
- `conversation_id`: Unique identifier for the interaction
- `context`: Additional context
- `tool_calls`: Array of tool call objects (for detailed tool analysis)
- `tool_definitions`: Array of available tools

**Important:**
- Agent names must match exactly (case-sensitive): `ACAgent` ≠ `acagent`
- Use arrays even for single agents: `["ACAgent"]` not `"ACAgent"`
- Ground truth (`expected_agents_to_invoke`) should reflect correct behavior, not actual system output

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

## Quick Start

### Prerequisites

1. **Azure Setup**: AI Foundry project with GPT-4o deployment
2. **Environment**: `.env` file configured (see main README)
3. **Installation**: Dependencies installed (`uv sync`)

### Run with Sample Data

**Run Directly:**
```bash
# Activate virtual environment
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/macOS

# Run evaluation with sample data
python -m src.agent_evaluation.agentic_ops.runner --config_file src/evaluations/offline/agentic_evaluation/experiment.yaml
```

### Run with Your Data

1. **Prepare your dataset**: Create `datasets/my_agent_data.jsonl` with required fields
2. **Update experiment.yaml**:
   ```yaml
   evaluation:
     input_file: my_agent_data.jsonl
   ```
3. **Run evaluation** (same command as above)

## Configuration

### experiment.yaml Structure

```yaml
app_name: Agentic-Evals
version: 1.0.0
experiment_name: Agentic_Evaluation_Experiment

evaluation:
  run_local: True  # Set False to push to Azure AI Foundry dashboard
  input_path: src/evaluations/offline/agentic_evaluation/datasets/
  input_file: agent_response_sample_data.jsonl
  output_path: src/evaluations/offline/reports/
  
  column_mapping:
    user_id: "${data.conversation_id}"
  
  evaluators:
    relevance_score: "relevance_evaluator"
    agents_invoked_eval: "custom_agents_invoked_evaluator"
    task_adherence_score: "task_adherence_evaluator"
  
  evaluator_config:
    relevance_score:
      column_mapping:
        query: "${data.query}"
        response: "${data.gt_agent_response}"
    
    agents_invoked_eval:
      column_mapping:
        expected_agents_to_invoke: "${data.expected_agents_to_invoke}"
        predicted_agents_to_invoke: "${data.selected_agents}"
    
    task_adherence_score:
      column_mapping:
        query: "${data.query}"
        response: "${data.response}"

pipeline:
  - base_path: evaluator
    module: eval_main.eval_main
    config_key: evaluation
```

### Selecting Evaluators

**Agent Metrics Only:**
```yaml
evaluators:
  agents_invoked_eval: "custom_agents_invoked_evaluator"
```

**Agent Metrics + Response Quality:**
```yaml
evaluators:
  agents_invoked_eval: "custom_agents_invoked_evaluator"
  relevance_score: "relevance_evaluator"
  task_adherence_score: "task_adherence_evaluator"
```

## Results

### Output Location

- **Local mode** (`run_local: True`): `src/evaluations/offline/reports/{run_id}_{eval_dir_name}.json`
- **Azure mode** (`run_local: False`): Results pushed to AI Foundry dashboard + local JSON

### Result Structure

```json
{
  "metrics": {
    "agents_invoke_accuracy": 0.80,
    "recall@1": 0.85,
    "recall@2": 0.90,
    "recall@3": 0.95,
    "relevance_score": 4.2,
    "task_adherence_score": 4.5
  },
  "rows": [
    {
      "conversation_id": "001",
      "query": "Set AC to 24 degrees",
      "outputs": {
        "agents_invoke_accuracy": true,
        "recall@1": 1.0,
        "recall@2": 1.0,
        "recall@3": 1.0,
        "relevance_score": 5,
        "task_adherence_score": 5
      }
    }
  ],
  "studio_url": "https://ai.azure.com/..."  // If run_local: False
}
```

### Interpretation

| Metric | Good | Needs Improvement |
|--------|------|-------------------|
| Invocation Accuracy | ≥ 0.80 | < 0.80 |
| Recall@K | ≥ 0.85 | < 0.85 |
| Relevance/Task Adherence | ≥ 4.0 | < 4.0 |

**Common Patterns:**
- **Low Invocation Accuracy + High Recall@K**: Agent routing close but not exact (consider relaxing exact match requirement)
- **Low Recall@1, High Recall@3**: Agent selection logic needs refinement (correct agents but wrong priority)
- **High Agent Counts**: Over-invocation issue (calling too many agents)

From the repository root:

```bash
python -m src.agent_evaluation.agentic_ops.runner --config_file src/evaluations/offline/agentic_evaluation_custom/experiment.yaml
```

## Output

Results are saved to the configured output path:
- **JSON Report**: `{output_path}/{run_id}_{eval_dir_name}.json`
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
7. **Regression Testing**: Ensure agent behavior remains consistent across updates

## Data Provenance

All sample datasets included in this repository are **fully synthetic**. They use fictional entities (Northwind Health, Contoso) and simulated agent interactions (smart-home device controls, weather lookups). No real customer data, personally identifiable information, or production telemetry is included in any dataset.
