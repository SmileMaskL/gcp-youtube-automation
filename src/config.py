# src/config.py
import os
import json
import logging
from google.cloud import secretmanager_v1 # Correct import for secretmanager client

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize Secret Manager client globally
secret_client = None

def _initialize_secret_client():
    """Initializes the Google Secret Manager client."""
    global secret_client
    if secret_client is None:
        try:
            # Authenticate using GOOGLE_APPLICATION_CREDENTIALS environment variable
            # which is set by GitHub Actions in the workflow.
            secret_client = secretmanager_v1.SecretManagerServiceClient()
            logging.info("Google Secret Manager client initialized successfully.")
        except Exception as e:
            logging.error(f"Failed to initialize Google Secret Manager client: {e}")
            # Depending on strictness, you might want to raise an exception here
            # to halt execution if secret manager is critical.

def get_secret(secret_name):
    """
    Retrieves a secret from GitHub Actions environment variables or GCP Secret Manager.
    Prioritizes environment variables.
    """
    # 1. Try to get from GitHub Actions environment variables
    env_value = os.getenv(secret_name.upper()) # GitHub secrets are usually uppercase
    if env_value:
        logging.info(f"Secret '{secret_name}' loaded from environment variable.")
        return env_value

    # 2. If not found in environment, try GCP Secret Manager
    _initialize_secret_client() # Ensure client is initialized
    if secret_client is None:
        logging.error(f"Secret Manager client not initialized. Cannot retrieve secret '{secret_name}'.")
        return None

    project_id = os.getenv("GCP_PROJECT_ID")
    if not project_id:
        logging.error("GCP_PROJECT_ID environment variable not set. Cannot retrieve secrets from GCP Secret Manager.")
        return None

    try:
        # GCP Secret Manager secret names are typically lowercase and hyphenated.
        # However, for consistency with GitHub Secrets, we will try the exact secret_name first,
        # and then a converted version (e.g., OPENAI_KEYS_JSON -> openai-keys-json) if needed.
        # For simplicity, let's assume direct mapping or you standardize naming.
        # Given your `OPENAI_KEYS_JSON` vs `openai-api-keys` example, we need to handle this.
        # Let's standardize on the GitHub Secrets names for GCP Secret Manager as well as per your request (2단계: 키 이름 통일).
        # So, the secret name in GCP should ideally be "OPENAI_KEYS_JSON" not "openai-api-keys".
        # If not, you'll need to map them explicitly here.
        name = f"projects/{project_id}/secrets/{secret_name}/versions/latest"
        response = secret_client.access_secret_version(request={"name": name})
        secret_value = response.payload.data.decode("UTF-8")
        logging.info(f"Secret '{secret_name}' loaded from GCP Secret Manager.")
        return secret_value
    except Exception as e:
        logging.warning(f"Could not retrieve secret '{secret_name}' from GCP Secret Manager: {e}")
        return None

def get_json_secret(secret_name):
    """Retrieves a secret and parses it as JSON."""
    secret_value = get_secret(secret_name)
    if secret_value:
        try:
            return json.loads(secret_value)
        except json.JSONDecodeError as e:
            logging.error(f"Failed to parse secret '{secret_name}' as JSON: {e}")
            return None
    return None

