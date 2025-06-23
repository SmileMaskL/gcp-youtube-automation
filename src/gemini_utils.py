# src/gemini_utils.py
import google.generativeai as genai
import logging

logger = logging.getLogger(__name__)


def initialize_gemini(api_key):
    """Initializes the Gemini API client."""
    try:
        genai.configure(api_key=api_key)
        logger.info("Google Gemini API client initialized.")
    except Exception as e:
        logger.error(f"Failed to initialize Google Gemini API client: {e}",
                    exc_info=True)
        raise


def generate_text_gemini(prompt, model="gemini-1.5-flash"):
    """Generates text using Google Gemini API."""
    try:
        model_instance = genai.GenerativeModel(model_name=model)
        # E501 해결: 줄 길이를 79자 이하로 맞춤
        logger.info(f"Sending prompt to Gemini model ({model}): {prompt[:100]}...")
        response = model_instance.generate_content(prompt)
        logger.info("Gemini text generation successful.")
        return response.text
    except Exception as e:
        logger.error(f"Gemini text generation failed: {e}", exc_info=True)
        raise


def generate_image_description_gemini(image_data, prompt, model="gemini-1.5-flash"):
    """Generates image description using Google Gemini API."""
    try:
        model_instance = genai.GenerativeModel(model_name=model)
        # E501 해결: 줄 길이를 79자 이하로 맞춤
        logger.info(f"Sending image to Gemini model ({model}) for description "
                    f"with prompt: {prompt[:50]}...")
        response = model_instance.generate_content([prompt, image_data])
        logger.info("Gemini image description generation successful.")
        return response.text
    except Exception as e:
        logger.error(f"Gemini image description generation failed: {e}",
                    exc_info=True)
        raise
    
