from app import db



class Lesson(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'), nullable=False)
    weekday = db.Column(db.Integer, nullable=False)  # 1 - Пн, 7 - Вс
    lesson_number = db.Column(db.Integer, nullable=False)  # Номер пары
    week_type = db.Column(db.String(100), nullable=False)  # Тип недели (числитель 1,2 /знаменатель) ч1 ч2 з1 з2
    lesson_type = db.Column(db.String(100), nullable=False)  # Тип недели (числитель 1,2 /знаменатель) [Пр] [Лек] [Лаб]
    attendances = db.relationship('Attendance', backref='lesson', lazy=True)
