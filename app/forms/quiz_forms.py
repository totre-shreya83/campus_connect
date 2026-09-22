from flask_wtf import FlaskForm
from wtforms import IntegerField, SubmitField
from wtforms.validators import DataRequired, NumberRange


class StartQuizForm(FlaskForm):
    num_questions = IntegerField(
        "Number of Questions",
        default=10,
        validators=[
            DataRequired(),
            NumberRange(min=5, max=50),
        ],
    )

    submit = SubmitField("Start Mock Test")
