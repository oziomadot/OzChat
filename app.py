#!/usr/bin/env python3
"""
NaijaStay Recommender Web Application
Fully self-contained Flask app with RAG-powered policy chat
"""

from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import os
import traceback
from datetime import datetime
from rag_pipeline_lite import RAGPipelineLite as RAGPipeline
from dotenv import load_dotenv
from openai import OpenAI
import os



load_dotenv()






# Global client - lazy init
_openai_client = None

def get_client():
    global _openai_client
    if _openai_client is None:
        api_key = os.environ.get("OPEN_ROUTER") or os.environ.get("OPENAI_API_KEY")
        base_url = os.environ.get("OPENAI_BASE_URL", "https://openrouter.ai/api/v1")
        
        if not api_key:
            print("⚠️  No API key found - LLM features disabled")
            _openai_client = None  # or mock client for testing
        else:
            _openai_client = OpenAI(api_key=api_key, base_url=base_url, organization=os.environ.get("OPENAI_ORG_ID"))
    
    return _openai_client


model="openrouter/free"


app = Flask(__name__)
CORS(app)

# Prompt template for RAG responses
prompt = """
You are the NSR knowledge assistant.

Use ONLY the provided context to answer the question.

Rules:
- If the answer is not in the context, say you could not find it.
- Do not invent information.
- Write clearly and professionally.
- Reference document names when possible.

Context:
{context}

Question:
{query}

Answer:
"""

rag_pipeline = None

def get_rag_pipeline():
    """Lazy initialization of RAG pipeline."""
    global rag_pipeline
    if rag_pipeline is None:
        try:
            rag_pipeline = RAGPipeline(
                vector_db_path="./nsr_vector_db",
                collection_name="nsr_policies",
                top_k=20,
                enable_reranking=True,
                use_ensemble=True
            )
            print("✅ RAG Pipeline initialized successfully")
        except Exception as e:
            print(f"❌ Failed to initialize RAG Pipeline: {e}")
            rag_pipeline = None
    return rag_pipeline

# def format_humanistic_response(question, retrieved_chunks):
#     """Generate humanistic answers based on retrieved chunks."""
#     if not retrieved_chunks:
#         return ("I'm sorry, I don't have information about that in our policy documents. "
#                 "I can only help with questions about NSR policies and procedures.")
    
#     context = "\n\n".join(chunk['content'] for chunk in retrieved_chunks)
    
#     # Simplified humanistic mapping
#     q = question.lower()
#     c = context.lower()
    
