"""Read-only, task-scoped retrieval for the pinned Member 1 descriptor index.

The local records are transport objects, not replacements for Member 3's schemas.
Pass chunk_factory=DescriptorChunk from Member 3 when wiring Dependencies.
"""
from dataclasses import dataclass
from pathlib import Path
import json
import re
from typing import Callable

from scripts.descriptor_data import CRITERIA, ROOT, SOURCE_URL, VERSION
from scripts.download_descriptors import EXPECTED_SHA256

COLLECTION_NAME = "writing_descriptors"
MAX_TOP_K = 3
QUERY_VERSION = "member2_criterion_v1"
QUERIES = {
    "task_achievement": "Academic Task 1 report: overview, key features, accurate comparisons and supporting data.",
    "task_response": "Academic Task 2 essay: address all parts, clear position, develop and support relevant ideas.",
    "coherence_cohesion": "Logical organization, progression, paragraphing, cohesive devices and referencing.",
    "lexical_resource": "Vocabulary range, precision, collocation, spelling and word formation errors.",
    "grammatical_range_accuracy": "Sentence structure range, complex sentences, grammar accuracy and punctuation.",
}


class RetrievalError(RuntimeError):
    """Stable public error; never includes essay, source text or backend diagnostics."""

    code = "RETRIEVAL_INVALID"

    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(f"{self.code}: {reason}")


@dataclass(frozen=True, slots=True)
class DescriptorChunk:
    chunk_id: str
    test_part: str
    criterion: str
    band: int
    version: str
    source_url: str
    text: str


@dataclass(frozen=True, slots=True)
class BandZeroPolicy:
    test_part: str
    band: int
    text: str
    source_page: int


def _arguments(task_type, criterion, top_k):
    task_type = getattr(task_type, "value", task_type)
    criterion = getattr(criterion, "value", criterion)
    if not isinstance(task_type, str) or task_type not in CRITERIA:
        raise RetrievalError("invalid_task_type")
    if not isinstance(criterion, str) or criterion not in CRITERIA[task_type]:
        raise RetrievalError("invalid_criterion")
    if type(top_k) is not int or not 1 <= top_k <= MAX_TOP_K:
        raise RetrievalError("invalid_top_k")
    return task_type, criterion


