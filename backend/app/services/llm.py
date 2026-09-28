from google import genai
from app.config import settings

class LLMService:
    def __init__(self):
        self.client = None

    def initialize(self):
        if settings.GEMINI_API_KEY:
            self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        else:
            print("WARNING: GEMINI_API_KEY not found in config. LLM will fail.")

    def generate_grounded_answer(self, query: str, context: str) -> str:
        if not self.client:
            raise RuntimeError("LLM client not initialized. Check API key.")
            
        prompt = f"""You are a medical AI assistant. Answer the user's question using ONLY the provided medical context. 
If the context does not contain enough information to answer the question, state that you cannot answer based on the provided evidence.

Context:
{context}

Question:
{query}

Answer:"""

        response = self.client.models.generate_content(
            model="gemini-2.5-flash", 
            contents=prompt
        )
        return response.text

llm_service = LLMService()
