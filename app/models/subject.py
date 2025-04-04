from app import db



class Subject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=True, nullable=False)
    lessons = db.relationship('Lesson', backref='subject', lazy=True)
