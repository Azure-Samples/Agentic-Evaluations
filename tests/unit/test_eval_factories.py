"""Unit tests for eval_factory modules across all evaluation samples."""

import pytest

# ---------------------------------------------------------------------------
# Agentic Evaluation - EvaluatorFactory
# ---------------------------------------------------------------------------

class TestAgenticEvaluationFactory:
    def test_get_relevance_evaluator(self):
        from src.evaluations.offline.agentic_evaluation.eval_factory import \
            EvaluatorFactory

        result = EvaluatorFactory.get_evaluator_factory("relevance_evaluator")
        assert result is not None
        assert "Relevance" in result.__name__

    def test_get_custom_agents_evaluator(self):
        from src.evaluations.offline.agentic_evaluation.eval_factory import \
            EvaluatorFactory

        result = EvaluatorFactory.get_evaluator_factory("custom_agents_invoked_evaluator")
        assert result is not None
        assert result.__name__ == "EvaluateAgentsInvoked"

    def test_get_task_adherence_evaluator(self):
        from src.evaluations.offline.agentic_evaluation.eval_factory import \
            EvaluatorFactory

        result = EvaluatorFactory.get_evaluator_factory("task_adherence_evaluator")
        assert result is not None
        assert "TaskAdherence" in result.__name__

    def test_get_tool_call_accuracy_evaluator(self):
        from src.evaluations.offline.agentic_evaluation.eval_factory import \
            EvaluatorFactory

        result = EvaluatorFactory.get_evaluator_factory("tool_call_accuracy_evaluator")
        assert result is not None
        assert "ToolCallAccuracy" in result.__name__

    def test_invalid_evaluator_raises(self):
        from src.evaluations.offline.agentic_evaluation.eval_factory import \
            EvaluatorFactory

        with pytest.raises(ValueError, match="not found"):
            EvaluatorFactory.get_evaluator_factory("nonexistent_evaluator")

    def test_all_registered_evaluators_are_callable(self):
        from src.evaluations.offline.agentic_evaluation.eval_factory import \
            EvaluatorFactory

        for name in EvaluatorFactory.EVALUATOR_FACTORIES:
            result = EvaluatorFactory.get_evaluator_factory(name)
            assert callable(result), f"{name} factory is not callable"


# ---------------------------------------------------------------------------
# AI Judge Evaluation Custom - EvaluatorFactory
# ---------------------------------------------------------------------------

class TestAiJudgeEvaluationFactory:
    def test_get_custom_coherence(self):
        from src.evaluations.offline.ai_judge_evaluation_custom.eval_factory import \
            EvaluatorFactory

        result = EvaluatorFactory.get_evaluator_factory("custom_coherence_evaluator")
        assert result.__name__ == "CoherenceEvaluatorCustom"

    def test_get_custom_relevance(self):
        from src.evaluations.offline.ai_judge_evaluation_custom.eval_factory import \
            EvaluatorFactory

        result = EvaluatorFactory.get_evaluator_factory("custom_relevance_evaluator")
        assert result.__name__ == "RelevanceEvaluatorCustom"

    def test_get_custom_fluency(self):
        from src.evaluations.offline.ai_judge_evaluation_custom.eval_factory import \
            EvaluatorFactory

        result = EvaluatorFactory.get_evaluator_factory("custom_fluency_evaluator")
        assert result.__name__ == "FluencyEvaluatorCustom"

    def test_get_custom_similarity(self):
        from src.evaluations.offline.ai_judge_evaluation_custom.eval_factory import \
            EvaluatorFactory

        result = EvaluatorFactory.get_evaluator_factory("custom_similarity_evaluator")
        assert result.__name__ == "SimilarityEvaluatorCustom"

    def test_get_builtin_relevance(self):
        from src.evaluations.offline.ai_judge_evaluation_custom.eval_factory import \
            EvaluatorFactory

        result = EvaluatorFactory.get_evaluator_factory("relevance_evaluator")
        assert "Relevance" in result.__name__

    def test_get_builtin_coherence(self):
        from src.evaluations.offline.ai_judge_evaluation_custom.eval_factory import \
            EvaluatorFactory

        result = EvaluatorFactory.get_evaluator_factory("coherence_evaluator")
        assert "Coherence" in result.__name__

    def test_invalid_evaluator_raises(self):
        from src.evaluations.offline.ai_judge_evaluation_custom.eval_factory import \
            EvaluatorFactory

        with pytest.raises(ValueError, match="not found"):
            EvaluatorFactory.get_evaluator_factory("invalid_evaluator")

    def test_all_registered_evaluators_are_callable(self):
        from src.evaluations.offline.ai_judge_evaluation_custom.eval_factory import \
            EvaluatorFactory

        for name in EvaluatorFactory.EVALUATOR_FACTORIES:
            result = EvaluatorFactory.get_evaluator_factory(name)
            assert callable(result), f"{name} factory is not callable"


# ---------------------------------------------------------------------------
# Pipeline Experiment Evaluation - EvaluatorFactory
# ---------------------------------------------------------------------------

