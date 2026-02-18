"""MinIO S3 client for object storage."""
import json
from typing import Optional
import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class MinIOClient:
    """MinIO S3 client wrapper."""
    
    def __init__(self):
        self.s3_client = boto3.client(
            "s3",
            endpoint_url=f"http://{settings.minio_endpoint}",
            aws_access_key_id=settings.minio_access_key,
            aws_secret_access_key=settings.minio_secret_key,
            config=Config(signature_version="s3v4"),
            region_name="us-east-1",  # MinIO doesn't use regions, but boto3 requires one
        )
        self.bucket = settings.minio_bucket
    
    async def ensure_bucket_exists(self) -> None:
        """Create bucket if it doesn't exist."""
        try:
            self.s3_client.head_bucket(Bucket=self.bucket)
            logger.info("minio.bucket_exists", bucket=self.bucket)
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "404":
                try:
                    self.s3_client.create_bucket(Bucket=self.bucket)
                    logger.info("minio.bucket_created", bucket=self.bucket)
                except ClientError as create_error:
                    logger.error(
                        "minio.bucket_create_failed",
                        bucket=self.bucket,
                        error=str(create_error),
                    )
                    raise
            else:
                logger.error(
                    "minio.bucket_check_failed",
                    bucket=self.bucket,
                    error=str(e),
                )
                raise
    
    def upload_json(
        self, factory_id: int, job_id: str, data: dict
    ) -> str:
        """Upload JSON data to MinIO and return presigned URL.
        
        Args:
            factory_id: Factory ID for key prefix
            job_id: Job ID for filename
            data: JSON-serializable data
            
        Returns:
            Presigned URL for downloading the object
        """
        key = f"{factory_id}/analytics/{job_id}.json"
        
        try:
            self.s3_client.put_object(
                Bucket=self.bucket,
                Key=key,
                Body=json.dumps(data, indent=2, default=str),
                ContentType="application/json",
            )
            logger.info(
                "minio.upload_success",
                bucket=self.bucket,
                key=key,
                factory_id=factory_id,
                job_id=job_id,
            )
            return self.generate_presigned_url(key)
        except ClientError as e:
            logger.error(
                "minio.upload_failed",
                bucket=self.bucket,
                key=key,
                error=str(e),
            )
            raise
    
    def generate_presigned_url(self, key: str, expiry: int = 3600) -> str:
        """Generate presigned URL for object access.
        
        Args:
            key: Object key
            expiry: URL expiration time in seconds (default: 1 hour)
            
        Returns:
            Presigned URL string
        """
        try:
            url = self.s3_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket, "Key": key},
                ExpiresIn=expiry,
            )
            return url
        except ClientError as e:
            logger.error(
                "minio.presign_failed",
                bucket=self.bucket,
                key=key,
                error=str(e),
            )
            raise
    
    def delete_object(self, key: str) -> None:
        """Delete object from bucket.
        
        Args:
            key: Object key to delete
        """
        try:
            self.s3_client.delete_object(Bucket=self.bucket, Key=key)
            logger.info("minio.delete_success", bucket=self.bucket, key=key)
        except ClientError as e:
            logger.error(
                "minio.delete_failed",
                bucket=self.bucket,
                key=key,
                error=str(e),
            )
            raise


# Singleton instance
_minio_client: Optional[MinIOClient] = None


def get_minio_client() -> MinIOClient:
    """Get or create MinIO client instance."""
    global _minio_client
    if _minio_client is None:
        _minio_client = MinIOClient()
    return _minio_client
