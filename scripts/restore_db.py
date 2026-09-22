"""
Restore a CampusConnect MySQL database from a gzipped SQL backup.

Usage:
    python scripts\restore_db.py "path\to\backup.sql.gz"

WARNING:
    This restores the database contents from the selected backup.
    Use only when a database restore is actually required.
"""

import gzip
import os
import shutil
import subprocess
import sys
from urllib.parse import urlparse

from dotenv import load_dotenv


load_dotenv()


def parse_db_url(url):
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


def restore_backup(gz_path):

    if not os.path.isfile(gz_path):
        print("Backup file not found:")
        print(gz_path)
        return False

    database_url = os.environ.get("DATABASE_URL")

    if not database_url:
        print("DATABASE_URL is not configured.")
        return False

    db_conf = parse_db_url(database_url)

    mysql_path = os.environ.get(
        "MYSQL_PATH",
        "mysql"
    )

    print("Starting database restore...")
    print(
        f"Database: {db_conf['database']}"
    )
    print(
        f"Backup: {gz_path}"
    )

    cmd = [
        mysql_path,
        f"--host={db_conf['host']}",
        f"--port={db_conf['port']}",
        f"--user={db_conf['user']}",
        f"--password={db_conf['password']}",
        db_conf["database"],
    ]

    try:

        with gzip.open(
            gz_path,
            "rb"
        ) as backup_file:

            result = subprocess.run(
                cmd,
                stdin=backup_file,
                stderr=subprocess.PIPE,
                text=True
            )

        if result.returncode != 0:
            print("Database restore failed:")
            print(result.stderr)
            return False

        print()
        print("==============================")
        print("DATABASE RESTORE SUCCESSFUL")
        print("==============================")

        return True

    except Exception as e:
        print("Restore error:")
        print(e)
        return False


if __name__ == "__main__":

    if len(sys.argv) != 2:
        print(
            "Usage: python scripts\\restore_db.py "
            "\"path\\to\\backup.sql.gz\""
        )
        sys.exit(1)

    success = restore_backup(
        sys.argv[1]
    )

    sys.exit(
        0 if success else 1
    )
