# Agent Evaluation using Azure AI Foundry Built-in Evaluators

## Overview

This evaluation framework demonstrates how to use **Azure AI Foundry's built-in evaluators** to assess AI Agents, GenAI systems, and RAG (Retrieval-Augmented Generation) applications. Built-in evaluators are production-ready, pre-configured metrics provided by Azure AI Foundry SDK that require no custom code or prompty templates.

**Why use built-in evaluators?**
- **Zero Configuration**: Ready to use out-of-the-box with standard parameters
- **Production-Ready**: Tested and optimized by Azure AI team
- **Consistent Results**: Standardized scoring across different projects
- **Quick Start**: Evaluate your AI Agent or GenAI system in minutes without custom implementation
- **Azure Integration**: Seamless integration with Azure AI Foundry dashboard and tracking
- **Agent-Specific Metrics**: Includes experimental evaluators for agent tool calling and task adherence

This folder provides a comprehensive example for evaluating AI agents using both standard GenAI metrics and specialized agent-specific evaluators.

## Evaluation Metrics

### Current Configuration

This example is configured with both standard GenAI and specialized agent-specific evaluators:

#### Standard GenAI Metrics

- **Relevance**: Measures how well the response addresses the query
  - Score range: 1-5
  - Evaluates directness and pertinence to the question
  - Assesses if the response directly answers what was asked
  - Use case: Ensuring responses are on-topic and address user intent
  - **Required parameters**: `query`, `response`

#### Agent-Specific Metrics (Experimental)

- **Task Adherence**: Evaluates whether the agent follows task instructions and constraints
  - Score range: 1-5
  - Assesses instruction following and constraint adherence
  - Checks if the agent completes the task as specified
  - Use case: Validating agent behavior against task definitions
  - **Required parameters**: `query`, `response`
  - **Optional parameters**: `tool_definitions`

- **Tool Call Accuracy**: Measures correctness of tool invocations
  - Score range: 1-5
  - Evaluates if the right tools are called with correct parameters
  - Assesses tool selection logic and parameter accuracy
  - Use case: Ensuring agents use tools appropriately
  - **Required parameters**: `query`, `tool_calls`, `tool_definitions`

- **Intent Resolution**: Assesses how well the agent resolves user intent
  - Score range: 1-5
  - Evaluates understanding and completion of user goals
  - Measures end-to-end intent satisfaction
  - Use case: Validating agent successfully addresses user needs
  - **Required parameters**: `query`, `response`, `tool_definitions`

> **Note**: Agent-specific evaluators (TaskAdherence, ToolCallAccuracy, IntentResolution) are experimental features in the Azure AI Evaluation SDK and may be subject to changes.

### Additional Built-in Evaluators Available

You can easily add more built-in evaluators from Azure AI Foundry if needed:

**Additional Standard GenAI/RAG Metrics:**
- **Coherence**: Logical flow and consistency of the response
- **Groundedness**: Whether response is grounded in provided context (RAG scenarios)
- **Fluency**: Linguistic quality and readability
- **Similarity**: Semantic similarity to ground truth
- **F1 Score**: Token-level overlap with ground truth

> **Note**: This framework focuses on agent-specific evaluations. For comprehensive GenAI/RAG evaluations, see the [genai_evaluation_foundry](../genai_evaluation_foundry) folder.

