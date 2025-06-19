import os
from datetime import datetime
from google.cloud import firestore

class UsageTracker:
    def __init__(self):
        self.db = firestore.Client(project=os.getenv("GCP_PROJECT_ID"))
        self.collection = self.db.collection("api_usage")

    def record_usage(self, service, tokens_used):
        doc_ref = self.collection.document(datetime.now().isoformat())
        doc_ref.set({
            "service": service,
            "tokens": tokens_used,
            "timestamp": datetime.now(),
            "api_key": os.getenv("CURRENT_API_KEY", "unknown")
        })

    def get_usage(self, service, time_range="daily"):
        now = datetime.now()
        if time_range == "daily":
            start_time = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif time_range == "monthly":
            start_time = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        else:
            start_time = now.replace(year=now.year - 1)
        
        query = self.collection.where("service", "==", service)\
                              .where("timestamp", ">=", start_time)
        docs = query.stream()
        
        total = 0
        for doc in docs:
            total += doc.to_dict().get("tokens", 0)
        return total
