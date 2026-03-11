# NaijaStay Recommender (NSR) Project

## Overview
This is a prototype for a hotel recommendation system in Nigeria, using user data (location, age, gender, preferences, budget) for personalized suggestions. Built for MSc in Software Engineering.

## Setup Instructions
1. Clone the repository: `git clone <your-repo-url>`.
2. Navigate to the project: `cd nsr-project`.
3. Create and activate virtual environment:
   - `python -m venv venv`
   - Windows: `venv\Scripts\activate`
   - macOS/Linux: `source venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`.
5. (Optional) Set environment variables: Create `.env` file with keys (e.g., `PAYSTACK_SECRET_KEY=your_key`).

## Run Instructions
1. **Run ingestion first**: `python ingestion.py` (to create vector database)
2. **Run web app**: `python app.py` (starts Flask server)
3. **Access UI**: Open http://localhost:5000 in browser
4. **Test endpoints**: `python test_webapp.py` (comprehensive testing)
5. For tests: `python -m unittest discover`.
6. Notes on reproducibility: Seeds are fixed (e.g., random.seed(42)) for deterministic results. Use the same Python version (3.10+) for consistency.

## Web Application

### Features
- **Chat Interface**: Modern web UI for policy questions
- **Humanistic Responses**: Professional, warm, and helpful AI assistant tone
- **API Endpoints**: RESTful API for integration
- **Real-time Status**: Health monitoring and connection status
- **Citations**: Automatic source attribution with snippets
- **Guardrails**: Input validation and error handling

### Endpoints
- **GET /** - Web chat interface with modern UI
- **POST /chat** - API endpoint for questions with citations and snippets
- **GET /health** - Service status and health monitoring

### API Usage
```bash
# Health check
curl http://localhost:5000/health

# Chat API
curl -X POST http://localhost:5000/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the data privacy policy?"}'
```

### Response Format
```json
{
  "answer": "Response text with citations",
  "citations": [
    {
      "source_doc": "Data Privacy Policy",
      "chunk_id": "chunk_3",
      "snippet": "NSR is committed to protecting personal data...",
      "similarity_score": 0.85
    }
  ],
  "num_chunks_retrieved": 5,
  "processing_time": 0.15
}
```

## Corpus Integration
Policies/procedures from the document corpus are referenced in code (e.g., data privacy in user handling).

## Troubleshooting
- If issues with dependencies: Recreate venv and reinstall.
- Contact: [your-email].

## Ingestion
**Run `python ingestion.py` to parse, chunk, embed, and index the policy_corpus/ folder.**

### Error Handling
- Added try-except blocks for file loading issues
- Logs problematic files and continues processing
- Graceful handling of unsupported file formats

### Scalability
- For larger corpus, implement batch processing
- ChromaDB handles millions of vectors efficiently
- Consider distributed processing for very large datasets

### Reproducibility
- Model is deterministic; no seeds needed
- Embeddings are consistent across runs
- Vector database persists between sessions

### Next Steps
- ✅ **RAG Pipeline**: Run `python rag_pipeline.py` to use the retrieval-augmented generation system
- ✅ **Test RAG**: Run `python test_rag.py` to test the complete RAG functionality
- ✅ **Integration Guide**: See `rag_integration_guide.py` for integration examples
- Add real-time document updates
- Implement user-specific policy filtering
- Create API endpoints for policy queries

## RAG (Retrieval-Augmented Generation) Implementation

### Features
- **Top-k Retrieval**: Configurable number of relevant chunks retrieved
- **Re-ranking**: Optional re-ranking for improved relevance
- **Guardrails**: Corpus-only responses with output length limits
- **Citations**: Automatic source citation in responses
- **Semantic Search**: Advanced similarity-based document retrieval

### Usage Examples

```python
from rag_pipeline import RAGPipeline

# Initialize RAG pipeline
rag = RAGPipeline(top_k=5, enable_reranking=True)

# Query the system
result = rag.query("What is the data privacy policy?")
print(result['response'])  # Answer with citations
```

### Integration Patterns
- **Policy Assistant**: Answer user questions about NSR policies
- **Compliance Checking**: Verify actions against policies
- **Enhanced Recommendations**: Add policy context to hotel suggestions
- **Chatbot**: Conversational interface for policy queries

### API Integration
```python
# Example Flask endpoint
@app.post("/api/policy-query")
def policy_query(request):
    result = rag.query(request.question)
    return {
        "answer": result["response"],
        "sources": [chunk["source_doc"] for chunk in result["retrieved_chunks"]]
    }