See the [Azure AI Foundry documentation](https://learn.microsoft.com/azure/ai-studio/how-to/evaluate-generative-ai-app) for the complete list of available evaluators.

## Dataset Format

### For Standard GenAI Evaluation

Your evaluation dataset should be in JSONL format with the following fields:

```json
{
  "query": "What is machine learning?",
  "response": "Machine learning is a subset of artificial intelligence..."
}
```

**Required fields:**
- `query`: The user's question or input
- `response`: The generated response to evaluate

**Optional fields (for other evaluators):**
- `context`: Retrieved context for groundedness evaluation
- `ground_truth`: Reference answer for similarity/F1 score evaluation

### For Agent Evaluation (with Tool Calling)

When evaluating agents that use tools, your dataset should include additional fields:

```json
{
  "query": "What's the weather in Seattle?",
  "response": "The current weather in Seattle is 65°F and partly cloudy.",
  "tool_calls": [
    {
      "name": "fetch_weather",
      "arguments": {
        "location": "Seattle"
      }
    }
  ],
  "tool_definitions": [
    {
      "name": "fetch_weather",
      "description": "Retrieves current weather information for a given location",
      "parameters": {
        "type": "object",
        "properties": {
          "location": {
            "type": "string",
            "description": "The city or location to get weather for"
          }
        },
        "required": ["location"]
      }
    }
  ]
}
```

**Required fields for agent evaluation:**
- `query`: The user's question or input
- `response`: The agent's final response
- `tool_calls`: List of tool invocations made by the agent (required for ToolCallAccuracyEvaluator)
- `tool_definitions`: Schema definitions of available tools (required for ToolCallAccuracyEvaluator and IntentResolutionEvaluator)

**Field Descriptions:**

- **tool_calls**: Array of objects, each containing:
  - `name`: Name of the tool that was called
  - `arguments`: JSON object with parameter values passed to the tool

- **tool_definitions**: Array of objects defining available tools:
  - `name`: Tool name
  - `description`: What the tool does
  - `parameters`: JSON schema defining tool parameters (type, properties, required fields)

## How to Add More Built-in Evaluators

### Step 1: Import the Evaluator

Update `eval_factory.py` to import additional built-in evaluators:

**For Standard GenAI Evaluators:**
```python
from azure.ai.evaluation import RelevanceEvaluator
```

**For Agent-Specific Evaluators:**
```python
from azure.ai.evaluation import (
    TaskAdherenceEvaluator,
    ToolCallAccuracyEvaluator,
    IntentResolutionEvaluator
)
```

**Register in Factory:**
```python
class EvaluatorFactory:
    EVALUATOR_FACTORIES = {
        # Standard GenAI Evaluator
        "relevance_evaluator": RelevanceEvaluator,
        
        # Agent-Specific Evaluators (Experimental)
        "task_adherence_evaluator": TaskAdherenceEvaluator,
        "tool_call_accuracy_evaluator": ToolCallAccuracyEvaluator,
        "intent_resolution_evaluator": IntentResolutionEvaluator,
    }
```

### Step 2: Configure in `experiment.yaml`

**Example Configuration with Agent Evaluators:**

```yaml
evaluation:
  evaluators:
    relevance_score: "relevance_evaluator"
    task_adherence_score: "task_adherence_evaluator"
    tool_call_accuracy_score: "tool_call_accuracy_evaluator"
    intent_resolution_score: "intent_resolution_evaluator"
  
  evaluator_config:
    relevance_score:
      column_mapping:
        query: "${data.query}"
        response: "${data.response}"
    
    task_adherence_score:
      column_mapping:
        query: "${data.query}"
        response: "${data.response}"
        # tool_definitions: "${data.tool_definitions}"  # Optional
    
    tool_call_accuracy_score:
      column_mapping:
        query: "${data.query}"
        tool_calls: "${data.tool_calls}"           # Required
        tool_definitions: "${data.tool_definitions}"  # Required
    
    intent_resolution_score:
      column_mapping:
        query: "${data.query}"
        response: "${data.response}"
        tool_definitions: "${data.tool_definitions}"  # Required
```

**Critical Parameter Requirements:**

| Evaluator | Required Parameters | Optional Parameters |
|-----------|-------------------|-------------------|
| RelevanceEvaluator | `query`, `response` | - |
| TaskAdherenceEvaluator | `query`, `response` | `tool_definitions` |
| ToolCallAccuracyEvaluator | `query`, `tool_calls`, `tool_definitions` | - |
| IntentResolutionEvaluator | `query`, `response`, `tool_definitions` | - |

## How to Run

### Prerequisites

1. Azure AI Foundry project configured
2. Azure OpenAI deployment (GPT-4 recommended)
3. Environment variables set (see main README)
4. Dataset prepared in JSONL format

### Run the Evaluation

From the repository root:

**For Agent Evaluation (with tool calling):**
```bash
python -m src.agent_evaluation.agentic_ops.runner --config_file src/evaluations/offline/agent_evaluation_foundry/experiment.yaml
```

**For Standard GenAI Evaluation:**
```bash
# Use a dataset without tool_calls/tool_definitions fields
python -m src.agent_evaluation.agentic_ops.runner --config_file src/evaluations/offline/agent_evaluation_foundry/experiment.yaml
```

### Local vs Azure Execution

**Local Execution** (`run_local: True`):
- Faster iteration during development
- Multi-threaded execution on your machine
- Results saved locally as JSON
- Use for quick testing and debugging

**Azure AI Foundry Execution** (`run_local: False`):
- Results pushed to Azure AI Foundry dashboard
- Centralized tracking and visualization
- Team collaboration features
- Use for production evaluations and tracking

## Output

Results are saved to the configured output path:
- **JSON Report**: `{output_path}/{experiment_name}.json`
- **Azure AI Foundry Dashboard**: Automatic upload when `run_local: False` for visualization and tracking

### Report Contents

The JSON report includes:

**Per-Sample Results:**
```json
{
  "outputs.relevance_score.gpt_relevance": 5,
  "outputs.task_adherence_score.gpt_task_adherence": 5,
  "outputs.tool_call_accuracy_score.gpt_tool_call_accuracy": 5,
  "outputs.intent_resolution_score.gpt_intent_resolution": 5
}
```

**Aggregate Metrics:**
- Mean, median, standard deviation for each evaluator
- Score distributions across all samples
- Token usage statistics (prompt tokens, completion tokens, total tokens per evaluator)
- Pass/fail counts based on configured thresholds

**Sample Report Table:**

| Metric | Score | Threshold | Status | Prompt Tokens | Completion Tokens | Total Tokens |
|--------|-------|-----------|--------|---------------|-------------------|--------------|
| Relevance | 5.00 | 3 | ✅ PASS | 1,595 | 51 | 1,645 |
| Task Adherence | 5.00 | 3 | ✅ PASS | 2,827 | 95 | 2,922 |
| Tool Call Accuracy | 5.00 | 3 | ✅ PASS | 2,143 | 315 | 2,457 |
| Intent Resolution | 5.00 | 3 | ✅ PASS | 1,901 | 50 | 1,951 |

**Metadata:**
- Evaluation run timestamp
- Configuration used (evaluators, thresholds, model)
- Studio URL for Azure AI Foundry dashboard (when run_local: False)

## When to Use Built-in vs Custom Evaluators

### Use Built-in Evaluators When:
- You need standard quality metrics (relevance, coherence, fluency)
- You're evaluating agent tool calling behavior (tool accuracy, task adherence, intent resolution)
- You want quick setup without custom code
- You're establishing baseline metrics
- You need production-tested, consistent evaluations
- You're new to GenAI or agent evaluation

### Use Custom Evaluators When:
- You need domain-specific evaluation criteria
- You have unique scoring rubrics
- You want to customize prompts and scoring logic
- You need evaluations not available in built-in set
- See `ai_judge_evaluation_custom` folder for custom evaluator examples

## Evaluation Best Practices

### For Agent Evaluation

1. **Tool Definitions Accuracy**: Ensure `tool_definitions` in your dataset match the actual tools your agent has access to
2. **Tool Call Format**: Verify `tool_calls` follows the expected schema (name, arguments)
3. **Representative Samples**: Include diverse scenarios (single tool, multiple tools, no tools, error cases)
4. **Threshold Configuration**: Set appropriate score thresholds based on your agent's complexity
5. **Iterative Testing**: Start with small samples locally before running full evaluations

### For GenAI Evaluation

1. **Context Quality**: For RAG systems, ensure retrieved context is relevant and complete
2. **Ground Truth**: Provide accurate ground truth for similarity/F1 score evaluations
3. **Query Diversity**: Test across different query types (factual, analytical, creative)
4. **Baseline Establishment**: Run evaluations before and after model changes to track improvements

## Example Use Cases

### Agent Use Cases

1. **Tool Selection Validation**: Verify agents choose correct tools for given tasks (ToolCallAccuracyEvaluator)
2. **Multi-Tool Workflows**: Assess agents handling complex tasks requiring multiple tool invocations
3. **Intent Fulfillment**: Ensure agents successfully complete user requests end-to-end (IntentResolutionEvaluator)
4. **Task Compliance**: Check agents follow instructions and constraints (TaskAdherenceEvaluator)
5. **Agent Comparison**: Compare different agent architectures using standardized metrics

### GenAI Use Cases

1. **Quick Quality Check**: Rapidly evaluate a new GenAI model with standard metrics
2. **Baseline Establishment**: Create baseline quality metrics before custom tuning
3. **RAG System Validation**: Assess basic relevance and groundedness of RAG responses
4. **Model Comparison**: Compare different models using standardized metrics
5. **CI/CD Integration**: Add quality gates in deployment pipelines with built-in evaluators

## Folder Structure

```
agent_evaluation_foundry/
├── datasets/
│   ├── __init__.py
│   ├── rag_sample.jsonl           # Sample GenAI/RAG dataset
│   └── agent_sample.jsonl         # Sample agent dataset with tool calls
├── evaluator/
│   └── eval_main.py               # Evaluation execution logic
├── report/                        # Evaluation results output
│   ├── __init__.py
│   └── Agent_Evaluation_Experiment.json  # Latest evaluation results
├── eval_factory.py               # Evaluator factory (built-in evaluators)
├── experiment.yaml               # Evaluation configuration
└── README.md                     # This file
```

## Next Steps

1. **Run the Default Configuration**: Test with the provided agent sample data
2. **Add Your Dataset**: Replace `agent_sample.jsonl` with your own agent interaction data
3. **Customize Evaluators**: Add or remove evaluators based on your evaluation needs
4. **View Results**: Check Azure AI Foundry dashboard for detailed visualizations (when run_local: False)
5. **Iterate and Improve**: Use evaluation results to improve your agent's performance
6. **Explore Custom Evaluators**: If you need custom metrics, see the `ai_judge_evaluation_custom` folder

## Resources

- [Azure AI Foundry Evaluation Documentation](https://learn.microsoft.com/azure/ai-studio/how-to/evaluate-generative-ai-app)
- [Built-in Evaluators Reference](https://learn.microsoft.com/azure/ai-studio/how-to/evaluate-generative-ai-app#built-in-evaluators)
- [Azure AI Foundry SDK](https://learn.microsoft.com/python/api/azure-ai-evaluation)
- [Agent Evaluation Samples](https://github.com/Azure-Samples/azureai-samples/tree/main/scenarios/evaluate/Supported_Evaluation_Metrics/Agent_Evaluation)
- [Azure AI Evaluation Package](https://pypi.org/project/azure-ai-evaluation/)

## Troubleshooting

### Common Issues

**Missing tool_definitions field:**
```
KeyError: 'tool_definitions'
```
- Ensure your dataset includes `tool_definitions` for agent evaluators
- Check column mappings in experiment.yaml match dataset fields

**Authentication errors:**
```
Azure authentication failed
```
- Run `az login` to authenticate
- Verify Azure OpenAI endpoint and API key in .env

**Evaluator not found:**
```
ImportError: cannot import name 'ToolCallAccuracyEvaluator'
```
- Ensure `azure-ai-evaluation>=1.0.0` is installed
- Update package: `pip install --upgrade azure-ai-evaluation`

**Low scores on agent metrics:**
- Review `tool_definitions` accuracy in your dataset
- Verify `tool_calls` format matches expected schema
- Check agent responses align with task instructions 
