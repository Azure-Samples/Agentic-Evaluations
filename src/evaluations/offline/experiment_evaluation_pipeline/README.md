# Experiment & Evaluation Pipeline for AI Agents

## Overview

This framework demonstrates a **complete end-to-end pipeline** for AI agent experimentation and evaluation. The pipeline consists of two stages:

1. **Experiment Stage (Inference)**: Execute agent interactions with a chat server and collect responses
2. **Evaluation Stage**: Assess agent performance using Azure AI Foundry's built-in evaluators

This modular pipeline architecture allows you to:
- **Separate concerns**: Keep inference logic separate from evaluation logic
- **Reuse evaluations**: Run evaluations on pre-collected responses without re-running inference
- **Flexible experimentation**: Easily swap different agent implementations or evaluation metrics
- **Track lineage**: Maintain clear traceability from queries → responses → evaluation scores

## Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        EXPERIMENT & EVALUATION PIPELINE                      │
└─────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────┐
│  Stage 1: EXPERIMENT │
│    (Inference)       │
└──────────────────────┘
         │
         │  Input: agent_utterances.jsonl
         │  ┌──────────────────────────────────┐
         │  │ query, session_id, tool_calls,   │
         │  │ tool_definitions, response_gt    │
         │  └──────────────────────────────────┘
         ↓
┌─────────────────────────────┐
│  Agent Inference Module     │
│  (experiment/               │
│   agent_inference.py)       │
│                             │
│  • Read queries from JSONL  │
│  • Send to chat server      │
│  • Collect responses        │
│  • Write to output JSONL    │
└─────────────────────────────┘
         │
         │  HTTP POST: localhost:8000/chat
         │  Payload: {message, session_id}
         ↓
┌─────────────────────────────┐
│  Chat Server (localhost)    │
│  • Process user query       │
│  • Invoke agent logic       │
│  • Call tools if needed     │
│  • Return final response    │
└─────────────────────────────┘
         │
         │  Output: agent_responses.jsonl
         │  ┌──────────────────────────────────┐
         │  │ query, session_id, response      │
         │  └──────────────────────────────────┘
         ↓
┌──────────────────────┐
│ Stage 2: EVALUATION  │
└──────────────────────┘
         │
         │  Input: agent_responses.jsonl
         ↓
┌─────────────────────────────┐
│  Evaluation Module          │
│  (evaluator/eval_main.py)   │
│                             │
│  • Load responses           │
│  • Apply evaluators:        │
│    - RelevanceEvaluator     │
│    - TaskAdherenceEvaluator │
│  • Calculate metrics        │
│  • Generate report          │
└─────────────────────────────┘
         │
         │  Output: Evaluation Report
         │  ┌──────────────────────────────────┐
         │  │ Agent_Evaluation_Experiment.json │
         │  │ • Relevance scores               │
         │  │ • Task adherence scores          │
         │  │ • Aggregate metrics              │
         │  │ • Token usage stats              │
         │  └──────────────────────────────────┘
         ↓
┌─────────────────────────────┐
│  Results & Tracking         │
│  • Local JSON report        │
│  • Azure AI Foundry         │
│    Dashboard (optional)     │
└─────────────────────────────┘
```

## Why Build Pipelines?

**Modular Design Benefits:**
- **Separation of Concerns**: Inference and evaluation are independent stages
- **Reusability**: Evaluate the same responses with different metrics without re-running inference
- **Flexibility**: Swap agent implementations without changing evaluation code


**Example Use Cases:**
1. Run inference once, try multiple evaluation configurations
2. Collect responses from production, evaluate offline
3. Compare different agent versions using the same evaluation metrics


## Pipeline Configuration

### Understanding the Two-Stage Pipeline

The pipeline is defined in `experiment.yaml` and consists of two sequential stages:

#### Stage 1: Experiment (Inference)
Executes the agent inference module to collect responses from your chat server.

#### Stage 2: Evaluation
Applies Azure AI Foundry evaluators to assess the quality of collected responses.

### Configuring `experiment.yaml`

The configuration file has three main sections:

#### 1. Experiment Section (Inference Configuration)

```yaml
experiment:
  input_path: src/evaluations/offline/experiment_evaluation_pipeline/datasets/
  input_file: agent_utterances.jsonl          # Dataset with queries
  output_path: src/evaluations/offline/experiment_evaluation_pipeline/datasets/
  output_file: agent_responses.jsonl         # Where responses are saved
  base_url: http://localhost:8000            # Chat server endpoint
