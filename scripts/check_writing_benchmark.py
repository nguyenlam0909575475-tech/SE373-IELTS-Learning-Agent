"""Check the packaged Academic Writing benchmark using only the Python standard library."""

import hashlib
import json
import math
import re
import unicodedata
from collections import Counter
from pathlib import Path, PurePosixPath
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
FIELDS = {"case_id", "task_type", "exam_question", "essay", "material", "scores", "feedback", "source"}
COMMON_SCORES = {"coherence_cohesion", "lexical_resource", "grammatical_range_accuracy", "overall_band"}


def normalize(text):
    return " ".join(unicodedata.normalize("NFKC", text).casefold().split())


def validate_record(row, *, root=ROOT):
    if not isinstance(row, dict) or set(row) != FIELDS:
        raise ValueError("Each benchmark record must have exactly the eight documented fields")
    for key in ("case_id", "exam_question", "essay", "feedback", "source"):
        if not isinstance(row[key], str) or not row[key].strip():
            raise ValueError(f"Missing text field: {key}")
    if row["task_type"] not in ("task1", "task2"):
        raise ValueError("Only Academic task1/task2 are accepted")
    source = urlsplit(row["source"])
    if source.scheme != "https" or not source.hostname:
        raise ValueError("A public HTTPS source URL is required")
    first = "task_achievement" if row["task_type"] == "task1" else "task_response"
    scores = row["scores"]
    if not isinstance(scores, dict) or set(scores) != COMMON_SCORES | {first}:
        raise ValueError("Need exactly four task-specific criterion scores and overall_band")
    if any(
        isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) or not 0 <= v <= 9
        for v in scores.values()
    ):
        raise ValueError("Scores must be finite numbers in [0,9]")
    if row["task_type"] == "task2":
        if row["material"] is not None:
            raise ValueError("Task 2 material must be null")
        return
    if re.search(
        r"\bwrite\s+(?:a|an)\s+(?:(?:formal|informal|personal)\s+)?letter\b", row["exam_question"], re.I
    ) or re.match(r"\s*Dear\s+", row["essay"], re.I):
        raise ValueError("General Training Task 1 letters are excluded")
    material = row["material"]
    if not isinstance(material, str) or not material.startswith("evals/materials/") or "\\" in material:
        raise ValueError("Task 1 material must be a repository-relative evals/materials/ path")
    relative = PurePosixPath(material)
    path = (root / material).resolve()
    if (
        ".." in relative.parts
        or not path.is_relative_to((root / "evals/materials").resolve())
        or not path.is_file()
        or not path.stat().st_size
    ):
        raise ValueError("Missing or invalid Task 1 image: " + material)
    if path.suffix.lower() not in (".png", ".jpg", ".jpeg"):
        raise ValueError("Task 1 material must be PNG/JPEG")


def load_benchmark(split, *, root=ROOT):
    if split not in ("dev", "test"):
        raise ValueError("split must be dev or test")
    rows = json.loads((root / f"evals/benchmark_{split}/benchmark.json").read_text(encoding="utf-8"))
    if not isinstance(rows, list) or not rows:
        raise ValueError("Benchmark must be a nonempty JSON array")
    for row in rows:
        validate_record(row, root=root)
    return rows


def check_benchmark(*, root=ROOT):
    splits = {s: load_benchmark(s, root=root) for s in ("dev", "test")}
    dev, test = splits["dev"], splits["test"]
    if {normalize(r["essay"]) for r in dev} & {normalize(r["essay"]) for r in test}:
        raise ValueError("Duplicate essay across dev/test")
    if {(r["task_type"], normalize(r["exam_question"])) for r in dev} & {
        (r["task_type"], normalize(r["exam_question"])) for r in test
    }:
        raise ValueError("Duplicate question across dev/test")

    def image_hashes(rows):
        return {hashlib.sha256((root / r["material"]).read_bytes()).hexdigest() for r in rows if r["material"]}

    if image_hashes(dev) & image_hashes(test):
        raise ValueError("Same Task 1 image across dev/test")
    rows = dev + test
    if len({r["case_id"] for r in rows}) != len(rows):
        raise ValueError("Duplicate case ID")
    if len({normalize(r["essay"]) for r in rows}) != len(rows):
        raise ValueError("Duplicate essay")
    if len(rows) < 30 or {r["task_type"] for r in rows} != {"task1", "task2"}:
        raise ValueError("Need at least 30 essays covering both Academic Tasks")
    bands = [r["scores"]["overall_band"] for r in rows]
    if min(bands) != 4 or max(bands) != 8:
        raise ValueError("Overall bands must span 4.0 to 8.0")
    return dict(
        total=len(rows),
        splits={s: len(rs) for s, rs in splits.items()},
        tasks=dict(sorted(Counter(r["task_type"] for r in rows).items())),
        task1_images=len({r["material"] for r in rows if r["material"]}),
    )


if __name__ == "__main__":
    try:
        print(json.dumps(check_benchmark(), ensure_ascii=False, indent=2))
    except (ValueError, FileNotFoundError, KeyError) as exc:
        raise SystemExit(str(exc)) from None