class AppConfig:
    """
    Manages application configuration, including API keys and settings.
    Handles API key rotation for OpenAI and Gemini.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AppConfig, cls).__new__(cls)
            cls._instance._load_config_data()
        return cls._instance

    def _load_config_data(self):
        self.config = {}

        # Load OpenAI Keys
        openai_keys_json = get_json_secret("OPENAI_KEYS_JSON")
        if openai_keys_json and isinstance(openai_keys_json, list):
            self.config["OPENAI_KEYS"] = [key for key in openai_keys_json if key] # Filter out empty keys
            self.openai_key_index = 0
            logging.info(f"Loaded {len(self.config['OPENAI_KEYS'])} OpenAI API keys.")
        else:
            self.config["OPENAI_KEYS"] = []
            logging.warning("No valid OpenAI API keys loaded.")

        # Load Gemini API Key
        gemini_api_key = get_secret("GEMINI_API_KEY")
        if gemini_api_key:
            self.config["GEMINI_API_KEY"] = [gemini_api_key] # Store as list for rotation
            self.gemini_key_index = 0
            logging.info("Loaded Gemini API key.")
        else:
            self.config["GEMINI_API_KEY"] = []
            logging.warning("No valid Gemini API key loaded.")

        # Load other API keys
        self.config["ELEVENLABS_API_KEY"] = get_secret("ELEVENLABS_API_KEY")
        self.config["ELEVENLABS_VOICE_ID"] = os.getenv("ELEVENLABS_VOICE_ID", "uyVNoMrnUku1dZyVEXwD") # Default to Anna Kim
        self.config["YOUTUBE_OAUTH_CREDENTIALS"] = get_json_secret("YOUTUBE_OAUTH_CREDENTIALS")
        self.config["NEWS_API_KEY"] = get_secret("NEWS_API_KEY")
        self.config["PEXELS_API_KEY"] = get_secret("PEXELS_API_KEY")
        self.config["GOOGLE_API_KEY"] = get_secret("GOOGLE_API_KEY") # For other Google APIs if needed

        # Load GCP settings
        self.config["GCP_PROJECT_ID"] = os.getenv("GCP_PROJECT_ID")
        self.config["GCP_BUCKET_NAME"] = os.getenv("GCP_BUCKET_NAME")

        # Set font path
        self.config["FONT_PATH"] = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'fonts', 'Catfont.ttf')
        if not os.path.exists(self.config["FONT_PATH"]):
            logging.error(f"Font file not found at {self.config['FONT_PATH']}. Please ensure Catfont.ttf is in the fonts directory.")

        # API usage tracking (simplified for demonstration, could use a database for persistence)
        self.api_usage = {
            "openai": 0,
            "gemini": 0
        }
        self.api_limits = { # Example limits, adjust based on actual free tier quotas
            "openai": {"daily": 500000, "monthly": 5000000}, # Example tokens/requests
            "gemini": {"daily": 1000, "monthly": 20000} # Example requests
        }

    def get_next_openai_key(self):
        """Returns the next OpenAI API key in a round-robin fashion."""
        if not self.config["OPENAI_KEYS"]:
            logging.error("No OpenAI API keys available.")
            return None
        key = self.config["OPENAI_KEYS"][self.openai_key_index]
        self.openai_key_index = (self.openai_key_index + 1) % len(self.config["OPENAI_KEYS"])
        logging.info(f"Using OpenAI API key: {self.openai_key_index} (rotated)")
        return key

    def get_next_gemini_key(self):
        """Returns the next Gemini API key in a round-robin fashion."""
        if not self.config["GEMINI_API_KEY"]:
            logging.error("No Gemini API keys available.")
            return None
        key = self.config["GEMINI_API_KEY"][self.gemini_key_index]
        self.gemini_key_index = (self.gemini_key_index + 1) % len(self.config["GEMINI_API_KEY"])
        logging.info(f"Using Gemini API key: {self.gemini_key_index} (rotated)")
        return key

    def get(self, key, default=None):
        """Retrieves a configuration value."""
        return self.config.get(key, default)

    def update_api_usage(self, api_name, usage_amount):
        """Updates API usage count and checks against limits."""
        if api_name in self.api_usage:
            self.api_usage[api_name] += usage_amount
            logging.info(f"API usage for {api_name}: {self.api_usage[api_name]}")
            # Basic limit check (daily/monthly tracking would require persistent storage)
            if self.api_usage[api_name] > self.api_limits.get(api_name, {}).get("daily", float('inf')):
                logging.warning(f"Daily API limit for {api_name} potentially exceeded!")

def load_config():
    """Returns the singleton AppConfig instance."""
    return AppConfig()

# Initialize secret client when module is loaded to catch potential issues early
_initialize_secret_client()
