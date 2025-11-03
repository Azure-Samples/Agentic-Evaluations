# Custom Evaluators Framework

This directory contains the simplified framework for creating custom evaluators. The framework is designed to make it easy to add new evaluation metrics by only requiring a prompty file and minimal code changes.

## Quick Start

1. **Copy the template**: Use `prompts/template.prompty` as your starting point
2. **Create your prompty**: Define your evaluation criteria and examples
3. **Create evaluator class**: Inherit from `BaseCustomEvaluator`
4. **Register**: Add to `eval_factory.py`
5. **Configure**: Update your `experiment.yaml`

## Directory Structure

```
evaluator_repo/
├── coherence.py              # CoherenceEvaluatorCustom
├── relevance.py              # RelevanceEvaluatorCustom  
├── fluency.py                # FluencyEvaluatorCustom
├── similarity.py             # SimilarityEvaluatorCustom
└── prompts/
    ├── coherence.prompty     # Coherence evaluation prompt
    ├── relevance.prompty     # Relevance evaluation prompt
    ├── fluency.prompty       # Fluency evaluation prompt
    ├── similarity.prompty    # Similarity evaluation prompt
    └── template.prompty      # Template for new evaluators
```

## Available Evaluators

| Evaluator | File | Prompty | Purpose |
|-----------|------|---------|---------|
| `CoherenceEvaluatorCustom` | `coherence.py` | `coherence.prompty` | Text coherence and flow |
| `RelevanceEvaluatorCustom` | `relevance.py` | `relevance.prompty` | Response relevance to query |
| `FluencyEvaluatorCustom` | `fluency.py` | `fluency.prompty` | Language fluency and grammar |
| `SimilarityEvaluatorCustom` | `similarity.py` | `similarity.prompty` | Similarity to ground truth |

## Creating a New Evaluator

### 1. Create Your Prompty File

Copy `prompts/template.prompty` and customize:

```yaml
---
name: MyCustom
description: Evaluates my custom metric
# ... model configuration
inputs:
  query:
    type: string
  response:
    type: string
---
system:
# Your evaluation instructions

user:
# Your metric definition and examples
QUERY: {{query}}
RESPONSE: {{response}}

# Use structured output format:
<S0>thoughts</S0>, <S1>explanation</S1>, <S2>score</S2>
```

### 2. Create Evaluator Class

```python
from ......agent_evaluation.agentic_ops.base_evaluator import BaseCustomEvaluator

class MyCustomEvaluator(BaseCustomEvaluator):
    def __init__(self, model_config=None):
        super().__init__(
            prompty_file_name="my_custom.prompty",
            result_key="my_custom_score",
            model_config=model_config
        )

    def __call__(self, query: str, response: str, **kwargs):
        return self.evaluate(query=query, response=response, **kwargs)
```

### 3. Register in Factory

Add to `eval_factory.py`:

```python
from .evaluator.evaluator_repo.my_custom import MyCustomEvaluator

EVALUATOR_FACTORIES = {
    # ... existing
    "my_custom_evaluator": MyCustomEvaluator,
}
```

### 4. Configure in YAML

Add to `experiment.yaml`:

```yaml
evaluators:
  my_score: "my_custom_evaluator"
evaluator_config:
  my_score:
    column_mapping:
      query: "${data.query}"
      response: "${data.response}"
```

## Best Practices

### Prompty Design
- Use 1-5 scoring scale for consistency
- Provide clear examples for each score level
- Use structured output format `<S0>`, `<S1>`, `<S2>`
- Include placeholder variables with `{{variable_name}}`

### Code Structure
- Inherit from `BaseCustomEvaluator` for consistency
- Use descriptive `result_key` names (e.g., `my_metric_score_custom`)
- Handle additional parameters via `**kwargs`

### Error Handling
- The base class handles score extraction automatically
- Fallback patterns are built-in for robustness
- Logging is handled automatically

## Environment Variables

Ensure these are set for Azure OpenAI:

```bash
EVAL_AZURE_OPENAI_ENDPOINT=your_endpoint
EVAL_AZURE_OPENAI_KEY=your_key
EVAL_AZURE_OPENAI_VERSION=your_version
EVAL_AZURE_OPENAI_MODEL=your_model
```

## Troubleshooting

- **Score not extracted**: Check prompty output format uses `<S2>score</S2>`
- **File not found**: Verify prompty file is in `prompts/` directory
- **Import error**: Ensure evaluator is registered in `eval_factory.py`
- **Column mapping**: Verify data field names in `experiment.yaml`

## Examples

See the existing evaluators (`coherence.py`, `relevance.py`) and their corresponding prompty files for complete examples of different evaluation types.






###
### Quick Start: Adding a Custom Evaluator

The framework provides a simplified approach to add custom evaluators. You only need to create a prompty file and register the evaluator.

#### Step 1: Create a Custom Evaluator Class

Create your evaluator by inheriting from `BaseCustomEvaluator`:

