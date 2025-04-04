from app import db
from app.models.student import Student

class StudentRepository:
    @staticmethod
    def get_by_id(student_id: int) -> Student | None:
        return db.session.get(Student, student_id)

    @staticmethod
    def get_by_group_id(group_id: int) -> list[Student]:
        return Student.query.filter_by(group_id=group_id).all()

    @staticmethod
    def create(name: str, group_id: int) -> Student:
        student = Student(name=name, group_id=group_id)
        db.session.add(student)
        db.session.commit()
        return student

    @staticmethod
    def delete(student_id: int) -> None:
        student = db.session.get(Student, student_id)
        if student:
            db.session.delete(student)
            db.session.commit()