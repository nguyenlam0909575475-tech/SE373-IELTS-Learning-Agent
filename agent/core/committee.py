"""Dual-Examiner and Moderator Grading Committee (UC-07).

Owned by Member 3. Implements:
1. Independent execution of Examiner A and Examiner B with isolated contexts (Examiner B never
   receives Examiner A's output) and read-only scope.
2. Deterministic divergence detection: triggers Moderator if and only if
   `abs(overall_A - overall_B) > 0.5` OR `max(abs(crit_A - crit_B)) >= 1.0`.
3. Moderator resolution that cites evidence from at least one examiner, keeps the final score
   within `[min(A, B), max(A, B)]` unless justified, or escalates to teacher approval
   (`needs_teacher_review = True`) when examiners conflict on off-topic status.
4. Full coordination trace (`CommitteeAssessmentResult`) for observability and evaluation.
"""

from __future__ import annotations

from collections.abc import Callable

from pydantic import BaseModel, Field

from skills.writing_assessment.checks import (
    DEFAULT_DISCLAIMER,
    CriterionAssessment,
    WritingAssessment,
    compute_ielts_overall_band,
)


class DivergenceMetrics(BaseModel):
    overall_diff: float
    max_criterion_diff: float
    divergent_criteria: dict[str, float] = Field(default_factory=dict)
    off_topic_conflict: bool = False
    trigger_moderator: bool


class ModeratorDecision(BaseModel):
    final_assessment: WritingAssessment
    rationale: str = Field(..., min_length=10)
    cited_quotes: list[str] = Field(..., min_length=1)
    out_of_bounds_justification: str | None = None
    needs_teacher_review: bool = False


class CommitteeAssessmentResult(BaseModel):
    examiner_a: WritingAssessment
    examiner_b: WritingAssessment
    examiner_b_isolated: bool = True
    divergence: DivergenceMetrics
    moderator_called: bool
    moderator_decision: ModeratorDecision | None = None
    final_assessment: WritingAssessment
    needs_teacher_review: bool = False


ExaminerCallable = Callable[[str, str, str], WritingAssessment]
ModeratorCallable = Callable[[str, str, WritingAssessment, WritingAssessment], ModeratorDecision]


def compute_divergence(
    examiner_a: WritingAssessment,
    examiner_b: WritingAssessment,
) -> DivergenceMetrics:
    """Calculate overall and per-criterion divergence between Examiner A and Examiner B."""
    overall_diff = round(abs(examiner_a.overall_band - examiner_b.overall_band), 2)

    bands_a = {c.criterion: c.band for c in examiner_a.criteria}
    bands_b = {c.criterion: c.band for c in examiner_b.criteria}

    divergent_criteria: dict[str, float] = {}
    max_crit_diff = 0.0

    for crit_name, band_a in bands_a.items():
        if crit_name in bands_b:
            diff = round(abs(band_a - bands_b[crit_name]), 2)
            if diff > max_crit_diff:
                max_crit_diff = diff
            if diff >= 1.0:
                divergent_criteria[crit_name] = diff

    off_topic_a = "off_topic" in examiner_a.flags
    off_topic_b = "off_topic" in examiner_b.flags
    off_topic_conflict = off_topic_a != off_topic_b

    trigger_moderator = overall_diff > 0.5 or max_crit_diff >= 1.0 or off_topic_conflict

    return DivergenceMetrics(
        overall_diff=overall_diff,
        max_criterion_diff=max_crit_diff,
        divergent_criteria=divergent_criteria,
        off_topic_conflict=off_topic_conflict,
        trigger_moderator=trigger_moderator,
    )


def merge_consensus_assessments(
    examiner_a: WritingAssessment,
    examiner_b: WritingAssessment,
) -> WritingAssessment:
    """Combine two within-threshold assessments without calling the Moderator."""
    bands_b = {c.criterion: c for c in examiner_b.criteria}
    merged_criteria: list[CriterionAssessment] = []

    for crit_a in examiner_a.criteria:
        crit_b = bands_b.get(crit_a.criterion, crit_a)
        avg_crit = compute_ielts_overall_band([crit_a.band, crit_a.band, crit_b.band, crit_b.band])
        merged_criteria.append(
            CriterionAssessment(
                criterion=crit_a.criterion,
                band=avg_crit,
                evidence=crit_a.evidence,
                descriptor_refs=sorted(set(crit_a.descriptor_refs + crit_b.descriptor_refs)),
                comment=f"[Consensus A & B] {crit_a.comment}",
            )
        )

    overall = compute_ielts_overall_band([c.band for c in merged_criteria])
    combined_flags = list(dict.fromkeys(examiner_a.flags + examiner_b.flags))

    return WritingAssessment(
        task_type=examiner_a.task_type,
        word_count=examiner_a.word_count,
        criteria=merged_criteria,
        overall_band=overall,
        corrections=examiner_a.corrections or examiner_b.corrections,
        flags=combined_flags,
        disclaimer=DEFAULT_DISCLAIMER,
    )


