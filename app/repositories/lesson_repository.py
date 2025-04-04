from app import db
from app.models.lesson import Lesson

class LessonRepository:
    @staticmethod
    def get_by_id(lesson_id: int) -> Lesson | None:
        return db.session.get(Lesson, lesson_id)

    @staticmethod
    def get_by_group_id(group_id: int) -> list[Lesson]:
        return Lesson.query.filter_by(group_id=group_id).all()

    @staticmethod
    def get_by_day_and_type(group_id: int, weekday: int, week_type: str) -> list[Lesson]:
        return Lesson.query.filter_by(group_id=group_id, weekday=weekday, week_type=week_type).all()

    @staticmethod
    def create(subject_id: int, group_id: int, weekday: int, lesson_number: int, week_type: str, lesson_type: str) -> Lesson:
        lesson = Lesson(subject_id=subject_id, group_id=group_id, weekday=weekday, lesson_number=lesson_number, week_type=week_type, lesson_type=lesson_type)
        db.session.add(lesson)
        db.session.commit()
        return lesson

    @staticmethod
    def update(lesson_id: int, subject_id: int, weekday: int, lesson_number: int, week_type: str, lesson_type: str) -> Lesson | None:
        lesson = db.session.get(Lesson, lesson_id)
        if lesson:
            lesson.subject_id = subject_id
            lesson.weekday = weekday
            lesson.lesson_number = lesson_number
            lesson.week_type = week_type
            lesson.lesson_type = lesson_type
            db.session.commit()
        return lesson

    @staticmethod
    def delete(lesson_id: int) -> None:
        lesson = db.session.get(Lesson, lesson_id)
        if lesson:
            db.session.delete(lesson)
            db.session.commit()