import uuid

ALLOWED_EXTENSIONS = {
    "pdf",
    "ppt",
    "pptx",
    "doc",
    "docx",
}

ALLOWED_MIME_TYPES = {
    "application/pdf",
    "application/vnd.ms-powerpoint",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


def allowed_file(filename):
    if "." not in filename:
        return False

    ext = filename.rsplit(".", 1)[1].lower()

    return ext in ALLOWED_EXTENSIONS


def get_extension(filename):
    return filename.rsplit(".", 1)[1].lower()


def generate_secure_s3_key(prefix, original_filename):
    ext = get_extension(original_filename)
    unique_name = f"{uuid.uuid4().hex}.{ext}"

    return f"{prefix}/{unique_name}"
