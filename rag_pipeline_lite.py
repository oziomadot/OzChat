import os
import numpy as np
import chromadb
from typing import List, Dict, Optional
from dataclasses import dataclass
from dotenv import load_dotenv
from rank_bm25 import BM25Okapi
from openai import OpenAI
import os

load_dotenv()
# Global client - lazy init
_openai_client = None

def cosine_similarity_simple(a, b):
    """Pure Python cosine similarity to avoid sklearn dependency"""
    a = np.array(a)
    b = np.array(b)
    if a.ndim == 1:
        a = a.reshape(1, -1)
    if b.ndim == 1:
        b = b.reshape(1, -1)
    
    dot_product = np.dot(a, b.T)
    norm_a = np.linalg.norm(a, axis=1)
    norm_b = np.linalg.norm(b, axis=1)
    
    # Avoid division by zero
    norm_a = np.where(norm_a == 0, 1, norm_a)
    norm_b = np.where(norm_b == 0, 1, norm_b)
    
    return dot_product / (norm_a[:, np.newaxis] * norm_b)

def get_client():
    global _openai_client
    if _openai_client is None:
        api_key = os.environ.get("OPEN_ROUTER") or os.environ.get("OPENAI_API_KEY")
        base_url = os.environ.get("OPENAI_BASE_URL", "https://openrouter.ai/api/v1")
        
        if not api_key:
            print("⚠️  No API key found - LLM features disabled")
            _openai_client = None
        else:
            _openai_client = OpenAI(api_key=api_key, base_url=base_url)
    
    return _openai_client

model="openrouter/free"

@dataclass
class RetrievedChunk:
    content: str
    source_doc: str
    chunk_id: str
    similarity_score: float

