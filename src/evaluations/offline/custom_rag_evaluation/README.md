# Evaluation of Agentic Systems using Azure AI Foundry

This folder shows the sample for RAG evaluation using custom evaluators with Azure AI Foundry.

## Folder Structure

```
custom_rag_evaluation/
├── datasets/                              # Sample data for evaluation
│   ├── __init__.py
│   └── agent_response_sample_data.jsonl   # Sample evaluation dataset
├── data_preprocessing/                     # Data processing utilities
│   ├── __init__.py
│   └── data_processing.py                 # Data preprocessing logic
├── evaluator/                             # Core evaluation components
│   └── evaluator_repo/
│       ├── coherence.py                   # CoherenceEvaluatorCustom
│       ├── relevance.py                   # RelevanceEvaluatorCustom
│       ├── fluency.py                     # FluencyEvaluatorCustom 
│       └── prompts/
│           ├── coherence.prompty
│           ├── relevance.prompty
│           ├── fluency.prompty            
│           └── similarity.prompty
├── report/                                # Evaluation results and reports
│   ├── __init__.py
│   └── Agentic_Evaluation_Experiment.json # Sample evaluation results
├── eval_factory.py                       # Evaluator factory and registration
├── experiment.yaml                       # Evaluation configuration
└── README.md                             # This file
```

## Key Components

### Custom Evaluators

- **CoherenceEvaluatorCustom** (`coherence.py`): Evaluates logical flow and consistency
- **RelevanceEvaluatorCustom** (`relevance.py`): Assesses response relevance to query
- **FluencyEvaluatorCustom** (`fluency.py`): Measures linguistic quality and readability  
- **SimilarityEvaluatorCustom** (`relevance.py`): Compares response to ground truth

### Configuration Files

- **experiment.yaml**: Main configuration for evaluation pipeline
- **eval_factory.py**: Registers and manages available evaluators

### Prompty Templates

Each custom evaluator uses a corresponding `.prompty` file that defines:
- Evaluation criteria and scoring rubrics
- System prompts and instructions
- Input/output specifications
- Example scoring scenarios

## Usage

Run the evaluation pipeline using:

```bash
python -m src.agent_evaluation.agentic_ops.runner --config_file src/evaluations/offline/custom_rag_evaluation/experiment.yaml
```

## Architecture Notes

- **Base Infrastructure**: Core evaluation framework located in `src/agent_evaluation/agentic_ops/`
- **Prompty-Driven**: Each evaluator uses structured prompty files for consistent evaluation
- **Extensible Design**: Easy to add new custom evaluators following the established patterns
- **Azure AI Integration**: Leverages Azure AI Foundry for orchestration and Azure OpenAI for scoring 
