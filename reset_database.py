import os
import shutil
from rag_pipeline_lite import RAGPipelineLite

def reset_vector_database():
    """Clear existing vector database and re-ingest with OpenAI embeddings"""
    print("🗑️  Resetting vector database...")
    
    # Remove existing vector database
    if os.path.exists("./nsr_vector_db"):
        shutil.rmtree("./nsr_vector_db")
        print("✅ Removed existing vector database")
    
    # Re-run ingestion with OpenAI embeddings
    print("🚀 Re-ingesting with OpenAI embeddings (1536 dimensions)...")
    os.system("python ingestion_lite.py")

if __name__ == "__main__":
    reset_vector_database()
