import os
from langchain_community.document_loaders import PyPDFLoader, UnstructuredHTMLLoader, TextLoader, UnstructuredMarkdownLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter, MarkdownHeaderTextSplitter
from bs4 import BeautifulSoup  # For extra HTML cleaning
import re  # For text cleaning
from sentence_transformers import SentenceTransformer
import numpy as np
import chromadb
from chromadb.utils import embedding_functions

from dotenv import load_dotenv
load_dotenv()


def parse_and_clean(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    if ext == '.pdf':
        loader = PyPDFLoader(file_path)
        pages = loader.load()
        text = '\n'.join(page.page_content for page in pages)
    elif ext == '.html':
        loader = UnstructuredHTMLLoader(file_path)
        docs = loader.load()
        text = docs[0].page_content
        # Extra clean with BS4
        soup = BeautifulSoup(text, 'html.parser')
        text = soup.get_text(separator='\n', strip=True)
    elif ext == '.md':
        loader = UnstructuredMarkdownLoader(file_path)
        docs = loader.load()
        text = docs[0].page_content
    elif ext == '.txt':
        loader = TextLoader(file_path)
        docs = loader.load()
        text = docs[0].page_content
    else:
        raise ValueError(f"Unsupported format: {ext}")

    # Clean: Remove extra spaces, lines, non-printable chars
    text = re.sub(r'\s+', ' ', text)  # Normalize whitespace
    text = re.sub(r'[^\x00-\x7F]+', '', text)  # Remove non-ASCII if needed
    text = text.strip()

    return text  # Return cleaned raw text

def format_docs(docs):
    # This removes the "chunk 0" and path logic from the citation
    clean_context = []
    for doc in docs:
        source_name = os.path.basename(doc.metadata.get('source', 'Policy')).split('.')[0]
        clean_context.append(f"Content: {doc.page_content}\nSource: {source_name}")
    return "\n\n".join(clean_context)



def chunk_text(text, by_headings=True):
    if by_headings:  # Preferred for policies (e.g., split on #, ##)
        splitter = MarkdownHeaderTextSplitter(headers_to_split_on=[("#", "Header 1"), ("##", "Header 2")])
        chunks = splitter.split_text(text)
    else:  # Fallback: Token windows with overlap
        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200, length_function=len)
        chunks = splitter.create_documents([text])

    return [chunk.page_content for chunk in chunks]  # List of chunk strings


def embed_chunks(chunks):
    model = SentenceTransformer('all-MiniLM-L6-v2')  # Free, local model ~80MB download on first run
    embeddings = model.encode(chunks, batch_size=32, show_progress_bar=True)
    return embeddings  # NumPy array of shape (num_chunks, 384)


def store_in_chroma(chunks, embeddings):
    client = chromadb.PersistentClient(path="./nsr_vector_db")  # Local dir for persistence
    collection = client.get_or_create_collection(name="nsr_policies")
    
    # Add chunks with embeddings
    collection.add(
    documents=chunks,
    embeddings=embeddings.tolist(),
    ids=[f"{file}_chunk_{i}" for i in range(len(chunks))],
    metadatas=[{"source": file} for _ in chunks]
    )
    print(f"Stored {len(chunks)} chunks in Chroma.")
    return collection  # Return collection for querying


def query_chroma(collection, query_text, n_results=3):
    model = SentenceTransformer('all-MiniLM-L6-v2')
    query_emb = model.encode([query_text])
    results = collection.query(query_embeddings=query_emb.tolist(), n_results=n_results)
    return results


# Example usage
if __name__ == "__main__":
    corpus_dir = 'policy_corpus/'
    
    # Process all documents
    all_chunks = []
    all_embeddings = []
    
    for file in os.listdir(corpus_dir):
        if file.endswith(('.pdf', '.html', '.md', '.txt')):
            cleaned_text = parse_and_clean(os.path.join(corpus_dir, file))
            print(f"Parsed {file}: {cleaned_text[:200]}...")  # Preview
            
            chunks = chunk_text(cleaned_text)
            print(f"Chunked {file} into {len(chunks)} chunks.")
            
            if chunks:  # Only embed if there are chunks
                embeddings = embed_chunks(chunks)
                all_chunks.extend(chunks)  # For storage
                all_embeddings.extend(embeddings)
                print(f"Embedded {len(chunks)} chunks for {file}.")
    
    # Store in ChromaDB
    if all_chunks:
        collection = store_in_chroma(all_chunks, np.array(all_embeddings))
        
        # Query test
        query = "What is the data privacy policy?"
        results = query_chroma(collection, query, n_results=3)
        print("\nTop chunks:", results['documents'])
    


