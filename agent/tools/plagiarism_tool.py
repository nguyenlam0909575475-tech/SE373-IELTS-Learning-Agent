"""Read-only, local word n-gram comparison with exact essay offsets for plagiarism check.

Similarity is the fraction of essay tokens covered by shared n-grams with
the best single corpus source. This is a copying heuristic, not a semantic
plagiarism verdict. Defaults are provisional until calibrated on real data.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from threading import Lock

from .contracts import (
    Evidence,
    Member4DependencyError,
    PlagiarismMatch,
    PlagiarismResult,
)

_TOKENS = re.compile(r"[^\W_]+(?:['’-][^\W_]+)*", re.UNICODE)
DEFAULT_CORPUS_PATH = Path(__file__).resolve().parents[2] / "data/corpus_plagiarism/corpus.jsonl"
_SOURCE_ID = re.compile(r"[A-Za-z0-9_.:-]{1,100}\Z")
_CHECKER_LOCK = Lock()


@dataclass(frozen=True)
class CorpusEntry:
    source_id: str
    text: str
    source_url: str
    license: str | None = None
    task_type: str | None = None
    exam_question: str | None = None
    topic: str | None = None

    @classmethod
    def from_record(cls, record):
        """Accept Member 1's six fields and legacy records without inventing a license."""
        if not isinstance(record, dict):
            raise ValueError("corpus record must be an object")
        required = {key: record[key] for key in ("source_id", "text", "source_url")}
        optional = {key: record[key] for key in ("license", "task_type", "exam_question", "topic") if key in record}
        return cls(**required, **optional)


class PlagiarismChecker:
    def __init__(
        self, corpus, *, threshold: float = 0.8,
        ngram_size: int = 5, min_shared_words: int = 20,
    ):
        if isinstance(threshold, bool) or not isinstance(threshold, (int, float)) or not 0 < threshold <= 1:
            raise ValueError("threshold must be in (0, 1]")
        if type(ngram_size) is not int or ngram_size < 2:
            raise ValueError("ngram_size must be an integer >= 2")
        if type(min_shared_words) is not int or min_shared_words < ngram_size:
            raise ValueError("min_shared_words must be >= ngram_size")
        try:
            entries = tuple(corpus)
        except TypeError:
            raise Member4DependencyError("PLAGIARISM_CORPUS_INVALID") from None
        if not entries:
            raise Member4DependencyError("PLAGIARISM_CORPUS_MISSING")
        seen = set()
        self._sources = []
        for entry in entries:
            if not isinstance(entry, CorpusEntry) or any(
                not isinstance(item, str) or not item.strip()
                for item in (entry.source_id, entry.text, entry.source_url)
            ) or entry.source_id in seen:
                raise Member4DependencyError("PLAGIARISM_CORPUS_INVALID")
            if not _SOURCE_ID.fullmatch(entry.source_id) or any(
                item is not None and (not isinstance(item, str) or not item.strip())
                for item in (entry.license, entry.exam_question, entry.topic)
            ) or entry.task_type not in (None, "task1", "task2"):
                raise Member4DependencyError("PLAGIARISM_CORPUS_INVALID")
            tokens = [m.group().casefold() for m in _TOKENS.finditer(entry.text)]
            if len(tokens) < ngram_size:
                raise Member4DependencyError("PLAGIARISM_CORPUS_INVALID")
            grams = {tuple(tokens[i:i + ngram_size]) for i in range(len(tokens) - ngram_size + 1)}
            self._sources.append((entry.source_id, grams))
            seen.add(entry.source_id)
        self.entries = entries
        self.threshold = float(threshold)
        self.ngram_size = ngram_size
        self.min_shared_words = min_shared_words

    @classmethod
    def from_file(cls, path: str | Path, **options):
        """Load a JSON array, or JSONL for an explicitly named .jsonl file.

        Every source needs its ID, text and URL; a list of links alone
        cannot be compared. No network calls or silent clean fallback.
        """
        if Path(path).suffix.lower() == ".jsonl":
            return cls.from_jsonl(path, **options)
        try:
            data = json.loads(Path(path).read_text(encoding="utf-8"))
            if not isinstance(data, list):
                raise ValueError("corpus must be an array")
            entries = [CorpusEntry.from_record(record) for record in data]
        except FileNotFoundError:
            raise Member4DependencyError("PLAGIARISM_CORPUS_MISSING") from None
        except (OSError, UnicodeError, ValueError, TypeError, KeyError):
            raise Member4DependencyError("PLAGIARISM_CORPUS_INVALID") from None
        return cls(entries, **options)

    @classmethod
    def from_jsonl(cls, path: str | Path, **options):
        """Load permitted sources explicitly; never download or write a corpus."""
        try:
            with Path(path).open(encoding="utf-8") as stream:
                entries = [CorpusEntry.from_record(json.loads(line)) for line in stream if line.strip()]
        except FileNotFoundError:
            raise Member4DependencyError("PLAGIARISM_CORPUS_MISSING") from None
        except (OSError, UnicodeError, ValueError, TypeError, KeyError):
            raise Member4DependencyError("PLAGIARISM_CORPUS_INVALID") from None
        return cls(entries, **options)

    def check_plagiarism(self, essay: str) -> PlagiarismResult:
        if not isinstance(essay, str):
            raise TypeError("essay must be a string")
        tokens = list(_TOKENS.finditer(essay))
        words = [m.group().casefold() for m in tokens]
        size = self.ngram_size
        if len(words) < size:
            return PlagiarismResult(False, 0.0)
        query = [tuple(words[i:i + size]) for i in range(len(words) - size + 1)]
        maximum = 0.0
        possible = False
        matches = []
        for source_id, grams in self._sources:
            intervals = []
            for i, gram in enumerate(query):
                if gram in grams:
                    if intervals and i <= intervals[-1][1]:
                        intervals[-1][1] = i + size
                    else:
                        intervals.append([i, i + size])
            shared = sum(end - start for start, end in intervals)
            similarity = shared / len(words)
            maximum = max(maximum, similarity)
            possible |= similarity >= self.threshold and shared >= self.min_shared_words
            for start, end in intervals:
                left, right = tokens[start].start(), tokens[end - 1].end()
                matches.append(PlagiarismMatch(source_id, Evidence(essay[left:right], left, right)))
        return PlagiarismResult(possible, maximum, matches)


@lru_cache(maxsize=1)
def _load_checker(path: str, modified_ns: int, size: int) -> PlagiarismChecker:
    # The file signature invalidates the index after a corpus update.
    return PlagiarismChecker.from_file(path)


def get_default_checker() -> PlagiarismChecker:
    """Reuse the read-only index; missing/changed/broken data never becomes a clean result."""
    path = Path(DEFAULT_CORPUS_PATH)
    try:
        stat = path.stat()
    except FileNotFoundError:
        raise Member4DependencyError("PLAGIARISM_CORPUS_MISSING") from None
    except OSError:
        raise Member4DependencyError("PLAGIARISM_CORPUS_INVALID") from None
    with _CHECKER_LOCK:
        return _load_checker(str(path.resolve()), stat.st_mtime_ns, stat.st_size)


def check_plagiarism(essay: str) -> PlagiarismResult:
    """Check the shipped corpus, reusing its index across requests."""
    return get_default_checker().check_plagiarism(essay)
