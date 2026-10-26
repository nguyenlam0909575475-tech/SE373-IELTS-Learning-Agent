"""Build a reproducible public Academic Writing comparison corpus, without band labels."""

import argparse
import hashlib
import json
import re
import unicodedata
from collections import Counter, defaultdict, deque
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/corpus_plagiarism/raw"
PARQUET_NAME = "data/train-00000-of-00001.parquet"
SOURCES = [
    dict(
        repo="hai2131/IELTS-essays-task-1",
        task_type="task1",
        text_key="content",
        question_key="subject",
        revision="acf8025d107dbe8bb823bb82c551c69696417da4",
        sha256="05cdca522cad0ae239b8eaef2c29dea136f02356f7aa0b9a21eee842c5e95ed9",
    ),
    dict(
        repo="chillies/ielts-writing-task2-essays",
        task_type="task2",
        text_key="essay_text",
        question_key="question",
        revision="fa42fa7a2b02941e002cfbf5146c3176ba21f413",
        sha256="634370b1a7c306bf6154f7294fe0d74f4cc9099243175023da806e2e11614128",
    ),
]
ACADEMIC_TOPICS = {"Bar Chart", "Line Graph", "Process Diagram", "Multiple Graphs", "Table", "Map", "Pie Chart"}
WORDS = re.compile(r"\b[A-Za-z0-9]+(?:[-'][A-Za-z0-9]+)*\b")
LETTER = re.compile(r"\bwrite\s+(?:a|an)\s+(?:(?:formal|informal|personal)\s+)?letter\b", re.I)
SALUTATION = re.compile(r"^\s*Dear\s+[^\n,.!]{1,65}[,.!]", re.I)
VISUAL_PROMPT = re.compile(
    r"\b(?:charts?|graphs?|tables?|diagrams?|maps?)\s+(?:below|shows?\b|illustrates?\b)"
    r"|\bsummari[sz]e\s+the\s+information\b",
    re.I,
)


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def text_hash(text):
    """Normalize only the duplicate key; the exported essay stays byte-for-byte as a string."""
    return sha256(" ".join(unicodedata.normalize("NFKC", text).casefold().split()).encode("utf-8"))


def prepare_rows(rows, source, excluded, seen, min_words=50):
    accepted, counts = [], Counter()
    for index, raw in enumerate(rows):
        text, question = raw.get(source["text_key"]), raw.get(source["question_key"])
        topic = raw.get("topic")
        if not all(isinstance(x, str) and x.strip() for x in (text, question, topic)):
            counts["missing_text_question_or_topic"] += 1
            continue
        if LETTER.search(question) or SALUTATION.match(text):
            counts["general_training_letter"] += 1
            continue
        if (source["task_type"] == "task1" and topic not in ACADEMIC_TOPICS) or (
            source["task_type"] == "task2" and VISUAL_PROMPT.search(question)
        ):
            counts["outside_academic_task_scope"] += 1
            continue
        if len(WORDS.findall(text)) < min_words:
            counts["under_minimum_words"] += 1
            continue
        key = text_hash(text)
        if key in excluded:
            counts["evaluation_overlap"] += 1
            continue
        if key in seen:
            counts["duplicate"] += 1
            continue
        seen.add(key)
        accepted.append(
            dict(
                source_id=f"hf_{source['task_type']}_{index:06d}_{key[:16]}",
                task_type=source["task_type"],
                exam_question=question,
                text=text,
                topic=topic,
                source_url=f"https://huggingface.co/datasets/{source['repo']}/viewer/default/train?row={index}",
            )
        )
    return accepted, counts


def sample_diverse(rows, limit):
    """Rotate topics, then questions, with stable hash ranking within each question."""
    if limit < 0 or limit > len(rows):
        raise ValueError(f"Requested {limit} essays, but only {len(rows)} eligible essays available")
    groups = defaultdict(lambda: defaultdict(list))
    for row in rows:
        groups[row["topic"]][row["exam_question"]].append(row)
    topics = deque(
        deque(
            deque(sorted(group, key=lambda row: sha256(row["source_id"].encode())))
            for _, group in sorted(questions.items())
        )
        for _, questions in sorted(groups.items())
    )
    selected = []
    while len(selected) < limit:
        questions = topics.popleft()
        group = questions.popleft()
        selected.append(group.popleft())
        if group:
            questions.append(group)
        if questions:
            topics.append(questions)
    return selected


def evaluation_exclusions():
    """Read existing evaluation data, without changing its records, labels or split."""
    hashes, files = set(), []
    paths = [ROOT / "evals/data/5_basic_cases.json"]
    paths.extend(ROOT / f"evals/benchmark_{split}/benchmark.json" for split in ("dev", "test"))
    total = 0
    for path in paths:
        data = json.loads(path.read_text(encoding="utf-8"))
        records = data if isinstance(data, list) else [data]
        for row in records:
            hashes.add(text_hash(row["essay"]))
            total += 1
        files.append(dict(path=path.relative_to(ROOT).as_posix(), sha256=sha256(path.read_bytes())))
    return hashes, dict(records_read=total, unique_essay_hashes=len(hashes), files=files)


