"""Real Member 1 data, N2 validation, N3 graph and N4 tools; no network/model inference."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from agent.tools.compute_tool import compute_band, count_words
from agent.tools.plagiarism_tool import PlagiarismChecker
from scripts.descriptor_data import VERSION, load_dataset
from skills.writing_assessment import validators
from src.agent.contracts import DependencyFailure, DescriptorChunk, ErrorCode, ResolvedWritingTask
from src.agent.graph import build_graph
from src.agent.schemas import Flag
from src.agent.team_adapters import MappingTaskBank, build_team_dependencies
from src.tools.rag_descriptors import DescriptorRetriever

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def public_checker():
    return PlagiarismChecker.from_jsonl(ROOT / "data/corpus_plagiarism/corpus.jsonl")


class DescriptorCollection:
    """Synthetic storage backend; N2's actual query/shape/filter validation still runs."""

    metadata = {"descriptor_version": VERSION, "embedding_model": "all-MiniLM-L6-v2"}

    def query(self, *, where, n_results, **kwargs):
        task, criterion = where["$and"]
        rows = [row for row in load_dataset()
                if row["test_part"] == task["test_part"] and row["criterion"] == criterion["criterion"]]
        rows.sort(key=lambda row: abs(row["band"] - 6))
        rows = rows[:n_results]
        return {"ids": [[row["chunk_id"] for row in rows]],
                "documents": [[row["text"] for row in rows]],
                "metadatas": [[{key: val for key, val in row.items() if key != "text"} for row in rows]]}


class Examiner:
    """Controlled draft replaces LLM inference only, so failures and retries are deterministic."""

    def __init__(self, *, invalid_refs=False, provider_error=False):
        self.calls = 0
        self.invalid_refs = invalid_refs
        self.provider_error = provider_error
        self.closed = False

    def close(self):
        self.closed = True

    def generate(self, data):
        self.calls += 1
        if self.provider_error:
            raise DependencyFailure(ErrorCode.LLM_TIMEOUT)
        quote = data.submission.essay[:20]
        names = list(dict.fromkeys(chunk.criterion for chunk in data.chunks))
        return {"criteria": [
            {"criterion": name, "band": 7.0 if i == 3 else 6.0,
             "evidence": [{"quote": quote, "start_char": 0, "end_char": len(quote)}],
             "descriptor_refs": ["INVENTED" if self.invalid_refs else
                                 next(c.chunk_id for c in data.chunks if c.criterion == name)],
             "comment": "Controlled test draft, not an accuracy evaluation."}
            for i, name in enumerate(names)
        ], "corrections": [], "off_topic": False}


def dependencies(task_type, examiner, *, checker=None, material="Complete synthetic table data."):
    task = ResolvedWritingTask(
        item_id="PUBLIC_TEST", task_type=task_type, task_prompt="Discuss the supplied question.",
        task_material_text=material if task_type == "task1" else None,
        source="public", source_url="https://example.org/question",
    )
    return build_team_dependencies(
        task_bank=MappingTaskBank({task.item_id: task}), examiner=examiner,
        plagiarism_checker=checker,
        retriever=DescriptorRetriever(collection=DescriptorCollection(),
                                     chunk_factory=lambda **row: DescriptorChunk.model_validate(row)),
    )


def invoke(deps, essay, task_type="task2"):
    return build_graph(dependencies=deps).invoke(
        {"request": {"item_id": "PUBLIC_TEST", "task_type": task_type, "essay": essay}}
    )


@pytest.mark.parametrize("task_type", ["task1", "task2"])
def test_real_corpus_through_team_graph(public_checker, task_type):
    assert len(public_checker.entries) == 1800
    entry = next(row for row in public_checker.entries if row.task_type == task_type)
    essay = "\n\U0001f600 " + entry.text
    examiner = Examiner()
    deps = dependencies(task_type, examiner, checker=public_checker)
    plagiarism = deps.tools.check_plagiarism(essay)
    assert plagiarism.possible_plagiarism and plagiarism.max_similarity == 1
    assert any(match.source_id == entry.source_id for match in plagiarism.matches)
    assert all(essay[m.evidence.start_char:m.evidence.end_char] == m.evidence.quote for m in plagiarism.matches)
    result = invoke(deps, essay, task_type)["result"]
    assert result.status == "success"
    assert result.assessment.word_count == count_words(essay)
    assert result.assessment.overall_band == compute_band([6, 6, 6, 7]) == 6.5
    assert Flag.POSSIBLE_PLAGIARISM in result.assessment.flags
    assert examiner.calls == 1
    from skills.writing_assessment.checks import validate_writing_assessment

    chunks = [chunk for name in dict.fromkeys(c.criterion for c in result.assessment.criteria)
              for chunk in deps.retriever.retrieve_descriptors(result.assessment.task_type, name)]
    assert validate_writing_assessment(
        result.assessment, essay, expected_word_count=count_words(essay),
        retrieved_descriptors=chunks, plagiarism_result=plagiarism,
    ).passed


def test_bad_refs_use_bounded_repair_with_real_validators(public_checker):
    examiner = Examiner(invalid_refs=True)
    result = invoke(dependencies("task2", examiner, checker=public_checker),
                    public_checker.entries[-1].text)["result"]
    assert result.status == "error" and result.code == ErrorCode.ASSESSMENT_VALIDATION_FAILED
    assert result.retry_count == 2 and examiner.calls == 3


def test_missing_corpus_stops_before_examiner(monkeypatch, tmp_path):
    monkeypatch.setattr("agent.tools.plagiarism_tool.DEFAULT_CORPUS_PATH", tmp_path / "missing.jsonl")
    examiner = Examiner()
    result = invoke(dependencies("task2", examiner), "A complete synthetic essay about libraries.")["result"]
    assert result.status == "error" and result.code == ErrorCode.DEPENDENCY_UNAVAILABLE
    assert examiner.calls == 0


def test_provider_timeout_does_not_return_a_grade(public_checker):
    examiner = Examiner(provider_error=True)
    result = invoke(dependencies("task2", examiner, checker=public_checker),
                    public_checker.entries[-1].text)["result"]
    assert result.status == "error" and result.code == ErrorCode.LLM_TIMEOUT
    assert examiner.calls == 1


def test_task1_filename_is_not_chart_content(public_checker):
    examiner = Examiner()
    result = invoke(dependencies("task1", examiner, checker=public_checker, material=None),
                    public_checker.entries[0].text, "task1")["result"]
    assert result.status == "error" and result.code == ErrorCode.INVALID_TASK
    assert examiner.calls == 0


def test_n4_refs_accept_canonical_member1_chunks(assessment):
    chunks = [row for row in load_dataset() if row["test_part"] == "task2"]
    aliases = {"coherence_and_cohesion": "coherence_cohesion",
               "grammatical_range_and_accuracy": "grammatical_range_accuracy"}
    for row in assessment["criteria"]:
        row["criterion"] = aliases.get(row["criterion"], row["criterion"])
        row["descriptor_refs"] = [next(c["chunk_id"] for c in chunks if c["criterion"] == row["criterion"])]
    assert validators.refs_validator(assessment, chunks) == []


@pytest.mark.parametrize("task_type", ["task1", "task2"])
def test_live_api_uses_real_team_tools(monkeypatch, public_checker, task_type):
    from types import SimpleNamespace

    from backend import live_service
    from backend.main import app

    examiner = Examiner()
    monkeypatch.setattr(live_service, "load_openai_settings",
                        lambda *_: SimpleNamespace(trace_model_version="controlled_test"))
    monkeypatch.setattr(live_service, "OpenAICompatibleExaminer", lambda _: examiner)
    monkeypatch.setattr(live_service, "get_live_retriever", lambda: DescriptorRetriever(
        collection=DescriptorCollection(), chunk_factory=lambda **row: DescriptorChunk.model_validate(row)))
    entry = next(row for row in public_checker.entries if row.task_type == task_type)
    essay = "\n\U0001f600 " + entry.text
    response = TestClient(app).post("/api/assess-writing", json={
        "task_type": task_type, "prompt": entry.exam_question, "essay": essay, "mock": False,
        "task_material_text": "Complete synthetic table data." if task_type == "task1" else None,
        "source_url": entry.source_url,
    })
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["execution_mode"] == "live"
    assert "possible_plagiarism" in body["assessment"]["flags"]
    assert body["assessment"]["overall_band"] == 6.5
    assert examiner.closed and examiner.calls == 1
    for criterion in body["assessment"]["criteria"]:
        for evidence in criterion["evidence"]:
            assert essay[evidence["start_char"]:evidence["end_char"]] == evidence["quote"]


def test_live_api_missing_material_and_provider_failure_have_no_grade(monkeypatch):
    from backend import live_service
    from backend.main import app

    client = TestClient(app)
    response = client.post("/api/assess-writing", json={
        "task_type": "task1", "prompt": "The chart shows data.", "essay": "A report.", "mock": False,
    })
    assert response.status_code == 422

    def unavailable(**kwargs):
        raise live_service.LiveAssessmentError(ErrorCode.LLM_TIMEOUT)

    monkeypatch.setattr("backend.main.run_live_assessment", unavailable)
    response = client.post("/api/assess-writing", json={
        "task_type": "task2", "prompt": "Discuss libraries.", "essay": "A private submission.", "mock": False,
    })
    assert response.status_code == 504
    assert response.json()["detail"]["code"] == "LLM_TIMEOUT"
    assert "assessment" not in response.json() and "private submission" not in response.text
