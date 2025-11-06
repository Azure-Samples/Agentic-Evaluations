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
┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                                    EXPERIMENT & EVALUATION PIPELINE                                                                  │
└─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘

 INPUT                    STAGE 1: EXPERIMENT                         STAGE 2: EVALUATION                        OUTPUT
┌─────────────┐         ┌──────────────────────┐         ┌──────────────────────┐         ┌──────────────────────┐         ┌─────────────────┐
│   Dataset   │         │  Agent Inference     │         │   Chat Server        │         │   Evaluators         │         │    Reports      │
│             │  ────>  │                      │  ────>  │                      │  ────>  │                      │  ────>  │                 │
│ agent_      │         │ • Read queries       │         │ • Process query      │         │ • Load responses     │         │ • JSON report   │
│ utterances  │         │ • Call chat server   │         │ • Invoke agent       │         │ • Apply metrics:     │         │ • Scores        │
│ .jsonl      │         │ • Collect responses  │         │ • Use tools          │         │   - Relevance        │         │ • Aggregates    │
│             │         │ • Save to JSONL      │         │ • Return response    │         │   - TaskAdherence    │         │ • Token stats   │
│ Fields:     │         │                      │         │                      │         │ • Generate report    │         │ • Dashboard     │
│ • query     │         │ experiment/          │         │ localhost:8000/chat  │         │                      │         │                 │
│ • session_id│         │ agent_inference.py   │         │                      │         │ evaluator/           │         │ report/         │
│ • tool_*    │         │                      │         │ POST: {message,      │         │ eval_main.py         │         │ Agent_Eval.json │
└─────────────┘         └──────────────────────┘         │       session_id}    │         └──────────────────────┘         └─────────────────┘
                                 │                        └──────────────────────┘                  │
                                 │                                 │                                │
                                 ▼                                 ▼                                ▼
                        agent_responses.jsonl           {response: "..."}              Metrics: Relevance=5
                        (query, session_id, response)                                  TaskAdherence=5
```

**Pipeline Flow:**
1. **Input Dataset** → Contains test queries with metadata
2. **Inference Module** → Sends queries to chat server, collects responses
3. **Chat Server** → Processes queries using agent logic and tools
4. **Evaluation Module** → Applies Azure AI Foundry evaluators to responses
5. **Output Reports** → JSON results + optional Azure AI Foundry dashboard

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

#### 1. Experiment Section (Inference Configuration)

```yaml
experiment:
  input_path: src/evaluations/offline/experiment_evaluation_pipeline/datasets/  # Input directory
  input_file: agent_utterances.jsonl          # Dataset with queries, session_ids, tool metadata
  output_path: src/evaluations/offline/experiment_evaluation_pipeline/datasets/ # Output directory
  output_file: agent_responses.jsonl         # Saved responses (query + session_id + response)
  base_url: http://localhost:8000            # Chat server endpoint
```

#### 2. Evaluation Section

```yaml
evaluation:
  run_local: False                            # True = local execution, False = push to Azure AI Foundry
  input_path: src/evaluations/offline/experiment_evaluation_pipeline/datasets/  # Input directory
  input_file: agent_responses.jsonl          # Output from experiment stage
  output_path: src/evaluations/offline/experiment_evaluation_pipeline/report/   # Report directory
  
  evaluators:
    relevance_score: "relevance_evaluator"           # Score name: evaluator type
    task_adherence_score: "task_adherence_evaluator"
  
  evaluator_config:
    relevance_score:
      column_mapping:
        query: "${data.query}"                # Map dataset field to evaluator parameter
        response: "${data.response}"
    task_adherence_score:
      column_mapping:
        query: "${data.query}"
        response: "${data.response}"
```

#### 3. Pipeline Section

```yaml
pipeline:
  - base_path: experiment                     # Folder containing the module
    module: agent_inference.inference_main    # module_file.function_name to execute
    config_key: experiment                    # Config section to pass as parameter
  
  - base_path: evaluator
    module: eval_main.eval_main
    config_key: evaluation
