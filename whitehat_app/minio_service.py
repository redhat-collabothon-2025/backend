import os
from datetime import timedelta

from minio import Minio
from minio.error import S3Error


class MinioService:

    def __init__(self):
        self.endpoint = os.getenv('MINIO_ENDPOINT', 'localhost:9000')
        self.access_key = os.getenv('MINIO_ACCESS_KEY', 'minioadmin')
        self.secret_key = os.getenv('MINIO_SECRET_KEY', 'minioadmin')
        self.secure = os.getenv('MINIO_SECURE', 'False').lower() == 'true'
        self.django_url = os.getenv('DJANGO_URL', 'http://localhost:8000')
        self.bucket = 'file-uploads'
        self.client = None
        self._initialized = False

    def _ensure_client(self):
        if self._initialized:
            return

        try:
            self.client = Minio(
                self.endpoint,
                access_key=self.access_key,
                secret_key=self.secret_key,
                secure=self.secure
            )
            self._ensure_bucket_exists()
            self._initialized = True
        except Exception as e:
            print(f"[MINIO] Failed to initialize: {str(e)}")

    def _ensure_bucket_exists(self):
        try:
            if not self.client.bucket_exists(self.bucket):
                self.client.make_bucket(self.bucket)
        except S3Error as e:
            print(f"[MINIO] Error creating bucket: {str(e)}")

    def get_upload_url(self, object_name, expires=timedelta(hours=1)):
        self._ensure_client()
        if not self.client:
            return None

        try:
            django_proxy_url = f"{self.django_url}/api/minio/{self.bucket}/{object_name}"
            return django_proxy_url
        except Exception as e:
            print(f"[MINIO] Error generating upload URL: {str(e)}")
            return None

    def get_download_url(self, object_name, expires=timedelta(hours=1)):
        self._ensure_client()
        if not self.client:
            return None

        try:
            django_proxy_url = f"{self.django_url}/api/minio/{self.bucket}/{object_name}"
            return django_proxy_url
        except Exception as e:
            print(f"[MINIO] Error generating download URL: {str(e)}")
            return None

    def file_exists(self, object_name):
        self._ensure_client()
        if not self.client:
            return False

        try:
            self.client.stat_object(self.bucket, object_name)
            return True
        except S3Error:
            return False


minio_service = MinioService()
