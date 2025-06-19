from datetime import datetime
from google.cloud import storage

class UsageTracker:
    def __init__(self, bucket_name):
        self.client = storage.Client()
        self.bucket = self.client.bucket(bucket_name)
        
    def check_daily_quota(self, limit=5):
        blob = self.bucket.blob("usage.json")
        try:
            data = json.loads(blob.download_as_text())
            if data["date"] != datetime.now().strftime("%Y-%m-%d"):
                data = {"date": datetime.now().strftime("%Y-%m-%d"), "count": 0}
        except:
            data = {"date": datetime.now().strftime("%Y-%m-%d"), "count": 0}
            
        if data["count"] >= limit:
            raise RuntimeError("일일 할당량 초과")
            
        data["count"] += 1
        blob.upload_from_string(json.dumps(data))
