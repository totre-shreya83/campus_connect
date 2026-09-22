from datetime import datetime, timedelta

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from sqlalchemy import func

from app import db
from app.models.user import User
from app.models.note import Note
from app.models.download import Download
from app.models.category import Category
from app.models.note_request import NoteRequest
from app.models.quiz import Quiz, QuizQuestion, QuizAttempt
from app.models.placement_resource import PlacementResource
from app.models.backup_log import BackupLog

from app.forms.admin_forms import CategoryForm
from app.utils.decorators import admin_required
from app.services.notification_service import create_notification
from app.services.points_service import award_points, get_contributor_leaderboard
from app.services.s3_service import delete_file_from_s3
from app.services.backup_service import get_storage_stats, list_recent_db_backups, run_database_backup


admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

PER_PAGE = 20


@admin_bp.before_request
@login_required
@admin_required
def restrict_to_admins():
    pass


@admin_bp.route("/")
def dashboard():
    stats = {
        "total_users": User.query.count(),
        "total_notes": Note.query.count(),
        "pending_approvals": Note.query.filter_by(
            approval_status="PENDING"
        ).count(),
        "total_downloads": db.session.query(
            func.coalesce(func.sum(Note.download_count), 0)
        ).scalar(),
        "open_requests": NoteRequest.query.filter_by(status="OPEN").count(),
        "total_quizzes": Quiz.query.count(),
        "total_questions": QuizQuestion.query.count(),
        "total_attempts": QuizAttempt.query.count(),
        "total_resources": PlacementResource.query.count(),
    }

    status_counts = dict(
        db.session.query(
            Note.approval_status,
            func.count(Note.id)
        )
        .group_by(Note.approval_status)
        .all()
    )

    chart_status = {
        "labels": ["Approved", "Pending", "Rejected"],
        "data": [
            status_counts.get("APPROVED", 0),
            status_counts.get("PENDING", 0),
            status_counts.get("REJECTED", 0),
        ],
    }

    six_months_ago = datetime.utcnow() - timedelta(days=180)

    monthly = (
        db.session.query(
            func.date_format(
                Note.uploaded_at, "%Y-%m"
            ).label("month"),
            func.count(Note.id),
        )
        .filter(Note.uploaded_at >= six_months_ago)
        .group_by("month")
        .order_by("month")
        .all()
    )

    chart_uploads = {
        "labels": [m for m, _ in monthly],
        "data": [c for _, c in monthly],
    }

    last_backup = BackupLog.query.order_by(
        BackupLog.created_at.desc()
    ).first()

    return render_template(
        "admin/dashboard.html",
        stats=stats,
        chart_status=chart_status,
        chart_uploads=chart_uploads,
        last_backup=last_backup,
    )


@admin_bp.route("/users")
def users():
    page = request.args.get("page", 1, type=int)
    search = request.args.get("q", "").strip()

    query = User.query

    if search:
        query = query.filter(
            db.or_(
                User.full_name.ilike(f"%{search}%"),
                User.email.ilike(f"%{search}%")
            )
        )

    pagination = query.order_by(
        User.created_at.desc()
    ).paginate(
        page=page,
        per_page=PER_PAGE,
        error_out=False
    )

    return render_template(
        "admin/users.html",
        users=pagination.items,
        pagination=pagination,
        args=request.args,
    )


@admin_bp.route("/users/<int:user_id>")
def user_detail(user_id):
    user = User.query.get_or_404(user_id)

    notes = Note.query.filter_by(
        uploader_id=user.id
    ).order_by(
        Note.uploaded_at.desc()
    ).limit(20).all()

    reqs = NoteRequest.query.filter_by(
        requester_id=user.id
    ).order_by(
        NoteRequest.created_at.desc()
    ).limit(20).all()

    attempts = QuizAttempt.query.filter_by(
        user_id=user.id
    ).order_by(
        QuizAttempt.attempted_at.desc()
    ).limit(20).all()

    return render_template(
        "admin/user_detail.html",
        user=user,
        notes=notes,
        reqs=reqs,
        attempts=attempts,
    )


