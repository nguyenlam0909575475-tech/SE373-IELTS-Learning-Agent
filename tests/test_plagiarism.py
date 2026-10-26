"""Unit tests for plagiarism copy spans, thresholds and corpus handling."""

import json
from dataclasses import asdict

import pytest

from agent.tools.contracts import Member4DependencyError
from agent.tools.plagiarism_tool import CorpusEntry, PlagiarismChecker, check_plagiarism


def entry(text, source_id="SYNTHETIC_1"):
    return CorpusEntry(source_id, text, "urn:se373:self-authored-test", "Self-authored synthetic test fixture")


def test_exact_copy_provides_original_offsets(essay):
    checker = PlagiarismChecker([entry(essay)])
    submitted = "\n😀 " + essay.upper() + "\n"
    result = checker.check_plagiarism(submitted)
    assert result.possible_plagiarism is True
    assert result.max_similarity == 1
    assert result.matches[0].source_id == "SYNTHETIC_1"
    span = result.matches[0].evidence
    assert span.start_char == 3
    assert submitted[span.start_char:span.end_char] == span.quote == essay.upper().rstrip(".")


def test_near_copy_with_one_substitution(essay):
    result = PlagiarismChecker([entry(essay)]).check_plagiarism(essay.replace("shared", "borrowed"))
    assert result.possible_plagiarism
    assert 0.8 <= result.max_similarity < 1
    assert len(result.matches) == 2


def test_copy_embedded_in_new_text_uses_essay_coverage(essay):
    submitted = essay + " " + " ".join(f"original{i}" for i in range(100))
    result = PlagiarismChecker([entry(essay)]).check_plagiarism(submitted)
    assert not result.possible_plagiarism
    assert result.max_similarity == pytest.approx(31 / 131)
    assert result.matches  # Evidence is still available below the flag threshold.


@pytest.mark.parametrize("submitted", ["", "hello", "A cyclist crossed the bridge beside a small orchard."])
def test_unrelated_or_short_text(essay, submitted):
    result = PlagiarismChecker([entry(essay)]).check_plagiarism(submitted)
    assert result.max_similarity == 0
    assert not result.possible_plagiarism and result.matches == []


def test_common_short_phrase_does_not_trigger_verdict(essay):
    result = PlagiarismChecker([entry(essay)]).check_plagiarism("Free community libraries help residents learn")
    assert result.max_similarity == 1
    assert not result.possible_plagiarism  # Default minimum is 20 shared words.


@pytest.mark.parametrize(("threshold", "flag"), [(0.75, True), (0.750001, False)])
def test_configured_threshold_boundary(threshold, flag):
    source = "one two three four five six"
    result = PlagiarismChecker([entry(source)], threshold=threshold, min_shared_words=5).check_plagiarism(source + " seven eight")
    assert result.max_similarity == 0.75
    assert result.possible_plagiarism is flag


def test_distinct_sources_return_their_ids_and_all_spans(essay):
    result = PlagiarismChecker([entry(essay), entry(essay, "SYNTHETIC_2")]).check_plagiarism(essay)
    assert {m.source_id for m in result.matches} == {"SYNTHETIC_1", "SYNTHETIC_2"}
    assert result.max_similarity == 1  # Never double-counted across sources.


def test_loader_is_read_only_and_preserves_metadata(tmp_path, essay):
    path = tmp_path / "corpus.jsonl"
    original = json.dumps(asdict(entry(essay)), ensure_ascii=False) + "\n"
    path.write_text(original, encoding="utf-8")
    assert PlagiarismChecker.from_jsonl(path).check_plagiarism(essay).possible_plagiarism
    assert path.read_text(encoding="utf-8") == original


@pytest.mark.parametrize("content", ["", "not json", "{}", '{"text":"unlicensed"}', "null", "[]"])
def test_missing_or_invalid_corpus_never_means_clean(tmp_path, content):
    path = tmp_path / "corpus.jsonl"
    path.write_text(content, encoding="utf-8")
    with pytest.raises(Member4DependencyError, match="PLAGIARISM_CORPUS_"):
        PlagiarismChecker.from_jsonl(path)


