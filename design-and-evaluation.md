# NaijaStay Policy Assistant - Design and Evaluation Documentation

## 1. Design and Architecture Decisions

### i) Technology Choices & Rationale

#### Core Architecture
- **Framework**: Flask web application with RAG (Retrieval-Augmented Generation)
- **Pattern**: Synchronous request/response with ChromaDB for vector storage
- **Deployment**: Railway (free tier) with persistent volume for vector database

#### Key Technology Decisions

**1. Embedding Model: all-MiniLM-L6-v2 (sentence-transformers)**
- **Rationale**: Fast inference (~20-80ms on CPU), zero cost, strong semantic performance
- **Trade-offs**: 384 dimensions (smaller than OpenAI's 1536), but sufficient for policy text
- **Alternative considered**: OpenAI text-embedding-3-small (higher quality but costs money + network latency)

**2. Vector Store: ChromaDB with PersistentClient**
- **Rationale**: Lightweight, local storage, survives redeploys via Railway volume
- **Benefits**: Zero external dependencies, fast startup, supports metadata
- **Alternatives**: Pinecone/Weaviate (managed but require API keys + limits)

**3. Chunking Strategy: Fixed-size (~600-800 chars with overlap)**
- **Rationale**: Policy documents are structured text, fixed-size works well
- **Benefits**: Context continuity, manageable chunk count (~16 items total)
- **Alternatives**: Recursive splitting (more natural but complex for small corpus)

**4. Retrieval: top_k=20 with reranking**
- **Rationale**: Balance recall vs context length for free LLM models
- **Benefits**: Enough candidates for relevant passages, reranking improves precision
- **Trade-offs**: Higher k → better recall but slower LLM generation

**5. Prompt Engineering: Strict instruction prompt**
- **Rationale**: Maximizes groundedness (achieved 100% in evaluation)
- **Key rules**: "ONLY use context", "Do not invent", explicit fallback
- **Benefits**: Prevents hallucinations, maintains professional tone

### Design Philosophy
**Priorities**: High factual accuracy + zero running costs + reasonable performance
**Trade-offs accepted**: Higher latency (cold starts + free LLM) for perfect faithfulness

## 2. Evaluation Approach and Results

### ii) Evaluation Methodology

#### Automated Evaluation
- **Dataset**: 24 questions covering PTO, remote work, expenses, security, holidays
- **Script**: `evaluate.py` measures end-to-end latency and response quality
- **Metrics**: p50/p95 latency, success rate, chunk retrieval counts
- **Environment**: Production deployment (https://ozchat-x5d3.onrender.com)

#### Manual Evaluation
- **Sample**: 15 answers manually reviewed for groundedness
- **Groundedness**: Every fact must be directly supported by retrieved context
- **Citation Accuracy**: Each cited chunk must actually support the statement
- **Scoring**: Binary (1=fully grounded, 0=partial/unsupported)

### Results Summary

**System Performance**:
- **Total queries**: 24 (100% success rate)
- **p50 latency**: 13.42 seconds
- **p95 latency**: 27.56 seconds
- **Primary bottleneck**: Render free-tier cold starts + slower free LLM models

**Answer Quality**:
- **Groundedness**: 100% (15/15 in manual review)
- **Citation Accuracy**: 100% (15/15 citations correctly support statements)
- **No hallucinations**: Model strictly follows RAG context

**Key Insights**:
- Extremely high factual accuracy and citation behavior
- Latency is main limitation (acceptable for policy queries)
- Robust handling of diverse policy topics
- Perfect faithfulness to retrieved documents

### Optimization Iterations
1. **Reduced top_k**: 20 → 10 for faster retrieval
2. **Disabled reranking**: In low-latency mode
3. **Model selection**: Switched to faster free models via OpenRouter
4. **Database reset**: Fixed embedding dimension mismatch (384→1536 for OpenAI compatibility)

## 3. Future Improvements

**Latency Reduction**:
- Upgrade to Railway hobby tier (always-on instances)
- Consider local LLM (Ollama) for sub-second responses
- Implement response caching for common queries

**Quality Enhancement**:
- Add query expansion for better semantic matching
- Implement hybrid search (semantic + keyword weighting)
- Add relevance feedback loop

**Scalability**:
- Automated document updates from policy sources
- Multi-user session management
- Advanced analytics and usage tracking