```

**Parameters:**
- `input_path`: Directory containing input dataset
- `input_file`: JSONL file with queries, session_ids, tool metadata
- `output_path`: Directory where responses will be saved
- `output_file`: Output JSONL file with query + response pairs
- `base_url`: URL of your chat server (agent endpoint)

**Input Dataset Format (agent_utterances.jsonl):**
```json
{
  "query": "How is the weather in Seattle?",
  "session_id": "session-1",
  "tool_calls": [...],
  "tool_definitions": [...],
  "response_gt": "Ground truth response (optional)"
}
```

**Output Format (agent_responses.jsonl):**
```json
{
  "query": "How is the weather in Seattle?",
  "session_id": "session-1",
  "response": "The weather in Seattle is currently cloudy with a temperature of 58°F."
}
```

#### 2. Evaluation Section

```yaml
evaluation:
  run_local: False                            # True = local execution, False = Azure AI Foundry
  input_path: src/evaluations/offline/experiment_evaluation_pipeline/datasets/
  input_file: agent_responses.jsonl          # Output from experiment stage
  output_path: src/evaluations/offline/experiment_evaluation_pipeline/report/
  
  evaluators:
    relevance_score: "relevance_evaluator"
    task_adherence_score: "task_adherence_evaluator"
  
  evaluator_config:
    relevance_score:
      column_mapping:
        query: "${data.query}"
        response: "${data.response}"
    
    task_adherence_score:
      column_mapping:
        query: "${data.query}"
        response: "${data.response}"
```

**Parameters:**
- `run_local`: Execute locally (True) or push to Azure AI Foundry (False)
- `input_path`: Directory containing responses from experiment stage
- `input_file`: JSONL file with agent responses (output from Stage 1)
- `output_path`: Directory for evaluation reports
- `evaluators`: Map of score names to evaluator types
- `evaluator_config`: Column mappings for each evaluator

#### 3. Pipeline Section

```yaml
pipeline:
  - base_path: experiment                     # Folder name in the project
    module: agent_inference.inference_main    # Module.function to execute
    config_key: experiment                    # Which config section to pass
  
  - base_path: evaluator
    module: eval_main.eval_main
    config_key: evaluation
```

**Pipeline Stage Structure:**
- `base_path`: Folder containing the module (relative to experiment_evaluation_pipeline/)
- `module`: Python module and function in format `module_name.function_name`
- `config_key`: Which section of experiment.yaml to pass to the function

**Execution Flow:**
1. Runner loads `experiment.yaml`
2. For each pipeline stage:
   - Import the module from `base_path`
   - Call the function with the config from `config_key`
   - Wait for completion before proceeding to next stage
3. Final report generated in `output_path`

### Adding Experiment to the Pipeline

To add a new experiment module to the pipeline:

**Step 1: Create Experiment Module**

Create a new folder under `experiment_evaluation_pipeline/`:
```
experiment_evaluation_pipeline/
├── experiment/              # Your experiment folder
│   ├── agent_inference.py  # Contains inference_main(config, args)
│   └── experiment_utils/   # Helper modules
```

**Step 2: Implement the Main Function**

Your module must have a function with signature: `function_name(config, args=None)`

```python
# experiment/agent_inference.py
import logging
from src.evaluations.offline.utils.file_operations import load_queries_from_jsonl, append_to_jsonl
from .experiment_utils.http_client import chat_http_request

