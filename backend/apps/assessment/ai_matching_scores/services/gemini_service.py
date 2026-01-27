from google import genai
from google.genai import types
from django.conf import settings
import logging
import json

logger = logging.getLogger(__name__)

class GeminiService:
    _client = None

    @classmethod
    def _get_client(cls):
        if not cls._client:
            if not settings.GEMINI_API_KEY:
                logger.warning("GEMINI_API_KEY not configured.")
                return None
            try:
                cls._client = genai.Client(api_key=settings.GEMINI_API_KEY)
            except Exception as e:
                logger.error(f"Failed to initialize Gemini Client: {e}")
                return None
        return cls._client

    @classmethod
    def get_embedding(cls, text: str):
        """
        Get embedding for text using 'text-embedding-004'.
        Returns list of floats or None.
        """
        client = cls._get_client()
        if not client:
            return None
        
        try:
            # Clean text
            text = text.strip()
            if not text:
                return None
                
            # Embed content
            result = client.models.embed_content(
                model="text-embedding-004",
                contents=text,
                config=types.EmbedContentConfig(
                    task_type="RETRIEVAL_DOCUMENT",
                    title="CV Embedding"
                )
            )
            return result.embeddings[0].values
        except Exception as e:
            logger.error(f"Gemini embedding error: {e}")
            return None

    @classmethod
    def generate_content(cls, prompt: str) -> str:
        """
        Generate text content using 'gemini-2.0-flash'.
        Returns string response or None.
        """
        client = cls._get_client()
        if not client:
            return None
            
        try:
            response = client.models.generate_content(
                model='gemini-2.0-flash',
                contents=prompt
            )
            return response.text
        except Exception as e:
            logger.error(f"Gemini generation error: {e}")
            return None

    @classmethod
    def generate_json(cls, prompt: str, schema: dict = None) -> dict:
        """
        Generate JSON content. 
        If schema is provided, uses structured output.
        Returns dict or None.
        """
        client = cls._get_client()
        if not client:
            return None
            
        try:
            config = types.GenerateContentConfig(
                response_mime_type='application/json',
                response_schema=schema if schema else None
            )
            
            response = client.models.generate_content(
                model='gemini-2.0-flash',
                contents=prompt,
                config=config
            )
            
            if response.text:
                return json.loads(response.text)
            return None
        except Exception as e:
            logger.error(f"Gemini JSON generation error: {e}")
            return None