def download(url, path):
    """Cache a complete response; failed downloads never become valid cache entries."""
    path.parent.mkdir(parents=True, exist_ok=True)
    request = Request(url, headers={"User-Agent": "IELTS-course-corpus/1.0"})
    with urlopen(request, timeout=120) as response:
        content = response.read()
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_bytes(content)
    temporary.replace(path)


def source_rows(source, offline):
    import pyarrow.parquet as parquet

    folder = RAW / source["repo"].replace("/", "__")
    path = folder / Path(PARQUET_NAME).name
    base = f"https://huggingface.co/datasets/{source['repo']}/resolve/{source['revision']}"
    if not path.exists():
        if offline:
            raise FileNotFoundError(f"Missing cached dataset: {path}")
        download(f"{base}/{PARQUET_NAME}", path)
    if sha256(path.read_bytes()) != source["sha256"]:
        raise ValueError(f"Dataset checksum mismatch: {path}")
    for name in ("README.md", "metadata.json"):
        target = folder / name
        if not target.exists() and not offline:
            url = (
                f"{base}/README.md"
                if name == "README.md"
                else f"https://huggingface.co/api/datasets/{source['repo']}/revision/{source['revision']}"
            )
            download(url, target)
    rows = parquet.read_table(path, columns=[source["text_key"], source["question_key"], "topic"]).to_pylist()
    return rows, path


def build(output, task1_limit=600, task2_limit=1200, min_words=50, offline=False):
    if min_words < 1:
        raise ValueError("min_words must be positive")
    excluded, exclusion_report = evaluation_exclusions()
    corpus, reports, seen = [], [], set()
    for source, limit in zip(SOURCES, (task1_limit, task2_limit), strict=True):
        rows, path = source_rows(source, offline)
        candidates, rejected = prepare_rows(rows, source, excluded, seen, min_words)
        selected = sample_diverse(candidates, limit)
        corpus.extend(selected)
        counts = [len(WORDS.findall(row["text"])) for row in selected]
        reports.append(
            dict(
                dataset=source["repo"],
                source_url=f"https://huggingface.co/datasets/{source['repo']}",
                publisher=source["repo"].split("/")[0],
                revision=source["revision"],
                download_url=f"https://huggingface.co/datasets/{source['repo']}/resolve/{source['revision']}/{PARQUET_NAME}",
                raw_file=path.relative_to(ROOT).as_posix(),
                raw_sha256=source["sha256"],
                rows_read=len(rows),
                filtered=dict(sorted(rejected.items())),
                raw_topics=len({r["topic"] for r in rows}),
                raw_questions=len({r[source["question_key"]] for r in rows}),
                eligible=len(candidates),
                selected=len(selected),
                eligible_not_selected=len(candidates) - len(selected),
                selected_topics=dict(sorted(Counter(r["topic"] for r in selected).items())),
                selected_questions=len({r["exam_question"] for r in selected}),
                word_count_range=[min(counts), max(counts)] if counts else None,
            )
        )
    assert len({r["source_id"] for r in corpus}) == len(corpus)
    corpus_hashes = {text_hash(r["text"]) for r in corpus}
    assert len(corpus_hashes) == len(corpus) and not corpus_hashes & excluded
    content = "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in corpus).encode("utf-8")
    manifest = dict(
        purpose="Public IELTS Academic Writing essays for plagiarism comparison; no gold band labels",
        corpus_file="corpus.jsonl",
        corpus_sha256=sha256(content),
        total_documents=len(corpus),
        task_counts=dict(sorted(Counter(r["task_type"] for r in corpus).items())),
        policy=dict(
            public_source_required=True,
            license_required=False,
            band_labels_included=False,
            original_text_preserved=True,
            min_words=min_words,
            deduplication="SHA256 of NFKC + casefold + collapsed whitespace; exact normalized text only",
            sampling="Round robin topics, then questions; deterministic SHA256 source_id rank within question",
            general_training_filter="Letter prompts/salutations; Task 1 topic allowlist; Task 2 visual prompt exclusion",
        ),
        evaluation_exclusions=exclusion_report,
        sources=reports,
        limitations=[
            "Automated scope filters; not independently reviewed for every essay.",
            "Near duplicates and paraphrases are not removed by exact-text deduplication.",
            "Public source authorship and human/AI origin are not independently authenticated.",
            "Corpus coverage alone does not establish plagiarism detection or false-positive rates.",
        ],
    )
    output.mkdir(parents=True, exist_ok=True)
    target = output / "corpus.jsonl"
    temporary = target.with_suffix(".jsonl.tmp")
    temporary.write_bytes(content)
    temporary.replace(target)
    (output / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "data/corpus_plagiarism")
    parser.add_argument("--task1-limit", type=int, default=600)
    parser.add_argument("--task2-limit", type=int, default=1200)
    parser.add_argument("--min-words", type=int, default=50)
    parser.add_argument("--offline", action="store_true", help="Use locally cached Parquet snapshots")
    args = parser.parse_args()
    report = build(args.output, args.task1_limit, args.task2_limit, args.min_words, args.offline)
    print(json.dumps({key: report[key] for key in ("total_documents", "task_counts", "corpus_sha256")}, indent=2))


if __name__ == "__main__":
    main()