class TestPipelineExperimentFactory:
    def test_get_relevance(self):
        from src.evaluations.offline.pipeline_experiment_evaluation.eval_factory import \
            EvaluatorFactory

        result = EvaluatorFactory.get_evaluator_factory("relevance_evaluator")
        assert "Relevance" in result.__name__

    def test_get_task_adherence(self):
        from src.evaluations.offline.pipeline_experiment_evaluation.eval_factory import \
            EvaluatorFactory

        result = EvaluatorFactory.get_evaluator_factory("task_adherence_evaluator")
        assert "TaskAdherence" in result.__name__

    def test_get_tool_call_accuracy(self):
        from src.evaluations.offline.pipeline_experiment_evaluation.eval_factory import \
            EvaluatorFactory

        result = EvaluatorFactory.get_evaluator_factory("tool_call_accuracy_evaluator")
        assert "ToolCallAccuracy" in result.__name__

    def test_invalid_raises(self):
        from src.evaluations.offline.pipeline_experiment_evaluation.eval_factory import \
            EvaluatorFactory

        with pytest.raises(ValueError, match="not found"):
            EvaluatorFactory.get_evaluator_factory("does_not_exist")


# ---------------------------------------------------------------------------
# Pipeline Multi-Agent Evaluation - EvaluatorFactory
# ---------------------------------------------------------------------------

class TestPipelineMultiAgentFactory:
    def test_get_relevance(self):
        from src.evaluations.offline.pipeline_multi_agent_evaluation.eval_factory import \
            EvaluatorFactory

        result = EvaluatorFactory.get_evaluator_factory("relevance_evaluator")
        assert "Relevance" in result.__name__

    def test_get_task_adherence(self):
        from src.evaluations.offline.pipeline_multi_agent_evaluation.eval_factory import \
            EvaluatorFactory

        result = EvaluatorFactory.get_evaluator_factory("task_adherence_evaluator")
        assert "TaskAdherence" in result.__name__

    def test_get_agents_invoked(self):
        from src.evaluations.offline.pipeline_multi_agent_evaluation.eval_factory import \
            EvaluatorFactory

        result = EvaluatorFactory.get_evaluator_factory("evaluate_agents_invoked")
        assert result.__name__ == "EvaluateAgentsInvoked"

    def test_get_custom_agents_invoked(self):
        from src.evaluations.offline.pipeline_multi_agent_evaluation.eval_factory import \
            EvaluatorFactory

        result = EvaluatorFactory.get_evaluator_factory("custom_agents_invoked_accuracy_eval")
        assert result.__name__ == "EvaluateAgentsInvoked"

    def test_invalid_raises(self):
        from src.evaluations.offline.pipeline_multi_agent_evaluation.eval_factory import \
            EvaluatorFactory

        with pytest.raises(ValueError, match="not found"):
            EvaluatorFactory.get_evaluator_factory("bogus")


# ---------------------------------------------------------------------------
# Pipeline Multi-Tool Agent Evaluation - EvaluatorFactory
# ---------------------------------------------------------------------------

class TestPipelineMultiToolFactory:
    def test_get_relevance(self):
        from src.evaluations.offline.pipeline_multi_tool_agent_evaluation.eval_factory import \
            EvaluatorFactory

        result = EvaluatorFactory.get_evaluator_factory("relevance_evaluator")
        assert "Relevance" in result.__name__

    def test_get_task_adherence(self):
        from src.evaluations.offline.pipeline_multi_tool_agent_evaluation.eval_factory import \
            EvaluatorFactory

        result = EvaluatorFactory.get_evaluator_factory("task_adherence_evaluator")
        assert "TaskAdherence" in result.__name__

    def test_get_tool_call_accuracy(self):
        from src.evaluations.offline.pipeline_multi_tool_agent_evaluation.eval_factory import \
            EvaluatorFactory

        result = EvaluatorFactory.get_evaluator_factory("tool_call_accuracy_evaluator")
        assert "ToolCallAccuracy" in result.__name__

    def test_invalid_raises(self):
        from src.evaluations.offline.pipeline_multi_tool_agent_evaluation.eval_factory import \
            EvaluatorFactory

        with pytest.raises(ValueError, match="not found"):
            EvaluatorFactory.get_evaluator_factory("unknown")


# ---------------------------------------------------------------------------
# RAG Evaluation Foundry - EvaluatorFactory
# ---------------------------------------------------------------------------

class TestRagEvaluationFoundryFactory:
    def test_get_relevance(self):
        from src.evaluations.offline.rag_evaluation_foundry.eval_factory import \
            EvaluatorFactory

        result = EvaluatorFactory.get_evaluator_factory("relevance_evaluator")
        assert "Relevance" in result.__name__

    def test_invalid_raises(self):
        from src.evaluations.offline.rag_evaluation_foundry.eval_factory import \
            EvaluatorFactory

        with pytest.raises(ValueError, match="not found"):
            EvaluatorFactory.get_evaluator_factory("missing")

    def test_only_has_relevance(self):
        from src.evaluations.offline.rag_evaluation_foundry.eval_factory import \
            EvaluatorFactory

        assert len(EvaluatorFactory.EVALUATOR_FACTORIES) == 1
        assert "relevance_evaluator" in EvaluatorFactory.EVALUATOR_FACTORIES