class DescriptorRetriever:
    """Synchronous retriever implementing the Member 3 retriever protocol.

    collection injection is for tests or an already opened Chroma collection.
    The default opens only an existing local DB and never creates a collection.
    """

    def __init__(self, db_path=None, *, collection=None,
                 chunk_factory: Callable = DescriptorChunk,
                 policy_path=None):
        self.db_path = Path(db_path) if db_path is not None else ROOT / "data/chroma_db"
        self.policy_path = Path(policy_path) if policy_path is not None else ROOT / "data/processed/descriptor_provenance.json"
        self._collection = collection
        self._chunk_factory = chunk_factory

    def _open_collection(self):
        if self._collection is None:
            if not (self.db_path / "chroma.sqlite3").is_file():
                raise RetrievalError("database_missing")
            try:
                import chromadb
                from chromadb.utils.embedding_functions import DefaultEmbeddingFunction

                client = chromadb.PersistentClient(path=str(self.db_path.resolve()))
                self._collection = client.get_collection(
                    name=COLLECTION_NAME, embedding_function=DefaultEmbeddingFunction()
                )
            except Exception:
                raise RetrievalError("database_unavailable") from None
        metadata = self._collection.metadata
        if not isinstance(metadata, dict) or metadata.get("descriptor_version") != VERSION:
            raise RetrievalError("collection_version_mismatch")
        if metadata.get("embedding_model") != "all-MiniLM-L6-v2":
            raise RetrievalError("embedding_model_mismatch")
        return self._collection

    def retrieve_descriptors(self, task_type, criterion, top_k=3):
        task_type, criterion = _arguments(task_type, criterion, top_k)
        query = f"IELTS Academic Writing {task_type}. {QUERIES[criterion]}"
        return self.retrieve_for_query(task_type, criterion, query, top_k)

    def retrieve_for_query(self, task_type, criterion, query, top_k=3):
        """Evaluation/search entrypoint; the same hard filters and validation apply."""
        task_type, criterion = _arguments(task_type, criterion, top_k)
        if not isinstance(query, str) or not query.strip() or len(query) > 2000:
            raise RetrievalError("invalid_query")
        try:
            collection = self._open_collection()
            raw = collection.query(
                query_texts=[query], n_results=top_k,
                where={"$and": [{"test_part": task_type}, {"criterion": criterion}]},
                include=["documents", "metadatas"],
            )
        except RetrievalError:
            raise
        except Exception:
            raise RetrievalError("query_failed") from None
        try:
            rows = []
            for key in ("ids", "documents", "metadatas"):
                batch = raw[key]
                if not isinstance(batch, list) or len(batch) != 1 or not isinstance(batch[0], list):
                    raise ValueError("Invalid result shape")
                rows.append(batch[0])
            ids, documents, metadatas = rows
            if not ids:
                raise RetrievalError("no_chunks")
            if not len(ids) == len(documents) == len(metadatas) or len(ids) > top_k:
                raise ValueError("Invalid result length")
            chunks, seen = [], set()
            expected = {"chunk_id", "test_part", "criterion", "band", "version", "source_url"}
            for cid, document, metadata in zip(ids, documents, metadatas):
                if not isinstance(metadata, dict) or set(metadata) != expected:
                    raise ValueError("Invalid metadata")
                if not isinstance(cid, str) or not re.fullmatch(r"[A-Za-z0-9_.:-]{1,100}", cid):
                    raise ValueError("Invalid ID")
                if cid in seen or metadata["chunk_id"] != cid:
                    raise ValueError("Duplicate or conflicting ID")
                if metadata["test_part"] != task_type or metadata["criterion"] != criterion:
                    raise ValueError("Filter violation")
                if type(metadata["band"]) is not int or metadata["band"] not in range(1, 10):
                    raise ValueError("Invented band")
                if metadata["version"] != VERSION or metadata["source_url"] != SOURCE_URL:
                    raise ValueError("Invalid provenance")
                if not isinstance(document, str) or not document.strip() or "\ufffd" in document:
                    raise ValueError("Invalid text")
                chunks.append(self._chunk_factory(**metadata, text=document))
                seen.add(cid)
            return chunks
        except RetrievalError:
            raise
        except Exception:
            raise RetrievalError("invalid_chunks") from None

    def get_band_zero_policy(self, task_type):
        """Separate policy channel. These records MUST NOT be descriptor_refs."""
        task_type = getattr(task_type, "value", task_type)
        if not isinstance(task_type, str) or task_type not in CRITERIA:
            raise RetrievalError("invalid_task_type")
        try:
            data = json.loads(self.policy_path.read_text(encoding="utf-8"))
            if data["source_url"] != SOURCE_URL or data["source_sha256"] != EXPECTED_SHA256:
                raise ValueError("Invalid policy provenance")
            policies = data["band_zero_policies"]
            if not isinstance(policies, list) or len(policies) != 2:
                raise ValueError("Expected both policies")
            validated = {}
            for policy in policies:
                if not isinstance(policy, dict) or set(policy) != {"test_part", "band", "text", "source_page"}:
                    raise ValueError("Invalid policy shape")
                task = policy["test_part"]
                if task not in CRITERIA or task in validated:
                    raise ValueError("Invalid policy task")
                if type(policy["band"]) is not int or policy["band"] != 0:
                    raise ValueError("Invalid policy band")
                if type(policy["source_page"]) is not int or policy["source_page"] != {"task1": 5, "task2": 9}[task]:
                    raise ValueError("Invalid source page")
                if not isinstance(policy["text"], str) or not policy["text"].strip() or "\ufffd" in policy["text"]:
                    raise ValueError("Invalid policy text")
                validated[task] = BandZeroPolicy(**policy)
            return validated[task_type]
        except Exception:
            raise RetrievalError("policy_unavailable") from None


def retrieve_descriptors(task_type, criterion, top_k=3):
    """Default tool: use DescriptorRetriever to configure DB path or DTO factories."""
    return DescriptorRetriever().retrieve_descriptors(task_type, criterion, top_k)


class Member3RetrieverAdapter:
    """Map our local error to Member 3's actual DependencyFailure constructor."""

    def __init__(self, retriever, *, failure_factory):
        self.retriever = retriever
        self.failure_factory = failure_factory

    def retrieve_descriptors(self, task_type, criterion, top_k=3):
        try:
            return self.retriever.retrieve_descriptors(task_type, criterion, top_k)
        except RetrievalError as exc:
            raise self.failure_factory(exc.code) from None
