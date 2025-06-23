# src/content_generator.py
import logging
from openai import OpenAI
import google.generativeai as genai

logger = logging.getLogger(__name__)


class ContentGenerator:
    def __init__(self, openai_api_key, gemini_api_key):
        self.openai_client = OpenAI(api_key=openai_api_key)
        genai.configure(api_key=gemini_api_key)
        self.gemini_model = genai.GenerativeModel('gemini-1.5-flash')
        logger.info("ContentGenerator initialized.")

    def generate_script(self, prompt, model_choice="openai"):
        """
        Generates a video script based on the given prompt using selected AI model.
        """
        if model_choice == "openai":
            return self._generate_with_openai(prompt)
        elif model_choice == "gemini":
            return self._generate_with_gemini(prompt)
        else:
            raise ValueError("Invalid model_choice. Must be 'openai' or 'gemini'.")

    def _generate_with_openai(self, prompt):
        """Internal method to generate content using OpenAI API."""
        try:
            logger.info("Generating script with OpenAI (GPT-4o)...")
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    # E501 해결: 줄 길이를 79자 이하로 맞춤
                    {"role": "system", "content": "You are a creative scriptwriter "
                                                  "for YouTube Shorts. Generate a concise "
                                                  "and engaging script (max 100 words) "
                                                  "for a short video. Include a catchy "
                                                  "title."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=250,
                temperature=0.7
            )
            script = response.choices[0].message.content
            logger.info("OpenAI script generation successful.")
            return script
        except Exception as e:
            logger.error(f"OpenAI script generation failed: {e}", exc_info=True)
            return "Failed to generate script with OpenAI."

    def _generate_with_gemini(self, prompt):
        """Internal method to generate content using Google Gemini API."""
        try:
            # E501 해결: 줄 길이를 79자 이하로 맞춤
            logger.info("Generating script with Google Gemini (gemini-1.5-flash)...")
            response = self.gemini_model.generate_content(prompt)
            script = response.text
            logger.info("Gemini script generation successful.")
            return script
        except Exception as e:
            logger.error(f"Gemini script generation failed: {e}", exc_info=True)
            return "Failed to generate script with Google Gemini."
    
