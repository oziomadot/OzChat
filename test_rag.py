#!/usr/bin/env python3
"""
Test script for RAG Pipeline demonstration.
Shows retrieval, re-ranking, and generation capabilities.
"""

from rag_pipeline import RAGPipeline
import json

def test_rag_pipeline():
    """Test the RAG pipeline with sample queries."""
    
    print("🚀 Initializing RAG Pipeline...")
    rag = RAGPipeline(
        vector_db_path="./nsr_vector_db",
        collection_name="nsr_policies",
        top_k=5,
        enable_reranking=True
    )
    
    # Test queries covering different policy areas
    test_queries = [
        "What is the data privacy policy?",
        "How do I make a booking and payment?",
        "What are the information security measures?",
        "What is the business continuity plan?",
        "How does the hotel recommendation algorithm work?",
        "What should I do if there's a data breach?",
        "Outside scope: What's the weather today?",  # Should be refused
        "Tell me about employee conduct policies"
    ]
    
    print("\n" + "="*80)
    print("🧪 TESTING RAG PIPELINE")
    print("="*80)
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n📝 Test {i}: {query}")
        print("-" * 60)
        
        # Check if query is relevant to corpus
        is_relevant = rag.is_corpus_relevant(query)
        print(f"🔍 Corpus Relevance: {'✅ Relevant' if is_relevant else '❌ Not Relevant'}")
        
        # Process query
        result = rag.query(query)
        
        print(f"🤖 Response: {result['response']}")
        print(f"📊 Chunks Retrieved: {result['num_chunks_retrieved']}")
        
        # Show top retrieved chunks
        if result['retrieved_chunks']:
            print("\n🔝 Top Retrieved Chunks:")
            for j, chunk in enumerate(result['retrieved_chunks'][:3], 1):
                print(f"  {j}. Score: {chunk['similarity_score']:.3f}")
                print(f"     Source: {chunk['source_doc']}")
                print(f"     Preview: {chunk['content'][:100]}...")
                print()
        
        print("-" * 60)

def test_reranking_comparison():
    """Compare results with and without re-ranking."""
    
    print("\n" + "="*80)
    print("🔄 RE-RANKING COMPARISON")
    print("="*80)
    
    query = "What security measures are in place for data protection?"
    
    # Test without re-ranking
    rag_no_rerank = RAGPipeline(enable_reranking=False)
    result_no_rerank = rag_no_rerank.query(query)
    
    # Test with re-ranking
    rag_rerank = RAGPipeline(enable_reranking=True)
    result_rerank = rag_rerank.query(query)
    
    print(f"Query: {query}\n")
    
    print("Without Re-ranking:")
    for i, chunk in enumerate(result_no_rerank['retrieved_chunks'][:3], 1):
        print(f"  {i}. Score: {chunk['similarity_score']:.3f} - {chunk['source_doc']}")
    
    print("\nWith Re-ranking:")
    for i, chunk in enumerate(result_rerank['retrieved_chunks'][:3], 1):
        print(f"  {i}. Score: {chunk['similarity_score']:.3f} - {chunk['source_doc']}")

def test_guardrails():
    """Test guardrail functionality."""
    
    print("\n" + "="*80)
    print("🛡️ GUARDRAILS TESTING")
    print("="*80)
    
    rag = RAGPipeline()
    
    # Test queries that should be refused
    out_of_scope_queries = [
        "What's the capital of France?",
        "Tell me about cryptocurrency trading",
        "How do I cook pasta?",
        "What are the latest sports scores?"
    ]
    
    print("Testing out-of-scope queries (should be refused):")
    for query in out_of_scope_queries:
        result = rag.query(query)
        print(f"Q: {query}")
        print(f"A: {result['response']}")
        print()

def interactive_demo():
    """Interactive demo for manual testing."""
    
    print("\n" + "="*80)
    print("🎮 INTERACTIVE DEMO")
    print("="*80)
    print("Type your questions about NSR policies (or 'quit' to exit):")
    
    rag = RAGPipeline()
    
    while True:
        try:
            query = input("\n❓ Your question: ").strip()
            
            if query.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
            
            if not query:
                continue
            
            result = rag.query(query)
            print(f"\n🤖 Response: {result['response']}")
            print(f"📊 Retrieved {result['num_chunks_retrieved']} chunks")
            
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

def main():
    """Run all tests."""
    
    try:
        # Run automated tests
        test_rag_pipeline()
        test_reranking_comparison()
        test_guardrails()
        
        # Optional: Interactive demo
        demo_choice = input("\n🎮 Run interactive demo? (y/n): ").strip().lower()
        if demo_choice in ['y', 'yes']:
            interactive_demo()
        
        print("\n✅ All tests completed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        print("Make sure you've run ingestion.py first to create the vector database.")

if __name__ == "__main__":
    main()
