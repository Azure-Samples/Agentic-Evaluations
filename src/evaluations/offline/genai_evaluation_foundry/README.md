# GenAI Evaluation using Azure AI Foundry Built-in Evaluators

## Overview

This evaluation framework demonstrates how to use **Azure AI Foundry's built-in evaluators** to assess GenAI and RAG (Retrieval-Augmented Generation) systems. Built-in evaluators are production-ready, pre-configured metrics provided by Azure AI Foundry SDK that require no custom code or prompty templates.

**Why use built-in evaluators?**
- **Zero Configuration**: Ready to use out-of-the-box with standard parameters
- **Production-Ready**: Tested and optimized by Azure AI team
- **Consistent Results**: Standardized scoring across different projects
- **Quick Start**: Evaluate your GenAI system in minutes without custom implementation
- **Azure Integration**: Seamless integration with Azure AI Foundry dashboard and tracking

This folder provides a minimal example for getting started with GenAI evaluations using only built-in Azure AI Foundry evaluators.

## Evaluation Metrics

### Built-in Metrics (Azure AI Foundry SDK)

Currently configured evaluator:

- **Relevance**: Measures how well the response addresses the query
  - Score range: 1-5
  - Evaluates directness and pertinence to the question
  - Assesses if the response directly answers what was asked
  - Use case: Ensuring responses are on-topic and address user intent

### Additional Built-in Evaluators Available

You can easily add more built-in evaluators from Azure AI Foundry:

- **Coherence**: Logical flow and consistency of the response
- **Groundedness**: Whether response is grounded in provided context (RAG scenarios)
- **Fluency**: Linguistic quality and readability
- **Similarity**: Semantic similarity to ground truth
- **F1 Score**: Token-level overlap with ground truth

See the [Azure AI Foundry documentation](https://learn.microsoft.com/azure/ai-studio/how-to/evaluate-generative-ai-app) for the complete list of available evaluators.

## Dataset Format

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

## How to Add More Built-in Evaluators

### Step 1: Import the Evaluator

Update `eval_factory.py` to import additional built-in evaluators:

```python
from azure.ai.evaluation import (
    RelevanceEvaluator,
    CoherenceEvaluator,
    GroundednessEvaluator,
    FluencyEvaluator,
    SimilarityEvaluator
)

class EvaluatorFactory:
    EVALUATOR_FACTORIES = {
        "relevance_evaluator": RelevanceEvaluator,
        "coherence_evaluator": CoherenceEvaluator,
        "groundedness_evaluator": GroundednessEvaluator,
        "fluency_evaluator": FluencyEvaluator,
        "similarity_evaluator": SimilarityEvaluator,
    }
```

### Step 2: Configure in `experiment.yaml`

Add the evaluators to your configuration:

```yaml
evaluation:
  evaluators:
    relevance_score: "relevance_evaluator"
    coherence_score: "coherence_evaluator"
    groundedness_score: "groundedness_evaluator"
    fluency_score: "fluency_evaluator"
    similarity_score: "similarity_evaluator"
  
  evaluator_config:
    relevance_score:
      column_mapping:
        query: "${data.query}"
        response: "${data.response}"
    coherence_score:
      column_mapping:
        query: "${data.query}"
        response: "${data.response}"
    groundedness_score:
      column_mapping:
        query: "${data.query}"
        response: "${data.response}"
        context: "${data.context}"  # Required for groundedness
    fluency_score:
      column_mapping:
        query: "${data.query}"
        response: "${data.response}"
    similarity_score:
      column_mapping:
        query: "${data.query}"
        response: "${data.response}"
        ground_truth: "${data.ground_truth}"  # Required for similarity
```

## How to Run

### Prerequisites

1. Azure AI Foundry project configured
2. Azure OpenAI deployment (GPT-4 recommended)
3. Environment variables set (see main README)
4. Dataset prepared in JSONL format

### Run the Evaluation

From the repository root:

```bash
python -m src.agent_evaluation.agentic_ops.runner --config_file src/evaluations/offline/genai_evaluation_foundry/experiment.yaml
```

## Output

Results are saved to the configured output path:
- **JSON Report**: `{output_path}/{experiment_name}.json`
- **Azure AI Foundry Dashboard**: Automatic upload for visualization and tracking

The report includes:
- Per-sample scores for each evaluator
- Aggregate statistics (mean, median, standard deviation)
- Score distributions
- Metadata about the evaluation run

## When to Use Built-in vs Custom Evaluators

### Use Built-in Evaluators When:
- You need standard quality metrics (relevance, coherence, fluency)
- You want quick setup without custom code
- You're establishing baseline metrics
- You need production-tested, consistent evaluations
- You're new to GenAI evaluation

### Use Custom Evaluators When:
- You need domain-specific evaluation criteria
- You have unique scoring rubrics
- You want to customize prompts and scoring logic
- You need evaluations not available in built-in set
- See `ai_judge_evaluation_custom` folder for custom evaluator examples

## Example Use Cases

1. **Quick Quality Check**: Rapidly evaluate a new GenAI model with standard metrics
2. **Baseline Establishment**: Create baseline quality metrics before custom tuning
3. **RAG System Validation**: Assess basic relevance and groundedness of RAG responses
4. **Model Comparison**: Compare different models using standardized metrics
5. **CI/CD Integration**: Add quality gates in deployment pipelines with built-in evaluators

## Folder Structure

```
genai_evaluation_foundry/
├── datasets/
│   ├── __init__.py
│   └── rag_sample.jsonl           # Sample evaluation dataset
├── evaluator/
│   └── eval_main.py               # Evaluation execution logic
├── report/                        # Evaluation results output
│   └── __init__.py
├── eval_factory.py               # Evaluator factory (built-in only)
├── experiment.yaml               # Evaluation configuration
└── README.md                     # This file
```

## Next Steps

1. **Run the Default Configuration**: Test with the provided sample data
2. **Add Your Dataset**: Replace `rag_sample.jsonl` with your own data
3. **Add More Evaluators**: Follow Step 1 and 2 above to add additional built-in evaluators
4. **View Results**: Check Azure AI Foundry dashboard for detailed visualizations
5. **Explore Custom Evaluators**: If you need custom metrics, see the `ai_judge_evaluation_custom` folder

## Resources

- [Azure AI Foundry Evaluation Documentation](https://learn.microsoft.com/azure/ai-studio/how-to/evaluate-generative-ai-app)
- [Built-in Evaluators Reference](https://learn.microsoft.com/azure/ai-studio/how-to/evaluate-generative-ai-app#built-in-evaluators)
- [Azure AI Foundry SDK](https://learn.microsoft.com/python/api/azure-ai-evaluation) 
