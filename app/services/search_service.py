from app.models.note import Note
from app import db
from sqlalchemy import or_

def smart_search_notes(query_text=None, subject=None, semester=None, department=None,
                        faculty=None, file_type=None, category_id=None, page=1, per_page=12):
    """
    Searches APPROVED notes across multiple metadata fields.
    - query_text: free-text search across title, subject, keywords, faculty, department
    - subject/semester/department/faculty/file_type: exact/partial filters, combinable with query_text
    """
    q = Note.query.filter_by(approval_status="APPROVED")

    if query_text:
        like = f"%{query_text.strip()}%"
        q = q.filter(
            or_(
                Note.title.ilike(like),
                Note.subject.ilike(like),
                Note.keywords.ilike(like),
                Note.faculty.ilike(like),
                Note.department.ilike(like),
                Note.description.ilike(like),
            )
        )

    if subject:
        q = q.filter(Note.subject.ilike(f"%{subject}%"))

    if department:
        q = q.filter(Note.department.ilike(f"%{department}%"))

    if faculty:
        q = q.filter(Note.faculty.ilike(f"%{faculty}%"))

    if semester:
        q = q.filter(Note.semester == semester)

    if file_type:
        q = q.filter(Note.file_type == file_type.lower())

    if category_id:
        q = q.filter(Note.category_id == category_id)

    q = q.order_by(Note.uploaded_at.desc())

    return q.paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )




