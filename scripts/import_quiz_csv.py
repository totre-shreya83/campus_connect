import os
import sys
import csv

sys.path.insert(
    0,
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )
)

from app import create_app, db
from app.models.quiz import Quiz, QuizQuestion, QuizOption


def import_quiz_csv(csv_path):
    app = create_app()

    with app.app_context():
        with open(
            csv_path,
            "r",
            encoding="utf-8-sig",
            newline=""
        ) as file:

            reader = csv.DictReader(
                file,
                delimiter=";"
            )

            quiz = Quiz.query.filter_by(
                title="Placement Mock Test"
            ).first()

            if not quiz:
                quiz = Quiz(
                    title="Placement Mock Test",
                    description="General Aptitude Mock Test for placement preparation."
                )

                db.session.add(quiz)
                db.session.flush()

            imported = 0
            skipped = 0

            for row in reader:

                question_text = (
                    row.get("Question", "") or ""
                ).strip()

                correct = (
                    row.get("Answer", "") or ""
                ).strip().upper()

                if not question_text:
                    skipped += 1
                    continue

                if correct not in {"A", "B", "C", "D"}:
                    skipped += 1
                    continue

                options = [
                    ("A", row.get("Option A", "")),
                    ("B", row.get("Option B", "")),
                    ("C", row.get("Option C", "")),
                    ("D", row.get("Option D", "")),
                ]

                if any(
                    not (option_text or "").strip()
                    for _, option_text in options
                ):
                    skipped += 1
                    continue

                question = QuizQuestion(
                    quiz_id=quiz.id,
                    question_text=question_text,
                    marks=1
                )

                db.session.add(question)
                db.session.flush()

                for letter, option_text in options:

                    option = QuizOption(
                        question_id=question.id,
                        option_text=option_text.strip(),
                        is_correct=(letter == correct)
                    )

                    db.session.add(option)

                imported += 1

            db.session.commit()

            print()
            print("Quiz import completed successfully.")
            print(f"Questions imported: {imported}")
            print(f"Rows skipped: {skipped}")
            print(f"Quiz: {quiz.title}")


if __name__ == "__main__":

    if len(sys.argv) != 2:
        print(
            "Usage: python scripts/import_quiz_csv.py <csv_file>"
        )
        sys.exit(1)

    import_quiz_csv(sys.argv[1])
