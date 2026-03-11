import os
import numpy as np
from sentence_transformers import SentenceTransformer
import chromadb
from typing import List, Dict, Tuple, Optional
import re
from dataclasses import dataclass
from dotenv import load_dotenv
from rank_bm25 import BM25Okapi
import math

load_dotenv()

@dataclass
class RetrievedChunk:
    content: str
    source_doc: str
    chunk_id: str
    similarity_score: float

class RAGPipeline:
    def __init__(self, 
                 vector_db_path: str = "./nsr_vector_db",
                 collection_name: str = "nsr_policies",
                 model_name: str = "all-MiniLM-L6-v2",
                 top_k: int = 20,  # Increased from 5 to 20 for better coverage
                 enable_reranking: bool = True,
                 use_ensemble: bool = True):  # New parameter for ensemble retrieval
        """
        Initialize RAG Pipeline with retrieval and generation capabilities.
        
        Args:
            vector_db_path: Path to ChromaDB database
            collection_name: Name of the collection
            model_name: Sentence transformer model name
            top_k: Number of chunks to retrieve
            enable_reranking: Whether to use re-ranking
            use_ensemble: Whether to use ensemble retrieval (semantic + BM25)
        """
        self.vector_db_path = vector_db_path
        self.collection_name = collection_name
        self.model_name = model_name
        self.top_k = top_k
        self.enable_reranking = enable_reranking
        self.use_ensemble = use_ensemble
        
        # Initialize embedding model
        self.embedding_model = SentenceTransformer(model_name)
        
        # Connect to ChromaDB
        self.client = chromadb.PersistentClient(path=vector_db_path)
        self.collection = self.client.get_collection(collection_name)
        
        # Initialize BM25 for keyword retrieval
        self.bm25 = None
        self.all_docs = []
        self._initialize_bm25()
        
        # System prompts for guardrails
        self.system_prompt = """
You are the NSR Policy Assistant, a friendly and professional colleague. 
Your goal is to explain our security measures clearly and warmly.

RULES:
1. SYNTHESIZE: Don't just list facts. Group related points (e.g., 'On the technical side...' or 'Regarding access...') to make it readable.
2. CITATIONS: Use natural, unobtrusive citations at the end of relevant sentences like (Policy Document, Section 5). 
3. HUMAN TONE: Use phrases like "We take security seriously," or "You'll be glad to know that..."
4. REFUSAL: If the info isn't there, say: "I'm sorry, I couldn't find details on that in our current policies. Would you like me to check with the IT team?"
5. NO CHUNK IDs: Never show raw technical terms like "chunk 5" to the user. Use Document Title or Section Name.
"""

        self.output_length_limit = 500  # Maximum response length

    def _initialize_bm25(self):
        """Initialize BM25 retriever with all documents from the collection."""
        try:
            # Get all documents from collection
            all_results = self.collection.get(include=['documents', 'metadatas'])
            
            if all_results['documents']:
                self.all_docs = all_results['documents']
                # Tokenize documents for BM25 (simple word tokenization)
                tokenized_docs = [doc.lower().split() for doc in self.all_docs]
                self.bm25 = BM25Okapi(tokenized_docs)
                print(f"✅ BM25 initialized with {len(self.all_docs)} documents")
            else:
                print("⚠️  No documents found for BM25 initialization")
                
        except Exception as e:
            print(f"❌ Failed to initialize BM25: {e}")
            self.bm25 = None

    def _semantic_retrieve(self, query: str, k: int) -> List[RetrievedChunk]:
        """Perform semantic retrieval using vector search."""
        try:
            # Generate query embedding
            query_embedding = self.embedding_model.encode([query])
            
            # Query ChromaDB
            results = self.collection.query(
                query_embeddings=query_embedding.tolist(),
                n_results=k
            )
            
            # Convert to RetrievedChunk objects
            chunks = []
            for i, (doc, metadata, distance) in enumerate(zip(
                results['documents'][0], 
                results['metadatas'][0] if results['metadatas'] else [{}] * k,
                results['distances'][0]
            )):
                chunk = RetrievedChunk(
                    content=doc,
                    source_doc=metadata.get('source', 'Unknown Document'),
                    chunk_id=metadata.get('chunk_id', f'chunk_{i}'),
                    similarity_score=1.0 - distance  # Convert distance to similarity
                )
                chunks.append(chunk)
            
            return chunks
            
        except Exception as e:
            print(f"❌ Semantic retrieval error: {e}")
            return []

    def _bm25_retrieve(self, query: str, k: int) -> List[RetrievedChunk]:
        """Perform BM25 keyword retrieval."""
        if not self.bm25:
            return []
        
        try:
            # Tokenize query
            tokenized_query = query.lower().split()
            
            # Get BM25 scores
            doc_scores = self.bm25.get_scores(tokenized_query)
            
            # Get top-k documents
            top_indices = np.argsort(doc_scores)[::-1][:k]
            
            chunks = []
            for i, idx in enumerate(top_indices):
                if idx < len(self.all_docs):
                    chunk = RetrievedChunk(
                        content=self.all_docs[idx],
                        source_doc=f"Document {idx}",
                        chunk_id=f"bm25_chunk_{i}",
                        similarity_score=float(doc_scores[idx])  # BM25 score
                    )
                    chunks.append(chunk)
            
            return chunks
            
        except Exception as e:
            print(f"❌ BM25 retrieval error: {e}")
            return []

    def _ensemble_retrieve(self, query: str, k: int) -> List[RetrievedChunk]:
        """Perform ensemble retrieval combining semantic and BM25."""
        if not self.use_ensemble:
            return self._semantic_retrieve(query, k)
        
        try:
            # Get results from both retrievers
            semantic_results = self._semantic_retrieve(query, k)
            bm25_results = self._bm25_retrieve(query, k)
            
            # Combine and deduplicate results
            all_results = semantic_results + bm25_results
            
            # Simple scoring: weighted average (0.6 semantic, 0.4 BM25)
            ensemble_results = []
            seen_content = set()
            
            for i, chunk in enumerate(all_results):
                content_hash = hash(chunk.content)
                if content_hash not in seen_content and len(ensemble_results) < k:
                    seen_content.add(content_hash)
                    
                    # Normalize scores to 0-1 range
                    semantic_score = chunk.similarity_score if chunk in semantic_results else 0
                    bm25_score = chunk.similarity_score if chunk in bm25_results else 0
                    
                    # Weighted ensemble score
                    ensemble_score = 0.6 * semantic_score + 0.4 * bm25_score
                    
                    ensemble_chunk = RetrievedChunk(
                        content=chunk.content,
                        source_doc=chunk.source_doc,
                        chunk_id=chunk.chunk_id,
                        similarity_score=ensemble_score
                    )
                    ensemble_results.append(ensemble_chunk)
            
            print(f"🔗 Ensemble: {len(semantic_results)} semantic + {len(bm25_results)} BM25 = {len(ensemble_results)} results")
            return ensemble_results
            
        except Exception as e:
            print(f"❌ Ensemble retrieval error: {e}")
            # Fallback to semantic retrieval
            return self._semantic_retrieve(query, k)

    def retrieve_chunks(self, query: str, top_k: Optional[int] = None) -> List[RetrievedChunk]:
        """
        Retrieve relevant chunks using ensemble retrieval (semantic + BM25).
        
        Args:
            query: User query
            top_k: Number of chunks to retrieve (overrides instance default)
            
        Returns:
            List of retrieved chunks with metadata
        """
        k = top_k or self.top_k
        
        try:
            # Use ensemble retrieval
            chunks = self._ensemble_retrieve(query, k)
            
            print(f"📚 Retrieved {len(chunks)} chunks using ensemble retrieval")
            return chunks
            
        except Exception as e:
            print(f"❌ Retrieval error: {e}")
            return []

    def rerank_chunks(self, query: str, chunks: List[RetrievedChunk]) -> List[RetrievedChunk]:
        """
        Re-rank retrieved chunks using cross-encoder similarity.
        
        Args:
            query: Original user query
            chunks: List of retrieved chunks
            
        Returns:
            Re-ranked list of chunks
        """
        if not self.enable_reranking or len(chunks) <= 1:
            return chunks
        
        try:
            # Create query and document embeddings for re-ranking
            query_emb = self.embedding_model.encode([query])
            doc_texts = [chunk.content for chunk in chunks]
            doc_embs = self.embedding_model.encode(doc_texts)
            
            # Compute cosine similarities
            from sklearn.metrics.pairwise import cosine_similarity
            similarities = cosine_similarity(query_emb, doc_embs)[0]
            
            # Re-rank chunks
            reranked_chunks = []
            for i, chunk in enumerate(chunks):
                reranked_chunk = RetrievedChunk(
                    content=chunk.content,
                    source_doc=chunk.source_doc,
                    chunk_id=chunk.chunk_id,
                    similarity_score=float(similarities[i])
                )
                reranked_chunks.append(reranked_chunk)
            
            # Sort by re-ranking score
            reranked_chunks.sort(key=lambda x: x.similarity_score, reverse=True)
            
            print(f"🔄 Re-ranked {len(chunks)} chunks")
            return reranked_chunks
            
        except ImportError:
            print("⚠️  sklearn not available, skipping re-ranking")
            return chunks
        except Exception as e:
            print(f"❌ Re-ranking error: {e}")
            return chunks

    def build_context(self, chunks: List[RetrievedChunk]) -> str:
        """
        Build context string from retrieved chunks.
        
        Args:
            chunks: List of retrieved chunks
            
        Returns:
            Formatted context string
        """
       
        # Limit chunks for context building
        chunks = chunks[:10]
        context_parts = []

        for i, chunk in enumerate(chunks):
            context_parts.append(
                f"""
    Document: {chunk.source_doc}
    Content:
    {chunk.content}
    """
            )

        return "\n\n".join(context_parts)

    def generate_response(self, query: str, chunks: List[RetrievedChunk]) -> str:
        """
        Generate response based on retrieved chunks.
        
        Args:
            query: User query
            chunks: Retrieved chunks
            
        Returns:
            Generated response
        """
        if not chunks:
            return "I'm sorry, I couldn't find relevant information in our policy documents to answer your question."
        
        # Simple keyword-based response generation (in production, use LLM)
        context = self.build_context(chunks)
        
        # Check for specific policy areas
        query_lower = query.lower()
        context_lower = context.lower()


       
        
        if "data privacy" in query_lower or "privacy" in query_lower:
            if "data privacy" in context_lower:
                return "I've checked our records and found that NSR is fully committed to protecting your personal data in accordance with Nigeria's Data Protection Act 2023. We collect only necessary information like your name, email, and preferences, always with your explicit consent. Your data is protected with enterprise-grade encryption, and we never share it with third parties without your permission."
        
        elif "booking" in query_lower or "payment" in query_lower:
            if "booking" in context_lower or "payment" in context_lower:
                return "Regarding our booking process, I can confirm that we use Paystack's secure payment system for all transactions. When you make a booking, you'll be redirected to Paystack's secure checkout where you can safely enter your payment details. We verify all transactions through webhooks to ensure everything goes smoothly."
        
        elif "security" in query_lower or "information security" in query_lower:
            if "security" in context_lower:
                return "I've reviewed our security measures and can assure you that we take data protection very seriously. Our systems are aligned with ISO 27001 standards and include multiple layers of security like mandatory multi-factor authentication, end-to-end encryption, and regular security audits. We also have a rapid incident response team ready to address any issues."
        
        elif "business continuity" in query_lower or "disaster" in query_lower:
            if "business continuity" in context_lower:
                return "Looking at our business continuity plans, I can confirm that NSR has comprehensive procedures in place to ensure our services remain available even during unexpected events. We regularly test our systems and have backup protocols to maintain service continuity for our users."
        
        elif "recommendation" in query_lower or "algorithm" in query_lower:
            if "recommendation" in context_lower:
                return "I've checked how our recommendation system works, and it uses a sophisticated hybrid approach that considers your location, budget, and personal preferences. We combine content-based filtering with collaborative filtering to provide you with the most suitable hotel recommendations. We also regularly audit our system to ensure fairness and prevent any bias."
        
        # Default response
        return f"Based on the information I have access to, I can help you with that. Our policies cover various aspects including data privacy, booking procedures, security measures, and recommendation guidelines. Could you please let me know which specific area you'd like to know more about?"

    

    def query(self, user_query: str, top_k: Optional[int] = None) -> Dict:
        """
        Main query method that retrieves chunks and generates response.
        """
        # Check if query is relevant to corpus
        if not self.is_corpus_relevant(user_query):
            return {
                "response": "I can only answer questions about NSR policies and procedures.",
                "retrieved_chunks": [],
                "num_chunks_retrieved": 0,
                "corpus_relevant": False
            }
        
        # Retrieve chunks
        chunks = self.retrieve_chunks(user_query, top_k)
        
        if not chunks:
            return {
                "response": "I couldn't find relevant information in our policy documents to answer your question.",
                "retrieved_chunks": [],
                "num_chunks_retrieved": 0,
                "corpus_relevant": True
            }
        
        # Re-rank if enabled
        if self.enable_reranking:
            chunks = self.rerank_chunks(user_query, chunks)
        
        # Generate response
        response = self.generate_response(user_query, chunks)
        
        return {
            "response": response,
            "retrieved_chunks": [
                {
                    "content": c.content,
                    "source_doc": c.source_doc,
                    "chunk_id": c.chunk_id,
                    "similarity_score": c.similarity_score
                }
                for c in chunks
            ],
            "num_chunks_retrieved": len(chunks),
            "corpus_relevant": True
        }
