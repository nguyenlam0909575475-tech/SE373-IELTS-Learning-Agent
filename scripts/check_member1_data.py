"""Validate Member 1 deliverables without calling an LLM or modifying source data."""

import hashlib
import json
from collections import Counter
from pathlib import Path
from urllib.parse import urlsplit

try:
    from .build_ielts_plagiarism_corpus import WORDS, evaluation_exclusions, text_hash
    from .check_writing_benchmark import check_benchmark
    from .descriptor_data import load_dataset
except ImportError:
    from build_ielts_plagiarism_corpus import WORDS, evaluation_exclusions, text_hash
    from check_writing_benchmark import check_benchmark
    from descriptor_data import load_dataset

ROOT = Path(__file__).resolve().parents[1]
BASIC_FIELDS = {"id", "task_type", "exam_question", "essay", "material", "scores", "expected", "source"}
BASIC_IDS = {
    "case_01_task1_normal",
    "case_02_task2_normal",
    "case_03a_task1_under_length",
    "case_03b_task2_under_length",
    "case_04_off_topic_advanced",
    "case_05_grammar_errors",
}
CORPUS_FIELDS = {"source_id", "task_type", "exam_question", "text", "topic", "source_url"}


def public_url(value):
    if not isinstance(value, str):
        return False
    url = urlsplit(value)
    return url.scheme == "https" and bool(url.hostname) and url.hostname not in ("localhost", "127.0.0.1")


def validate_basic_cases(rows, *, root=ROOT):
    if not isinstance(rows, list) or len(rows) != 6:
        raise ValueError("Need six basic cases for five functional groups")
    if {r.get("id") for r in rows} != BASIC_IDS:
        raise ValueError("Unexpected or duplicate basic case IDs")
    for row in rows:
        if set(row) != BASIC_FIELDS:
            raise ValueError("Basic cases need exactly eight fields")
        if row["task_type"] not in ("task1", "task2") or not row["essay"] or not row["exam_question"]:
            raise ValueError("Missing task, question or essay")
        if row["scores"] is not None:
            raise ValueError("Basic-case scores must remain null")
        if not public_url(row["source"]):
            raise ValueError("Basic case requires a public source URL")
        expected = row["expected"]
        if not isinstance(expected, dict):
            raise ValueError("expected must be an object")
        required = expected.get("required_flags", [])
        forbidden = expected.get("forbidden_flags", [])
        if set(required) & set(forbidden):
            raise ValueError("Contradictory expected flags")
        short = len(WORDS.findall(row["essay"])) < (150 if row["task_type"] == "task1" else 250)
        if short != ("under_length" in required) or ("under_length" in forbidden and short):
            raise ValueError("under_length expectation differs from the Member 4 word-count contract")
        if row["task_type"] == "task1":
            material = row["material"]
            if not isinstance(material, dict) or set(material) != {"path", "url"}:
                raise ValueError("Task 1 basic case needs material path and URL")
            path = (root / material["path"]).resolve()
            if (
                not path.is_relative_to((root / "evals/materials").resolve())
                or not path.is_file()
                or not public_url(material["url"])
            ):
                raise ValueError("Missing or invalid basic-case image")
        elif row["material"] is not None:
            raise ValueError("Task 2 material must be null")
    off_topic = next(r for r in rows if r["id"] == "case_04_off_topic_advanced")["expected"]
    if "off_topic" not in off_topic.get("required_flags", []) or off_topic.get("criterion_band_max") != {
        "task_response": 5.0
    }:
        raise ValueError("Off-topic case must enforce Task Response <=5.0")
    grammar = next(r for r in rows if r["id"] == "case_05_grammar_errors")["expected"]
    if "grammar" not in grammar.get("correction_categories_contains", []):
        raise ValueError("Grammar case must require a grammar correction")
    return len(rows)


def check_member1_data():
    chunks = load_dataset()
    benchmark = check_benchmark()
    basic = json.loads((ROOT / "evals/data/5_basic_cases.json").read_text(encoding="utf-8"))
    basic_count = validate_basic_cases(basic)
    path = ROOT / "data/corpus_plagiarism/corpus.jsonl"
    manifest = json.loads(path.with_name("manifest.json").read_text(encoding="utf-8"))
    content = path.read_bytes()
    if hashlib.sha256(content).hexdigest() != manifest["corpus_sha256"]:
        raise ValueError("Corpus differs from its manifest SHA256")
    rows = [json.loads(line) for line in content.decode("utf-8").splitlines() if line.strip()]
    for row in rows:
        if set(row) != CORPUS_FIELDS:
            raise ValueError("Corpus must have exactly the six Member 1 fields")
        if any(not isinstance(v, str) or not v.strip() for v in row.values()):
            raise ValueError("Corpus fields must contain text")
        if row["task_type"] not in ("task1", "task2") or not public_url(row["source_url"]):
            raise ValueError("Corpus needs an Academic task and public URL")
        if len(WORDS.findall(row["text"])) < manifest["policy"]["min_words"]:
            raise ValueError("Corpus essay below preprocessing minimum")
    if (
        len(rows) != manifest["total_documents"]
        or dict(Counter(r["task_type"] for r in rows)) != manifest["task_counts"]
    ):
        raise ValueError("Corpus counts differ from manifest")
    if len({r["source_id"] for r in rows}) != len(rows):
        raise ValueError("Duplicate corpus ID")
    corpus_hashes = {text_hash(r["text"]) for r in rows}
    excluded, _ = evaluation_exclusions()
    if len(corpus_hashes) != len(rows) or corpus_hashes & excluded:
        raise ValueError("Duplicate corpus text or overlap with evaluation essays")
    return dict(
        descriptor_chunks=len(chunks),
        corpus_documents=len(rows),
        benchmark_documents=benchmark["total"],
        benchmark_splits=benchmark["splits"],
        basic_cases=basic_count,
    )


if __name__ == "__main__":
    try:
        print(json.dumps(check_member1_data(), ensure_ascii=False, indent=2))
    except (ValueError, KeyError, OSError) as exc:
        raise SystemExit(str(exc)) from None
