from datetime import datetime
from pymongo import MongoClient
from django.conf import settings


class TrackingLogger:

    def __init__(self):
        self.client = None
        self.db = None
        self.collection = None
        self._connect()

    def _connect(self):
        try:
            mongo_url = settings.MONGO_PUBLIC_URL
            if not mongo_url:
                return

            self.client = MongoClient(mongo_url, serverSelectionTimeoutMS=5000)
            self.client.admin.command('ping')
            self.db = self.client['whitehat_logs']
            self.collection = self.db['tracking_logs']

            self.collection.create_index([('timestamp', -1)])
            self.collection.create_index([('campaign_id', 1)])
            self.collection.create_index([('user_email', 1)])
            self.collection.create_index([('action_type', 1)])

        except Exception as e:
            print(f"[TRACKING_LOGGER] MongoDB connection failed: {str(e)}")
            self.client = None

    def log_email_open(self, user_email, campaign_id, campaign_name, template_type, tracking_id):
        if self.client is None or self.collection is None:
            return

        try:
            log_entry = {
                'timestamp': datetime.now(),
                'action_type': 'email_open',
                'user_email': user_email,
                'campaign_id': str(campaign_id) if campaign_id else None,
                'campaign_name': campaign_name,
                'template_type': template_type,
                'tracking_id': tracking_id,
                'risk_increase': 5
            }
            self.collection.insert_one(log_entry)
        except Exception as e:
            print(f"[TRACKING_LOGGER] Failed to log email open: {str(e)}")

    def log_link_click(self, user_email, campaign_id, campaign_name, template_type, tracking_id, severity):
        if self.client is None or self.collection is None:
            return

        try:
            log_entry = {
                'timestamp': datetime.now(),
                'action_type': 'link_click',
                'user_email': user_email,
                'campaign_id': str(campaign_id) if campaign_id else None,
                'campaign_name': campaign_name,
                'template_type': template_type,
                'tracking_id': tracking_id,
                'severity': severity,
                'risk_increase': 25
            }
            self.collection.insert_one(log_entry)
        except Exception as e:
            print(f"[TRACKING_LOGGER] Failed to log link click: {str(e)}")

    def get_campaign_stats(self, campaign_id):
        if self.client is None or self.collection is None:
            return None

        try:
            opens = self.collection.count_documents({
                'campaign_id': str(campaign_id),
                'action_type': 'email_open'
            })
            clicks = self.collection.count_documents({
                'campaign_id': str(campaign_id),
                'action_type': 'link_click'
            })

            return {
                'total_opens': opens,
                'total_clicks': clicks,
                'click_rate': (clicks / opens * 100) if opens > 0 else 0
            }
        except Exception:
            return None

    def close(self):
        if self.client:
            self.client.close()


tracking_logger = TrackingLogger()
