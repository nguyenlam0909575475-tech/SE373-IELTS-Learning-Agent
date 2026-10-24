"""Scope/failure tests; fixtures are synthetic, not grading benchmarks."""
import copy
import importlib.util
import json
import tempfile
import unittest
from dataclasses import asdict
from enum import Enum
from pathlib import Path
from unittest.mock import Mock, patch

from scripts.descriptor_data import CRITERIA, SOURCE_URL, VERSION
from scripts.download_descriptors import EXPECTED_SHA256
from src.tools.rag_descriptors import (
    DescriptorRetriever,
    Member3RetrieverAdapter,
    RetrievalError,
    retrieve_descriptors,
)


def synthetic_chunk(task="task2", criterion="lexical_resource", band=7):
    return dict(chunk_id=f"writing_{task}_{criterion}_b{band}_2023_05",
                test_part=task, criterion=criterion, band=band, version=VERSION,
                source_url=SOURCE_URL, text="SYNTHETIC descriptor for retrieval contract testing.")


def collection_for(chunks=None):
    chunks = chunks if chunks is not None else [synthetic_chunk()]
    collection = Mock()
    collection.metadata = {"descriptor_version": VERSION, "embedding_model": "all-MiniLM-L6-v2"}
    collection.query.return_value = {
        "ids": [[c["chunk_id"] for c in chunks]],
        "documents": [[c["text"] for c in chunks]],
        "metadatas": [[{k: v for k, v in c.items() if k != "text"} for c in chunks]],
    }
    return collection


