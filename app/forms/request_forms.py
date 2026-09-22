from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, IntegerField, SubmitField
from wtforms.validators import DataRequired, Length, Optional, NumberRange


class CreateRequestForm(FlaskForm):
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
        validators=[
            Optional(),
            Length(max=100)
        ]
    )

    description = TextAreaField(
        "Description",
        validators=[
            DataRequired(),
            Length(max=1000)
        ]
    )

    submit = SubmitField("Post Request")


class ReplyRequestForm(FlaskForm):
    message = TextAreaField(
        "Message",
        validators=[
            Optional(),
            Length(max=1000)
        ]
    )

    file = FileField(
        "Attach a file (optional)",
        validators=[
            FileAllowed(
                ["pdf", "ppt", "pptx", "doc", "docx"],
                "Only PDF, PPT/PPTX, DOC/DOCX allowed."
            )
        ]
    )

    submit = SubmitField("Reply")
