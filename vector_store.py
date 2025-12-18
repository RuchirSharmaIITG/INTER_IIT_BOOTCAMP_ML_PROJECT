import os
import json
import logging
from sentence_transformers import SentenceTransformer, util
import torch

log = logging.getLogger("vector_store")

class EpisodicStore:
    """
    Simple episodic store using sentence-transformers for semantic search.
    - add_event(text, metadata)
    - query(query_text, k)
    - persist/load (simple JSON)
    """

    def __init__(self, path: str = "episodic_store.json"):
        self.path = path
        self.docs = []  # List of {"text":..., "embedding":..., "metadata":...}
        self.model = SentenceTransformer('all-MiniLM-L6-v2') # Loads the model

        if os.path.exists(self.path):
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    loaded_docs = json.load(f)
                    for doc in loaded_docs:
                        # Convert embedding from list back to torch.Tensor
                        doc['embedding'] = torch.tensor(doc['embedding'])
                    self.docs = loaded_docs
            except Exception:
                self.docs = []


    def add_event(self, text: str, metadata: dict = None):
        # Encode the text to get its vector embedding
        embedding = self.model.encode(text, convert_to_tensor=True)
        self.docs.append({
            "text": text,
            "embedding": embedding,
            "metadata": metadata or {}
        })
        self.persist()


    def persist(self):
        try:
            # Create a serializable copy of docs
            docs_to_save = []
            for doc in self.docs:
                serializable_doc = doc.copy()
                # Convert tensor to a list for JSON serialization
                serializable_doc['embedding'] = doc['embedding'].tolist()
                docs_to_save.append(serializable_doc)

            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(docs_to_save, f, ensure_ascii=False, indent=2)
        except Exception as e:
            log.warning("Failed to persist episodic store: %s", e)


    def query(self, query_text: str, k: int = 5):
        if not self.docs:
            return []

        # Encode the query to get its embedding
        query_embedding = self.model.encode(query_text, convert_to_tensor=True)

        # Get all stored document embeddings
        corpus_embeddings = torch.stack([doc['embedding'] for doc in self.docs])

        # Use the library's semantic search utility to find the top k hits
        hits = util.semantic_search(query_embedding, corpus_embeddings, top_k=k)

        # The result is a list of lists, we take the first list for our single query
        hits = hits[0]

        results = []
        for hit in hits:
            doc_index = hit['corpus_id']
            doc = self.docs[doc_index]
            results.append({
                "text": doc["text"],
                "score": hit['score'],
                "metadata": doc.get("metadata", {})
            })
        return results