def inference_main(config, args=None):
    """
    Main inference function called by the pipeline runner
    
    Args:
        config: Dictionary with experiment configuration from experiment.yaml
        args: Optional command-line arguments
    """
    logging.info("Starting agent inference...")
    
    # Access configuration
    input_path = config["input_path"]
    input_file = config["input_file"]
    output_path = config["output_path"]
    output_file = config["output_file"]
    base_url = config["base_url"]
    
    # Load queries
    queries = load_queries_from_jsonl(input_path, input_file)
    
    # Process each query
    for item in queries:
        query = item["query"]
        session_id = item["session_id"]
        
        # Call chat server
        response = chat_http_request(base_url, query, session_id)
        
        # Save response
        output_data = {
            "query": query,
            "session_id": session_id,
            "response": response
        }
        append_to_jsonl(output_path, output_file, output_data)
    
    logging.info(f"Inference complete. Responses saved to {output_file}")
```

**Step 3: Add Configuration Section**

Add your experiment configuration to `experiment.yaml`:

```yaml
experiment:
  input_path: src/evaluations/offline/experiment_evaluation_pipeline/datasets/
  input_file: agent_utterances.jsonl
  output_path: src/evaluations/offline/experiment_evaluation_pipeline/datasets/
  output_file: agent_responses.jsonl
  base_url: http://localhost:8000
  # Add any custom parameters your experiment needs
  timeout: 70
  max_retries: 3
```

**Step 4: Add to Pipeline**

Register your experiment in the pipeline section:

```yaml
pipeline:
  - base_path: experiment
    module: agent_inference.inference_main    # module_file.function_name
    config_key: experiment                    # References the experiment: section above
  
  - base_path: evaluator
    module: eval_main.eval_main
    config_key: evaluation
```

**Step 5: Run the Pipeline**

```bash
python -m src.agent_evaluation.agentic_ops.runner --config_file src/evaluations/offline/experiment_evaluation_pipeline/experiment.yaml
```

The runner will:
1. Execute `experiment/agent_inference.py::inference_main()` with `experiment` config
2. Execute `evaluator/eval_main.py::eval_main()` with `evaluation` config
3. Generate final evaluation report

### Example: Custom Experiment Module

Here's an example of adding a custom preprocessing experiment:

```yaml
# Add to experiment.yaml
preprocessing:
  input_path: data/raw/
  input_file: queries.jsonl
  output_path: data/processed/
  output_file: cleaned_queries.jsonl
  filters: ["remove_duplicates", "validate_format"]

pipeline:
  - base_path: preprocessing
    module: clean_data.preprocess_main
    config_key: preprocessing
  
  - base_path: experiment
    module: agent_inference.inference_main
    config_key: experiment
  
  - base_path: evaluator
    module: eval_main.eval_main
    config_key: evaluation
```

This creates a three-stage pipeline: preprocess → inference → evaluation.

## Evaluation Metrics

This example demonstrates **Relevance** and **Task Adherence** evaluators as samples, but the framework supports all Azure AI Foundry built-in evaluators.

### Current Configuration

This example is configured with both standard GenAI and specialized agent-specific evaluators:

#### Standard GenAI Metrics

- **Relevance**: Measures how well the response addresses the query (Score: 1-5)
  - **Required**: `query`, `response`

#### Agent-Specific Metrics (Experimental)

- **Task Adherence**: Evaluates instruction following and constraint adherence (Score: 1-5)
  - **Required**: `query`, `response`

**Other Available Evaluators:**
- **Tool Call Accuracy**: Measures tool invocation correctness (requires `query`, `tool_calls`, `tool_definitions`)
- **Intent Resolution**: Assesses user intent fulfillment (requires `query`, `response`, `tool_definitions`)
- **Coherence, Groundedness, Fluency, Similarity, F1 Score**: Standard GenAI/RAG metrics

> See [Azure AI Foundry documentation](https://learn.microsoft.com/azure/ai-studio/how-to/evaluate-generative-ai-app) for complete evaluator list.

## Dataset Format

### Input Dataset (agent_utterances.jsonl)

For inference stage:

```json
{
  "query": "How is the weather in Seattle?",
  "session_id": "session-1",
  "tool_calls": [...],           // Optional: for evaluation
  "tool_definitions": [...],     // Optional: for evaluation
  "response_gt": "..."           // Optional: ground truth
}
```

### Output Dataset (agent_responses.jsonl)

Generated by inference stage:

```json
{
  "query": "How is the weather in Seattle?",
  "session_id": "session-1",
  "response": "The weather in Seattle is currently cloudy with a temperature of 58°F."
}
```

## How to Add More Evaluators

**Step 1:** Import evaluator in `eval_factory.py`:

```python
from azure.ai.evaluation import RelevanceEvaluator, TaskAdherenceEvaluator