class RetrievalTests(unittest.TestCase):
    def assert_retrieval_error(self, retriever, reason, *args):
        with self.assertRaises(RetrievalError) as error:
            retriever.retrieve_descriptors(*(args or ("task2", "lexical_resource")))
        self.assertEqual(error.exception.code, "RETRIEVAL_INVALID")
        self.assertEqual(error.exception.reason, reason)

    def test_all_eight_scopes_use_hard_and_filter(self):
        for task, criteria in CRITERIA.items():
            for criterion in criteria:
                with self.subTest(task=task, criterion=criterion):
                    collection = collection_for([synthetic_chunk(task, criterion)])
                    result = DescriptorRetriever(collection=collection).retrieve_descriptors(task, criterion)
                    self.assertEqual(asdict(result[0]), synthetic_chunk(task, criterion))
                    query = collection.query.call_args.kwargs
                    self.assertEqual(query["where"], {"$and": [{"test_part": task}, {"criterion": criterion}]})
                    self.assertEqual(query["n_results"], 3)
                    self.assertEqual(query["include"], ["documents", "metadatas"])

    def test_enum_inputs_and_member3_factory(self):
        class Task(str, Enum):
            TASK2 = "task2"
        class Criterion(str, Enum):
            LEXIS = "lexical_resource"
        factory = Mock(side_effect=lambda **fields: fields)
        retriever = DescriptorRetriever(collection=collection_for(), chunk_factory=factory)
        result = retriever.retrieve_descriptors(Task.TASK2, Criterion.LEXIS, 1)
        self.assertEqual(result, [synthetic_chunk()])
        factory.assert_called_once_with(**synthetic_chunk())

    def test_invalid_arguments_fail_before_backend(self):
        cases = [("task3", "lexical_resource", 3), (None, "lexical_resource", 3),
                 ([], "lexical_resource", 3), ("task1", "task_response", 3),
                 ("task2", "task_achievement", 3), ("task2", None, 3),
                 ("task2", "lexical_resource", True), ("task2", "lexical_resource", 0),
                 ("task2", "lexical_resource", 4), ("task2", "lexical_resource", 1.5)]
        for args in cases:
            with self.subTest(args=args):
                collection = collection_for()
                with self.assertRaises(RetrievalError):
                    DescriptorRetriever(collection=collection).retrieve_descriptors(*args)
                collection.query.assert_not_called()

    def test_missing_db_is_not_created(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "absent"
            self.assert_retrieval_error(DescriptorRetriever(path), "database_missing")
            self.assertFalse(path.exists())

    def test_default_tool_uses_retriever_contract(self):
        with patch.object(DescriptorRetriever, "retrieve_descriptors", return_value=["sentinel"]) as method:
            self.assertEqual(retrieve_descriptors("task2", "lexical_resource"), ["sentinel"])
            method.assert_called_once_with("task2", "lexical_resource", 3)

    def test_empty_result_stops_without_fallback(self):
        self.assert_retrieval_error(DescriptorRetriever(collection=collection_for([])), "no_chunks")

    def test_backend_exception_is_redacted(self):
        collection = collection_for()
        collection.query.side_effect = RuntimeError("SENSITIVE ESSAY / KEY")
        with self.assertRaises(RetrievalError) as error:
            DescriptorRetriever(collection=collection).retrieve_descriptors("task2", "lexical_resource")
        self.assertEqual(str(error.exception), "RETRIEVAL_INVALID: query_failed")

    def test_wrong_task_criterion_source_and_corrupt_fields_rejected(self):
        mutations = [("test_part", "task1"), ("criterion", "coherence_cohesion"),
                     ("band", True), ("band", 0), ("band", 6.5), ("band", float("nan")),
                     ("text", ""), ("text", "broken \ufffd"), ("text", None),
                     ("version", "wrong"), ("source_url", "https://example.com"),
                     ("chunk_id", "invalid id")]
        for field, value in mutations:
            with self.subTest(field=field, value=value):
                chunk = dict(synthetic_chunk(), **{field: value})
                self.assert_retrieval_error(DescriptorRetriever(collection=collection_for([chunk])), "invalid_chunks")

    def test_result_shape_and_id_mismatch_rejected(self):
        good = collection_for().query.return_value
        bads = [None, {}, {**good, "documents": None}, {**good, "ids": []},
                {**good, "documents": [[]]}, {**good, "metadatas": [[{}]]},
                {**good, "ids": [["different_id"]]}, {**good, "ids": [[], []]}]
        for raw in bads:
            with self.subTest(raw=raw):
                collection = collection_for()
                collection.query.return_value = raw
                self.assert_retrieval_error(DescriptorRetriever(collection=collection), "invalid_chunks")

    def test_duplicate_ids_and_too_many_results_rejected(self):
        self.assert_retrieval_error(DescriptorRetriever(collection=collection_for([synthetic_chunk()] * 2)), "invalid_chunks")
        chunks = [synthetic_chunk(band=b) for b in (5, 6)]
        self.assert_retrieval_error(DescriptorRetriever(collection=collection_for(chunks)), "invalid_chunks", "task2", "lexical_resource", 1)

    def test_invalid_collection_identity_prevents_query(self):
        for key, value, reason in [("descriptor_version", "old", "collection_version_mismatch"),
                                   ("embedding_model", "other-model", "embedding_model_mismatch")]:
            collection = collection_for()
            collection.metadata[key] = value
            self.assert_retrieval_error(DescriptorRetriever(collection=collection), reason)
            collection.query.assert_not_called()

    def test_custom_query_preserves_filters(self):
        collection = collection_for()
        retriever = DescriptorRetriever(collection=collection)
        retriever.retrieve_for_query("task2", "lexical_resource", "Repeated vocabulary", 2)
        self.assertEqual(collection.query.call_args.kwargs["query_texts"], ["Repeated vocabulary"])
        for query in ("", None, "x" * 2001):
            with self.assertRaises(RetrievalError):
                retriever.retrieve_for_query("task2", "lexical_resource", query)

    def test_dependency_failure_adapter(self):
        class ActualFailure(RuntimeError):
            pass
        factory = Mock(side_effect=lambda code: ActualFailure(code))
        adapter = Member3RetrieverAdapter(DescriptorRetriever(collection=collection_for([])), failure_factory=factory)
        with self.assertRaisesRegex(ActualFailure, "RETRIEVAL_INVALID"):
            adapter.retrieve_descriptors("task2", "lexical_resource")
        factory.assert_called_once_with("RETRIEVAL_INVALID")

    def test_policy_stays_separate_from_refs(self):
        data = {"source_url": SOURCE_URL, "source_sha256": EXPECTED_SHA256,
                "band_zero_policies": [dict(test_part=task, band=0, text="SYNTHETIC Band 0 policy.", source_page=page)
                                       for task, page in (("task1", 5), ("task2", 9))]}
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "policy.json"
            path.write_text(json.dumps(data), encoding="utf-8")
            retriever = DescriptorRetriever(collection=collection_for(), policy_path=path)
            policy = retriever.get_band_zero_policy("task1")
            self.assertEqual(policy.source_page, 5)
            self.assertFalse(hasattr(policy, "chunk_id"))
            for mutate in (lambda d: d.update(source_sha256="0" * 64),
                           lambda d: d["band_zero_policies"][0].update(source_page=9),
                           lambda d: d["band_zero_policies"][0].update(band=True),
                           lambda d: d["band_zero_policies"].pop()):
                bad = copy.deepcopy(data)
                mutate(bad)
                path.write_text(json.dumps(bad), encoding="utf-8")
                with self.assertRaises(RetrievalError):
                    retriever.get_band_zero_policy("task1")

    def test_policy_missing_is_an_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(RetrievalError):
                DescriptorRetriever(policy_path=Path(tmp) / "absent").get_band_zero_policy("task1")


@unittest.skipUnless(importlib.util.find_spec("chromadb"), "Requires pinned Chroma dependency")
class ChromaRetrievalTests(unittest.TestCase):
    def test_real_persistence_query_and_scope_without_model_download(self):
        import chromadb
        from chromadb.utils.embedding_functions import DefaultEmbeddingFunction

        # Real Chroma persistence/filters, deterministic replacement only for embedding.
        chunks = [synthetic_chunk(task, criterion, band)
                  for task, criteria in CRITERIA.items() for criterion in criteria for band in (5, 7)]
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
            client = chromadb.PersistentClient(path=tmp)
            with patch.object(DefaultEmbeddingFunction, "__call__", lambda self, input: [[1., 0., 0.] for _ in input]):
                collection = client.create_collection("writing_descriptors", embedding_function=DefaultEmbeddingFunction(),
                                                     metadata={"descriptor_version": VERSION, "embedding_model": "all-MiniLM-L6-v2"})
                collection.add(ids=[c["chunk_id"] for c in chunks], documents=[c["text"] for c in chunks],
                               metadatas=[{k: v for k, v in c.items() if k != "text"} for c in chunks])
                # Exercise the production existing-DB opening path, not injected collection.
                retriever = DescriptorRetriever(tmp)
                for task, criteria in CRITERIA.items():
                    for criterion in criteria:
                        result = retriever.retrieve_descriptors(task, criterion, 3)
                        self.assertEqual(len(result), 2)
                        self.assertTrue(all(c.test_part == task and c.criterion == criterion for c in result))
                self.assertEqual(collection.count(), len(chunks))


if __name__ == "__main__":
    unittest.main()