def default_moderator_reconcile(
    topic: str,
    essay_text: str,
    examiner_a: WritingAssessment,
    examiner_b: WritingAssessment,
) -> ModeratorDecision:
    """Deterministic fallback/baseline moderator that reconciles Examiner A and B using cited evidence."""
    del topic, essay_text
    off_topic_a = "off_topic" in examiner_a.flags
    off_topic_b = "off_topic" in examiner_b.flags
    needs_teacher = off_topic_a != off_topic_b

    bands_b = {c.criterion: c for c in examiner_b.criteria}
    reconciled_criteria: list[CriterionAssessment] = []
    cited_quotes: list[str] = []

    for crit_a in examiner_a.criteria:
        crit_b = bands_b.get(crit_a.criterion, crit_a)
        reconciled_band = compute_ielts_overall_band(
            [crit_a.band, crit_a.band, crit_b.band, crit_b.band]
        )
        chosen_evidence = (
            crit_a.evidence if len(crit_a.evidence) >= len(crit_b.evidence) else crit_b.evidence
        )
        if chosen_evidence:
            cited_quotes.append(chosen_evidence[0].quote)

        reconciled_criteria.append(
            CriterionAssessment(
                criterion=crit_a.criterion,
                band=reconciled_band,
                evidence=chosen_evidence,
                descriptor_refs=sorted(set(crit_a.descriptor_refs + crit_b.descriptor_refs)),
                comment=(
                    f"[Moderator Reconciled A({crit_a.band}) & B({crit_b.band})]: "
                    f"{crit_a.comment} | {crit_b.comment}"
                ),
            )
        )

    final_overall = compute_ielts_overall_band([c.band for c in reconciled_criteria])
    combined_flags = list(dict.fromkeys(examiner_a.flags + examiner_b.flags))

    final_assessment = WritingAssessment(
        task_type=examiner_a.task_type,
        word_count=examiner_a.word_count,
        criteria=reconciled_criteria,
        overall_band=final_overall,
        corrections=examiner_a.corrections + examiner_b.corrections,
        flags=combined_flags,
        disclaimer=DEFAULT_DISCLAIMER,
    )

    rationale = (
        f"Moderator reconciled Examiner A (Overall {examiner_a.overall_band}) and "
        f"Examiner B (Overall {examiner_b.overall_band}) into Final Band {final_overall} "
        f"based on verbatim evidence quotes: {cited_quotes[:2]}."
    )
    if needs_teacher:
        rationale += " Escalated to Teacher Review due to conflict on off_topic status."

    return ModeratorDecision(
        final_assessment=final_assessment,
        rationale=rationale,
        cited_quotes=cited_quotes,
        out_of_bounds_justification=None,
        needs_teacher_review=needs_teacher,
    )


def validate_moderator_decision(
    examiner_a: WritingAssessment,
    examiner_b: WritingAssessment,
    decision: ModeratorDecision,
) -> list[str]:
    """Verify UC-07 Acceptance Criterion #3 on Moderator output."""
    errors: list[str] = []

    low_bound = min(examiner_a.overall_band, examiner_b.overall_band)
    high_bound = max(examiner_a.overall_band, examiner_b.overall_band)
    final_band = decision.final_assessment.overall_band

    if not (low_bound <= final_band <= high_bound) and not decision.out_of_bounds_justification:
        errors.append(
            f"Moderator final overall_band ({final_band}) is outside Examiner A/B range "
            f"[{low_bound}, {high_bound}] without out_of_bounds_justification."
        )

    all_examiner_quotes = {ev.quote for c in examiner_a.criteria for ev in c.evidence} | {
        ev.quote for c in examiner_b.criteria for ev in c.evidence
    }

    if not any(q in all_examiner_quotes for q in decision.cited_quotes):
        errors.append(
            "Moderator decision must cite at least one evidence quote from Examiner A or Examiner B."
        )

    return errors


def run_committee_assessment(
    task_type: str,
    topic: str,
    essay_text: str,
    examiner_a_fn: ExaminerCallable,
    examiner_b_fn: ExaminerCallable,
    moderator_fn: ModeratorCallable = default_moderator_reconcile,
) -> CommitteeAssessmentResult:
    """Execute the full UC-07 Dual-Examiner + Conditional Moderator pipeline."""
    # Examiner A and Examiner B receive only (task_type, topic, essay_text) -> isolated inputs
    assessment_a = examiner_a_fn(task_type, topic, essay_text)
    assessment_b = examiner_b_fn(task_type, topic, essay_text)

    divergence = compute_divergence(assessment_a, assessment_b)

    if divergence.trigger_moderator:
        mod_decision = moderator_fn(topic, essay_text, assessment_a, assessment_b)
        return CommitteeAssessmentResult(
            examiner_a=assessment_a,
            examiner_b=assessment_b,
            examiner_b_isolated=True,
            divergence=divergence,
            moderator_called=True,
            moderator_decision=mod_decision,
            final_assessment=mod_decision.final_assessment,
            needs_teacher_review=mod_decision.needs_teacher_review,
        )

    merged = merge_consensus_assessments(assessment_a, assessment_b)
    return CommitteeAssessmentResult(
        examiner_a=assessment_a,
        examiner_b=assessment_b,
        examiner_b_isolated=True,
        divergence=divergence,
        moderator_called=False,
        moderator_decision=None,
        final_assessment=merged,
        needs_teacher_review=False,
    )
