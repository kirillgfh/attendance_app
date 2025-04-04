from app import db
from app.models.attendance import Attendance


class Group(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    moderator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    students = db.relationship('Student', backref='group', lazy=True)
    lessons = db.relationship('Lesson', backref='group', lazy=True)


    def __repr__(self):
            return f'<Group {self.name}>'


    @property
    def attendance_percentage(self):
        total_attended = 0
        total_classes = 0

        for student in self.students:
            for lesson in self.lessons:
                attended_count = Attendance.query.filter_by(
                    student_id=student.id,
                    lesson_id=lesson.id,
                    status=True
                ).count()

                total_lessons = Attendance.query.filter_by(
                    student_id=student.id,
                    lesson_id=lesson.id
                ).count()

                total_attended += attended_count
                total_classes += total_lessons

        if total_classes == 0:
            return 0  # Если нет занятий, возвращаем 0

        return round((total_attended / total_classes) * 100, 2)

