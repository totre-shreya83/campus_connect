# CampusConnect Backup & Recovery Guide

## 1. Database Backup

CampusConnect uses mysqldump to create a backup of the MySQL database.

The backup process is:

MySQL Database
    ?
mysqldump
    ?
SQL file
    ?
gzip compression
    ?
Amazon S3

Database backups are stored under:

backups/db/

Example:

s3://campusconnect-dev-shreya-2026/backups/db/campusconnect_YYYYMMDD_HHMMSS.sql.gz

Each successful backup is recorded in the backup_logs table.

---

## 2. Creating a Database Backup

From the CampusConnect project folder, run:

python scripts\backup_db.py

The script:

1. Creates a MySQL database dump.
2. Compresses the dump using gzip.
3. Uploads the compressed backup to S3.
4. Records the backup in backup_logs.

---

## 3. Database Restore

The restore script is:

scripts\restore_db.py

To restore a backup:

python scripts\restore_db.py "backups\campusconnect_YYYYMMDD_HHMMSS.sql.gz"

A restore should only be performed when recovery is required because it changes the database contents.

---

## 4. S3 File Backup

CampusConnect stores uploaded files in Amazon S3.

S3 Bucket Versioning is enabled.

Versioning allows previous versions of files to be recovered if an object is accidentally overwritten or deleted.

Important:

S3 Versioning does NOT back up the MySQL database.

The MySQL database is protected separately using mysqldump.

---

## 5. S3 File Recovery

To recover an older file version:

1. Open the CampusConnect S3 bucket.
2. Locate the required file.
3. View the object's versions.
4. Select the required previous version.
5. Restore or download that version.

---

## 6. Admin Backup Dashboard

Administrators can open:

/admin/backup

The dashboard displays:

- S3 object count
- S3 storage usage
- S3 Versioning status
- Recent database backups
- Backup history

---

## 7. Backup Verification

A successful backup can be verified by checking:

1. The local .sql.gz file exists.
2. The compressed backup can be opened.
3. The backup exists in S3.
4. A DATABASE SUCCESS entry exists in backup_logs.
5. The Admin Backup page displays the backup.

---

## 8. Security

Never commit the .env file to Git.

AWS credentials and database credentials must remain private.

For production deployments, database passwords should not be exposed through command-line arguments. A protected MySQL configuration file can be used instead.

---

## 9. Recovery Summary

Database recovery:

python scripts\restore_db.py "path\to\backup.sql.gz"

S3 file recovery:

Use S3 Versioning to recover the required previous object version.

Database recovery and S3 file recovery are independent processes.
