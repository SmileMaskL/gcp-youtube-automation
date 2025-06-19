from datetime import datetime, timedelta
import json
from google.cloud import storage

class UsageTracker:
    def __init__(self):
        self.bucket_name = "your-bucket-name"
        self.client = storage.Client()
        
    def check_usage(self):
        blob = self.client.bucket(self.bucket_name).blob("usage.json")
        
        try:
            data = json.loads(blob.download_as_text())
            if data["date"] != datetime.now().strftime("%Y-%m-%d"):
                data = {"date": datetime.now().strftime("%Y-%m-%d"), "count": 0}
        except:
            data = {"date": datetime.now().strftime("%Y-%m-%d"), "count": 0}
            
        if data["count"] >= 5:  # 일일 최대 5개 영상
            raise Exception("일일 할당량 초과")
            
        data["count"] += 1
        blob.upload_from_string(json.dumps(data))
