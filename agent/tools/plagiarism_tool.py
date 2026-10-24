"""Read-only, local word n-gram comparison with exact essay offsets.

Similarity is the fraction of essay tokens covered by shared n-grams with
the best single corpus source. This is a copying heuristic, not a semantic
plagiarism verdict. Defaults are provisional until calibrated on real data.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

from .contracts import (
    Evidence,
    Member4DependencyError,
    PlagiarismMatch,
    PlagiarismResult,
)

_TOKENS = re.compile(r"[^\W_]+(?:['’-][^\W_]+)*", re.UNICODE)
DEFAULT_CORPUS_PATH = Path(__file__).resolve().parents[2] / "data/knowledge/sample_corpus_links.json"


@dataclass(frozen=True)
class CorpusEntry:
    source_id: str
    text: str
    source_url: str
    license: str


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
        entries = tuple(corpus)
        if not entries:
            raise Member4DependencyError("PLAGIARISM_CORPUS_MISSING")
        seen = set()
        self._sources = []
        for entry in entries:
            if not isinstance(entry, CorpusEntry) or any(
                not isinstance(item, str) or not item.strip()
                for item in (entry.source_id, entry.text, entry.source_url, entry.license)
            ) or entry.source_id in seen:
                raise Member4DependencyError("PLAGIARISM_CORPUS_INVALID")
            tokens = [m.group().casefold() for m in _TOKENS.finditer(entry.text)]
            if len(tokens) < ngram_size:
                raise Member4DependencyError("PLAGIARISM_CORPUS_INVALID")
            grams = {tuple(tokens[i:i + ngram_size]) for i in range(len(tokens) - ngram_size + 1)}
            self._sources.append((entry.source_id, grams))
            seen.add(entry.source_id)
        self.threshold = float(threshold)
        self.ngram_size = ngram_size
        self.min_shared_words = min_shared_words

    @classmethod
    def from_file(cls, path: str | Path, **options):
        """Load a JSON array, or JSONL for an explicitly named .jsonl file.

        Every source needs its text, URL and license; a list of links alone
        cannot be compared. No network calls or silent clean fallback.
        """
        if Path(path).suffix.lower() == ".jsonl":
            return cls.from_jsonl(path, **options)
        try:
            data = json.loads(Path(path).read_text(encoding="utf-8"))
            if not isinstance(data, list):
                raise ValueError("corpus must be an array")
            entries = [CorpusEntry(**record) for record in data]
        except FileNotFoundError:
            raise Member4DependencyError("PLAGIARISM_CORPUS_MISSING") from None
        except (OSError, UnicodeError, ValueError, TypeError):
            raise Member4DependencyError("PLAGIARISM_CORPUS_INVALID") from None
        return cls(entries, **options)

    @classmethod
    def from_jsonl(cls, path: str | Path, **options):
        """Load permitted sources explicitly; never download or write a corpus."""
        try:
            with Path(path).open(encoding="utf-8") as stream:
                entries = [CorpusEntry(**json.loads(line)) for line in stream if line.strip()]
        except FileNotFoundError:
            raise Member4DependencyError("PLAGIARISM_CORPUS_MISSING") from None
        except (OSError, UnicodeError, ValueError, TypeError):
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


def check_plagiarism(essay: str) -> PlagiarismResult:
    """Default tool. Missing corpus is an error, never a clean result.

    The agent can construct one PlagiarismChecker and reuse its bound method
    across requests rather than rebuilding the corpus index each time.
    """
    return PlagiarismChecker.from_file(DEFAULT_CORPUS_PATH).check_plagiarism(essay)
