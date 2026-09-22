import boto3
from flask import current_app

from app import db
from app.models.backup_log import BackupLog


def log_backup(backup_type, status, location=None, size_mb=None):
    """Records a backup attempt. backup_type: DATABASE | FILES"""
    log = BackupLog(
        backup_type=backup_type,
        status=status,
        location=location,
        size_mb=size_mb,
    )

    db.session.add(log)
    db.session.commit()

    return log


def _get_s3_client():
    return boto3.client(
        "s3",
        aws_access_key_id=current_app.config["AWS_ACCESS_KEY_ID"],
        aws_secret_access_key=current_app.config["AWS_SECRET_ACCESS_KEY"],
        region_name=current_app.config["AWS_REGION"],
    )


def get_storage_stats():
    """Return S3 object count, total size, and bucket versioning status."""

    s3 = _get_s3_client()
    bucket = current_app.config["S3_BUCKET_NAME"]

    stats = {
        "object_count": 0,
        "total_size_mb": 0.0,
        "versioning": "Unknown",
        "error": None,
    }

    try:
        paginator = s3.get_paginator("list_objects_v2")

        total_bytes = 0
        count = 0

        for page in paginator.paginate(Bucket=bucket):
            for obj in page.get("Contents", []):
                total_bytes += obj["Size"]
                count += 1

        stats["object_count"] = count
        stats["total_size_mb"] = round(
            total_bytes / (1024 * 1024),
            2
        )

        versioning = s3.get_bucket_versioning(
            Bucket=bucket
        )

        stats["versioning"] = versioning.get(
            "Status",
            "Disabled"
        )

    except Exception as e:
        stats["error"] = str(e)

    return stats


def list_recent_db_backups(limit=10):
    """List the most recent database dumps stored in S3."""

    s3 = _get_s3_client()
    bucket = current_app.config["S3_BUCKET_NAME"]

    prefix = current_app.config.get(
        "BACKUP_PREFIX",
        "backups/db/"
    )

    try:
        response = s3.list_objects_v2(
            Bucket=bucket,
            Prefix=prefix
        )

        objects = response.get("Contents", [])

        objects.sort(
            key=lambda o: o["LastModified"],
            reverse=True
        )

        return [
            {
                "key": obj["Key"],
                "size_mb": round(
                    obj["Size"] / (1024 * 1024),
                    2
                ),
                "last_modified": obj["LastModified"],
            }
            for obj in objects[:limit]
        ]

    except Exception:
        return []

from pathlib import Path
import subprocess
import sys


def run_database_backup():
    """Run the existing database backup script and return its result."""

    project_root = Path(__file__).resolve().parents[2]
    script_path = project_root / "scripts" / "backup_db.py"

    result = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=str(project_root),
        capture_output=True,
        text=True,
    )

    return {
        "success": result.returncode == 0,
        "output": (result.stdout or "") + (result.stderr or ""),
    }

