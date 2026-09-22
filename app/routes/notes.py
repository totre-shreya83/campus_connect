from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user

from app import db
from app.models.note import Note
from app.models.category import Category
from app.models.download import Download
from app.forms.note_forms import UploadNoteForm, EditNoteForm
from app.utils.file_validators import (
    allowed_file,
    generate_secure_s3_key,
)
from app.services.s3_service import (
    upload_file_to_s3,
    generate_presigned_download_url,
    delete_file_from_s3,
)
from app.services.search_service import smart_search_notes


notes_bp = Blueprint(
    "notes",
    __name__,
    url_prefix="/notes"
)

PER_PAGE = 12


@notes_bp.route("/")
@login_required
def list_notes():
    return redirect(url_for("notes.search"))


@notes_bp.route("/search")
@login_required
def search():
    page = request.args.get("page", 1, type=int)

    query_text = request.args.get("q", "").strip() or None
    subject = request.args.get("subject", "").strip() or None
    department = request.args.get("department", "").strip() or None
    faculty = request.args.get("faculty", "").strip() or None
    file_type = request.args.get("file_type", "").strip() or None
    category_id = request.args.get("category_id", type=int)

    semester = request.args.get("semester", "").strip() or None
    semester = int(semester) if semester and semester.isdigit() else None

    pagination = smart_search_notes(
        query_text=query_text,
        subject=subject,
        semester=semester,
        department=department,
        faculty=faculty,
        file_type=file_type,
        category_id=category_id,
        page=page,
        per_page=PER_PAGE,
    )

    categories = Category.query.order_by(Category.name).all()

    return render_template(
        "notes/search_results.html",
        notes=pagination.items,
        categories=categories,
        pagination=pagination,
        args=request.args,
    )


@notes_bp.route("/upload", methods=["GET", "POST"])
@login_required
def upload():
    form = UploadNoteForm()
    form.category_id.choices = [(0, "No Category")] + [
        (c.id, c.name)
        for c in Category.query.order_by(Category.name).all()
    ]

    if form.validate_on_submit():
        file = form.file.data

        if not allowed_file(file.filename):
            flash(
                "Invalid file type.",
                "danger"
            )

            return render_template(
                "notes/upload.html",
                form=form
            )

        s3_key = generate_secure_s3_key(
            "notes",
            file.filename
        )

        upload_file_to_s3(
            file,
            s3_key
        )

        note = Note(
            title=form.title.data.strip(),
            description=form.description.data,
            subject=form.subject.data.strip(),
            semester=form.semester.data,
            department=form.department.data.strip(),
            faculty=(
                form.faculty.data.strip()
                if form.faculty.data
                else None
            ),
            keywords=(
                form.keywords.data.strip()
                if form.keywords.data
                else None
            ),
            category_id=(
                form.category_id.data
                if form.category_id.data != 0
                else None
            ),
            file_type=file.filename.rsplit(
                ".",
                1
            )[1].lower(),
            file_name=file.filename,
            s3_key=s3_key,
            uploader_id=current_user.id,
            approval_status="PENDING",
        )

        db.session.add(note)
        db.session.commit()

        flash(
            "Note uploaded! It will be visible after admin approval.",
            "success"
        )

        return redirect(
            url_for("notes.my_uploads")
        )

    return render_template(
        "notes/upload.html",
        form=form
    )


@notes_bp.route("/my-uploads")
@login_required
def my_uploads():
    notes = (
        Note.query
        .filter_by(
            uploader_id=current_user.id
        )
        .order_by(
            Note.uploaded_at.desc()
        )
        .all()
    )

    return render_template(
        "notes/my_uploads.html",
        notes=notes
    )


@notes_bp.route("/<int:note_id>")
@login_required
def view(note_id):
    note = Note.query.get_or_404(note_id)

    if (
        note.approval_status != "APPROVED"
        and note.uploader_id != current_user.id
        and not current_user.is_admin()
    ):
        abort(403)

    return render_template(
        "notes/view.html",
        note=note
    )


@notes_bp.route("/<int:note_id>/download")
@login_required
def download(note_id):
    note = Note.query.get_or_404(note_id)

    if (
        note.approval_status != "APPROVED"
        and note.uploader_id != current_user.id
        and not current_user.is_admin()
    ):
        abort(403)

    url = generate_presigned_download_url(
        note.s3_key,
        expires_in=300,
        download_filename=note.file_name
    )

    if not url:
        flash(
            "Could not generate download link. Try again.",
            "danger"
        )

        return redirect(
            url_for(
                "notes.view",
                note_id=note.id
            )
        )

    note.download_count = (
        note.download_count or 0
    ) + 1

    db.session.add(
        Download(
            note_id=note.id,
            user_id=current_user.id
        )
    )

    db.session.commit()

    return redirect(url)


@notes_bp.route(
    "/<int:note_id>/edit",
    methods=["GET", "POST"]
)
@login_required
def edit(note_id):
    note = Note.query.get_or_404(note_id)

    if note.uploader_id != current_user.id:
        abort(403)

    form = EditNoteForm(obj=note)
    form.category_id.choices = [(0, "No Category")] + [
        (c.id, c.name)
        for c in Category.query.order_by(Category.name).all()
    ]

    if form.validate_on_submit():
        note.title = form.title.data.strip()
        note.description = form.description.data
        note.subject = form.subject.data.strip()
        note.semester = form.semester.data
        note.department = form.department.data.strip()
        note.faculty = (
            form.faculty.data.strip()
            if form.faculty.data
            else None
        )
        note.keywords = (
            form.keywords.data.strip()
            if form.keywords.data
            else None
        )
        note.category_id = (
            form.category_id.data
            if form.category_id.data != 0
            else None
        )

        db.session.commit()

        flash(
            "Note updated.",
            "success"
        )

        return redirect(
            url_for("notes.my_uploads")
        )

    return render_template(
        "notes/edit.html",
        form=form,
        note=note
    )


@notes_bp.route(
    "/<int:note_id>/delete",
    methods=["POST"]
)
@login_required
def delete(note_id):
    note = Note.query.get_or_404(note_id)

    if (
        note.uploader_id != current_user.id
        and not current_user.is_admin()
    ):
        abort(403)

    delete_file_from_s3(
        note.s3_key
    )

    db.session.delete(note)
    db.session.commit()

    flash(
        "Note deleted.",
        "info"
    )

    return redirect(
        url_for("notes.my_uploads")
    )







