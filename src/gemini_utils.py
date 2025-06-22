import os
import logging
import google.generativeai as genai
from google.cloud import secretmanager

logger = logging.getLogger(__name__)

class GeminiClient:
    def __init__(self):
        self._initialize_client()
    
    def _initialize_client(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            try:
                client = secretmanager.SecretManagerServiceClient()
                secret_name = f"projects/{os.getenv('GCP_PROJECT_ID')}/secrets/gemini-api-key/versions/latest"
                response = client.access_secret_version(name=secret_name)
                api_key = response.payload.data.decode("UTF-8")
            except Exception as e:
                logger.error(f"Failed to load Gemini key: {e}")
                raise
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-pro')

    def generate_content(self, prompt):
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            return None
