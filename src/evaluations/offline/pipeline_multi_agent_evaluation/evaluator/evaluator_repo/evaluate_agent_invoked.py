from .eval_utils.evaluation_utils import agent_invoked_accuracy, calculate_match_percentage

class EvaluateAgentsInvoked:
    def __init__(self):
        pass

    def __call__(self, expected_agents_to_invoke, predicted_agents_to_invoke, turn_number=None, turn_type=None, **kwargs):
        expected = [expected_agent for expected_agent in expected_agents_to_invoke]

        # Orchestrator is always invoked as a routing layer and is not part of task-agent ground truth.
        predicted = [
            predicted_agent
            for predicted_agent in predicted_agents_to_invoke
            if str(predicted_agent).strip().lower() != "orchestratoragent"
        ]

        exact_match = agent_invoked_accuracy(predicted, expected)

        extra = {
            # Numeric score for consistency with other evaluators.
            "agents_invoke_accuracy": 1.0 if exact_match else 0.0,
            "agents_invoke_match_percentage": calculate_match_percentage(expected, predicted),
            "agents_invoke_exact_match": exact_match,
        }
        return dict(**extra)
    

   