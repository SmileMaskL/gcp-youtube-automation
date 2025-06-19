import logging
from google.cloud import logging as cloud_logging

def setup_logging():
    client = cloud_logging.Client()
    client.setup_logging()
    
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    return logger

logger = setup_logging()

def log_error(error_message, context=None):
    error_data = {
        "message": error_message,
        "context": context or {},
        "timestamp": datetime.now().isoformat()
    }
    
    # Cloud Logging에 기록
    logger.error(error_message, extra=error_data)
    
    # Firestore에 에러 기록 (선택적)
    try:
        from google.cloud import firestore
        db = firestore.Client()
        db.collection("errors").add(error_data)
    except:
        pass
