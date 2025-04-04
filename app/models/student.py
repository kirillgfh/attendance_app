from app import db

# Таблица студентов
class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'), nullable=False)
    attendances = db.relationship('Attendance', backref='student', lazy=True)

