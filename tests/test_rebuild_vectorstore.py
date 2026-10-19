import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import chromadb
from chromadb.utils.embedding_functions import DefaultEmbeddingFunction
from scripts.descriptor_data import ROOT, load_dataset
from scripts.rebuild_vectorstore import COLLECTION, rebuild


class RebuildTests(unittest.TestCase):
    def test_persistence_filters_stale_ids_and_other_collection(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
            client = chromadb.PersistentClient(path=tmp)
            other = client.create_collection('unrelated', embedding_function=None)
            other.add(ids=['keep'], embeddings=[[1., 0., 0.]])
            # Only embedding inference is replaced; persistence/query/filtering use real Chroma.
            with patch.object(DefaultEmbeddingFunction, '__call__', lambda self, input: [[1., 0., 0.] for _ in input]):
                rebuild(ROOT / 'data/processed/writing_descriptors.json', tmp)
                col = client.get_collection(COLLECTION)
                col.add(ids=['stale'], documents=['old'], embeddings=[[1., 0., 0.]], metadatas=[{'test_part': 'task1'}])
                rebuild(ROOT / 'data/processed/writing_descriptors.json', tmp)
            reopened = chromadb.PersistentClient(path=tmp).get_collection(COLLECTION)
            self.assertEqual(reopened.count(), 72)
            self.assertNotIn('stale', reopened.get()['ids'])
            self.assertEqual(other.get()['ids'], ['keep'])
            result = reopened.query(query_embeddings=[[1., 0., 0.]], n_results=3,
                where={'$and': [{'test_part': 'task1'}, {'criterion': 'lexical_resource'}]})
            self.assertEqual(len(result['ids'][0]), 3)
            self.assertTrue(all(m['test_part'] == 'task1' and m['criterion'] == 'lexical_resource' for m in result['metadatas'][0]))
            stored = reopened.get(include=['documents', 'metadatas'])
            actual = {cid: dict(meta, text=text) for cid, meta, text in zip(stored['ids'], stored['metadatas'], stored['documents'])}
            self.assertEqual(actual, {c['chunk_id']: c for c in load_dataset()})

    def test_invalid_source_does_not_create_database(self):
        with tempfile.TemporaryDirectory() as tmp:
            source, db = Path(tmp) / 'bad.json', Path(tmp) / 'db'
            source.write_text(json.dumps({'chunks': []}), encoding='utf-8')
            with self.assertRaises(ValueError):
                rebuild(source, db)
            self.assertFalse(db.exists())
