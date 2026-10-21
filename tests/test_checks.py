"""Unit tests for Member 3's writing_assessment checks (UC-02) and committee workflow (UC-07)."""

from __future__ import annotations

from typing import Any

from agent.core.committee import (
    compute_divergence,
    run_committee_assessment,
    validate_moderator_decision,
)
from skills.writing_assessment.checks import (
    DEFAULT_DISCLAIMER,
    WritingAssessment,
    compute_ielts_overall_band,
    repair_evidence_offsets,
    validate_writing_assessment,
)

SAMPLE_ESSAY = (
    "Some people think universities should only teach job skills. "
    "On the one hand, universities prepare students for jobs. "
    "Knowledge is important because knowledge helps people get knowledge. "
    "Although employers want practical skills, academic theory remains essential. "
    "In conclusion, both views have merits."
)

RETRIEVED_REFS = {
    "task2_task_response_band_5",
    "task2_task_response_band_6",
    "task2_coherence_and_cohesion_band_6",
    "task2_lexical_resource_band_5",
    "task2_grammatical_range_and_accuracy_band_6",
}


def _make_valid_payload() -> dict[str, Any]:
    q1 = "In conclusion, both views have merits."
    q2 = "On the one hand, universities prepare students for jobs."
    q3 = "Knowledge is important because knowledge helps people get knowledge."
    q4 = "Although employers want practical skills, academic theory remains essential."

    return {
        "task_type": "task2",
        "word_count": 210,
        "criteria": [
            {
                "criterion": "task_response",
                "band": 5.5,
                "evidence": [
                    {
                        "quote": q1,
                        "start_char": SAMPLE_ESSAY.index(q1),
                        "end_char": SAMPLE_ESSAY.index(q1) + len(q1),
                    }
                ],
                "descriptor_refs": ["task2_task_response_band_5"],
                "comment": "Conclusion is too brief and essay is under 250 words.",
            },
            {
                "criterion": "coherence_and_cohesion",
                "band": 6.0,
                "evidence": [
                    {
                        "quote": q2,
                        "start_char": SAMPLE_ESSAY.index(q2),
                        "end_char": SAMPLE_ESSAY.index(q2) + len(q2),
                    }
                ],
                "descriptor_refs": ["task2_coherence_and_cohesion_band_6"],
                "comment": "Clear progression with basic cohesive devices.",
            },
            {
                "criterion": "lexical_resource",
                "band": 5.5,
                "evidence": [
                    {
                        "quote": q3,
                        "start_char": SAMPLE_ESSAY.index(q3),
                        "end_char": SAMPLE_ESSAY.index(q3) + len(q3),
                    }
                ],
                "descriptor_refs": ["task2_lexical_resource_band_5"],
                "comment": "Noticeable repetition of the word knowledge.",
            },
            {
                "criterion": "grammatical_range_and_accuracy",
                "band": 6.0,
                "evidence": [
                    {
                        "quote": q4,
                        "start_char": SAMPLE_ESSAY.index(q4),
                        "end_char": SAMPLE_ESSAY.index(q4) + len(q4),
                    }
                ],
                "descriptor_refs": ["task2_grammatical_range_and_accuracy_band_6"],
                "comment": "Uses subordinate clauses accurately.",
            },
        ],
        "overall_band": 6.0,
        "corrections": [
            {
                "original": q3,
                "suggestion": "Theoretical knowledge is vital for intellectual growth.",
                "reason": "Avoids repeating 'knowledge' three times in one sentence.",
                "category": "lexis",
            }
        ],
        "flags": ["under_length"],
        "disclaimer": DEFAULT_DISCLAIMER,
    }


def test_ielts_overall_band_rounding() -> None:
    assert compute_ielts_overall_band([6.0, 6.0, 6.5, 6.5]) == 6.5  # 6.25 -> 6.5
    assert compute_ielts_overall_band([6.0, 6.5, 6.5, 6.5]) == 6.5  # 6.375 -> 6.5
    assert compute_ielts_overall_band([6.5, 6.5, 7.0, 7.0]) == 7.0  # 6.75 -> 7.0
    assert compute_ielts_overall_band([6.0, 6.0, 6.0, 6.5]) == 6.0  # 6.125 -> 6.0


def test_valid_writing_assessment_passes() -> None:
    payload = _make_valid_payload()
    res = validate_writing_assessment(
        payload,
        essay_text=SAMPLE_ESSAY,
        expected_task_type="task2",
        expected_word_count=210,
        retrieved_descriptor_ids=RETRIEVED_REFS,
    )
    assert res.passed is True
    assert res.errors == []
    assert res.assessment is not None
    assert res.assessment.overall_band == 6.0


