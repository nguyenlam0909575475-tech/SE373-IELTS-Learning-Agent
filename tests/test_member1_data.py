import copy
import json
from pathlib import Path

import pytest

from scripts.check_member1_data import check_member1_data, validate_basic_cases

ROOT = Path(__file__).resolve().parents[1]


def basic_cases():
    return json.loads((ROOT / "evals/data/5_basic_cases.json").read_text(encoding="utf-8"))


def test_full_member1_package():
    report = check_member1_data()
    assert report["descriptor_chunks"] == 72
    assert report["corpus_documents"] == 1800
    assert report["benchmark_documents"] == 84
    assert report["basic_cases"] == 6


def test_basic_cases_use_member5_id():
    rows = basic_cases()
    assert len({row["id"] for row in rows}) == 6
    assert all("case_id" not in row for row in rows)


def test_basic_cases_do_not_acquire_invented_score_labels():
    rows = basic_cases()
    rows[0]["scores"] = {"overall_band": 6}
    with pytest.raises(ValueError, match="scores must remain null"):
        validate_basic_cases(rows)


def test_short_case_must_explicitly_require_under_length():
    rows = basic_cases()
    rows[2]["expected"].pop("required_flags")
    with pytest.raises(ValueError, match="under_length"):
        validate_basic_cases(rows)


def test_basic_cases_require_public_sources_and_real_images():
    for field, value in [
        ("source", "file:///private/source.pdf"),
        ("material", {"path": "evals/materials/missing.png", "url": "https://example.org/chart.png"}),
    ]:
        rows = copy.deepcopy(basic_cases())
        rows[0][field] = value
        with pytest.raises(ValueError):
            validate_basic_cases(rows)


def test_word_count_contract_matches_member4():
    from agent.tools.compute_tool import WORD_PATTERN
    from scripts.build_ielts_plagiarism_corpus import WORDS

    assert WORDS.pattern == WORD_PATTERN
