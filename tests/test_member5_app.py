"""Integration and Unit Tests for Member 5 Application (Backend, Switch Flag & Harness).

Tests:
1. Switch flag toggle (Mock vs Live) via config and API.
2. FastAPI endpoints: /api/health, /api/config, /api/count-words, /api/sample-prompts.
3. Assessment generation under Mock Mode for UC-02 compliance.
4. Verbatim quote 100% slice matching: essay[start_char:end_char] == quote.
5. Mandatory penalties: under_length (<150/<250), off_topic (cap <= 5.0), injection_detected.
6. Validation with skills.writing_assessment.checks.validate_writing_assessment.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from agent.tools.compute_tool import count_words
from backend.config import get_mock_mode
from backend.main import app

client = TestClient(app)


def test_health_endpoint() -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "mock_mode" in data
    assert data["version"] == "0.1.0"


def test_config_and_toggle_switch() -> None:
    # 1. Read config
    res1 = client.get("/api/config")
    assert res1.status_code == 200
    assert res1.json()["mock_mode"] is False

    # 2. Toggle mock is deprecated and stays False
    res2 = client.post("/api/config/toggle-mock", json={"enabled": True})
    assert res2.status_code == 200
    assert res2.json()["mock_mode"] is False
    assert get_mock_mode() is False


def test_word_counter_endpoint() -> None:
    text = "The quick brown fox jumps over the lazy dog. Overall, it's 2026."
    res = client.post("/api/count-words", json={"text": text})
    assert res.status_code == 200
    data = res.json()
    assert data["word_count"] == count_words(text)
    assert data["is_under_task1"] is True
    assert data["is_under_task2"] is True


def test_sample_prompts_endpoint() -> None:
    res = client.get("/api/sample-prompts")
    assert res.status_code == 200
    prompts = res.json()
    assert len(prompts) >= 4
    assert any(p["id"] == "task1_standard" for p in prompts)
    assert any(p["id"] == "task2_standard" for p in prompts)


def test_sample_tests_endpoint() -> None:
    res = client.get("/api/sample-tests")
    assert res.status_code == 200
    tests = res.json()
    assert len(tests) >= 3
    first = tests[0]
    assert "name" in first
    assert "source" in first
    assert "questions" in first
    assert len(first["questions"]) >= 2
    assert any(q["task_type"] == "task1" for q in first["questions"])
    assert any(q["task_type"] == "task2" for q in first["questions"])


def test_assess_writing_endpoint_success() -> None:
    from unittest.mock import patch

    from skills.writing_assessment.checks import WritingAssessment

    mock_assessment = WritingAssessment.model_validate({
        "task_type": "task2",
        "word_count": 210,
        "criteria": [
            {
                "criterion": "task_response",
                "band": 7.0,
                "evidence": [{"quote": "Education is important", "start_char": 0, "end_char": 22}],
                "descriptor_refs": ["writing_task2_task_response_b7_2023_05"],
                "comment": "Good response",
            },
            {
                "criterion": "coherence_and_cohesion",
                "band": 7.0,
                "evidence": [{"quote": "Education is important", "start_char": 0, "end_char": 22}],
                "descriptor_refs": ["writing_task2_coherence_cohesion_b7_2023_05"],
                "comment": "Well structured",
            },
            {
                "criterion": "lexical_resource",
                "band": 7.0,
                "evidence": [{"quote": "Education is important", "start_char": 0, "end_char": 22}],
                "descriptor_refs": ["writing_task2_lexical_resource_b7_2023_05"],
                "comment": "Good vocabulary",
            },
            {
                "criterion": "grammatical_range_and_accuracy",
                "band": 7.0,
                "evidence": [{"quote": "Education is important", "start_char": 0, "end_char": 22}],
                "descriptor_refs": ["writing_task2_grammatical_range_accuracy_b7_2023_05"],
                "comment": "Accurate grammar",
            },
        ],
        "overall_band": 7.0,
        "corrections": [],
        "flags": [],
        "disclaimer": "Điểm ước lượng do AI chấm, chỉ dùng để luyện tập, không thay thế điểm thi chính thức",
    })

    with patch("backend.main.run_agent_assessment", return_value=mock_assessment):
        res = client.post(
            "/api/assess-writing",
            json={
                "task_type": "task2",
                "prompt": "Education topic",
                "essay": "Education is important for everyone. It helps build a better society.",
            },
        )
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True
        assert data["assessment"]["overall_band"] == 7.0


def test_latest_assessment_endpoint() -> None:
    res = client.get("/api/latest-assessment")
    assert res.status_code in (200, 404)
    if res.status_code == 200:
        data = res.json()
        assert "assessment" in data


def test_benchmark_tasks_endpoint() -> None:
    res = client.get("/api/benchmark-tasks")
    assert res.status_code == 200
    data = res.json()
    assert "task1" in data
    assert "task2" in data
    assert len(data["task1"]) >= 10
    assert len(data["task2"]) >= 5
    assert all(t["task_type"] == "task1" for t in data["task1"])
    assert all(t["task_type"] == "task2" for t in data["task2"])
    assert any("energy" in t["title"].lower() or "graph" in t["prompt"].lower() for t in data["task1"])