class RAGPipelineLite:
    def __init__(self, vector_db_path="./nsr_vector_db", collection_name="nsr_policies",
                top_k=20, enable_reranking=True, use_ensemble=True):
        self.vector_db_path = vector_db_path
        self.collection_name = collection_name
        self.top_k = top_k
        self.enable_reranking = enable_reranking
        self.use_ensemble = use_ensemble

        try:
            self.client = chromadb.PersistentClient(path=vector_db_path)
            print(f"Connected to ChromaDB at: {vector_db_path}")

            # Check if collection exists first
            existing_collections = self.client.list_collections()
            collection_names = [c.name for c in existing_collections]
            print(f"Available collections: {collection_names}")

            if collection_name not in collection_names:
                print(f"❌ Collection '{collection_name}' does NOT exist. Creating it now...")
                self.collection = self.client.create_collection(
                    name=collection_name,
                )
            else:
                self.collection = self.client.get_collection(name=collection_name)
                print(f"✅ Loaded existing collection '{collection_name}' with {self.collection.count()} items")

        except Exception as e:
            print(f"❌ ChromaDB init failed: {type(e).__name__}: {str(e)}")
            raise

        # BM25 init
        self.bm25 = None
        self.all_docs = []
        self._initialize_bm25()
        self.output_length_limit = 500

    def _initialize_bm25(self):
        try:
                all_results = self.collection.get(include=['documents', 'metadatas'])
                if all_results['documents']:
                    self.all_docs = all_results['documents']
                    tokenized_docs = [doc.lower().split() for doc in self.all_docs]
                    self.bm25 = BM25Okapi(tokenized_docs)
        except Exception as e:
                print(f"⚠️ BM25 init error: {e}")

    def _get_openai_embedding(self, text: str) -> List[float]:
        """Get embedding from OpenAI API instead of local model"""
        client = get_client()
        if client is None:
            # Fallback to simple TF-IDF style embedding
            words = text.lower().split()
            # Create simple frequency-based embedding
            vocab = set(words)
            embedding = [words.count(word) / len(words) for word in sorted(vocab)]
            # Pad/truncate to fixed size
            if len(embedding) < 384:
                embedding.extend([0.0] * (384 - len(embedding)))
            else:
                embedding = embedding[:384]
            return embedding
        
        try:
            response = client.embeddings.create(
                model="text-embedding-ada-002",  # or "text-embedding-3-small" for smaller
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"⚠️ OpenAI embedding error: {e}")
            # Fallback to simple embedding
            words = text.lower().split()
            vocab = set(words)
            embedding = [words.count(word) / len(words) for word in sorted(vocab)]
            if len(embedding) < 384:
                embedding.extend([0.0] * (384 - len(embedding)))
            else:
                embedding = embedding[:384]
            return embedding

    def _semantic_retrieve(self, query: str, k: int) -> List[RetrievedChunk]:
        query_emb = [self._get_openai_embedding(query)]
        results = self.collection.query(query_embeddings=query_emb, n_results=k)
        chunks = []
        if results['documents'] and results['documents'][0]:
            metadatas = results.get('metadatas', [{}]*len(results['documents'][0]))[0]
            distances = results.get('distances', [[0]*len(results['documents'][0])])[0]
            for i, (doc, meta, dist) in enumerate(zip(results['documents'][0], metadatas, distances)):
                chunks.append(RetrievedChunk(
                    content=doc,
                    source_doc=meta.get('source', 'Unknown Document') if meta else 'Unknown Document',
                    chunk_id=meta.get('chunk_id', f'chunk_{i}') if meta else f'chunk_{i}',
                    similarity_score=1.0 - dist
                ))
        return chunks

    def _bm25_retrieve(self, query: str, k: int) -> List[RetrievedChunk]:
        if not self.bm25:
            return []
        scores = self.bm25.get_scores(query.lower().split())
        top_idx = np.argsort(scores)[::-1][:k]
        return [RetrievedChunk(content=self.all_docs[i], source_doc=f"Document {i}",
                               chunk_id=f"bm25_chunk_{i}", similarity_score=float(scores[i]))
                for i in top_idx]

    def _ensemble_retrieve(self, query: str, k: int) -> List[RetrievedChunk]:
        if not self.use_ensemble:
            return self._semantic_retrieve(query, k)
        sem = self._semantic_retrieve(query, k)
        bm = self._bm25_retrieve(query, k)
        combined, seen = [], set()
        for c in sem + bm:
            h = hash(c.content)
            if h not in seen and len(combined) < k:
                seen.add(h)
                combined.append(c)
        return combined

    def retrieve_chunks(self, query: str, top_k: Optional[int] = None) -> List[RetrievedChunk]:
        k = top_k or self.top_k
        return self._ensemble_retrieve(query, k)

    def rerank_chunks(self, query: str, chunks: List[RetrievedChunk]) -> List[RetrievedChunk]:
        if not self.enable_reranking or len(chunks) <= 1:
            return chunks
        query_emb = [self._get_openai_embedding(query)]
        doc_embs = [self._get_openai_embedding(c.content) for c in chunks]
        sims = cosine_similarity_simple(query_emb, doc_embs)[0]
        for i, c in enumerate(chunks):
            c.similarity_score = float(sims[i])
        return sorted(chunks, key=lambda x: x.similarity_score, reverse=True)

    def build_context(self, chunks: List[RetrievedChunk]) -> str:
        return "\n\n".join([f"[{c.source_doc}] {c.content}" for c in chunks]) if chunks else ""

    def generate_response(self, query: str, chunks: List[RetrievedChunk]) -> str:
        if not chunks:
            return "I'm sorry, I couldn't find relevant information in our documents."
        context = self.build_context(chunks)
        prompt = f"""
You are the NSR Policy Assistant. Answer the user question using ONLY the context below. Be clear, professional, and friendly.

Context:
{context}

Question:
{query}
"""
        client = get_client()
        if client is None:
            return "LLM unavailable in this environment"
        try:
            resp = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2
            )
            return resp.choices[0].message.content.strip()
        except Exception as e:
            print(f"❌ OpenAI API error: {e}")
            return "I'm sorry, I couldn't generate a response at this time."

    def is_corpus_relevant(self, query: str) -> bool:
        relevant_keywords = ["privacy","data","security","booking","payment","hotel",
                             "recommendation","algorithm","policy","procedure","guideline",
                             "continuity","disaster","business","operations","service",
                             "terms","conditions","agreement","contract","legal","compliance", "user","customer",
                            "host","guest","review","rating","commission","fee","charge"]
        return any(k in query.lower() for k in relevant_keywords)

    def query(self, user_query: str, top_k: Optional[int] = None) -> Dict:
        chunks = self.retrieve_chunks(user_query, top_k)
        if not chunks:
            return {
                "response": "I couldn't find relevant information in our policy documents to answer your question.",
                "retrieved_chunks": [], "num_chunks_retrieved": 0, "corpus_relevant": True
            }
        if self.enable_reranking:
            chunks = self.rerank_chunks(user_query, chunks)
        response = self.generate_response(user_query, chunks)
        if len(response) > self.output_length_limit:
            response = response[:self.output_length_limit] + "..."
        return {
            "response": response,
            "retrieved_chunks": [{"content": c.content, "source_doc": c.source_doc,
                                  "chunk_id": c.chunk_id, "similarity_score": c.similarity_score} for c in chunks],
            "num_chunks_retrieved": len(chunks),
            "corpus_relevant": True
        }
