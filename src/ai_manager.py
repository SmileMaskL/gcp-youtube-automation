import logging
import openai
import google.generativeai as genai # For Google Gemini
from src.config import load_config # Import the new config loader

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class AIManager:
    def __init__(self):
        self.config = load_config() # Load the singleton config instance
        self.openai_client = None
        self.gemini_client_initialized = False

    def _initialize_openai_client(self):
        """Initializes OpenAI client with the next available key."""
        api_key = self.config.get_next_openai_key()
        if api_key:
            self.openai_client = openai.OpenAI(api_key=api_key)
            logging.info("OpenAI client initialized with rotated key.")
        else:
            logging.warning("No OpenAI API key available for initialization.")
            self.openai_client = None

    def _initialize_gemini_client(self):
        """Initializes Gemini client with the next available key."""
        api_key = self.config.get_next_gemini_key()
        if api_key:
            genai.configure(api_key=api_key)
            self.gemini_client_initialized = True
            logging.info("Google Gemini client initialized with rotated key.")
        else:
            logging.warning("No Gemini API key available for initialization.")
            self.gemini_client_initialized = False

    def generate_text_with_openai(self, prompt, model="gpt-4o", max_tokens=1000):
        """Generates text using OpenAI's GPT models."""
        self._initialize_openai_client() # Get next key for each call
        if not self.openai_client:
            logging.error("OpenAI client not initialized. Cannot generate text.")
            return None
        
        try:
            response = self.openai_client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=0.7
            )
            # Update API usage for OpenAI (e.g., based on tokens or requests)
            self.config.update_api_usage("openai", response.usage.total_tokens)
            return response.choices[0].message.content
        except openai.APIError as e:
            logging.error(f"OpenAI API Error: {e}")
            return None
        except Exception as e:
            logging.error(f"An unexpected error occurred with OpenAI API: {e}")
            return None

    def generate_text_with_gemini(self, prompt, model="gemini-pro", max_tokens=1000):
        """Generates text using Google Gemini models."""
        self._initialize_gemini_client() # Get next key for each call
        if not self.gemini_client_initialized:
            logging.error("Google Gemini client not initialized. Cannot generate text.")
            return None
        
        try:
            model_instance = genai.GenerativeModel(model)
            response = model_instance.generate_content(prompt, generation_config=genai.types.GenerationConfig(max_output_tokens=max_tokens))
            # Update API usage for Gemini (e.g., based on requests)
            self.config.update_api_usage("gemini", 1) # Each call is 1 request
            return response.text
        except Exception as e:
            logging.error(f"An error occurred with Google Gemini API: {e}")
            # Consider specific error handling for rate limits etc.
            return None

    def generate_content_with_rotation(self, prompt, preferred_model="gpt-4o"):
        """
        Generates content using AI, rotating between OpenAI and Gemini.
        Prioritizes a preferred model if available and within limits.
        """
        # Simple rotation logic: alternate between OpenAI and Gemini
        # For more advanced logic, you could track usage and switch based on quota.
        if self.config.get("OPENAI_KEYS") and self.config.get("GEMINI_API_KEY"):
            # Check which API was used last or based on a simple counter
            # For strict rotation, you might need a persistent counter or a more complex state.
            # For this example, let's alternate based on an internal counter or simple modulo.
            # A more robust solution might involve a `usage_tracker` module
            # For simplicity, let's just prioritize preferred, then fallback.

            # Attempt to use preferred model first
            if preferred_model == "gpt-4o":
                if self.config.get_next_openai_key(): # Check if a key is available
                    logging.info("Attempting to generate content with OpenAI (preferred).")
                    content = self.generate_text_with_openai(prompt)
                    if content:
                        return content
                logging.warning("OpenAI failed or no key available. Falling back to Gemini.")
                return self.generate_text_with_gemini(prompt)
            elif preferred_model == "gemini-pro":
                if self.config.get_next_gemini_key(): # Check if a key is available
                    logging.info("Attempting to generate content with Gemini (preferred).")
                    content = self.generate_text_with_gemini(prompt)
                    if content:
                        return content
                logging.warning("Gemini failed or no key available. Falling back to OpenAI.")
                return self.generate_text_with_openai(prompt)
            else: # Fallback if preferred_model is invalid
                logging.warning(f"Invalid preferred_model: {preferred_model}. Attempting both.")
                if self.config.get_next_openai_key():
                    content = self.generate_text_with_openai(prompt)
                    if content: return content
                return self.generate_text_with_gemini(prompt)

        elif self.config.get("OPENAI_KEYS"):
            logging.info("Only OpenAI keys available. Using OpenAI.")
            return self.generate_text_with_openai(prompt)
        elif self.config.get("GEMINI_API_KEY"):
            logging.info("Only Gemini key available. Using Gemini.")
            return self.generate_text_with_gemini(prompt)
        else:
            logging.error("No AI keys available (OpenAI or Gemini). Cannot generate content.")
            return None

# Example usage (will be called from content_generator.py)
# ai_manager = AIManager()
# text = ai_manager.generate_content_with_rotation("Write a short script about today's hottest news.")
