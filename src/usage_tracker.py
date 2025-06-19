from datetime import datetime
from google.cloud import storage
import json

class UsageTracker:
    def __init__(self, bucket_name: str):
        self.client = storage.Client()
        self.bucket = self.client.bucket(bucket_name)
        
    def check_quota(self, service: str, daily_limit: int) -> bool:
        today = datetime.now().strftime("%Y-%m-%d")
        blob = self.bucket.blob(f"usage/{service}.json")
        
        try:
            data = json.loads(blob.download_as_text())
            if data["date"] != today:
                data = {"date": today, "count": 0}
        except:
            data = {"date": today, "count": 0}
            
        if data["count"] >= daily_limit:
            return False
            
        data["count"] += 1
        blob.upload_from_string(json.dumps(data))
        return True
