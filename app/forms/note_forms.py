from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import StringField, TextAreaField, IntegerField, SelectField, SubmitField
from wtforms.validators import DataRequired, Length, Optional, NumberRange, EqualTo


class UploadNoteForm(FlaskForm):
    title = StringField(
        "Title",
        validators=[DataRequired(), Length(max=200)]
    )

    description = TextAreaField(
        "Description",
        validators=[Optional(), Length(max=2000)]
    )

    subject = StringField(
        "Subject",
        validators=[DataRequired(), Length(max=100)]
    )

    semester = IntegerField(
        "Semester",
        validators=[
            DataRequired(),
            NumberRange(min=1, max=8)
        ]
    )

    department = StringField(
        "Department",
        validators=[DataRequired(), Length(max=100)]
    )

    faculty = StringField(
        "Faculty",
        validators=[Optional(), Length(max=100)]
    )

    category_id = SelectField("Category", coerce=int, validators=[Optional()])

    keywords = StringField(
        "Keywords (comma separated)",
        validators=[Optional(), Length(max=255)]
    )

    file = FileField(
        "File",
        validators=[
            FileRequired(),
            FileAllowed(
                ["pdf", "ppt", "pptx", "doc", "docx"],
                "Only PDF, PPT/PPTX, DOC/DOCX allowed."
            ),
        ],
    )

    submit = SubmitField("Upload Note")


class EditNoteForm(FlaskForm):
    title = StringField(
        "Title",
        validators=[DataRequired(), Length(max=200)]
    )

    description = TextAreaField(
        "Description",
        validators=[Optional(), Length(max=2000)]
    )

    subject = StringField(
        "Subject",
        validators=[DataRequired(), Length(max=100)]
    )

    semester = IntegerField(
        "Semester",
        validators=[
            DataRequired(),
            NumberRange(min=1, max=8)
        ]
    )

    department = StringField(
        "Department",
        validators=[DataRequired(), Length(max=100)]
    )

    faculty = StringField(
        "Faculty",
        validators=[Optional(), Length(max=100)]
    )

    category_id = SelectField("Category", coerce=int, validators=[Optional()])

    keywords = StringField(
        "Keywords (comma separated)",
        validators=[Optional(), Length(max=255)]
    )

    submit = SubmitField("Save Changes")