```python
# In evaluator_repo/my_custom_evaluator.py
from ......agent_evaluation.agentic_ops.base_evaluator import BaseCustomEvaluator
from typing import Dict, Union

class MyCustomEvaluator(BaseCustomEvaluator):
    def __init__(self, model_config=None):
        super().__init__(
            prompty_file_name="my_custom.prompty",  # Your prompty file
            result_key="my_custom_score",           # Score key in results
            model_config=model_config
        )

    def __call__(self, query: str, response: str, **kwargs) -> Dict[str, Union[str, float]]:
        return self.evaluate(query=query, response=response, **kwargs)
```

#### Step 2: Create a Prompty File

Create your prompty file in `evaluator_repo/prompts/my_custom.prompty`:

```yaml
---
name: MyCustom
description: Evaluates my custom metric for QA scenario
model:
  api: chat
  parameters:
    temperature: 0.0
    max_tokens: 800
    response_format:
      type: text

inputs:
  query:
    type: string
  response:
    type: string
---
system:
# Your evaluation instructions here

user:
# Definition of your metric
**MyCustom** refers to...

# Ratings (1-5 scale)
## [MyCustom: 1] - Poor
## [MyCustom: 2] - Below Average  
## [MyCustom: 3] - Average
## [MyCustom: 4] - Good
## [MyCustom: 5] - Excellent

# Data
QUERY: {{query}}
RESPONSE: {{response}}

# Tasks
Please provide your assessment Score:
- **ThoughtChain**: Let's think step by step:
- **Explanation**: Brief explanation
- **Score**: Integer score 1-5

## Format: <S0>thoughts</S0>, <S1>explanation</S1>, <S2>score</S2>
```

#### Step 3: Register in EvaluatorFactory

Add to `eval_factory.py`:

```python
from .evaluator.evaluator_repo.my_custom_evaluator import MyCustomEvaluator

class EvaluatorFactory:
    EVALUATOR_FACTORIES = {
        # ... existing evaluators
        "my_custom_evaluator": MyCustomEvaluator,
    }
```

#### Step 4: Update Configuration

Add to your `experiment.yaml`:

```yaml
evaluation:
  evaluators:
    my_custom_score: "my_custom_evaluator"
  evaluator_config:
    my_custom_score:
      column_mapping:
        query: "${data.query}"
        response: "${data.response}"
```

### Example: Adding Custom Relevance Evaluator

Let's walk through adding a custom relevance evaluator:

#### 1. Create the Evaluator Class

```python
# In evaluator_repo/relevance.py
from ......agent_evaluation.agentic_ops.base_evaluator import BaseCustomEvaluator
from typing import Dict, Union

class RelevanceEvaluatorCustom(BaseCustomEvaluator):
    def __init__(self, model_config=None):
        super().__init__(
            prompty_file_name="relevance.prompty",
            result_key="relevance_score_custom",
            model_config=model_config
        )

    def __call__(self, query: str, response: str, **kwargs) -> Dict[str, Union[str, float]]:
        return self.evaluate(query=query, response=response, **kwargs)
```

#### 2. Create relevance.prompty (already included in the framework)

#### 3. Register in eval_factory.py

```python
from .evaluator.evaluator_repo.relevance import RelevanceEvaluatorCustom

class EvaluatorFactory:
    EVALUATOR_FACTORIES = {
        "relevance_evaluator": RelevanceEvaluator,  # Azure built-in
        "custom_relevance_evaluator": RelevanceEvaluatorCustom,  # Your custom one
    }
```

#### 4. Update experiment.yaml

```yaml
evaluation:
  evaluators:
    custom_relevance_score: "custom_relevance_evaluator"
  evaluator_config:
    custom_relevance_score:
      column_mapping:
        query: "${data.query}"
        response: "${data.response}"
```

### Available Custom Evaluators

The framework includes these ready-to-use custom evaluators:

| Evaluator | Purpose | Required Inputs | Output Key |
|-----------|---------|----------------|------------|
| `CoherenceEvaluatorCustom` | Text coherence and flow | `query`, `response` | `coherence_score_custom` |
| `RelevanceEvaluatorCustom` | Response relevance to query | `query`, `response` | `relevance_score_custom` |
| `FluencyEvaluatorCustom` | Language fluency | `response` | `fluency_score_custom` |
| `SimilarityEvaluatorCustom` | Similarity to ground truth | `query`, `response`, `ground_truth` | `similarity_score_custom` |

### Best Practices

1. **Prompty Design**: Use structured output format with `<S0>`, `<S1>`, `<S2>` tags
2. **Score Extraction**: The framework automatically extracts scores from `<S2>score</S2>` tags
3. **Error Handling**: Include fallback patterns and default scores
4. **Placeholders**: Use `{{variable_name}}` format in prompty files
5. **Testing**: Test your evaluator with sample data before deployment

### Advanced Features

- **Multi-parameter Evaluation**: Pass additional parameters via `**kwargs`
- **Custom Score Extraction**: Override `_extract_score()` method for custom patterns
- **Flexible Input Mapping**: Map any data fields to prompty placeholders
- **Environment Configuration**: All Azure OpenAI settings via environment variables

### Troubleshooting

- **Missing Prompty File**: Check file path and extension (.prompty)
- **Score Extraction Failed**: Verify structured output format in prompty
- **Import Errors**: Ensure evaluator is properly registered in eval_factory.py
- **Column Mapping**: Verify data field names match experiment.yaml configuration 