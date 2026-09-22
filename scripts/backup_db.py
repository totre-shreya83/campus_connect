"""
Creates a compressed mysqldump of the CampusConnect database
and uploads it to S3.

Run:
    python scripts\backup_db.py
"""

import os
import sys
import gzip
import shutil
import subprocess
from datetime import datetime
from urllib.parse import urlparse

sys.path.insert(
    0,
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..")
    )
)

from app import create_app
from app.services.backup_service import log_backup, _get_s3_client


def parse_db_url(url):
    """Parse mysql+pymysql://user:password@host:port/database."""

    parsed = urlparse(
        url.replace(
            "mysql+pymysql://",
            "mysql://"
        )
    )

    return {
        "user": parsed.username,
        "password": parsed.password,
        "host": parsed.hostname or "localhost",
        "port": str(parsed.port or 3306),
        "database": parsed.path.lstrip("/"),
    }


def run_backup():
    app = create_app("development")

    with app.app_context():

        db_conf = parse_db_url(
            app.config["SQLALCHEMY_DATABASE_URI"]
        )

        timestamp = datetime.utcnow().strftime(
            "%Y%m%d_%H%M%S"
        )

        backup_dir = os.path.abspath(
            os.path.join(
                os.path.dirname(__file__),
                "..",
                "backups"
            )
        )

        os.makedirs(
            backup_dir,
            exist_ok=True
        )

        sql_path = os.path.join(
            backup_dir,
            f"campusconnect_{timestamp}.sql"
        )

        gz_path = sql_path + ".gz"

        mysqldump = os.environ.get(
            "MYSQLDUMP_PATH",
            "mysqldump"
        )

        cmd = [
            mysqldump,
            f"--host={db_conf['host']}",
            f"--port={db_conf['port']}",
            f"--user={db_conf['user']}",
            f"--password={db_conf['password']}",
            "--single-transaction",
            "--routines",
            "--triggers",
            db_conf["database"],
        ]

        try:

            print("Starting database backup...")
            print(
                f"Database: {db_conf['database']}"
            )

            with open(
                sql_path,
                "w",
                encoding="utf-8"
            ) as out:

                result = subprocess.run(
                    cmd,
                    stdout=out,
                    stderr=subprocess.PIPE,
                    text=True
                )

            if result.returncode != 0:

                print(
                    "mysqldump failed:"
                )
                print(result.stderr)

                log_backup(
                    "DATABASE",
                    "FAILED"
                )

                return

            print("Database dump created.")

            # Compress SQL dump
            with open(
                sql_path,
                "rb"
            ) as f_in:

                with gzip.open(
                    gz_path,
                    "wb"
                ) as f_out:

                    shutil.copyfileobj(
                        f_in,
                        f_out
                    )

            os.remove(sql_path)

            size_mb = round(
                os.path.getsize(gz_path)
                / (1024 * 1024),
                2
            )

            print(
                f"Compressed backup: {size_mb} MB"
            )

            # Upload to S3
            prefix = app.config.get(
                "BACKUP_PREFIX",
                "backups/db/"
            )

            s3_key = (
                f"{prefix}"
                f"campusconnect_{timestamp}.sql.gz"
            )

            s3 = _get_s3_client()

            print(
                f"Uploading to S3: {s3_key}"
            )

            s3.upload_file(
                gz_path,
                app.config["S3_BUCKET_NAME"],
                s3_key
            )

            location = (
                f"s3://"
                f"{app.config['S3_BUCKET_NAME']}/"
                f"{s3_key}"
            )

            log_backup(
                "DATABASE",
                "SUCCESS",
                location=location,
                size_mb=size_mb
            )

            print()
            print("================================")
            print("BACKUP SUCCESSFUL")
            print("================================")
            print(f"Location: {location}")
            print(f"Size: {size_mb} MB")

        except Exception as e:

            print(
                "Backup error:"
            )
            print(e)

            try:
                log_backup(
                    "DATABASE",
                    "FAILED"
                )
            except Exception as log_error:
                print(
                    "Could not write backup log:"
                )
                print(log_error)


if __name__ == "__main__":
    run_backup()