```

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

> <details>
> <summary><b>💡 Click to expand: Example implementation</b></summary>
>
> ```python
> # experiment/agent_inference.py
> import logging
> from src.evaluations.offline.utils.file_operations import load_queries_from_jsonl, append_to_jsonl
> from .experiment_utils.http_client import chat_http_request
>
> def inference_main(config, args=None):
>     """
>     Main inference function called by the pipeline runner
>     
>     Args:
>         config: Dictionary with experiment configuration from experiment.yaml
>         args: Optional command-line arguments
>     """
>     logging.info("Starting agent inference...")
>     
>     # Access configuration
>     input_path = config["input_path"]
>     input_file = config["input_file"]
>     output_path = config["output_path"]
>     output_file = config["output_file"]
>     base_url = config["base_url"]
>     
>     # Load queries
>     queries = load_queries_from_jsonl(input_path, input_file)
>     
>     # Process each query
>     for item in queries:
>         query = item["query"]
>         session_id = item["session_id"]
>         
>         # Call chat server
>         response = chat_http_request(base_url, query, session_id)
>         
>         # Save response
>         output_data = {
>             "query": query,
>             "session_id": session_id,
>             "response": response
>         }
>         append_to_jsonl(output_path, output_file, output_data)
>     
>     logging.info(f"Inference complete. Responses saved to {output_file}")
> ```
>
> </details>

**Step 3: Add Configuration Section**

Add your experiment configuration to `experiment.yaml`:

```yaml
experiment:
  input_path: src/evaluations/offline/experiment_evaluation_pipeline/datasets/
  input_file: agent_utterances.jsonl
  output_path: src/evaluations/offline/experiment_evaluation_pipeline/datasets/
  output_file: agent_responses.jsonl
  base_url: http://localhost:8000
```

**Step 4: Add to Pipeline**

Register your experiment in the pipeline section:

```yaml
pipeline:
  - base_path: experiment                    # References experiment: section
    module: agent_inference.inference_main   
    config_key: experiment                   
  - base_path: evaluator                     # References evaluation: section
    module: eval_main.eval_main
    config_key: evaluation
```

**Step 5: Run the Pipeline**

```bash
python -m src.agent_evaluation.agentic_ops.runner --config_file src/evaluations/offline/experiment_evaluation_pipeline/experiment.yaml
```

### Example: Custom Experiment Module

Add custom preprocessing stage to the pipeline:

```yaml
preprocessing:
  input_path: data/raw/
  input_file: queries.jsonl
  output_path: data/processed/
  output_file: cleaned_queries.jsonl
  filters: ["remove_duplicates", "validate_format"]  # Custom parameters

pipeline:
  - base_path: preprocessing              # Stage 1: Preprocess
    module: clean_data.preprocess_main
    config_key: preprocessing
  - base_path: experiment                 # Stage 2: Inference
    module: agent_inference.inference_main
    config_key: experiment
  - base_path: evaluator                  # Stage 3: Evaluation
    module: eval_main.eval_main
    config_key: evaluation
```

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
For detailed instructions on adding more evaluators, refer to [agent_evaluation_foundry](https://github.com/Azure-Samples/Agentic-Evaluations/tree/inference_pipeline/src/evaluations/offline/agent_evaluation_foundry). This resource provides examples and guidance for integrating additional Azure AI Foundry evaluators into your pipeline.

## How to Run

### Prerequisites

1. **Azure AI Foundry Setup**
   - Azure AI Foundry project configured
   - Azure OpenAI deployment (GPT-4 recommended for evaluators)
   - Environment variables set (see main README)

2. **Chat Server Running**
   - Your agent/chat server must be running at the configured `base_url` (default: `http://localhost:8000` or other api endpoint)
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
