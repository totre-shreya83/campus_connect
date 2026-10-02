import boto3
from flask import current_app
from botocore.exceptions import ClientError
from botocore.config import Config


def _get_s3_client():
    kwargs = {
        "region_name": current_app.config["AWS_REGION"],
        "config": Config(
            signature_version="s3v4",
            s3={
                "addressing_style": "virtual"
            }
        )
    }

    # Local development can use explicit AWS credentials.
    # Production can leave them blank and use the EC2 IAM role.
    if (
        current_app.config.get("AWS_ACCESS_KEY_ID")
        and current_app.config.get("AWS_SECRET_ACCESS_KEY")
    ):
        kwargs["aws_access_key_id"] = current_app.config["AWS_ACCESS_KEY_ID"]
        kwargs["aws_secret_access_key"] = current_app.config[
            "AWS_SECRET_ACCESS_KEY"
        ]

    return boto3.client("s3", **kwargs)


def upload_file_to_s3(file_obj, s3_key):
    """Uploads a file-like object to S3 privately."""
    s3 = _get_s3_client()
    bucket = current_app.config["S3_BUCKET_NAME"]

    s3.upload_fileobj(
        file_obj,
        bucket,
        s3_key
    )

    return s3_key


def generate_presigned_download_url(
    s3_key,
    expires_in=300,
    download_filename=None
):
    """Generates a temporary signed URL for downloading a private S3 object."""

    s3 = _get_s3_client()
    bucket = current_app.config["S3_BUCKET_NAME"]

    params = {
        "Bucket": bucket,
        "Key": s3_key,
    }

    if download_filename:
        params["ResponseContentDisposition"] = (
            f'attachment; filename="{download_filename}"'
        )

    try:
        url = s3.generate_presigned_url(
            "get_object",
            Params=params,
            ExpiresIn=expires_in
        )

        return url

    except ClientError as e:
        current_app.logger.error(
            f"S3 presign error: {e}"
        )

        return None


def delete_file_from_s3(s3_key):
    s3 = _get_s3_client()
    bucket = current_app.config["S3_BUCKET_NAME"]

    s3.delete_object(
        Bucket=bucket,
        Key=s3_key
    )
