import logging
from openai import OpenAI
import google.generativeai as genai

logger = logging.getLogger(__name__)

class ContentGenerator:
    def __init__(self, openai_api_key=None, gemini_api_key=None, ai_model="openai"):
        self.openai_client = OpenAI(api_key=openai_api_key) if openai_api_key else None
        
        if gemini_api_key:
            genai.configure(api_key=gemini_api_key)
            self.gemini_model = genai.GenerativeModel('gemini-pro')
        else:
            self.gemini_model = None

        self.ai_model = ai_model
        
        # 수정: 83자 → 분할 (원본 17번 라인)
        if self.ai_model == "openai" and not self.openai_client:
            logger.warning(
                "OpenAI client not initialized. Falling back to Gemini if available."
            )
            self.ai_model = "gemini" if self.gemini_model else None
        elif self.ai_model == "gemini" and not self.gemini_model:
            logger.warning(
                "Gemini model not initialized. Falling back to OpenAI if available."
            )
            self.ai_model = "openai" if self.openai_client else None
        
        if not self.ai_model:
            logger.error("No AI models are available for content generation.")
            raise ValueError("No AI models available for content generation.")

    def generate_script(self, topic: str):
        if self.ai_model == "openai":
            if not self.openai_client:
                logger.error("OpenAI client not initialized. Cannot generate script with OpenAI.")
                return None
            try:
                response = self.openai_client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant for creating engaging YouTube Shorts scripts. Provide a concise, impactful script that is around 60 seconds long. Focus on a single trending topic. The script should be suitable for text-to-speech conversion and on-screen text."},
                        {"role": "user", "content": f"Generate a YouTube Shorts script about the trending topic: '{topic}'"}
                    ],
                    max_tokens=200,
                    temperature=0.7
                )
                script = response.choices[0].message.content.strip()
                logger.info(f"OpenAI generated script for topic: {topic}")
                return script
            except Exception as e:
                logger.error(f"Error generating script with OpenAI: {e}")
                return None
        
        elif self.ai_model == "gemini":
            if not self.gemini_model:
                logger.error("Gemini model not initialized. Cannot generate script with Gemini.")
                return None
            try:
                response = self.gemini_model.generate_content(
                    f"Generate a YouTube Shorts script about the trending topic: '{topic}'. Keep it concise and engaging, suitable for a 60-second video with on-screen text.",
                    generation_config=genai.types.GenerationConfig(
                        max_output_tokens=200,
                        temperature=0.7
                    )
                )
                script = response.text.strip()
                logger.info(f"Gemini generated script for topic: {topic}")
                return script
            except Exception as e:
                logger.error(f"Error generating script with Gemini: {e}")
                return None
        else:
            logger.error("No valid AI model selected for script generation.")
            return None