@admin_bp.route("/users/<int:user_id>/toggle-active", methods=["POST"])
def toggle_active(user_id):
    user = User.query.get_or_404(user_id)

    if user.id == current_user.id:
        flash(
            "You cannot deactivate your own account.",
            "danger"
        )
        return redirect(url_for("admin.users"))

    user.is_active_flag = not user.is_active_flag
    db.session.commit()

    flash(
        f"User {'activated' if user.is_active_flag else 'deactivated'}.",
        "success"
    )

    return redirect(url_for("admin.users"))


@admin_bp.route("/users/<int:user_id>/toggle-role", methods=["POST"])
def toggle_role(user_id):
    user = User.query.get_or_404(user_id)

    if user.id == current_user.id:
        flash(
            "You cannot change your own role.",
            "danger"
        )
        return redirect(url_for("admin.users"))

    user.role = "ADMIN" if user.role == "STUDENT" else "STUDENT"
    db.session.commit()

    flash(
        f"Role changed to {user.role}.",
        "success"
    )

    return redirect(url_for("admin.users"))


@admin_bp.route("/notes")
def notes():
    page = request.args.get("page", 1, type=int)
    status = request.args.get(
        "status", "PENDING"
    ).upper()

    query = Note.query

    if status in ("PENDING", "APPROVED", "REJECTED"):
        query = query.filter_by(
            approval_status=status
        )

    pagination = query.order_by(
        Note.uploaded_at.desc()
    ).paginate(
        page=page,
        per_page=PER_PAGE,
        error_out=False
    )

    return render_template(
        "admin/notes.html",
        notes=pagination.items,
        pagination=pagination,
        status=status,
    )


@admin_bp.route("/notes/<int:note_id>/approve", methods=["POST"])
def approve_note(note_id):
    note = Note.query.get_or_404(note_id)

    if note.approval_status == "APPROVED":
        flash("Note is already approved.", "info")
        return redirect(url_for("admin.notes"))

    note.approval_status = "APPROVED"

    create_notification(
        user_id=note.uploader_id,
        message=f"Your note '{note.title}' was approved and is now public.",
        type="note_approved",
    )

    award_points(
        note.uploader_id,
        "note_approved",
        reference_id=note.id
    )

    db.session.commit()

    flash(
        f"Approved '{note.title}'. Uploader awarded 10 points.",
        "success"
    )

    return redirect(url_for("admin.notes"))


@admin_bp.route("/notes/<int:note_id>/reject", methods=["POST"])
def reject_note(note_id):
    note = Note.query.get_or_404(note_id)

    reason = request.form.get(
        "reason", ""
    ).strip()

    note.approval_status = "REJECTED"

    message = f"Your note '{note.title}' was rejected."

    if reason:
        message += f" Reason: {reason}"

    create_notification(
        user_id=note.uploader_id,
        message=message,
        type="note_rejected",
    )

    db.session.commit()

    flash(
        f"Rejected '{note.title}'.",
        "info"
    )

    return redirect(url_for("admin.notes"))


@admin_bp.route("/notes/<int:note_id>/delete", methods=["POST"])
def delete_note(note_id):
    note = Note.query.get_or_404(note_id)

    try:
        delete_file_from_s3(note.s3_key)
    except Exception as e:
        flash(
            f"S3 delete warning: {e}",
            "warning"
        )

    Download.query.filter_by(note_id=note.id).delete(synchronize_session=False)

    db.session.delete(note)
    db.session.commit()

    flash("Note deleted.", "info")

    return redirect(url_for("admin.notes"))


