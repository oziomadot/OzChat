import os
import chromadb
from pypdf import PdfReader
from rank_bm25 import BM25Okapi
from rag_pipeline_lite import RAGPipelineLite
import numpy as np

def load_documents_from_folder(folder_path):
    """Load text and PDF documents from a folder."""
    documents = []
    metadatas = []
    
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        
        if filename.endswith('.txt'):
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                documents.append(content)
                metadatas.append({'source': filename, 'chunk_id': f'{filename}_0'})
                
        elif filename.endswith('.pdf'):
            try:
                reader = PdfReader(file_path)
                content = ""
                for page in reader.pages:
                    content += page.extract_text() + "\n"
                documents.append(content)
                metadatas.append({'source': filename, 'chunk_id': f'{filename}_0'})
            except Exception as e:
                print(f"Error reading {filename}: {e}")
    
    return documents, metadatas

def chunk_documents(documents, metadatas, chunk_size=1000, overlap=200):
    """Split documents into chunks with overlap."""
    chunks = []
    chunk_metadatas = []
    
    for doc, meta in zip(documents, metadatas):
        words = doc.split()
        for i in range(0, len(words), chunk_size - overlap):
            chunk_words = words[i:i + chunk_size]
            chunk_text = ' '.join(chunk_words)
            chunks.append(chunk_text)
            chunk_meta = meta.copy()
            chunk_meta['chunk_id'] = f"{meta['source']}_chunk_{i // (chunk_size - overlap)}"
            chunk_metadatas.append(chunk_meta)
    
    return chunks, chunk_metadatas

def main():
    print("🚀 Starting lightweight ingestion...")
    
    # Initialize RAG pipeline
    rag = RAGPipelineLite()
    
    # Load documents
    print("📄 Loading documents...")
    documents, metadatas = load_documents_from_folder('policy_corpus')
    print(f"Loaded {len(documents)} documents")
    
    if not documents:
        print("❌ No documents found!")
        return
    
    # Chunk documents
    print("✂️  Chunking documents...")
    chunks, chunk_metadatas = chunk_documents(documents, metadatas)
    print(f"Created {len(chunks)} chunks")
    
    # Generate embeddings using OpenAI API
    print("🔢 Generating embeddings (using OpenAI API)...")
    embeddings = []
    for i, chunk in enumerate(chunks):
        if i % 10 == 0:
            print(f"Processing chunk {i+1}/{len(chunks)}")
        
        try:
            embedding = rag._get_openai_embedding(chunk)
            embeddings.append(embedding)
        except Exception as e:
            print(f"Error generating embedding for chunk {i}: {e}")
            # Use fallback embedding
            embedding = rag._get_openai_embedding(chunk)  # This will use the fallback
            embeddings.append(embedding)
    
    # Add to ChromaDB
    print("💾 Storing in ChromaDB...")
    rag.collection.add(
        embeddings=embeddings,
        documents=chunks,
        metadatas=chunk_metadatas,
        ids=[f"doc_{i}" for i in range(len(chunks))]
    )
    
    print(f"✅ Successfully ingested {len(chunks)} chunks!")
    print(f"📊 Collection '{rag.collection_name}' now has {rag.collection.count()} items")

if __name__ == "__main__":
    main()
