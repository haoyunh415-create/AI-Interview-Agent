"""Tests for Evaluator agent — scoring logic and report formatting."""

from agents.evaluator import Evaluator


class TestShouldFollowup:
    def test_needs_followup_true(self):
        result = Evaluator.should_followup({"needs_followup": True})
        assert result is True

    def test_needs_followup_false(self):
        result = Evaluator.should_followup({"needs_followup": False})
        assert result is False

    def test_low_depth_triggers_followup(self):
        result = Evaluator.should_followup({"depth": 3, "correctness": 7})
        assert result is True

    def test_low_correctness_triggers_followup(self):
        result = Evaluator.should_followup({"depth": 7, "correctness": 3})
        assert result is True

    def test_high_scores_no_followup(self):
        result = Evaluator.should_followup({"depth": 8, "correctness": 8})
        assert result is False

    def test_both_low_triggers_followup(self):
        result = Evaluator.should_followup({"depth": 4, "correctness": 4})
        assert result is True

    def test_boundary_depth_5_no_followup(self):
        result = Evaluator.should_followup({"depth": 5, "correctness": 7})
        assert result is False

    def test_boundary_correctness_5_no_followup(self):
        result = Evaluator.should_followup({"depth": 7, "correctness": 5})
        assert result is False

    def test_non_dict_input(self):
        assert Evaluator.should_followup(None) is False
        assert Evaluator.should_followup("not a dict") is False


class TestFormatReport:
    def test_full_scores(self):
        report = Evaluator.format_report(
            {
                "correctness": 8,
                "logic": 7,
                "depth": 6,
                "expression": 9,
                "summary": "Good answer",
                "improvement": "Go deeper",
                "needs_followup": False,
            }
        )
        assert "正确性: 8" in report
        assert "逻辑: 7" in report
        assert "深度: 6" in report
        assert "表达: 9" in report
        assert "Good answer" in report
        assert "Go deeper" in report

    def test_report_with_followup(self):
        report = Evaluator.format_report(
            {
                "correctness": 5,
                "logic": 5,
                "depth": 5,
                "expression": 5,
                "summary": "OK",
                "improvement": "Study more",
                "needs_followup": True,
                "followup_reason": "Too shallow",
            }
        )
        assert "追问原因" in report
        assert "Too shallow" in report

    def test_report_without_followup(self):
        report = Evaluator.format_report(
            {
                "correctness": 8,
                "logic": 8,
                "depth": 8,
                "expression": 8,
                "summary": "Excellent",
                "improvement": "Keep going",
                "needs_followup": False,
            }
        )
        assert "追问原因" not in report

    def test_missing_keys_handled(self):
        report = Evaluator.format_report({})
        assert "?:" in report or "?" in report
        assert "无" in report

    def test_non_dict_input(self):
        report = Evaluator.format_report("error")
        assert report == "error"