#     if "data privacy" in q or "privacy" in q:
#         if "data privacy" in c:
#             return ("I've checked our records and NSR is fully committed to protecting your "
#                     "personal data according to Nigeria's Data Protection Act 2023. "
#                     "We collect only necessary information with your consent, and your data "
#                     "is protected with enterprise-grade encryption.")
#     if "booking" in q or "payment" in q:
#         if "booking" in c or "payment" in c:
#             return ("Regarding our booking process, we use Paystack's secure payment system. "
#                     "Transactions are verified via webhooks for smooth processing.")
#     if "security" in q:
#         if "security" in c:
#             return ("NSR takes data protection seriously with ISO 27001-aligned systems, "
#                     "multi-factor authentication, and end-to-end encryption.")
#     if "business continuity" in q or "disaster" in q:
#         if "business continuity" in c:
#             return ("NSR has comprehensive business continuity plans with regular tests "
#                     "and backup protocols to ensure service availability.")
#     if "recommendation" in q or "algorithm" in q:
#         if "recommendation" in c:
#             return ("Our recommendation system uses hybrid filtering based on location, budget, "
def format_humanistic_response(question, retrieved_chunks):
    if not retrieved_chunks:
        return "No info available."

    client = get_client()
    if client is None:
        return "LLM unavailable in this environment"

    context = "\n\n".join(chunk['content'] for chunk in retrieved_chunks)

    # Let an LLM summarize
    prompt = f"""
    You are a helpful assistant.
    Summarize the following context to answer the question:
    Context: {context}
    Question: {question}
    Answer:
    """
    response = client.chat.completions.create(
        model=model,
        messages=[{"role":"user","content":prompt}],
        temperature=0
    )
    return response.choices[0].message.content


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>NaijaStay Recommender - Policy Chat</title>
<style>
/* Minimal inline styling for chat */
body { font-family: sans-serif; background:#f0f2f5; display:flex; justify-content:center; align-items:center; height:100vh; }
.container { width: 90%; max-width: 700px; background:white; border-radius:20px; box-shadow:0 10px 30px rgba(0,0,0,0.1); overflow:hidden; }
.header { background:#4CAF50; color:white; padding:15px; text-align:center; }
.chat-container { height:400px; overflow-y:auto; padding:15px; background:#f9f9f9; }
.message { margin:10px 0; padding:10px 15px; border-radius:15px; max-width:75%; word-wrap:break-word; }
.user-message { background:#007bff; color:white; margin-left:auto; text-align:right; }
.bot-message { background:#e9ecef; color:#333; margin-right:auto; }
.input-container { display:flex; gap:10px; padding:10px; border-top:1px solid #eee; }
.input-field { flex:1; padding:10px; border-radius:20px; border:1px solid #ccc; font-size:16px; }
.send-button { padding:10px 20px; border:none; border-radius:20px; background:#007bff; color:white; cursor:pointer; }
.send-button:disabled { background:#ccc; cursor:not-allowed; }
</style>
</head>
<body>
<div class="container">
<div class="header"><h2>🏨 NaijaStay Policy Assistant</h2></div>
<div class="chat-container" id="chatContainer">
<div class="message bot-message">👋 Hello! Ask me about NSR policies, booking, security, or recommendations.</div>
</div>
<div class="input-container">
<input type="text" id="messageInput" class="input-field" placeholder="Type your question..." maxlength="500">
<button id="sendButton" class="send-button">Send</button>
</div>
</div>
<script>
const chatContainer = document.getElementById('chatContainer');
const messageInput = document.getElementById('messageInput');
const sendButton = document.getElementById('sendButton');

function addMessage(content, isUser=false){
    const div = document.createElement('div');
    div.className = 'message ' + (isUser?'user-message':'bot-message');
    div.textContent = content;
    chatContainer.appendChild(div);
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

async function sendMessage(){
    const msg = messageInput.value.trim();
    if(!msg) return;
    addMessage(msg,true);
    messageInput.value='';
    sendButton.disabled=true;
    try{
        const res = await fetch('/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({question:msg})});
        const data = await res.json();
        if(res.ok){ addMessage(data.answer); } else { addMessage('❌ '+(data.error||'Something went wrong')); }
    } catch(e){ addMessage('❌ Connection error.'); }
    sendButton.disabled=false;
}

sendButton.addEventListener('click',sendMessage);
messageInput.addEventListener('keypress',(e)=>{ if(e.key==='Enter'){ e.preventDefault(); sendMessage(); } });
</script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        question = data.get('question','').strip()
        if not question:
            return jsonify({'error':'Question cannot be empty'}),400
        if len(question)>500:
            return jsonify({'error':'Question too long'}),400

        rag = get_rag_pipeline()
        if rag is None:
            return jsonify({'error':'RAG pipeline unavailable'}),503

        start = datetime.now()
        result = rag.query(question)
        elapsed = (datetime.now()-start).total_seconds()
        answer = format_humanistic_response(question,result['retrieved_chunks'])
        return jsonify({
            'answer': answer,
            'citations': result['retrieved_chunks'],
            'num_chunks_retrieved': result['num_chunks_retrieved'],
            'processing_time': round(elapsed,3)
        })
    except Exception as e:
        print(traceback.format_exc())
        return jsonify({'error':'Internal server error'}),500

@app.route('/health')
def health():
    rag = get_rag_pipeline()
    return jsonify({
        'status':'healthy' if rag else 'degraded',
        'timestamp': datetime.utcnow().isoformat()+'Z',
        'rag_pipeline':'available' if rag else 'unavailable',
        'version':'1.0.0'
    })

if __name__ == '__main__':
    print("🚀 NaijaStay Recommender running...")
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)  # debug=False for production