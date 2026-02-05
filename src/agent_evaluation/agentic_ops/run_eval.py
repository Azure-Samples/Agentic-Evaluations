import os
import inspect
import uuid
from dotenv import load_dotenv
from azure.ai.evaluation import evaluate
from azure.ai.projects import AIProjectClient
import logging
from azure.identity import DefaultAzureCredential

def get_logger(name: str):
    level = os.environ.get("LOG_LEVEL", "INFO").upper()
    logging.basicConfig(level=getattr(logging, level, logging.INFO))
    return logging.getLogger(name)

logger = get_logger(__name__)

# Reduce verbosity of Azure SDK logs by default. Honor AZURE_SDK_LOG_LEVEL or fall back to LOG_LEVEL or WARNING.
azure_sdk_level = os.environ.get("AZURE_SDK_LOG_LEVEL") or os.environ.get("LOG_LEVEL", "WARNING")
try:
    azure_level_value = getattr(logging, azure_sdk_level.upper(), logging.WARNING)
except Exception:
    azure_level_value = logging.WARNING
# Apply to top-level azure logger and the HTTP logging policy used by Azure SDK
logging.getLogger("azure").setLevel(azure_level_value)
logging.getLogger("azure.core.pipeline.policies.http_logging_policy").setLevel(azure_level_value)

load_dotenv(override=True)

def should_pass_config(factory_func):
    """Returns True if the function accepts at least one argument (i.e., config)."""
    sig = inspect.signature(factory_func)
    return any(
        param.default == inspect.Parameter.empty
        and param.kind in (inspect.Parameter.POSITIONAL_OR_KEYWORD, inspect.Parameter.KEYWORD_ONLY)
        for param in sig.parameters.values()
    )

def setup_evaluation(config, EvaluatorFactory, azure_ai_project=None, credential=None):
    """Setup the evaluation based on the provided configuration."""
    model_config = {
        "azure_endpoint": os.environ.get("EVAL_AZURE_OPENAI_ENDPOINT"),
        "azure_deployment": os.environ.get("EVAL_AZURE_OPENAI_MODEL"),
        "api_version": os.environ.get("EVAL_AZURE_OPENAI_VERSION"),
    }
    column_mapping = config.get("column_mapping", {})
    evaluators = {}
    evaluator_config = {}

    for name, factory_name in config.get("evaluators", {}).items():
        factory_func = EvaluatorFactory.get_evaluator_factory(factory_name)
        # Config used at eval time
        specific_config = config.get("evaluator_config", {}).get(name, {})
        resolved_config = {
            k: (dict(column_mapping) if v == "use_column_mapping" else v)
            for k, v in specific_config.items()
        }
        # Instantiate evaluator with only what's needed
        sig = inspect.signature(factory_func)
        
        # Check what parameters the evaluator factory function accepts
        if "azure_ai_project" in sig.parameters and "credential" in sig.parameters and "model_config" in sig.parameters:
            evaluator_instance = factory_func(model_config=model_config, azure_ai_project=azure_ai_project, credential=credential)
        elif "azure_ai_project" in sig.parameters and "credential" in sig.parameters:
            evaluator_instance = factory_func(azure_ai_project=azure_ai_project, credential=credential)
        elif "azure_ai_project" in sig.parameters and "model_config" in sig.parameters:
            evaluator_instance = factory_func(model_config=model_config, azure_ai_project=azure_ai_project)
        elif "credential" in sig.parameters and "model_config" in sig.parameters:
            evaluator_instance = factory_func(model_config=model_config, credential=credential)
        elif "azure_ai_project" in sig.parameters:
            evaluator_instance = factory_func(azure_ai_project=azure_ai_project)
        elif "credential" in sig.parameters:
            evaluator_instance = factory_func(credential=credential)
        elif "model_config" in sig.parameters:
            evaluator_instance = factory_func(model_config=model_config)
        elif should_pass_config(factory_func):
            evaluator_instance = factory_func(resolved_config)
        else:
            evaluator_instance = factory_func()

        evaluators[name] = evaluator_instance
        evaluator_config[name] = resolved_config  # this gets passed to evaluate()
    return evaluators, evaluator_config

