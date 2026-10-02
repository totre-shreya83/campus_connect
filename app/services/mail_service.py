import boto3
from flask import current_app
from botocore.exceptions import ClientError


def _get_ses_client():
    kwargs = {
        "region_name": current_app.config["AWS_REGION"]
    }

    # Local development can use explicit AWS credentials.
    # Production can leave them blank and use the EC2 IAM role.
    if current_app.config.get("AWS_ACCESS_KEY_ID") and current_app.config.get(
        "AWS_SECRET_ACCESS_KEY"
    ):
        kwargs["aws_access_key_id"] = current_app.config["AWS_ACCESS_KEY_ID"]
        kwargs["aws_secret_access_key"] = current_app.config[
            "AWS_SECRET_ACCESS_KEY"
        ]

    return boto3.client("ses", **kwargs)


def send_email(to_address, subject, body_text, body_html=None):
    """
    Send an email through AWS SES.

    When SES_ENABLED is false, no email is sent. Instead, the
    attempted email is logged and False is returned.
    """

    if not current_app.config.get("SES_ENABLED"):
        current_app.logger.info(
            f"[SES disabled] Would have emailed {to_address}: {subject}"
        )
        return False

    ses = _get_ses_client()

    body = {
        "Text": {
            "Data": body_text,
            "Charset": "UTF-8",
        }
    }

    if body_html:
        body["Html"] = {
            "Data": body_html,
            "Charset": "UTF-8",
        }

    try:
        ses.send_email(
            Source=current_app.config["SES_SENDER_EMAIL"],
            Destination={
                "ToAddresses": [to_address]
            },
            Message={
                "Subject": {
                    "Data": subject,
                    "Charset": "UTF-8",
                },
                "Body": body,
            },
        )

        current_app.logger.info(
            f"SES email sent successfully to {to_address}: {subject}"
        )

        return True

    except ClientError as e:
        current_app.logger.error(
            f"SES send failed for {to_address}: {e}"
        )
        return False

    except Exception as e:
        current_app.logger.error(
            f"Unexpected email error for {to_address}: {e}"
        )
        return False


def send_password_reset_email(user, reset_url):
    return send_email(
        to_address=user.email,
        subject="CampusConnect — Reset your password",
        body_text=(
            f"Hi {user.full_name},\n\n"
            "You requested a password reset for your CampusConnect account.\n\n"
            "Click the link below to reset your password. "
            "This link is valid for 1 hour:\n\n"
            f"{reset_url}\n\n"
            "If you did not request this password reset, you can safely "
            "ignore this email.\n\n"
            "CampusConnect"
        ),
    )


def send_notification_email(user, message):
    return send_email(
        to_address=user.email,
        subject="CampusConnect notification",
        body_text=(
            f"Hi {user.full_name},\n\n"
            f"{message}\n\n"
            "You can log in to CampusConnect to view more details.\n\n"
            "CampusConnect"
        ),
    )
