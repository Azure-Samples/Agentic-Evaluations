# Evaluation Framework using Azure AI Foundry

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Azure](https://img.shields.io/badge/Azure-AI%20Foundry-blue.svg)](https://azure.microsoft.com/en-us/products/ai-foundry)

A comprehensive framework that enables **quick setup, experimentation, and evaluation** for both **Agentic systems** and **GenAI applications** (such as RAG). Built on Azure AI Foundry SDK, this framework features a **configurable, pipeline-based architecture** that allows you to add your own modules as plug-and-play components. Evaluation is simplified through just **2-3 steps**, supporting both Azure AI Foundry's built-in evaluation metrics and custom metrics tailored to your specific use cases.

## Overview

This repository provides a **reproducible, config-driven evaluation pipeline** designed for rapid experimentation with GenAI and agentic systems. The framework combines:

- **Plug-and-Play Architecture**: Modular pipeline design where you can easily add custom data loaders, preprocessors, evaluators, and reporting modules without modifying core framework code
- **Quick Setup**: Get started with evaluations in 2-3 simple steps - configure your experiment YAML, register evaluators, and run
- **Dual Evaluation Support**: Seamlessly use Azure AI Foundry's built-in evaluators for standardized scoring alongside custom evaluators for domain-specific or agent-level metrics
- **Flexible Workflows**: Organized into modular stages (data loading, preprocessing, evaluation, reporting) driven by experiment YAMLs, allowing you to swap datasets, models, or evaluators instantly
- **Multiple Use Cases**: Evaluate agentic systems (tool invocation, agent selection, multi-step reasoning) as well as GenAI applications like RAG (relevance, groundedness, coherence)
- **Comprehensive Visualization**: Results automatically integrate with Azure AI Foundry Evaluation dashboard for comparison across experiments and runs

Whether you're building sophisticated agentic workflows or optimizing RAG applications, this framework accelerates your evaluation process from days to hours.

### Key Features

- **🎯 Azure AI Foundry SDK Integration**: Built on [Azure AI Evaluation SDK](https://pypi.org/project/azure-ai-evaluation/) for enterprise-grade evaluation capabilities
- **⚖️ Dual Evaluator Support**: Use Azure AI Foundry's built-in evaluators ([see full list](https://learn.microsoft.com/en-us/azure/ai-foundry/concepts/evaluation-evaluators/general-purpose-evaluators)) alongside custom evaluators tailored to your domain
- **🔌 Highly Customizable Pipelines**: Add your own modules for data preprocessing, model inferencing, evaluation, and reporting as plug-and-play components
- **📝 Config-Driven Architecture**: YAML-based configuration for pipelines, evaluators, and experiments - no code changes required
- **📈 AI Foundry Integration**: Automatic visualization and comparison of evaluation results across experiments

### Evaluation Pipeline Diagram
![Evaluation Pipeline](./assets/Eval-pipeline.png)


## Repository Structure

```text
src/
├── agent_evaluation/
│   └── agentic_ops/
│       ├── runner.py
│       └── run_eval.py
│
├── evaluations/
│   └── offline/
│       └── agentic_evaluation/
│           ├── data_loader/
│           │   ├── <*your data loader connector.py
│           ├── data_preprocessing/
│           │   ├── <*your data preprocessing.py
│           ├── datasets/
│           │   ├── <agent_response.jsonl>
│           ├── evaluator/
│           │   ├── evaluator_repo/
│           │   └── <eval_script>.py
│       ├── <**future Evals**>/
│       ├── data_sets/
│           └── DataForEvals/
│               └── golden_datasets.xlsx
```


## Pipeline Flow

1. **data_loading**: download evaluation data from blob storage
2. **data_preprocessing**: Filter the datasets and quality checks
4. **Evaluation**: Run selected evaluators.
5. **Reporting**: View results on AI Foundry dashboard

## Prerequisites

- Azure Subscription with permissions
- Azure CLI installed and authenticated
- Azure AI Foundry project and GPT-4o deployment
- Python 3.11+
- Git
- Prerequisite set up steps for Azure AI Foundry projects
      If this is your first time running evaluations and logging it to your Azure AI Foundry project, you might need to do a few additional setup steps:

      1. Create and connect your storage account to your Azure AI Foundry project at the resource level. This bicep template provisions and connects a storage account to your Foundry project with key authentication.
      2. Make sure the connected storage account has access to all projects.
      3. If you connected your storage account with Microsoft Entra ID, make sure to give MSI (Microsoft Identity) permissions for Storage Blob Data Owner to both your account and Foundry project resource in Azure portal.

      Reference: https://learn.microsoft.com/en-us/azure/ai-foundry/how-to/develop/evaluate-sdk#evaluate-on-test-dataset-using-evaluate


## Azure Services Used

- **Azure AI Foundry** (evaluation and model hosting)
- **GPT-4o** - LLM as a judgment

## Installation & Setup

### 1. Clone the Repository

```bash
git clone https://github.com/Azure-Samples/Agentic-Evaluations.git
cd Agentic-Evaluations
git checkout -b "your branch"
```

### 2. Install Dependencies

```bash
uv sync

# Activate virtual environment
.venv\Scripts\activate         # PowerShell (Windows)
source venv/bin/activate       # Linux/macOS
```

### 3. Install Azure CLI & Login
```
az login
```

### 4. create env file based on Azure AI Foundry set up (refer to env_template)


### 5. Run the Evaluations (as is with sample files provided):
To run agent_end_response_evaluation
```bash
python -m src.agent_evaluation.agentic_ops.runner --config_file src/evaluations/offline/agentic_evaluation/experiment.yaml
```


## Running the Pipeline

### Folder template allows quick changes 
1. Add a different datasets (in golden dataset format) and provide the path. -> <datasets folder>
2. Add Agentic/GenAI Inference component - comming soon!!
4. Filter the required columns and flatten the response in jsonl format - <data_transform.py. > Comming soon!!
5. Run your custom evaluations, add your metrics -> <eval_factory_config.py, experiments.yaml. >

### Understand the config. 
```yaml
app_name: Agentic-Evals
version: 1.0.0
experiment_name: Agentic_Evaluation_Experiment
evaluation:  #evaluation configuration. 
  run_local: True #Make it False if you wish to push the eval results to AI Foundry. Make sure your AI foundry setup and keys are added to env. 
  input_path: src/evaluations/offline/agentic_evaluation/datasets/
  input_file: agent_response_sample_data.jsonl
  output_path: src/evaluations/offline/agentic_evaluation/report/
  column_mapping:
    user_id: "${data.conversation_id}"
  evaluators:
    relevance_score: "relevance_evaluator"
    agents_invoked_eval: "custom_agents_invoked_evaluator"
  evaluator_config:
    relevance_score:
      column_mapping:
        query: "${data.user_query}"
        response: "${data.gt_agent_response}" 
    agents_invoked_eval:
      column_mapping:
        expected_agents_to_invoke: "${data.expected_agents_to_invoke}"
        predicted_agents_to_invoke: "${data.selected_agents}"

pipeline: # pipeline to run the end to end flow. 
  - base_path: evaluator # folder name for evaluations
    module: eval_main.eval_main # module to run evaluations
    config_key: evaluation # mapped to the config for evaluations above. 

```
# How to Add Foundry's built in evaluations 
1. Register it in `EVALUATOR_FACTORIES` eval_factory_config.py
   for example - to add similarity evaluator SimilarityEvaluator
   ```
   from azure.ai.evaluation import RelevanceEvaluator, **SimilarityEvaluator**
   from .evaluator.evaluator_repo.evaluate_agent_invoked import EvaluateAgentsInvoked

   class EvaluatorFactory:
      """Configuration for available evaluators."""

      EVALUATOR_FACTORIES = {
         "relevance_evaluator": RelevanceEvaluator,
         **"similarity_evaluator": SimilarityEvaluator,**
         "custom_agents_invoked_evaluator": EvaluateAgentsInvoked,    
      }
   ```
2. Add metrics in evaluation section in config YAML
3. Run the pipeline 

## How to Add custom evaluations

1. Add your custom evaluator in `evaluator_repo/`
2. Register it in `EVALUATOR_FACTORIES` eval_factory_config.py
3. Add metrics in evaluation section in config YAML
4. Run the pipeline 

## Custom Evaluation Metrics for SLM Systems

| Metric                          | Description                                                       |
|---------------------------------|-------------------------------------------------------------------|
| Agent invoke accuracy           | checks if agents actually invoked is same as expected agents for a query |
| Recall@k                        | check the recall @1 to recall@3 for agents invoked.               |
| Relevance score                 | Built in evaluator checks the relevance of response to the query  |


## Built-in Evaluators (Azure AI Foundry)

| Evaluator                     | Query       | Response    | Context     | Ground Truth | Conversation |
|------------------------------|-------------|-------------|-------------|---------------|--------------|
| RelevanceEvaluator           | Required    | Required    | N/A         | N/A           | Yes          |
| FluencyEvaluator             | N/A         | Required    | N/A         | N/A           | Yes          |
| GroundednessEvaluator        | Optional    | Required    | Required    | N/A           | Yes          |
| SimilarityEvaluator          | Required    | Required    | N/A         | Required      | No           |
| RougeScoreEvaluator          | N/A         | Required    | N/A         | Required      | No           |
| ContentSafetyEvaluator       | Required    | Required    | N/A         | N/A           | Yes          |
| CodeVulnerabilityEvaluator   | Required    | Required    | N/A         | N/A           | Yes          |
| CoherenceEvaluator           | Required    | Required    | N/A         | N/A           | Yes          |

*For full list of evaluators, refer to the [AI Foundry Evaluator Reference](https://learn.microsoft.com/en-us/azure/ai-foundry/how-to/develop/evaluate-sdk)*

## Future Enhancements

- Multi-turn conversation evaluation
- More advanced visualization and comparative dashboards

## References
- [Azure AI Evaluatation SDK](https://learn.microsoft.com/en-us/python/api/overview/azure/ai-evaluation-readme?view=azure-python)
- [Azure AI Foundry Documentation](https://learn.microsoft.com/en-us/azure/ai-foundry/what-is-ai-foundry)
- [Agentic Evaluation in Azure](https://learn.microsoft.com/en-us/azure/ai-foundry/how-to/develop/agent-evaluate-sdk)
- [Built-in Evaluator Reference](https://learn.microsoft.com/en-us/azure/ai-foundry/how-to/develop/evaluate-sdk)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

This project welcomes contributions and suggestions. Most contributions require you to agree to a Contributor License Agreement (CLA) declaring that you have the right to, and actually do, grant us the rights to use your contribution. For details, visit https://cla.opensource.microsoft.com.

When you submit a pull request, a CLA bot will automatically determine whether you need to provide a CLA and decorate the PR appropriately (e.g., status check, comment). Simply follow the instructions provided by the bot. You will only need to do this once across all repos using our CLA.

This project has adopted the [Microsoft Open Source Code of Conduct](https://opensource.microsoft.com/codeofconduct/). For more information see the [Code of Conduct FAQ](https://opensource.microsoft.com/codeofconduct/faq/) or contact [opencode@microsoft.com](mailto:opencode@microsoft.com) with any additional questions or comments.