def test_rejects_fabricated_quote_and_bad_offsets() -> None:
    payload = _make_valid_payload()
    payload["criteria"][0]["evidence"][0]["quote"] = "This sentence is not in the essay."
    res = validate_writing_assessment(payload, essay_text=SAMPLE_ESSAY)
    assert res.passed is False
    assert any("not found verbatim" in e for e in res.errors)

    # Test wrong character offset for valid quote, then auto-repair
    payload2 = _make_valid_payload()
    payload2["criteria"][0]["evidence"][0]["start_char"] = 0
    payload2["criteria"][0]["evidence"][0]["end_char"] = 10
    res2 = validate_writing_assessment(payload2, essay_text=SAMPLE_ESSAY)
    assert res2.passed is False
    assert any("char offset" in e for e in res2.errors)

    repaired = repair_evidence_offsets(payload2, SAMPLE_ESSAY)
    res_repaired = validate_writing_assessment(repaired, essay_text=SAMPLE_ESSAY)
    assert res_repaired.passed is True


def test_rejects_wrong_task_part_descriptor_and_unretrieved_ref() -> None:
    payload = _make_valid_payload()
    payload["criteria"][0]["descriptor_refs"] = ["task1_task_achievement_band_6"]
    res = validate_writing_assessment(
        payload,
        essay_text=SAMPLE_ESSAY,
        retrieved_descriptor_ids=RETRIEVED_REFS,
    )
    assert res.passed is False
    assert any("task1" in e for e in res.errors)
    assert any("unretrieved" in e for e in res.errors)


def test_rejects_missing_under_length_and_off_topic_high_band() -> None:
    payload = _make_valid_payload()
    payload["flags"] = ["off_topic"]  # missing under_length AND task_response is 5.5 > 5.0
    res = validate_writing_assessment(payload, essay_text=SAMPLE_ESSAY)
    assert res.passed is False
    assert any("under_length" in e for e in res.errors)
    assert any("<= 5.0" in e for e in res.errors)


def test_committee_consensus_vs_moderator_trigger() -> None:
    payload_a = _make_valid_payload()
    payload_b = _make_valid_payload()

    ass_a = WritingAssessment.model_validate(payload_a)
    ass_b = WritingAssessment.model_validate(payload_b)

    # Case 1: Consensus (0.0 diff) -> Moderator NOT called
    res_consensus = run_committee_assessment(
        task_type="task2",
        topic="Universities topic",
        essay_text=SAMPLE_ESSAY,
        examiner_a_fn=lambda _t, _p, _e: ass_a,
        examiner_b_fn=lambda _t, _p, _e: ass_b,
    )
    assert res_consensus.moderator_called is False
    assert res_consensus.final_assessment.overall_band == 6.0

    # Case 2: Criterion divergence >= 1.0 (LR 5.5 vs 7.0) -> Moderator MUST be called
    payload_b_div = _make_valid_payload()
    payload_b_div["criteria"][2]["band"] = 7.0
    payload_b_div["overall_band"] = compute_ielts_overall_band([5.5, 6.0, 7.0, 6.0])
    ass_b_div = WritingAssessment.model_validate(payload_b_div)

    div_metrics = compute_divergence(ass_a, ass_b_div)
    assert div_metrics.trigger_moderator is True
    assert "lexical_resource" in div_metrics.divergent_criteria

    res_mod = run_committee_assessment(
        task_type="task2",
        topic="Universities topic",
        essay_text=SAMPLE_ESSAY,
        examiner_a_fn=lambda _t, _p, _e: ass_a,
        examiner_b_fn=lambda _t, _p, _e: ass_b_div,
    )
    assert res_mod.moderator_called is True
    assert res_mod.moderator_decision is not None
    assert validate_moderator_decision(ass_a, ass_b_div, res_mod.moderator_decision) == []


if __name__ == "__main__":
    test_ielts_overall_band_rounding()
    test_valid_writing_assessment_passes()
    test_rejects_fabricated_quote_and_bad_offsets()
    test_rejects_wrong_task_part_descriptor_and_unretrieved_ref()
    test_rejects_missing_under_length_and_off_topic_high_band()
    test_committee_consensus_vs_moderator_trigger()
    print("All Member 3 unit tests passed successfully!")
