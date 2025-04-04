from app import db
from app.models.attendance import Attendance
from datetime import date

class AttendanceRepository:
    @staticmethod
    def get_by_student_lesson_date(student_id: int, lesson_id: int, date: date) -> Attendance | None:
        return Attendance.query.filter_by(student_id=student_id, lesson_id=lesson_id, date=date).first()

    @staticmethod
    def create(student_id: int, lesson_id: int, date: date, status: bool) -> Attendance:
        attendance = Attendance(student_id=student_id, lesson_id=lesson_id, date=date, status=status)
        db.session.add(attendance)
        db.session.commit()
        return attendance

    @staticmethod
    def update(student_id: int, lesson_id: int, date: date, status: bool) -> Attendance | None:
        attendance = Attendance.query.filter_by(student_id=student_id, lesson_id=lesson_id, date=date).first()
        if attendance:
            attendance.status = status
            db.session.commit()
        return attendance

    @staticmethod
    def get_by_lesson_date(lesson_id: int, date: date) -> list[Attendance]:
        return Attendance.query.filter_by(lesson_id=lesson_id, date=date).all()

    @staticmethod
    def delete_by_student_id(student_id: int) -> None:
        Attendance.query.filter_by(student_id=student_id).delete()
        db.session.commit()