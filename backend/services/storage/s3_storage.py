import os
import re
import uuid
import logging
from typing import Optional
import boto3

logger = logging.getLogger("recallmatch.storage")


class S3StorageService:
    """Service to persist uploaded hospital inventory CSV files to AWS S3."""

    def __init__(
        self,
        bucket_name: Optional[str] = None,
        region_name: Optional[str] = None,
    ):
        self.bucket_name = bucket_name or os.getenv("RECLARO_S3_BUCKET")
        self.region_name = region_name or os.getenv("AWS_REGION", "us-east-1")
        self._s3_client = None

    def _get_client(self):
        if self._s3_client is None:
            self._s3_client = boto3.client("s3", region_name=self.region_name)
        return self._s3_client

    def _sanitize_filename(self, filename: str) -> str:
        """Strips path components and sanitizes the filename to prevent path traversal."""
        if not filename:
            return "inventory.csv"
        # Extract basename to remove any directory components (e.g., ../../ or /etc/)
        base = os.path.basename(filename.replace("\\", "/"))
        # Replace non-alphanumeric, non-hyphen, non-underscore, non-dot chars
        clean = re.sub(r"[^a-zA-Z0-9._-]", "_", base).lstrip(".")
        return clean if clean else "inventory.csv"

    def upload_inventory_csv(self, contents: bytes, filename: str) -> str:
        """
        Uploads original inventory CSV bytes to S3 and returns the S3 object key.
        Raises RuntimeError if RECLARO_S3_BUCKET is not configured.
        """
        if not self.bucket_name:
            raise RuntimeError("RECLARO_S3_BUCKET environment variable is not configured.")

        safe_name = self._sanitize_filename(filename)
        file_uuid = str(uuid.uuid4())
        object_key = f"inventory/{file_uuid}/{safe_name}"

        logger.info(
            f"Uploading inventory CSV to S3: bucket='{self.bucket_name}', "
            f"key='{object_key}', bytes={len(contents)}"
        )

        client = self._get_client()
        client.put_object(
            Bucket=self.bucket_name,
            Key=object_key,
            Body=contents,
            ContentType="text/csv",
        )

        return object_key
