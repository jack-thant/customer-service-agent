from __future__ import annotations

import uuid
from pathlib import Path

import boto3
from botocore.exceptions import ClientError

from app.core.config import settings


class S3StorageService:
    def __init__(self) -> None:
        if not settings.aws_s3_bucket:
            raise ValueError("AWS_S3_BUCKET is not configured")

        session_kwargs: dict[str, str] = {"region_name": settings.aws_region}

        if settings.aws_access_key_id and settings.aws_secret_access_key:
            session_kwargs["aws_access_key_id"] = settings.aws_access_key_id
            session_kwargs["aws_secret_access_key"] = settings.aws_secret_access_key

        self.bucket = settings.aws_s3_bucket
        self.prefix = settings.aws_s3_prefix.strip("/")
        self.client = boto3.client("s3", **session_kwargs)

    def make_object_key(self, filename: str) -> str:
        ext = Path(filename).suffix.lower()
        object_name = f"{uuid.uuid4().hex}{ext}"
        return f"{self.prefix}/{object_name}" if self.prefix else object_name

    def upload_bytes(self, *, data: bytes, key: str, content_type: str) -> str:
        self.client.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=data,
            ContentType=content_type,
        )
        return f"s3://{self.bucket}/{key}"

    def read_text(self, storage_path: str) -> str:
        bucket, key = self._parse_s3_uri(storage_path)
        response = self.client.get_object(Bucket=bucket, Key=key)
        body = response["Body"].read()
        return body.decode("utf-8", errors="ignore")

    def object_exists(self, storage_path: str) -> bool:
        bucket, key = self._parse_s3_uri(storage_path)
        try:
            self.client.head_object(Bucket=bucket, Key=key)
            return True
        except ClientError as exc:
            error_code = exc.response.get("Error", {}).get("Code")
            if error_code in {"404", "NoSuchKey", "NotFound"}:
                return False
            raise

    def _parse_s3_uri(self, storage_path: str) -> tuple[str, str]:
        if not storage_path.startswith("s3://"):
            raise ValueError(f"Not an S3 URI: {storage_path}")

        path = storage_path[len("s3://") :]
        if "/" not in path:
            raise ValueError(f"Invalid S3 URI: {storage_path}")

        bucket, key = path.split("/", 1)
        return bucket, key
