"""Self-authored fixtures; scores are test values, not benchmark labels."""

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="session", autouse=True)
def ensure_chroma_db() -> None:
    """Ensure ChromaDB exists before integration tests run."""
    db_file = ROOT / "data" / "chroma_db" / "chroma.sqlite3"
    if not db_file.is_file():
        from scripts.rebuild_vectorstore import rebuild
        source = ROOT / "data" / "processed" / "writing_descriptors.json"
        rebuild(source, db_file.parent)

ESSAY = (
    "Free community libraries help residents learn because they offer shared books, "
    "quiet study spaces and practical information. Public funding should support "
    "these services while local councils review their costs and benefits."
)
NAMES = ["task_response", "coherence_and_cohesion", "lexical_resource", "grammatical_range_and_accuracy"]


@pytest.fixture
def essay():
    return ESSAY


@pytest.fixture
def assessment():
    return {
        "task_type": "task2", "word_count": 31,
        "criteria": [
            {"criterion": name, "band": 6.0,
             "evidence": [{"quote": "Free community libraries", "start_char": 0, "end_char": 24}],
             "descriptor_refs": [f"MOCK_task2_{name}_6"], "comment": "Synthetic fixture only."}
            for name in NAMES
        ],
        "overall_band": 6.0, "flags": ["under_length"], "corrections": [],
        "disclaimer": "Điểm ước lượng do AI chấm, chỉ dùng để luyện tập, không thay thế điểm thi chính thức",
    }


@pytest.fixture
def chunks():
    return [
        {"chunk_id": f"MOCK_task2_{name}_6", "test_part": "task2", "criterion": name,
         "band": 6.0, "version": "SYNTHETIC_v1", "source_url": "urn:se373:synthetic-test",
         "text": "Synthetic descriptor placeholder, not an IELTS rubric."}
        for name in NAMES
    ]