def execute_eval(name, data_path, output_path, eval_config, EvaluatorFactory):
    """
    Evaluate the model using the given data and column mapping.
    """
    run_local = eval_config.get("run_local", False)
    
    # Azure project setup is only required when not running locally
    if not run_local:
        project_endpoint = os.environ.get("EVAL_AZURE_FOUNDRY_PROJECT_ENDPOINT")
        if not project_endpoint:
            logger.error("[EVALUATION][CUSTOM EVAL] - Environment variable 'EVAL_AZURE_FOUNDRY_PROJECT_ENDPOINT' is not set.")
            raise KeyError("Environment variable 'EVAL_AZURE_FOUNDRY_PROJECT_ENDPOINT' is not set. Please set it before running the evaluation.")

        # Resolve Azure AI project identifiers from environment (support multiple variable names) or parse connection string
        sub = os.environ.get("AZURE_SUBSCRIPTION_ID") or os.environ.get("EVAL_AZURE_SUBSCRIPTION_ID")
        rg = os.environ.get("AZURE_RESOURCE_GROUP_NAME") or os.environ.get("EVAL_AZURE_RESOURCE_GROUP_NAME")
        pname = os.environ.get("AZURE_PROJECT_NAME") or os.environ.get("EVAL_AZURE_PROJECT_NAME")

        # Fallback: parse EVAL_AZURE_FOUNDRY_CONNECTION_STRING which may be: connection_string;subscription_id;resource_group;project_name
        conn = os.environ.get("EVAL_AZURE_FOUNDRY_CONNECTION_STRING")
        if conn and (not sub or not rg or not pname):
            parts = conn.split(";")
            if len(parts) >= 4:
                sub = sub or parts[1]
                rg = rg or parts[2]
                pname = pname or parts[3]

        if not sub or not rg or not pname:
            logger.error("[EVALUATION][CUSTOM EVAL] - Missing Azure AI project identifiers. Set AZURE_SUBSCRIPTION_ID, AZURE_RESOURCE_GROUP_NAME and AZURE_PROJECT_NAME or provide them in EVAL_AZURE_FOUNDRY_CONNECTION_STRING.")
            raise KeyError("Azure AI project identifiers are not set (subscription_id/resource_group_name/project_name).")

        credential = DefaultAzureCredential()
        project = AIProjectClient(endpoint=project_endpoint, credential=credential)
        evaluators, evaluator_config = setup_evaluation(eval_config, EvaluatorFactory, azure_ai_project=project, credential=credential)
    else:
        # Running locally - no Azure project setup required
        logger.info("[EVALUATION][LOCAL] - Running evaluation locally without Azure AI project.")
        evaluators, evaluator_config = setup_evaluation(eval_config, EvaluatorFactory)

    final_evaluators = {name: func for name, func in evaluators.items()}
    final_evaluator_config = {name: cfg for name, cfg in evaluator_config.items()}
    logger.info("[EVALUATION][CUSTOM EVAL] - Evaluators: %s", final_evaluators)
    logger.info("[EVALUATION][CUSTOM EVAL] - Evaluator Config: %s", final_evaluator_config)
    uid_name = name+ '_'+ str(uuid.uuid4())[:8]  # Append a short UUID to the evaluation name


    # Evaluate the data using the coverage evaluator
    eval_kwargs = {
        "data": data_path,
        "evaluation_name": uid_name,
        "evaluators": final_evaluators,
        "evaluator_config": final_evaluator_config,
        "output_path": output_path,
    }
    if not run_local:
        azure_ai_project = {
            "subscription_id": str(sub),
            "resource_group_name": str(rg),
            "project_name": str(pname),
        }
        eval_kwargs["azure_ai_project"] = azure_ai_project

    result = evaluate(**eval_kwargs)
    return result
