from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Length, Optional


class CategoryForm(FlaskForm):
    name = StringField(
        "Category Name",
        validators=[DataRequired(), Length(max=100)]
    )
    description = StringField(
        "Description",
        validators=[Optional(), Length(max=255)]
    )
    submit = SubmitField("Save Category")


class RejectNoteForm(FlaskForm):
    reason = TextAreaField(
        "Rejection Reason",
        validators=[Optional(), Length(max=500)]
    )
    submit = SubmitField("Reject")
