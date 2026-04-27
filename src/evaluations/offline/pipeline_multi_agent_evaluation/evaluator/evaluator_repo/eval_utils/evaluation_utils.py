
def agent_invoked_accuracy(predicted, expected):
    """
    Evaluates the accuracy of agent invocation by comparing the predicted agents 
    with the expected agents. The order of agents does not matter.
    Args:
        predicted (list): A list of predicted agent names.
        expected (list): A list of expected agent names.
    Returns:
        bool: True if the predicted agents match the expected agents, False otherwise.
    """
    return set(predicted) == set(expected)

def calculate_match_percentage(expected, predicted):
    """
    Calculates the percentage of agents in the expected list that are present in the predicted list.
    Returns the percentage as a float.
    """
    if not expected:
        return 0.0  # Avoid division by zero if expected is empty

    expected_set = set(expected)
    predicted_set = set(predicted)
    match_count = len(expected_set.intersection(predicted_set))
    return (match_count / len(expected_set))

