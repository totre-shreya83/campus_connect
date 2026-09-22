from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user

from app import db
from app.models.placement_resource import PlacementResource
from app.utils.decorators import admin_required
from app.utils.file_validators import allowed_file, generate_secure_s3_key
from app.services.s3_service import upload_file_to_s3, generate_presigned_download_url

from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, SelectField, SubmitField
from wtforms.validators import DataRequired, Optional, Length


placement_bp = Blueprint(
    "placement",
    __name__,
    url_prefix="/placement"
)


SECTIONS = {
    "APTITUDE": {
        "label": "Aptitude",
        "desc": "Quantitative, Logical Reasoning, Verbal Ability"
    },
    "CODING": {
        "label": "Coding",
        "desc": "Arrays, Strings, Trees, SQL - practice on LeetCode"
    },
    "INTERVIEW": {
        "label": "Interview Questions",
        "desc": "Technical and company-wise questions"
    },
    "HR": {
        "label": "HR Questions",
        "desc": "Common HR round questions"
    },
    "RESUME": {
        "label": "Resume Tips",
        "desc": "Templates, ATS format, checklist"
    },
    "MATERIALS": {
        "label": "Placement Materials",
        "desc": "Previous papers, interview experiences, PDFs"
    },
}


class ResourceForm(FlaskForm):

    section = SelectField(
        "Section",
        choices=[
            (key, value["label"])
            for key, value in SECTIONS.items()
        ],
        validators=[DataRequired()]
    )

    title = StringField(
        "Title",
        validators=[
            DataRequired(),
            Length(max=200)
        ]
    )

    content = TextAreaField(
        "Text Content (optional)",
        validators=[
            Optional(),
            Length(max=5000)
        ]
    )

    external_link = StringField(
        "External Link (optional)",
        validators=[
            Optional(),
            Length(max=500)
        ]
    )

    file = FileField(
        "File (optional)",
        validators=[
            FileAllowed(
                ["pdf", "ppt", "pptx", "doc", "docx"],
                "Invalid file type."
            )
        ]
    )

    submit = SubmitField("Add Resource")


@placement_bp.route("/")
@login_required
def hub():
    return render_template(
        "placement/hub.html",
        sections=SECTIONS
    )


@placement_bp.route("/<section>")
@login_required
def section_view(section):

    section = section.upper()

    if section not in SECTIONS:
        abort(404)

    resources = (
        PlacementResource.query
        .filter_by(section=section)
        .order_by(PlacementResource.created_at.desc())
        .all()
    )

    return render_template(
        "placement/section.html",
        section_key=section,
        section_info=SECTIONS[section],
        resources=resources
    )


@placement_bp.route("/resource/<int:resource_id>")
@login_required
def view_resource(resource_id):

    resource = PlacementResource.query.get_or_404(
        resource_id
    )

    return render_template(
        "placement/view_resource.html",
        resource=resource
    )


@placement_bp.route(
    "/resource/<int:resource_id>/delete",
    methods=["POST"]
)
@login_required
@admin_required
def delete_resource(resource_id):

    resource = PlacementResource.query.get_or_404(
        resource_id
    )

    section = resource.section

    if resource.s3_key:
        from app.services.s3_service import delete_file_from_s3
        delete_file_from_s3(resource.s3_key)

    db.session.delete(resource)
    db.session.commit()

    flash(
        "Resource deleted successfully.",
        "success"
    )

    return redirect(
        url_for(
            "placement.section_view",
            section=section
        )
    )


@placement_bp.route("/resource/<int:resource_id>/download")
@login_required
def download_resource(resource_id):

    resource = PlacementResource.query.get_or_404(
        resource_id
    )

    if not resource.s3_key:
        abort(404)

    url = generate_presigned_download_url(
        resource.s3_key,
        expires_in=300
    )

    if not url:
        flash(
            "Could not generate download link.",
            "danger"
        )

        return redirect(
            url_for(
                "placement.view_resource",
                resource_id=resource.id
            )
        )

    return redirect(url)


@placement_bp.route(
    "/add",
    methods=["GET", "POST"]
)
@login_required
@admin_required
def add_resource():

    form = ResourceForm()

    if form.validate_on_submit():

        s3_key = None

        file = form.file.data

        if file and file.filename:

            if not allowed_file(file.filename):
                flash(
                    "Invalid file type.",
                    "danger"
                )

                return render_template(
                    "placement/add_resource.html",
                    form=form
                )

            s3_key = generate_secure_s3_key(
                "placement",
                file.filename
            )

            upload_file_to_s3(
                file,
                s3_key
            )

        resource = PlacementResource(
            section=form.section.data,
            title=form.title.data.strip(),
            content=form.content.data,
            s3_key=s3_key,
            external_link=(
                form.external_link.data.strip()
                if form.external_link.data
                else None
            ),
            created_by=current_user.id
        )

        db.session.add(resource)
        db.session.commit()

        flash(
            "Resource added.",
            "success"
        )

        return redirect(
            url_for(
                "placement.section_view",
                section=resource.section
            )
        )

    return render_template(
        "placement/add_resource.html",
        form=form
    )

