import logging
from newsapi import NewsApiClient # For fetching hot topics
from src.ai_manager import AIManager
from src.config import load_config # Ensure config is accessible

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_hot_topic(news_api_key):
    """Fetches a hot topic from a news API."""
    if not news_api_key:
        logging.warning("News API key not provided. Cannot fetch hot topics.")
        return "today's interesting facts" # Fallback topic

    newsapi = NewsApiClient(api_key=news_api_key)
    try:
        # Fetch top headlines, focusing on a general category or trending
        top_headlines = newsapi.get_top_headlines(language='en', page_size=5)
        if top_headlines and top_headlines['articles']:
            # Pick a random article title or combine a few
            article_titles = [article['title'] for article in top_headlines['articles'] if article['title']]
            if article_titles:
                topic = article_titles[0] # Just take the first one for simplicity
                logging.info(f"Fetched hot topic: {topic}")
                return topic
        logging.warning("Could not fetch hot topics from News API. Using a generic topic.")
        return "today's trending topics"
    except Exception as e:
        logging.error(f"Error fetching hot topics from News API: {e}")
        return "current events" # Fallback

def generate_content(config):
    """
    Generates content (script, title, description) for a video.
    Utilizes AI for script generation and News API for topic selection.
    """
    ai_manager = AIManager()
    news_api_key = config.get("NEWS_API_KEY")

    topic = get_hot_topic(news_api_key)
    
    # Example prompt for AI. Refine this for better content.
    prompt = (f"Generate a captivating and short video script for a 60-second YouTube Shorts video "
              f"about '{topic}'. The script should be engaging, informative, and suitable for all ages. "
              f"Include a catchy title and a brief description. The script should be in Korean. "
              f"Format: {{'title': 'Video Title', 'script': 'Video Script', 'description': 'Video Description'}}")

    logging.info(f"Generating content with AI for topic: {topic}")
    content_json_str = ai_manager.generate_content_with_rotation(prompt, preferred_model="gpt-4o")

    if content_json_str:
        try:
            content_data = json.loads(content_json_str)
            if "title" not in content_data or "script" not in content_data or "description" not in content_data:
                raise ValueError("AI response missing required fields (title, script, description).")
            
            logging.info("Content generated successfully.")
            return content_data
        except json.JSONDecodeError as e:
            logging.error(f"Failed to parse AI-generated content JSON: {e}. Raw content: {content_json_str}")
            return None
        except ValueError as e:
            logging.error(f"Invalid AI-generated content format: {e}. Raw content: {content_json_str}")
            return None
    else:
        logging.error("Failed to generate content from AI.")
        return None