def test_missing_default_corpus_fails_closed(monkeypatch, tmp_path, essay):
    monkeypatch.setattr("agent.tools.plagiarism_tool.DEFAULT_CORPUS_PATH", tmp_path / "missing.jsonl")
    with pytest.raises(Member4DependencyError, match="PLAGIARISM_CORPUS_MISSING"):
        check_plagiarism(essay=essay)


def test_duplicate_source_ids_are_rejected(essay):
    with pytest.raises(Member4DependencyError, match="INVALID"):
        PlagiarismChecker([entry(essay), entry(essay)])


@pytest.mark.parametrize("options", [
    {"threshold": 0}, {"threshold": 1.1}, {"threshold": float("nan")},
    {"threshold": True}, {"ngram_size": 1}, {"ngram_size": True},
    {"min_shared_words": 4}, {"min_shared_words": True},
])
def test_invalid_configuration(essay, options):
    with pytest.raises(ValueError):
        PlagiarismChecker([entry(essay)], **options)


@pytest.mark.parametrize("suffix", [".json", ".jsonl"])
def test_repository_corpus_file_formats_are_read_only(tmp_path, essay, suffix):
    path = tmp_path / ("corpus" + suffix)
    data = asdict(entry(essay))
    content = json.dumps([data] if suffix == ".json" else data)
    path.write_text(content, encoding="utf-8")
    assert PlagiarismChecker.from_file(path).check_plagiarism(essay).possible_plagiarism
    assert path.read_text(encoding="utf-8") == content


@pytest.mark.parametrize("content", ["", "[]", "{}", "null", '[{"source_url":"urn:link-only"}]'])
def test_json_placeholder_or_links_only_cannot_report_clean(tmp_path, content):
    path = tmp_path / "sample_corpus_links.json"
    path.write_text(content, encoding="utf-8")
    with pytest.raises(Member4DependencyError):
        PlagiarismChecker.from_file(path)


def test_member1_record_preserves_text_metadata_without_invented_license(tmp_path, essay):
    record = dict(source_id="PUBLIC_1", text="\n" + essay, source_url="https://example.org/essay",
                  task_type="task2", exam_question="Discuss libraries.", topic="Education")
    path = tmp_path / "public.jsonl"
    content = json.dumps(record) + "\n"
    path.write_text(content, encoding="utf-8")
    checker = PlagiarismChecker.from_file(path)
    assert checker.entries[0].license is None
    assert checker.entries[0].text == record["text"]
    assert checker.entries[0].topic == record["topic"]
    assert checker.check_plagiarism(essay).possible_plagiarism
    assert path.read_text(encoding="utf-8") == content


@pytest.mark.parametrize("changes", [
    {"source_id": "bad/id"}, {"task_type": "speaking"}, {"topic": 1}, {"exam_question": ""}, {"license": False},
])
def test_invalid_public_metadata_is_rejected(tmp_path, essay, changes):
    record = dict(source_id="PUBLIC_1", text=essay, source_url="https://example.org/essay")
    record.update(changes)
    path = tmp_path / "public.jsonl"
    path.write_text(json.dumps(record), encoding="utf-8")
    with pytest.raises(Member4DependencyError, match="INVALID"):
        PlagiarismChecker.from_file(path)


def test_default_index_reused_but_changed_or_missing_corpus_fails(monkeypatch, tmp_path, essay):
    from agent.tools import plagiarism_tool

    path = tmp_path / "public.jsonl"
    path.write_text(json.dumps(dict(source_id="PUBLIC_1", text=essay, source_url="https://example.org/essay")),
                    encoding="utf-8")
    monkeypatch.setattr(plagiarism_tool, "DEFAULT_CORPUS_PATH", path)
    first = plagiarism_tool.get_default_checker()
    assert plagiarism_tool.get_default_checker() is first
    assert check_plagiarism(essay).possible_plagiarism
    path.write_text("broken corpus", encoding="utf-8")
    with pytest.raises(Member4DependencyError, match="INVALID"):
        check_plagiarism(essay)
    path.unlink()
    with pytest.raises(Member4DependencyError, match="MISSING"):
        check_plagiarism(essay)
