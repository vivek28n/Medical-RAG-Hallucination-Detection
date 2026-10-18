"""
LLM service — Gemini integration with retry logic.

Provides:
  - Grounded medical answer generation (NB08 prompt)
  - Corrected answer generation for self-correction
  - Retry/error handling
"""

import time
from google import genai
from app.config import settings


class LLMService:
    def __init__(self):
        self.client = None

    def initialize(self):
        """Initialize the Gemini client using the API key from config."""
        if settings.GEMINI_API_KEY:
            self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
            print(f"Gemini client initialized (model: {settings.GEMINI_MODEL_NAME})")
        else:
            print("WARNING: GEMINI_API_KEY not found in config. LLM will fail.")

    def _generate_with_retry(self, prompt: str) -> str:
        """
        Call Gemini with model fallback and retry logic.
        Retries transient failures and falls back to alternate models if quota is exhausted.
        Sanitizes all error messages to guarantee API keys are never exposed.
        """
        if not self.client:
            raise RuntimeError("LLM client not initialized. Check API key.")

        candidates = [
            settings.GEMINI_MODEL_NAME,
            "gemini-3-flash-preview",
            "gemini-flash-lite-latest",
            "gemini-2.0-flash",
        ]
        seen = set()
        model_list = [m for m in candidates if not (m in seen or seen.add(m))]

        last_error = None

        for model_name in model_list:
            for attempt in range(1, settings.LLM_MAX_RETRIES + 1):
                try:
                    response = self.client.models.generate_content(
                        model=model_name,
                        contents=prompt
                    )

                    if response and response.text:
                        return response.text.strip()

                    last_error = f"Gemini ({model_name}) returned an empty response."

                except Exception as e:
                    last_error = str(e)
                    safe_err = last_error
                    if settings.GEMINI_API_KEY and settings.GEMINI_API_KEY in safe_err:
                        safe_err = safe_err.replace(settings.GEMINI_API_KEY, "[REDACTED]")

                    print(
                        f"Attempt {attempt}/{settings.LLM_MAX_RETRIES} on {model_name} "
                        f"failed: {safe_err[:120]}..."
                    )
                    if "429" in last_error or "RESOURCE_EXHAUSTED" in last_error or "404" in last_error:
                        # Quota exceeded or model unavailable: immediately attempt next candidate
                        break

                if attempt < settings.LLM_MAX_RETRIES:
                    time.sleep(settings.LLM_RETRY_DELAY)

        safe_last = str(last_error)
        if settings.GEMINI_API_KEY and settings.GEMINI_API_KEY in safe_last:
            safe_last = safe_last.replace(settings.GEMINI_API_KEY, "[REDACTED]")

        raise RuntimeError(
            f"Gemini generation failed on all candidate models. Last error: {safe_last}"
        )


    def generate_grounded_answer(self, query: str, context: str) -> str:
        """
        Generate a grounded medical answer.
        Prompt ported from Notebook 08 Cell 9.
        """
        prompt = f"""
You are a medical information assistant.

Answer the user's question using ONLY the provided medical context.

Rules:
1. Do not use outside knowledge.
2. Do not invent or assume facts.
3. If the context is insufficient, say that clearly.
4. Keep the answer evidence-based.
5. Preserve important medical qualifiers.
6. Do not provide diagnosis or personalized medical advice.
7. Mention the relevant source page for factual claims.

MEDICAL CONTEXT:
{context}

USER QUESTION:
{query}

ANSWER:
"""
        return self._generate_with_retry(prompt)

    def generate_corrected_answer(self, correction_prompt: str) -> str:
        """
        Generate a corrected answer using the correction prompt
        built by the CorrectionService.
        """
        return self._generate_with_retry(correction_prompt)


llm_service = LLMService()
