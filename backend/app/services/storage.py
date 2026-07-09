import os
import shutil
from io import BytesIO
import boto3
from botocore.exceptions import ClientError
from app.core.config import settings

class StorageService:
    def __init__(self):
        self.use_s3 = settings.USE_S3
        if self.use_s3:
            self.s3_client = boto3.client(
                "s3",
                endpoint_url=settings.S3_ENDPOINT_URL,
                aws_access_key_id=settings.S3_ACCESS_KEY,
                aws_secret_access_key=settings.S3_SECRET_KEY,
            )
            self.bucket_name = settings.S3_BUCKET
            self._ensure_bucket_exists()
        else:
            self.upload_dir = settings.UPLOAD_DIR
            os.makedirs(self.upload_dir, exist_ok=True)

    def _ensure_bucket_exists(self):
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
        except ClientError:
            try:
                self.s3_client.create_bucket(Bucket=self.bucket_name)
            except Exception as e:
                # In standard S3, bucket creation can fail if it already exists or permissions issue
                pass

    def upload_file(self, file_content: bytes, filename: str) -> str:
        """
        Uploads file and returns file path or S3 key.
        """
        if self.use_s3:
            key = f"materials/{os.urandom(8).hex()}_{filename}"
            self.s3_client.upload_fileobj(
                BytesIO(file_content),
                self.bucket_name,
                key
            )
            return key
        else:
            # Local Storage
            unique_name = f"{os.urandom(8).hex()}_{filename}"
            dest_path = os.path.join(self.upload_dir, unique_name)
            with open(dest_path, "wb") as buffer:
                buffer.write(file_content)
            return dest_path

    def delete_file(self, path_or_key: str) -> None:
        """
        Deletes the file from storage.
        """
        if self.use_s3:
            try:
                self.s3_client.delete_object(Bucket=self.bucket_name, Key=path_or_key)
            except Exception:
                pass
        else:
            if os.path.exists(path_or_key):
                try:
                    os.remove(path_or_key)
                except Exception:
                    pass

    def get_file_content(self, path_or_key: str) -> bytes:
        """
        Retrieves raw file bytes from storage.
        """
        if self.use_s3:
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=path_or_key)
            return response["Body"].read()
        else:
            if not os.path.exists(path_or_key):
                raise FileNotFoundError(f"File not found locally: {path_or_key}")
            with open(path_or_key, "rb") as f:
                return f.read()

storage_service = StorageService()