class EvaluatorFactory:
    EVALUATOR_FACTORIES = {
        "relevance_evaluator": RelevanceEvaluator,
        "task_adherence_evaluator": TaskAdherenceEvaluator,
    }
```

**Step 2:** Add to `experiment.yaml`:

```yaml
evaluation:
  evaluators:
    relevance_score: "relevance_evaluator"
    task_adherence_score: "task_adherence_evaluator"
  
  evaluator_config:
    relevance_score:
      column_mapping:
        query: "${data.query}"
        response: "${data.response}"
    task_adherence_score:
      column_mapping:
        query: "${data.query}"
        response: "${data.response}"
```

## How to Run

### Prerequisites

1. **Azure AI Foundry Setup**
   - Azure AI Foundry project configured
   - Azure OpenAI deployment (GPT-4 recommended for evaluators)
   - Environment variables set (see main README)

2. **Chat Server Running**
   - Your agent/chat server must be running at the configured `base_url` (default: `http://localhost:8000`)
   - Server must accept POST requests to `/chat` endpoint
   - Request format: `{"message": "...", "session_id": "..."}`
   - Response format: `{"response": "..."}`

3. **Dataset Prepared**
   - Input dataset in JSONL format with required fields
   - Located at path specified in `experiment.yaml`

### Running the Complete Pipeline

Execute both inference and evaluation stages:

```bash
python -m src.agent_evaluation.agentic_ops.runner --config_file src/evaluations/offline/experiment_evaluation_pipeline/experiment.yaml
```

**What Happens:**
1. **Stage 1 (Experiment)**: 
   - Reads queries from `agent_utterances.jsonl`
   - Sends each query to chat server at `localhost:8000/chat`
   - Collects responses in real-time
   - Writes to `agent_responses.jsonl`

2. **Stage 2 (Evaluation)**:
   - Reads responses from `agent_responses.jsonl`
   - Applies Relevance and Task Adherence evaluators
   - Generates evaluation report
   - Saves to `report/Agent_Evaluation_Experiment.json`
   - (Optional) Pushes to Azure AI Foundry dashboard if `run_local: False`

### Running Individual Stages

**Run Only Inference (Skip Evaluation):**

Comment out the evaluation stage in `experiment.yaml`:

```yaml
pipeline:
  - base_path: experiment
    module: agent_inference.inference_main
    config_key: experiment
  # - base_path: evaluator
  #   module: eval_main.eval_main
  #   config_key: evaluation
```

**Run Only Evaluation (Using Existing Responses):**

Comment out the experiment stage:

```yaml
pipeline:
  # - base_path: experiment
  #   module: agent_inference.inference_main
  #   config_key: experiment
  - base_path: evaluator
    module: eval_main.eval_main
    config_key: evaluation
```

This is useful when you want to:
- Re-run evaluation with different metrics
- Evaluate pre-collected responses
- Test evaluation configurations without calling the chat server

## Folder Structure

