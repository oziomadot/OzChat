#!/usr/bin/env python3
"""
Integration Guide: How to use RAG in your NaijaStay Recommender application.
This file shows practical examples of integrating the RAG pipeline.
"""

from rag_pipeline import RAGPipeline
from typing import List, Dict

class NSRPolicyAssistant:
    """
    Example integration of RAG pipeline into NSR application.
    This class demonstrates how to use RAG for policy-related queries.
    """
    
    def __init__(self):
        """Initialize the policy assistant with RAG pipeline."""
        self.rag = RAGPipeline(
            vector_db_path="./nsr_vector_db",
            collection_name="nsr_policies",
            top_k=3,  # Retrieve top 3 most relevant chunks
            enable_reranking=True
        )
    
    def answer_policy_question(self, question: str) -> Dict:
        """
        Answer user questions about NSR policies.
        
        Args:
            question: User's question about policies
            
        Returns:
            Dictionary with answer and metadata
        """
        return self.rag.query(question)
    
    def get_relevant_policies(self, topic: str) -> List[str]:
        """
        Get relevant policy documents for a given topic.
        
        Args:
            topic: Topic to search for (e.g., "privacy", "booking", "security")
            
        Returns:
            List of relevant policy content
        """
        result = self.rag.query(f"What are the policies related to {topic}?")
        return [chunk['content'] for chunk in result['retrieved_chunks']]
    
    def check_policy_compliance(self, action: str) -> Dict:
        """
        Check if an action complies with NSR policies.
        
        Args:
            action: Description of action to check
            
        Returns:
            Compliance information with relevant policies
        """
        query = f"What policies should be considered for: {action}?"
        return self.rag.query(query)

# Example usage in a Flask/FastAPI application
def api_endpoint_example():
    """Example of how to use RAG in a web API endpoint."""
    
    # Initialize once (could be done at app startup)
    policy_assistant = NSRPolicyAssistant()
    
    # Example API endpoint
    def handle_policy_query(user_question: str):
        """
        Flask/FastAPI endpoint example:
        
        @app.post("/api/policy-query")
        def policy_query(request):
            result = policy_assistant.answer_policy_question(request.question)
            return {
                "answer": result["response"],
                "sources": [chunk["source_doc"] for chunk in result["retrieved_chunks"]],
                "confidence": max(chunk["similarity_score"] for chunk in result["retrieved_chunks"])
            }
        """
        result = policy_assistant.answer_policy_query(user_question)
        return result

# Example integration with recommendation system
class EnhancedRecommender:
    """
    Example of integrating RAG with hotel recommendations
    to provide policy-aware suggestions.
    """
    
    def __init__(self):
        self.policy_assistant = NSRPolicyAssistant()
    
    def recommend_with_policies(self, user_preferences: Dict) -> Dict:
        """
        Provide hotel recommendations with relevant policy information.
        
        Args:
            user_preferences: User's hotel preferences
            
        Returns:
            Recommendations with policy context
        """
        # Get base recommendations (your existing logic)
        recommendations = []  # Your existing recommendation logic
        
        # Add relevant policy information
        privacy_info = self.policy_assistant.get_relevant_policies("data privacy")
        booking_info = self.policy_assistant.get_relevant_policies("booking")
        
        return {
            "recommendations": recommendations,
            "policy_information": {
                "privacy": privacy_info[:1],  # Most relevant privacy policy
                "booking": booking_info[:1]    # Most relevant booking policy
            }
        }

# Example chatbot integration
class PolicyChatbot:
    """
    Example of a simple chatbot using RAG for policy questions.
    """
    
    def __init__(self):
        self.rag = NSRPolicyAssistant()
        self.conversation_history = []
    
    def chat(self, user_message: str) -> str:
        """
        Process user message and return response.
        
        Args:
            user_message: User's message
            
        Returns:
            Chatbot response
        """
        # Store in conversation history
        self.conversation_history.append({"user": user_message})
        
        # Get RAG response
        result = self.rag.answer_policy_question(user_message)
        response = result["response"]
        
        # Store response
        self.conversation_history.append({"bot": response})
        
        return response
    
    def get_conversation_summary(self) -> List[Dict]:
        """Get summary of conversation history."""
        return self.conversation_history

# Usage examples
def demo_integration():
    """Demonstrate different integration patterns."""
    
    print("🔧 RAG Integration Examples")
    print("=" * 50)
    
    # 1. Basic policy assistant
    print("\n1. Basic Policy Assistant:")
    assistant = NSRPolicyAssistant()
    
    question = "What happens during a data breach?"
    result = assistant.answer_policy_question(question)
    print(f"Q: {question}")
    print(f"A: {result['response']}")
    
    # 2. Topic-based policy retrieval
    print("\n2. Topic-based Policy Retrieval:")
    privacy_policies = assistant.get_relevant_policies("privacy")
    print(f"Found {len(privacy_policies)} privacy-related policies")
    
    # 3. Compliance checking
    print("\n3. Compliance Checking:")
    compliance_result = assistant.check_policy_compliance("sharing user data with third parties")
    print(f"Compliance info: {compliance_result['response'][:100]}...")
    
    # 4. Enhanced recommendations
    print("\n4. Enhanced Recommendations:")
    recommender = EnhancedRecommender()
    enhanced = recommender.recommend_with_policies({
        "location": "Lagos",
        "budget": 50000,
        "preferences": ["wifi", "security"]
    })
    print(f"Enhanced rec includes {len(enhanced['policy_information'])} policy areas")
    
    # 5. Chatbot interaction
    print("\n5. Policy Chatbot:")
    chatbot = PolicyChatbot()
    
    chat_questions = [
        "How is my data protected?",
        "What payment methods are accepted?",
        "Is there a refund policy?"
    ]
    
    for q in chat_questions:
        response = chatbot.chat(q)
        print(f"Q: {q}")
        print(f"A: {response[:80]}...")
        print()

if __name__ == "__main__":
    demo_integration()
