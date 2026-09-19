"""
Storage service package for Reclaro.
Provides S3 inventory CSV object storage.
"""

from backend.services.storage.s3_storage import S3StorageService

__all__ = ["S3StorageService"]