```
experiment_evaluation_pipeline/
├── experiment/                          # STAGE 1: Inference
│   ├── agent_inference.py              # Main inference logic
│   └── experiment_utils/               # Inference utilities
│       ├── __init__.py
│       └── http_client.py             # Chat server HTTP client
│
├── datasets/                           # Data storage
│   ├── agent_utterances.jsonl         # INPUT: Queries + metadata
│   └── agent_responses.jsonl          # OUTPUT: Queries + responses
│
├── evaluator/                          # STAGE 2: Evaluation
│   ├── eval_main.py                   # Main evaluation logic
│   └── evaluator_repo/                # Evaluator implementations
│       ├── evaluate_agent_invoked.py
│       └── eval_utils/
│
├── report/                             # Evaluation results
│   └── Agent_Evaluation_Experiment.json
│
├── eval_factory.py                     # Evaluator factory
├── experiment.yaml                     # Pipeline configuration
└── README.md                           # This file
```

**Key Directories:**
- **experiment/**: Contains all inference-related code (Stage 1)
- **datasets/**: Stores input queries and output responses
- **evaluator/**: Contains evaluation logic and evaluator implementations (Stage 2)
- **report/**: Final evaluation reports (JSON format)

**Configuration Files:**
- **experiment.yaml**: Defines both experiment and evaluation stages, plus pipeline orchestration

## Next Steps

1. **Start Your Chat Server**: Ensure your agent is running at `http://localhost:8000`
2. **Prepare Your Dataset**: Create `agent_utterances.jsonl` with your test queries
3. **Configure Pipeline**: Update `experiment.yaml` with your paths and evaluators
4. **Run Complete Pipeline**: Execute both inference and evaluation stages
5. **Review Results**: Check the generated JSON report and Azure AI Foundry dashboard
6. **Iterate**: Modify queries, add evaluators, or change agent configuration based on results
7. **Extend Pipeline**: Add custom preprocessing or post-processing stages as needed

## Example Workflows

### Workflow 1: Initial Agent Testing
```bash
# 1. Run full pipeline with sample data
python -m src.agent_evaluation.agentic_ops.runner --config_file src/evaluations/offline/experiment_evaluation_pipeline/experiment.yaml

# 2. Review results in report/Agent_Evaluation_Experiment.json
# 3. Identify low-scoring queries
# 4. Improve agent prompts/logic
# 5. Re-run pipeline to validate improvements
```

### Workflow 2: Evaluator Experimentation
```bash
# 1. Run inference once to collect responses
# Comment out evaluation in pipeline, run inference only

# 2. Try different evaluator configurations
# Edit evaluators in experiment.yaml, run evaluation only multiple times

# 3. Compare evaluation results
# No need to re-run expensive inference step
```

### Workflow 3: Production Monitoring
```bash
# 1. Collect real user queries → agent_utterances.jsonl
# 2. Run inference against production agent
# 3. Evaluate with comprehensive metrics
# 4. Push results to Azure AI Foundry (run_local: False)
# 5. Track performance over time in dashboard
```

## Resources

- [Azure AI Foundry Evaluation Docs](https://learn.microsoft.com/azure/ai-studio/how-to/evaluate-generative-ai-app)
- [Built-in Evaluators Reference](https://learn.microsoft.com/azure/ai-studio/how-to/evaluate-generative-ai-app#built-in-evaluators)
- [Agent Evaluation Samples](https://github.com/Azure-Samples/azureai-samples/tree/main/scenarios/evaluate/Supported_Evaluation_Metrics/Agent_Evaluation)

## Troubleshooting

**Common Issues:**

| Error | Solution |
|-------|----------|
| `KeyError: 'tool_definitions'` | Ensure dataset includes required fields for agent evaluators |
| `Azure authentication failed` | Run `az login` and verify credentials |
| `ImportError: ToolCallAccuracyEvaluator` | Update package: `pip install --upgrade azure-ai-evaluation` |
| Chat server connection error | Verify server is running at configured `base_url` | 
