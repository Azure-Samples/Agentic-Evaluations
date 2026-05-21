# Agentic Operations Infrastructure

This folder contains the core infrastructure components for the agentic evaluation framework.

## Components

### Core Infrastructure Files

- **`runner.py`** - Pipeline orchestration and execution framework
- **`run_eval.py`** - Evaluation execution engine for Microsoft Foundry
- **`base_evaluator.py`** - Base class for all custom evaluators
- **`client.py`** - LLM client utilities for Azure OpenAI interaction

### Why These Files Are Here

The `agentic_ops` folder contains **stable infrastructure code** that:

1. **Rarely Changes** - Core framework components that provide foundational functionality
2. **Reusable Across Projects** - Can be used for different types of evaluations beyond just custom RAG
3. **Framework-Level** - Provides the plumbing that specific evaluations build upon

### Architecture Benefits

- **Separation of Concerns**: Infrastructure (here) vs. Implementation (evaluation-specific folders)
- **Code Reusability**: Base classes and utilities can be shared across multiple evaluation scenarios  
- **Maintainability**: Framework improvements benefit all evaluations automatically
- **Consistency**: Common patterns and utilities across all custom evaluators

## Usage

### For Custom Evaluator Development

```python
from src.agent_evaluation.agentic_ops.base_evaluator import BaseCustomEvaluator

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

### For Direct LLM Interaction

```python
from src.agent_evaluation.agentic_ops.client import LLMClient

client = LLMClient(temperature=0.0)
response = client.get_llm_response_with_prompty(messages)
```

## Dependencies

- **Azure OpenAI**: For LLM interactions
- **Microsoft Foundry**: For evaluation orchestration  
- **Python-dotenv**: For environment configuration
- **OpenAI SDK**: For Azure OpenAI client functionality

## Environment Variables

The infrastructure expects these environment variables:

```bash
# Azure OpenAI Configuration
EVAL_AZURE_OPENAI_ENDPOINT=your_endpoint
EVAL_AZURE_OPENAI_KEY=your_key  
EVAL_AZURE_OPENAI_MODEL=your_deployment_name
EVAL_AZURE_OPENAI_VERSION=your_api_version

# Microsoft Foundry Configuration  
EVAL_AZURE_FOUNDRY_PROJECT_ENDPOINT=your_project_endpoint
AZURE_SUBSCRIPTION_ID=your_subscription_id
AZURE_RESOURCE_GROUP_NAME=your_resource_group
AZURE_PROJECT_NAME=your_project_name
```

## Data Provenance

All sample datasets included in this repository are **fully synthetic**. They use fictional entities (Northwind Health, Contoso) and simulated agent interactions (smart-home device controls, weather lookups). No real customer data, personally identifiable information, or production telemetry is included in any dataset.