"""Reject fabricated evidence/refs and contradictory tool-derived results."""

from copy import deepcopy
from enum import Enum
from types import SimpleNamespace

import pytest

from agent.tools.compute_tool import compute_band
from agent.tools.contracts import PlagiarismResult, SecurityResult
from skills.writing_assessment.validators import consistency_validator, quote_validator, refs_validator


def check_consistency(assessment, **changes):
    args = dict(word_count=31, overall_band=6.0, plagiarism=PlagiarismResult(False, 0.0),
                security=SecurityResult(False), off_topic=False)
    args.update(changes)
    return consistency_validator(assessment, **args)


def test_tv3_fixture_passes_all_checks(assessment, essay, chunks):
    assert quote_validator(assessment, essay) == []
    assert refs_validator(assessment, chunks) == []
    assert check_consistency(assessment) == []


def test_attribute_and_enum_inputs_are_supported(assessment, essay, chunks):
    class Task(str, Enum):
        TASK2 = "task2"

    def wrap(item):
        if isinstance(item, dict):
            return SimpleNamespace(**{key: wrap(val) for key, val in item.items()})
        if isinstance(item, list):
            return [wrap(val) for val in item]
        return item

    assessment["task_type"] = Task.TASK2
    obj = wrap(assessment)
    assert quote_validator(obj, essay) == []
    assert refs_validator(obj, wrap(chunks)) == []
    assert check_consistency(obj) == []


@pytest.mark.parametrize("span", [
    {"quote": "Fabricated sentence", "start_char": 0, "end_char": 19},
    {"quote": "Free community libraries", "start_char": 1, "end_char": 25},
    {"quote": "Free community libraries", "start_char": -1, "end_char": 24},
    {"quote": "Free community libraries", "start_char": 0, "end_char": 9999},
    {"quote": "", "start_char": 0, "end_char": 0},
    {"quote": " ", "start_char": 4, "end_char": 5},
    {"quote": "Free", "start_char": False, "end_char": 4},
    {"quote": "Free", "start_char": 0.0, "end_char": 4},
    {"quote": "Free", "start_char": 4, "end_char": 0},
    {},
])
def test_invalid_quote_or_offset_is_caught(assessment, essay, span):
    assessment["criteria"][0]["evidence"] = [span]
    issues = quote_validator(assessment, essay)
    assert [(i.code, i.criterion) for i in issues] == [("evidence_invalid", "task_response")]


def test_matching_another_occurrence_is_not_enough(assessment):
    assessment["criteria"][0]["evidence"] = [{"quote": "word", "start_char": 1, "end_char": 5}]
    assert quote_validator(assessment, "word word")[0].code == "evidence_invalid"


def test_unicode_offsets_use_code_points(assessment):
    for item in assessment["criteria"]:
        item["evidence"] = [{"quote": "café", "start_char": 2, "end_char": 6}]
    assert quote_validator(assessment, "😀 café") == []


@pytest.mark.parametrize("missing", [None, []])
def test_empty_evidence(assessment, essay, missing):
    assessment["criteria"][0]["evidence"] = missing
    assert quote_validator(assessment, essay)[0].code == "evidence_missing"


@pytest.mark.parametrize("field,new", [
    ("task_type", "other"), ("criteria", []), ("criteria", [{}] * 4),
])
def test_invalid_consumed_schema(assessment, essay, chunks, field, new):
    assessment[field] = new
    assert quote_validator(assessment, essay)[0].code == "schema_invalid"
    assert refs_validator(assessment, chunks)[0].code == "schema_invalid"
    assert check_consistency(assessment)[0].code == "schema_invalid"


@pytest.mark.parametrize("refs", [[], ["INVENTED"], ["MOCK_task2_lexical_resource_6"],
                                  ["MOCK_task2_task_response_6"] * 2, [None], "not a list"])
def test_invalid_descriptor_refs(assessment, chunks, refs):
    assessment["criteria"][0]["descriptor_refs"] = refs
    issues = refs_validator(assessment, chunks)
    assert [(i.code, i.criterion) for i in issues] == [("refs_invalid", "task_response")]


@pytest.mark.parametrize("field,new", [
    ("test_part", "task1"), ("criterion", "task_achievement"),
    ("band", float("nan")), ("version", "bad/version"),
    ("chunk_id", "bad/id"), ("source_url", ""), ("text", ""),
])
def test_wrong_or_malformed_retrieval_is_rejected(assessment, chunks, field, new):
    chunks[0][field] = new
    assert refs_validator(assessment, chunks)[0].code == "refs_invalid"


def test_no_or_duplicate_chunks_are_rejected(assessment, chunks):
    assert refs_validator(assessment, [])[0].code == "refs_invalid"
    assert refs_validator(assessment, chunks + [deepcopy(chunks[0])])[0].code == "refs_invalid"


@pytest.mark.parametrize(("task", "count", "under"), [
    ("task1", 149, True), ("task1", 150, False),
    ("task2", 249, True), ("task2", 250, False), ("task2", 0, True),
])
def test_length_boundaries_do_not_deduct_band(assessment, task, count, under):
    assessment["task_type"] = task
    assessment["criteria"][0]["criterion"] = "task_achievement" if task == "task1" else "task_response"
    assessment["word_count"] = count
    assessment["flags"] = ["under_length"] if under else []
    assert check_consistency(assessment, word_count=count) == []
    assessment["flags"] = [] if under else ["under_length"]
    assert check_consistency(assessment, word_count=count)[0].code == "consistency_error"


@pytest.mark.parametrize("task", ["task1", "task2"])
@pytest.mark.parametrize(("band", "valid"), [(4, True), (5, True), (5.5, False)])
def test_off_topic_cap_only_applies_to_task_criterion(assessment, task, band, valid):
    assessment["task_type"] = task
    assessment["criteria"][0].update(criterion="task_achievement" if task == "task1" else "task_response", band=band)
    assessment["overall_band"] = compute_band([band, 6, 6, 6])
    assessment["flags"].append("off_topic")
    issues = check_consistency(assessment, off_topic=True, overall_band=assessment["overall_band"])
    assert (issues == []) is valid


@pytest.mark.parametrize(("field", "new"), [
    ("word_count", 30), ("overall_band", 6.5), ("flags", []),
    ("flags", ["under_length", "off_topic"]), ("flags", ["under_length", "unexpected"]),
    ("flags", ["under_length", "under_length"]),
])
def test_contradictory_output_fields(assessment, field, new):
    assessment[field] = new
    assert check_consistency(assessment)[0].code == "consistency_error"


def test_recomputes_mean_instead_of_trusting_matching_wrong_totals(assessment):
    assessment["overall_band"] = 7
    assert check_consistency(assessment, overall_band=7)[0].code == "consistency_error"
    assessment["criteria"][3]["band"] = 7
    assessment["overall_band"] = 6.5
    assert check_consistency(assessment, overall_band=6.5) == []


def test_tool_and_security_flags_cannot_be_suppressed(assessment):
    args = dict(plagiarism=PlagiarismResult(True, 1), security=SecurityResult(True))
    assert check_consistency(assessment, **args)[0].code == "consistency_error"
    assessment["flags"] += ["possible_plagiarism", "injection_detected"]
    assert check_consistency(assessment, **args) == []


@pytest.mark.parametrize("bad", [True, float("nan"), 10, "6"])
def test_invalid_bands_are_schema_errors(assessment, bad):
    assessment["criteria"][0]["band"] = bad
    assert check_consistency(assessment)[0].code == "schema_invalid"
