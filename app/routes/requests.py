from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user

from app import db
from app.models.note_request import NoteRequest, RequestReply
from app.models.note import Note
from app.models.user import User
from app.services.notification_service import create_notification
from app.forms.request_forms import CreateRequestForm, ReplyRequestForm
from app.utils.file_validators import allowed_file, generate_secure_s3_key
from app.services.s3_service import upload_file_to_s3


requests_bp = Blueprint("requests", __name__, url_prefix="/requests")

PER_PAGE = 10


@requests_bp.route("/")
@login_required
def list_requests():
    page = request.args.get("page", 1, type=int)

    query = NoteRequest.query.filter_by(status="OPEN")

    subject = request.args.get("subject", "").strip()
    semester = request.args.get("semester", "").strip()

    if subject:
        query = query.filter(
            NoteRequest.subject.ilike(f"%{subject}%")
        )

    if semester and semester.isdigit():
        query = query.filter(
            NoteRequest.semester == int(semester)
        )

    pagination = (
        query
        .order_by(NoteRequest.created_at.desc())
        .paginate(
            page=page,
            per_page=PER_PAGE,
            error_out=False
        )
    )

    return render_template(
        "requests/list.html",
        requests=pagination.items,
        pagination=pagination,
        args=request.args
    )


@requests_bp.route("/create", methods=["GET", "POST"])
@login_required
def create():
    form = CreateRequestForm()

    if form.validate_on_submit():
        req = NoteRequest(
            requester_id=current_user.id,
            subject=form.subject.data.strip(),
            semester=form.semester.data,
            department=(
                form.department.data.strip()
                if form.department.data
                else None
            ),
            description=form.description.data.strip(),
            status="OPEN"
        )

        db.session.add(req)
        db.session.flush()

        print("DEBUG: Creating notifications for request", req.id, "by user", current_user.id)
        # Notify all other students about the new note request.
        students = User.query.filter(
            User.role == "STUDENT",
            User.id != current_user.id
        ).all()
        print("DEBUG: Students to notify:", [(s.id, s.email) for s in students])
        for student in students:
            create_notification(
                user_id=student.id,
                message=(
                    f"New note request: '{req.subject}' "
                    f"(Sem {req.semester})"
                    + (
                        f" - {req.department}"
                        if req.department
                        else ""
                    )
                    + "."
                ),
                type="new_request",
            )

        db.session.commit()

        flash(
            "Your request has been posted. Other students can now respond.",
            "success"
        )

        return redirect(
            url_for(
                "requests.view",
                request_id=req.id
            )
        )

    if request.method == "GET":
        form.subject.data = request.args.get("subject", "")

        sem = request.args.get("semester", "")

        if sem.isdigit():
            form.semester.data = int(sem)

    return render_template(
        "requests/create.html",
        form=form
    )


@requests_bp.route("/<int:request_id>")
@login_required
def view(request_id):
    req = NoteRequest.query.get_or_404(request_id)

    form = ReplyRequestForm()

    return render_template(
        "requests/view.html",
        req=req,
        form=form
    )


@requests_bp.route(
    "/<int:request_id>/reply",
    methods=["POST"]
)
@login_required
def reply(request_id):
    req = NoteRequest.query.get_or_404(request_id)

    if req.status == "FULFILLED":
        flash(
            "This request has already been fulfilled.",
            "info"
        )

        return redirect(
            url_for(
                "requests.view",
                request_id=req.id
            )
        )

    form = ReplyRequestForm()

    if form.validate_on_submit():
        note_id = None
        file = form.file.data

        if file and file.filename:
            if not allowed_file(file.filename):
                flash(
                    "Invalid file type.",
                    "danger"
                )

                return redirect(
                    url_for(
                        "requests.view",
                        request_id=req.id
                    )
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
                title=(
                    f"{req.subject} - "
                    f"Sem {req.semester} (requested)"
                ),
                description=(
                    "Uploaded in response to a note request."
                ),
                subject=req.subject,
                semester=req.semester,
                department=req.department or "N/A",
                file_type=file.filename.rsplit(
                    ".",
                    1
                )[1].lower(),
                file_name=file.filename,
                s3_key=s3_key,
                uploader_id=current_user.id,
                approval_status="PENDING"
            )

            db.session.add(note)
            db.session.flush()

            note_id = note.id

        reply_obj = RequestReply(
            request_id=req.id,
            responder_id=current_user.id,
            note_id=note_id,
            message=form.message.data
        )

        db.session.add(reply_obj)

        create_notification(
            user_id=req.requester_id,
            message=f"Someone responded to your request for '{req.subject}' (Sem {req.semester}).",
            type="new_reply",
        )

        db.session.commit()

        flash(
            "Reply posted."
            + (
                " Uploaded note is pending admin approval."
                if note_id
                else ""
            ),
            "success"
        )

        return redirect(
            url_for(
                "requests.view",
                request_id=req.id
            )
        )

    flash(
        "Please provide a message or a file.",
        "danger"
    )

    return redirect(
        url_for(
            "requests.view",
            request_id=req.id
        )
    )


@requests_bp.route(
    "/<int:request_id>/fulfill",
    methods=["POST"]
)
@login_required
def fulfill(request_id):
    req = NoteRequest.query.get_or_404(request_id)

    if req.requester_id != current_user.id:
        abort(403)

    req.status = "FULFILLED"

    db.session.commit()

    flash(
        "Request marked as fulfilled. Thanks for confirming!",
        "success"
    )

    return redirect(
        url_for(
            "requests.view",
            request_id=req.id
        )
    )


@requests_bp.route("/my-requests")
@login_required
def my_requests():
    reqs = (
        NoteRequest.query
        .filter_by(
            requester_id=current_user.id
        )
        .order_by(
            NoteRequest.created_at.desc()
        )
        .all()
    )

    return render_template(
        "requests/my_requests.html",
        requests=reqs
    )



