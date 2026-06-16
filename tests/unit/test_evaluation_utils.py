"""Unit tests for agent evaluation utility functions (evaluation_utils, agent_tools)."""

import pytest

from src.evaluations.offline.pipeline_multi_agent_evaluation.evaluator.evaluator_repo.eval_utils.evaluation_utils import (
    agent_invoked_accuracy,
    calculate_match_percentage,
)


# ---------------------------------------------------------------------------
# agent_invoked_accuracy
# ---------------------------------------------------------------------------

class TestAgentInvokedAccuracy:
    def test_exact_match(self):
        """Same agents in same order should return True."""
        assert agent_invoked_accuracy(["AgentA", "AgentB"], ["AgentA", "AgentB"]) is True

    def test_same_agents_different_order(self):
        """Same agents in different order should return True (set comparison)."""
        assert agent_invoked_accuracy(["AgentB", "AgentA"], ["AgentA", "AgentB"]) is True

    def test_missing_agent(self):
        """Missing expected agent should return False."""
        assert agent_invoked_accuracy(["AgentA"], ["AgentA", "AgentB"]) is False

    def test_extra_agent(self):
        """Extra predicted agent should return False."""
        assert agent_invoked_accuracy(["AgentA", "AgentB", "AgentC"], ["AgentA", "AgentB"]) is False

    def test_empty_both(self):
        """Both empty should return True."""
        assert agent_invoked_accuracy([], []) is True

    def test_empty_predicted(self):
        """Empty predicted with non-empty expected should return False."""
        assert agent_invoked_accuracy([], ["AgentA"]) is False

    def test_empty_expected(self):
        """Non-empty predicted with empty expected should return False."""
        assert agent_invoked_accuracy(["AgentA"], []) is False

    def test_single_agent_match(self):
        """Single agent match should return True."""
        assert agent_invoked_accuracy(["AgentA"], ["AgentA"]) is True

    def test_duplicate_agents(self):
        """Duplicate agents should be treated as set."""
        assert agent_invoked_accuracy(["AgentA", "AgentA"], ["AgentA"]) is True


# ---------------------------------------------------------------------------
# calculate_match_percentage
# ---------------------------------------------------------------------------

class TestCalculateMatchPercentage:
    def test_full_match(self):
        """All expected in predicted should return 1.0."""
        assert calculate_match_percentage(["A", "B"], ["A", "B"]) == 1.0

    def test_partial_match(self):
        """Half expected in predicted should return 0.5."""
        assert calculate_match_percentage(["A", "B"], ["A"]) == 0.5

    def test_no_match(self):
        """No overlap should return 0.0."""
        assert calculate_match_percentage(["A", "B"], ["C", "D"]) == 0.0

    def test_empty_expected(self):
        """Empty expected should return 0.0 (avoid division by zero)."""
        assert calculate_match_percentage([], ["A"]) == 0.0

    def test_empty_predicted(self):
        """Empty predicted should return 0.0."""
        assert calculate_match_percentage(["A", "B"], []) == 0.0

    def test_extra_predicted_agents(self):
        """Extra predicted agents don't affect match percentage."""
        assert calculate_match_percentage(["A"], ["A", "B", "C"]) == 1.0

    def test_three_of_four(self):
        """3 out of 4 expected should return 0.75."""
        assert calculate_match_percentage(["A", "B", "C", "D"], ["A", "B", "C"]) == 0.75


# ---------------------------------------------------------------------------
# EvaluateAgentsInvoked
# ---------------------------------------------------------------------------

class TestEvaluateAgentsInvoked:
    @pytest.fixture
    def evaluator(self):
        from src.evaluations.offline.pipeline_multi_agent_evaluation.evaluator.evaluator_repo.evaluate_agent_invoked import (
            EvaluateAgentsInvoked,
        )
        return EvaluateAgentsInvoked()

    def test_exact_match_returns_accuracy_1(self, evaluator):
        """Exact match should set accuracy to 1.0."""
        result = evaluator(
            expected_agents_to_invoke=["ACAgent", "TVAgent"],
            predicted_agents_to_invoke=["ACAgent", "TVAgent"],
        )
        assert result["agents_invoke_accuracy"] == 1.0
        assert result["agents_invoke_exact_match"] is True
        assert result["agents_invoke_match_percentage"] == 1.0

    def test_orchestrator_filtered(self, evaluator):
        """OrchestratorAgent should be filtered from predicted."""
        result = evaluator(
            expected_agents_to_invoke=["ACAgent"],
            predicted_agents_to_invoke=["OrchestratorAgent", "ACAgent"],
        )
        assert result["agents_invoke_accuracy"] == 1.0
        assert result["agents_invoke_exact_match"] is True

    def test_mismatch(self, evaluator):
        """Mismatch should set accuracy to 0.0."""
        result = evaluator(
            expected_agents_to_invoke=["ACAgent", "TVAgent"],
            predicted_agents_to_invoke=["DishwasherAgent"],
        )
        assert result["agents_invoke_accuracy"] == 0.0
        assert result["agents_invoke_exact_match"] is False

    def test_partial_match_percentage(self, evaluator):
        """Partial match percentage should be calculated."""
        result = evaluator(
            expected_agents_to_invoke=["ACAgent", "TVAgent"],
            predicted_agents_to_invoke=["ACAgent"],
        )
        assert result["agents_invoke_match_percentage"] == 0.5
        assert result["agents_invoke_exact_match"] is False
