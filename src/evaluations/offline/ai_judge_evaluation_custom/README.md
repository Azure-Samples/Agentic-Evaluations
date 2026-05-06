# Custom AI Judge Evaluation for RAG Systems

## Overview

This evaluation provides **AI-as-a-Judge** evaluations using custom prompty templates. Unlike built-in evaluators with fixed criteria, custom AI judges let you define your own evaluation rubrics and scoring logic tailored to your domain.

**What's Included:**
- **Sample Dataset**: 4 RAG system responses in JSONL format
- **Pre-configured Evaluators**: Custom Coherence + Custom Relevance + Custom Fluency + Custom Similarity
- **Prompty Templates**: 4 customizable evaluation prompts in `evaluator/evaluator_repo/prompts/`
- **Ready to Run**: Complete configuration with `experiment.yaml`

**What is AI-as-a-Judge evaluation?**
- Uses LLMs (like GPT-4) to evaluate response quality based on defined criteria
- Provides scoring with reasoning and detailed feedback
- Evaluates subjective aspects like coherence, fluency, and relevance
- Combines the scalability of automated evaluation with the nuance of human assessment

This framework supports both **Azure AI Foundry built-in evaluators** and **custom evaluators** powered by prompty templates, allowing you to define your own evaluation criteria and scoring rubrics.

## Evaluation Metrics

### Built-in Metrics (Azure AI Foundry SDK)

| Metric | Description | Score Range | Use Case |
|--------|-------------|-------------|----------|
| **Relevance** | How well response addresses query | 1-5 | On-topic responses |
| **Coherence** | Logical flow and consistency | 1-5 | Response structure |

### Custom AI Judge Metrics (Prompty-Based)

All custom evaluators use prompty templates in `evaluator/evaluator_repo/prompts/` that define scoring criteria and rubrics:

| Evaluator | Prompty File | Measures | Score Range | Use Case |
|-----------|--------------|----------|-------------|----------|
| **Custom Coherence** | `custom_coherence.prompty` | Natural language flow, readability | 1-5 | User-friendliness of responses |
| **Custom Relevance** | `custom_relevance.prompty` | Directness, completeness of answer | 1-5 | Ensuring on-topic responses |
| **Custom Fluency** | `custom_fluency.prompty` | Grammar, syntax, linguistic quality | 1-5 | Identifying language errors |
| **Custom Similarity** | `custom_similarity.prompty` | Semantic similarity to ground truth | 1-5 | Factual accuracy validation |

## Dataset Format

Your evaluation dataset should be in JSONL format:

```json
{
  "query": "What is the weather like today?",
  "response": "The weather today is sunny with a high of 75 degrees...",
  "ground_truth": "Today's weather is sunny and 75°F..."
}
```

### Field Requirements

| Field | Required? | Description | Used By |
|-------|-----------|-------------|---------|
| `query` | ✅ Yes | User's question or input | All evaluators |
| `response` | ✅ Yes | Generated response to evaluate | All evaluators |
| `ground_truth` | Optional | Reference answer | Custom Similarity evaluator |

**Sample Dataset**: `datasets/rag_sample.jsonl` contains 4 simple query-response examples

**Important Notes:**
- Custom evaluators receive all dataset fields, so you can reference them in prompty templates
- Built-in evaluators only accept specific fields defined in their schemas

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
python -m src.agent_evaluation.agentic_ops.runner --config_file src/evaluations/offline/ai_judge_evaluation_custom/experiment.yaml
```

### Run with Your Data

1. **Prepare your dataset**: Create `datasets/my_rag_data.jsonl` with required fields
2. **Update experiment.yaml**:
   ```yaml
   evaluation:
     input_file: my_rag_data.jsonl
   ```
3. **Run evaluation** (same command as above)

## How to Add Custom Metrics

### Overview

Custom evaluators consist of three components:
1. **Prompty Template** (`.prompty` file): Defines evaluation criteria and rubric
2. **Evaluator Class** (Python file): Wraps prompty and handles scoring logic
3. **Factory Registration** (`eval_factory.py`): Makes evaluator available to framework

### Step 1: Create a Prompty Template

Create a new `.prompty` file in `evaluator/evaluator_repo/prompts/`:

```yaml
---
name: YourCustomEvaluator
description: Description of what this evaluator measures
model:
  api: chat
  configuration:
    type: azure_openai
  parameters:
    temperature: 0.0
    max_tokens: 800
    response_format:
      type: json_object
inputs:
  query:
    type: string
  response:
    type: string
outputs:
  your_metric_score:
    type: int
