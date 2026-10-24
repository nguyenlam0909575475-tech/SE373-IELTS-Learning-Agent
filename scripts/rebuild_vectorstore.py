"""Validate descriptors and synchronize a dedicated persistent Chroma collection."""
import argparse
import hashlib
import json
from pathlib import Path

try:
    from .descriptor_data import ROOT, VERSION, load_dataset
except ImportError:
    from descriptor_data import ROOT, VERSION, load_dataset

COLLECTION = 'writing_descriptors'


def rebuild(source, db_path):
    chunks = load_dataset(source)  # Fail before touching any existing collection.
    import chromadb
    from chromadb.utils.embedding_functions import DefaultEmbeddingFunction

    embedding = DefaultEmbeddingFunction()
    documents = [c['text'] for c in chunks]
    vectors = embedding(documents)  # Download/embedding failure preserves the old collection.
    digest = hashlib.sha256(Path(source).read_bytes()).hexdigest()
    client = chromadb.PersistentClient(path=str(Path(db_path).resolve()))
    collection = client.get_or_create_collection(
        name=COLLECTION, embedding_function=embedding,
        metadata={'descriptor_version': VERSION, 'embedding_model': 'all-MiniLM-L6-v2'},
    )
    if collection.metadata.get('embedding_model') != 'all-MiniLM-L6-v2':
        raise ValueError('Existing collection uses a different embedding model')
    ids = [c['chunk_id'] for c in chunks]
    collection.upsert(ids=ids, documents=documents, embeddings=vectors,
                      metadatas=[{k: v for k, v in c.items() if k != 'text'} for c in chunks])
    stale = sorted(set(collection.get()['ids']) - set(ids))
    if stale:
        collection.delete(ids=stale)
    if collection.count() != len(chunks):
        raise RuntimeError('Stored count does not match validated source')
    collection.modify(metadata={'descriptor_version': VERSION, 'embedding_model': 'all-MiniLM-L6-v2', 'source_sha256': digest})
    return {'collection': COLLECTION, 'count': collection.count(), 'source_sha256': digest, 'embedding_model': 'all-MiniLM-L6-v2', 'db_path': str(Path(db_path).resolve())}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=ROOT / 'data/processed/writing_descriptors.json')
    parser.add_argument('--db-path', type=Path, default=ROOT / 'data/chroma_db')
    parser.add_argument('--validate-only', action='store_true')
    args = parser.parse_args()
    try:
        result = {'validated_chunks': len(load_dataset(args.source))} if args.validate_only else rebuild(args.source, args.db_path)
    except (ValueError, OSError, ImportError) as exc:
        parser.exit(1, f'Rebuild failed: {exc}\n')
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