@admin_bp.route("/categories", methods=["GET", "POST"])
def categories():
    form = CategoryForm()

    if form.validate_on_submit():
        existing = Category.query.filter_by(
            name=form.name.data.strip()
        ).first()

        if existing:
            flash(
                "That category already exists.",
                "danger"
            )
        else:
            db.session.add(
                Category(
                    name=form.name.data.strip(),
                    description=form.description.data
                )
            )

            db.session.commit()

            flash(
                "Category created.",
                "success"
            )

        return redirect(url_for("admin.categories"))

    all_categories = Category.query.order_by(
        Category.name
    ).all()

    return render_template(
        "admin/categories.html",
        categories=all_categories,
        form=form,
    )


@admin_bp.route("/categories/<int:category_id>/delete", methods=["POST"])
def delete_category(category_id):
    category = Category.query.get_or_404(category_id)

    if category.notes:
        flash(
            "Cannot delete a category that still has notes assigned.",
            "danger"
        )
        return redirect(url_for("admin.categories"))

    db.session.delete(category)
    db.session.commit()

    flash(
        "Category deleted.",
        "info"
    )

    return redirect(url_for("admin.categories"))


@admin_bp.route("/requests")
def requests_list():
    page = request.args.get("page", 1, type=int)

    query = NoteRequest.query

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

    pagination = query.order_by(
        NoteRequest.created_at.desc()
    ).paginate(
        page=page,
        per_page=PER_PAGE,
        error_out=False
    )

    return render_template(
        "admin/requests.html",
        requests=pagination.items,
        pagination=pagination,
        args=request.args,
    )

@admin_bp.route("/placement")
def placement():
    resources = PlacementResource.query.order_by(
        PlacementResource.created_at.desc()
    ).all()

    return render_template(
        "admin/placement.html",
        resources=resources,
    )


@admin_bp.route("/placement/<int:resource_id>/delete", methods=["POST"])
def delete_resource(resource_id):
    resource = PlacementResource.query.get_or_404(
        resource_id
    )

    if resource.s3_key:
        try:
            delete_file_from_s3(resource.s3_key)
        except Exception as e:
            flash(
                f"S3 delete warning: {e}",
                "warning"
            )

    db.session.delete(resource)
    db.session.commit()

    flash(
        "Resource deleted.",
        "info"
    )

    return redirect(url_for("admin.placement"))


@admin_bp.route("/quizzes")
def quizzes():
    quiz_stats = []

    for quiz in Quiz.query.all():
        quiz_stats.append({
            "quiz": quiz,
            "question_count": QuizQuestion.query.filter_by(
                quiz_id=quiz.id
            ).count(),
            "attempt_count": QuizAttempt.query.filter_by(
                quiz_id=quiz.id
            ).count(),
            "avg_score": db.session.query(
                func.avg(QuizAttempt.score)
            ).filter_by(
                quiz_id=quiz.id
            ).scalar() or 0,
        })

    return render_template(
        "admin/quizzes.html",
        quiz_stats=quiz_stats,
    )


@admin_bp.route("/quizzes/<int:quiz_id>/delete", methods=["POST"])
def delete_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)

    db.session.delete(quiz)
    db.session.commit()

    flash(
        "Quiz bank deleted.",
        "info"
    )

    return redirect(url_for("admin.quizzes"))


@admin_bp.route("/contributors")
def contributors():
    leaders = get_contributor_leaderboard(
        limit=25
    )

    return render_template(
        "admin/contributors.html",
        leaders=leaders,
    )

@admin_bp.route("/backup")
def backup():
    logs = BackupLog.query.order_by(
        BackupLog.created_at.desc()
    ).limit(20).all()

    storage = get_storage_stats()
    db_backups = list_recent_db_backups(limit=10)

    return render_template(
        "admin/backup.html",
        logs=logs,
        storage=storage,
        db_backups=db_backups,
    )




@admin_bp.route("/backup/create", methods=["POST"])
def create_database_backup():
    """Create a database backup from the admin panel."""

    result = run_database_backup()

    if result["success"]:
        flash(
            "Database backup completed successfully.",
            "success"
        )
    else:
        flash(
            "Database backup failed. Check the backup history for details.",
            "danger"
        )

    return redirect(url_for("admin.backup"))

