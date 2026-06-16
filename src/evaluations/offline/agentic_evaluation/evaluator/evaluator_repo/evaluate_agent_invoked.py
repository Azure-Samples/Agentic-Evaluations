from .eval_utils.evaluation_utils import agent_invoked_accuracy, compute_recall


class EvaluateAgentsInvoked:
    def __init__(self):
        pass

    def __call__(self, expected_agents_to_invoke, predicted_agents_to_invoke, turn_number, turn_type, **kwargs):
        expected = [expected_agent for expected_agent in expected_agents_to_invoke]
        predicted = [predicted_agent for predicted_agent in predicted_agents_to_invoke]
        recall_k = {f"recall@{k}" : compute_recall(expected, predicted, k) for k in range(1, 4)}
        extra = {
            "agents_invoke_accuracy": agent_invoked_accuracy(predicted, expected),
            "num_expected" : len(expected_agents_to_invoke),
            "num_predicted":len(predicted_agents_to_invoke), 
        }
        return dict(recall_k, **extra)
    

   