---
system:
You are an AI judge that evaluates [DESCRIBE WHAT YOU'RE EVALUATING].

**Scoring Criteria:**
- Score 1: [Poor quality criteria]
- Score 2: [Below average criteria]
- Score 3: [Average criteria]
- Score 4: [Good criteria]
- Score 5: [Excellent criteria]

**Instructions:**
1. Analyze the response based on the criteria above
2. Provide your reasoning
3. Return a JSON object with the score

user:
Query: {{query}}
Response: {{response}}

Return your evaluation as JSON:
{
  "your_metric_score": <1-5>,
  "reasoning": "explanation of the score"
}
```

### Step 2: Create the Evaluator Class

Create a new evaluator file in `evaluator/evaluator_repo/`:

```python
# evaluator/evaluator_repo/your_custom_evaluator.py

from typing import Dict, Union
from ......agent_evaluation.agentic_ops.base_evaluator import BaseCustomEvaluator


class YourCustomEvaluator(BaseCustomEvaluator):
    """
    Custom evaluator that evaluates [DESCRIBE METRIC].
    
    [DETAILED DESCRIPTION OF WHAT THIS EVALUATOR MEASURES]
    
    Example:
        evaluator = YourCustomEvaluator()
        result = evaluator(query="...", response="...")
        # Returns: {"your_metric_score_custom": 4}
    """

    def __init__(self, model_config=None):
        """Initialize the evaluator."""
        super().__init__(
            prompty_file_name="your_custom_metric.prompty",
            result_key="your_metric_score_custom",
            model_config=model_config
        )

    def __call__(self, query: str, response: str, **kwargs) -> Dict[str, Union[str, float]]:
        """
        Evaluate the metric for given inputs.

        :param query: The query to be evaluated.
        :param response: The response to be evaluated.
        :return: The evaluation score.
        """
        return self.evaluate(query=query, response=response, **kwargs)
```

### Step 3: Register in `eval_factory.py`

```python
from .evaluator.evaluator_repo.your_custom_evaluator import YourCustomEvaluator

class EvaluatorFactory:
    EVALUATOR_FACTORIES = {
        # Azure built-in evaluators
        "relevance_evaluator": RelevanceEvaluator,
        "coherence_evaluator": CoherenceEvaluator,
        
        # Custom evaluators
        "custom_coherence_evaluator": CoherenceEvaluatorCustom,
        "custom_relevance_evaluator": RelevanceEvaluatorCustom,
        "custom_fluency_evaluator": FluencyEvaluatorCustom,
        "custom_similarity_evaluator": SimilarityEvaluatorCustom,
        "your_custom_evaluator": YourCustomEvaluator,  # Add here
    }
```

### Step 4: Configure in `experiment.yaml`

```yaml
evaluation:
  evaluators:
    relevance_score: "relevance_evaluator"
    coherence_score: "coherence_evaluator"
    custom_coherence_score: "custom_coherence_evaluator"
    custom_relevance_score: "custom_relevance_evaluator"
    custom_fluency_score: "custom_fluency_evaluator"
    custom_similarity_score: "custom_similarity_evaluator"
    your_metric: "your_custom_evaluator"  # Add your evaluator
  
  evaluator_config:
    your_metric:
      column_mapping:
        query: "${data.query}"
        response: "${data.response}"
```

## How to Run

### Prerequisites

1. Azure AI Foundry project configured
2. Azure OpenAI deployment (GPT-4 recommended for judge evaluations)
3. Environment variables set (see main README)
4. Dataset prepared in JSONL format

### Run the Evaluation

From the repository root:

```bash
python -m src.agent_evaluation.agentic_ops.runner --config_file src/evaluations/offline/ai_judge_evaluation_custom/experiment.yaml
```

## Prompty Template Features

Each `.prompty` file provides:

1. **Structured Scoring Rubrics**: Clear criteria for each score level (1-5)
2. **Model Configuration**: Temperature, max tokens, response format
3. **Input/Output Schema**: Typed parameters and expected outputs
4. **System Prompts**: Detailed instructions for the AI judge
5. **JSON Response Format**: Structured output with scores and reasoning

The prompty format ensures consistent, reproducible evaluations across different model versions.

## Output

Results are saved to the configured output path:
- **JSON Report**: `{output_path}/{run_id}_{eval_dir_name}.json`
- **Azure AI Foundry Dashboard**: Automatic upload for visualization

The report includes:
- Per-sample scores for each evaluator
- Aggregate statistics (mean, median, std dev)
- Score distributions and histograms
- Detailed reasoning from AI judges (in custom evaluators)

## Example Use Cases

1. **RAG Quality Assessment**: Evaluate retrieval-augmented generation systems across multiple quality dimensions
2. **A/B Testing**: Compare different retrieval strategies, prompt templates, or model versions
3. **Custom Rubrics**: Define domain-specific evaluation criteria using prompty templates
4. **Benchmark Creation**: Establish baseline quality metrics for your RAG system
5. **Regression Testing**: Monitor quality degradation across system updates

## Architecture

- **Base Infrastructure**: `src/agent_evaluation/agentic_ops/base_evaluator.py` provides the foundation
- **Prompty-Driven**: All custom evaluators use `.prompty` files for consistency
- **LLM Client**: `src/agent_evaluation/agentic_ops/client.py` handles Azure OpenAI interaction
- **Extensible**: Add new evaluators by creating prompty files and evaluator classes

## Data Provenance

All sample datasets included in this repository are **fully synthetic**. They use fictional entities (Northwind Health, Contoso) and simulated agent interactions (smart-home device controls, weather lookups). No real customer data, personally identifiable information, or production telemetry is included in any dataset.
