# GenAI Evaluation using Microsoft Foundry Built-in Evaluators

## Overview

This evaluation demonstrates how to use **Microsoft Foundry's built-in evaluators** to assess GenAI and RAG (Retrieval-Augmented Generation) systems. Built-in evaluators are production-ready, pre-configured metrics that require no custom code or prompty templates.

**What's Included:**
- **Sample Dataset**: 4 simple query-response examples in JSONL format
- **Pre-configured Evaluators**: Fluency + Coherence metrics
- **Ready to Run**: Complete configuration with `experiment.yaml`

**Why use built-in evaluators?**
- **Zero Configuration**: Ready to use out-of-the-box with standard parameters
- **Production-Ready**: Tested and optimized by Azure AI team
- **Consistent Results**: Standardized scoring across different projects
- **Quick Start**: Evaluate your GenAI system in minutes without custom implementation

## Evaluation Metrics

### Currently Configured Evaluators

| Metric | Description | Score Range | Use Case |
|--------|-------------|-------------|----------|
| **Fluency** | Linguistic quality and readability | 1-5 | Grammar, syntax, natural language flow |
| **Coherence** | Logical flow and consistency | 1-5 | Response structure, internal consistency |

### Additional Built-in Evaluators Available

You can easily add more built-in evaluators from Microsoft Foundry:

| Evaluator | Measures | Requires Ground Truth? |
|-----------|----------|------------------------|
| **Relevance** | How well response addresses query | No |
| **Groundedness** | Response grounded in context (RAG) | No (uses context) |
| **Similarity** | Semantic similarity to reference | Yes |
| **F1 Score** | Token-level overlap | Yes |

See the [Microsoft Foundry documentation](https://learn.microsoft.com/azure/ai-studio/how-to/evaluate-generative-ai-app) for the complete list of available evaluators.

## Dataset Format

Your evaluation dataset should be in JSONL format:

```json
{
  "query": "What is the weather like today?",
  "response": "The weather today is sunny with a high of 75 degrees..."
}
```

### Field Requirements

| Field | Required? | Description | Used By |
|-------|-----------|-------------|---------|
| `query` | ✅ Yes | User's question or input | All evaluators |
| `response` | ✅ Yes | Generated response to evaluate | All evaluators |
| `context` | Optional | Retrieved context for RAG | Groundedness evaluator |
| `ground_truth` | Optional | Reference answer | Similarity, F1 Score evaluators |

**Sample Dataset**: `datasets/rag_sample.jsonl` contains 4 simple query-response examples

## Quick Start

### Prerequisites

1. **Azure Setup**: AI Foundry project with GPT-4o deployment
2. **Environment**: `.env` file configured (see main README)
3. **Installation**: Dependencies installed (`pip install -r requirements.txt`)

### Run with Sample Data

**Run Directly:**
```bash
# Activate virtual environment
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/macOS

# Run evaluation with sample data
python -m src.agent_evaluation.agentic_ops.runner --config_file src/evaluations/offline/genai_evaluation_foundry/experiment.yaml
```

### Run with Your Data

1. **Prepare your dataset**: Create `datasets/my_rag_data.jsonl` with required fields
2. **Update experiment.yaml**:
   ```yaml
   evaluation:
     input_file: my_rag_data.jsonl
   ```
3. **Run evaluation** (same command as above)

## Configuration

### How to Add More Built-in Evaluators

**Step 1: Import the Evaluator** in `eval_factory.py`:

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

**Step 2: Configure in experiment.yaml**:

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

## Results

### Output Location

- **Local mode** (`run_local: True`): `src/evaluations/offline/reports/{run_id}_{eval_dir_name}.json`

### Result Structure

```json
{
  "metrics": {
    "fluency_score": 4.25,
    "coherence_score": 4.50
  },
  "rows": [
    {
      "query": "What is the deductible for Plan A?",
      "response": "The deductible for Plan A is $500...",
      "outputs": {
        "fluency_score": 5,
        "coherence_score": 5
      }
    }
  ],
  "studio_url": "https://ai.azure.com/..."  // If run_local: False
}
```

### Interpretation

| Metric | Good | Needs Improvement |
|--------|------|-------------------|
| Fluency | ≥ 4.0 | < 4.0 |
| Coherence | ≥ 4.0 | < 4.0 |
| Relevance | ≥ 4.0 | < 4.0 |
| Groundedness | ≥ 4.0 | < 4.0 |

**Common Patterns:**
- **Low Fluency**: Check for grammar errors, awkward phrasing, or unnatural language
- **Low Coherence**: Response may lack logical flow or contain contradictions
- **Low Relevance**: Response doesn't directly address the query (may be off-topic)
- **Low Groundedness**: Response contains information not supported by retrieved context

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

```
genai_evaluation_foundry/
├── datasets/
│   ├── __init__.py
│   └── rag_sample.jsonl           # Sample evaluation dataset
├── evaluator/
│   └── eval_main.py               # Evaluation execution logic
├── eval_factory.py               # Evaluator factory (built-in only)
├── experiment.yaml               # Evaluation configuration
└── README.md                     # This file
```

Evaluation reports are saved to `src/evaluations/offline/reports/` using `{run_id}_{eval_dir_name}.json`.

## Next Steps

1. **Run the Default Configuration**: Test with the provided sample data
2. **Add Your Dataset**: Replace `rag_sample.jsonl` with your own data
3. **Add More Evaluators**: Follow Step 1 and 2 above to add additional built-in evaluators
4. **Explore Custom Evaluators**: If you need custom metrics, see the `ai_judge_evaluation_custom` folder

## Resources

- [Microsoft Foundry Evaluation Documentation](https://learn.microsoft.com/azure/ai-studio/how-to/evaluate-generative-ai-app)
- [Built-in Evaluators Reference](https://learn.microsoft.com/azure/ai-studio/how-to/evaluate-generative-ai-app#built-in-evaluators)
- [Microsoft Foundry SDK](https://learn.microsoft.com/python/api/azure-ai-evaluation)

## Data Provenance

All sample datasets included in this repository are **fully synthetic**. They use fictional entities (Northwind Health, Contoso) and simulated agent interactions (smart-home device controls, weather lookups). No real customer data, personally identifiable information, or production telemetry is included in any dataset.
