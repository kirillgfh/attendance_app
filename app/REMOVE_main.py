from datetime import datetime, timedelta
from flask import Flask, render_template, redirect, url_for, flash, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///university.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(50), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def get_role(self):
        return self.role

class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('class.id'), nullable=False)
    attended = db.Column(db.Boolean, default=False)

class Class(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    else:
        return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        print('printuser', user)
        if user and user.check_password(password):
            login_user(user)
            flash('Вы успешно вошли в систему!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Неверное имя пользователя или пароль.', 'danger')

    return render_template('login.html')

@app.route('/dashboard')
@login_required
def dashboard():
    # Получаем сегодняшнюю дату
    today = datetime.now()
    
    # Создаем список из 6 дней, где последний элемент — сегодняшний день
    days = [[(today - timedelta(days=(5 - i))).strftime('%a'), (today - timedelta(days=(5 - i))).strftime('%d')] for i in range(6)]
    print('cockaaaaaaaaaaaaaaaaaa',days)
    if current_user.role not in [ 'moderator', 'admin']:
        flash('Вы не имеете доступа к этой странице.', 'danger')
        return redirect(url_for('logout'))

    students = User.query.filter(User.role == 'student').all()
    print('studentsprint', students[0], (students[0].get_role()))
    classes = Class.query.all()

    return render_template('dashboard.html', students=students, classes=classes, days=days, today_index=len(days) - 1)

@app.route('/mark_attendance', methods=['POST'])
@login_required
def mark_attendance():
    if current_user.role not in [ 'moderator', 'admin']:
        flash('Вы не имеете доступа к этой странице.', 'danger')
        return redirect(url_for('index'))

    for student in User.query.filter(User.role == 'student').all():
        class_id = request.form.get(f'class_{student.id}')
        attended = request.form.get(f'attended_{student.id}') == '1'

        attendance = Attendance(student_id=student.id, class_id=class_id, attended=attended)
        db.session.add(attendance)

    db.session.commit()
    flash('Посещения успешно сохранены!', 'success')
    return redirect(url_for('dashboard'))

# @app.route('/attendance')
# @login_required
# def attendance():
#     if current_user.role not in [ 'moderator', 'admin']:
#         flash('Вы не имеете доступа к этой странице.', 'danger')
#         return redirect(url_for('dashboard'))
#     return render_template('attendance.html')

@app.route('/admin')
@login_required
def admin():
    if current_user.role != 'admin':
        flash('Вы не имеете доступа к этой странице.', 'danger')
        return redirect(url_for('dashboard'))

    # Сбор статистики посещений
    attendance_stats = []
    students = User.query.filter(User.role == 'student').all()
    classes = Class.query.all()

    for student in students:
        for class_ in classes:
            attended_count = Attendance.query.filter_by(
                student_id=student.id,
                class_id=class_.id,
                attended=True
            ).count()

            total_classes = Attendance.query.filter_by(
                student_id=student.id,
                class_id=class_.id
            ).count()

            attendance_percentage = (attended_count / total_classes * 100) if total_classes > 0 else 0

            attendance_stats.append({
                "student": student,
                "class_name": class_.name,
                "attended_count": attended_count,
                "total_classes": total_classes,
                "attendance_percentage": round(attendance_percentage, 2)
            })

    return render_template('admin.html', attendance_stats=attendance_stats)

@app.route('/manage_users')
@login_required
def manage_users():
    if current_user.role != 'admin':
        flash('Вы не имеете доступа к этой странице.', 'danger')
        return redirect(url_for('dashboard'))

    users = User.query.all()
    return render_template('manage_users.html', users=users)

@app.route('/add_user', methods=['POST'])
@login_required
def add_user():
    if current_user.role != 'admin':
        flash('Вы не имеете доступа к этой странице.', 'danger')
        return redirect(url_for('dashboard'))

    username = request.form['username']
    password = request.form['password']
    role = request.form['role']

    if User.query.filter_by(username=username).first():
        flash('Пользователь с таким именем уже существует.', 'danger')
        return redirect(url_for('manage_users'))

    new_user = User(username=username, role=role)
    new_user.set_password(password)
    db.session.add(new_user)
    db.session.commit()

    flash('Пользователь успешно добавлен.', 'success')
    return redirect(url_for('manage_users'))

@app.route('/manage_classes')
@login_required
def manage_classes():
    if current_user.role != 'admin':
        flash('Вы не имеете доступа к этой странице.', 'danger')
        return redirect(url_for('dashboard'))

    classes = Class.query.all()
    return render_template('manage_classes.html', classes=classes)

@app.route('/add_class', methods=['POST'])
@login_required
def add_class():
    if current_user.role != 'admin':
        flash('Вы не имеете доступа к этой странице.', 'danger')
        return redirect(url_for('dashboard'))

    name = request.form['name']

    if Class.query.filter_by(name=name).first():
        flash('Предмет с таким названием уже существует.', 'danger')
        return redirect(url_for('manage_classes'))

    new_class = Class(name=name)
    db.session.add(new_class)
    db.session.commit()

    flash('Предмет успешно добавлен.', 'success')
    return redirect(url_for('manage_classes'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы вышли из системы.', 'success')
    return redirect(url_for('login'))

@app.route('/test_carousel', methods=['GET', 'POST'])
def test_carousel():

    return render_template('test_carousel.html')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        
        if not User.query.filter_by(username='moderator').first():
            moderator_user = User(username='moderator', role='moderator')
            moderator_user.set_password('moderator123')
            db.session.add(moderator_user)

        if not User.query.filter_by(username='1').first():
            moderator_user = User(username='1', role='admin')
            moderator_user.set_password('1')
            db.session.add(moderator_user)
        
        if not User.query.filter_by(username='student1').first():
            student1 = User(username='student1', role='student')
            student1.set_password('student123')
            db.session.add(student1)
        
        if not User.query.filter_by(username='student2').first():
            student2 = User(username='student2', role='student')
            student2.set_password('student123')
            db.session.add(student2)
        
        if not Class.query.first():
            math_class = Class(name='Математика')
            physics_class = Class(name='Физика')
            db.session.add(math_class)
            db.session.add(physics_class)
        
        db.session.commit()
        
    app.run(debug=True)