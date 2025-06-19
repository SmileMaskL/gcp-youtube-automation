import logging
from datetime import datetime

class UsageTracker:
    def __init__(self):
        self.usage = {
            'openai': {'count': 0, 'last_reset': datetime.now()},
            'gemini': {'count': 0, 'last_reset': datetime.now()}
        }
        
    def increment(self, service):
        self.usage[service]['count'] += 1
        
    def check_quota(self, service, max_quota):
        # 월간 쿼터 리셋
        if (datetime.now() - self.usage[service]['last_reset']).days > 30:
            self.usage[service]['count'] = 0
            self.usage[service]['last_reset'] = datetime.now()
            
        return self.usage[service]['count'] < max_quota
