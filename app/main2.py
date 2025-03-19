import os
from datetime import datetime, timedelta
from pprint import pprint
from flask import Flask, jsonify, render_template, redirect, url_for, flash, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import secrets  # Для генерации случайного пароля
import locale
# from empty_attendances_script import create_empty_attendances
from utils.get_schedule import get_lessons_for_group, get_subjects
from utils.get_week_type import get_week_type
from flask_caching import Cache
import re

from sqlalchemy.orm import joinedload
from utils.check_access import role_required
from flask_apscheduler import APScheduler
from apscheduler.triggers.cron import CronTrigger

# Устанавливаем русскую локаль для корректного отображения дней недели
locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')

# Инициализация Flask-приложения
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'

# Указываем путь к базе данных
basedir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))  # Переход на уровень выше
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(basedir, "instance", "university.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
# migrate = Migrate(app, db)

# Настройка кэширования
cache = Cache(config={'CACHE_TYPE': 'SimpleCache'})  # Используем простой in-memory кэш
cache.init_app(app)


# Инициализация планировщика
scheduler = APScheduler()
scheduler.init_app(app)
# scheduler.start()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(50), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password, method="pbkdf2:sha256")

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# Новая таблица групп
class Group(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    moderator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    students = db.relationship('Student', backref='group', lazy=True)
    lessons = db.relationship('Lesson', backref='group', lazy=True)

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

# Таблица студентов
class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'), nullable=False)
    attendances = db.relationship('Attendance', backref='student', lazy=True)

# Таблица предметов
class Subject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=True, nullable=False)
    lessons = db.relationship('Lesson', backref='subject', lazy=True)

# Таблица уроков
class Lesson(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'), nullable=False)
    weekday = db.Column(db.Integer, nullable=False)  # 1 - Пн, 7 - Вс
    lesson_number = db.Column(db.Integer, nullable=False)  # Номер пары
    week_type = db.Column(db.String(100), nullable=False)  # Тип недели (числитель 1,2 /знаменатель) ч1 ч2 з1 з2
    lesson_type = db.Column(db.String(100), nullable=False)  # Тип недели (числитель 1,2 /знаменатель) [Пр] [Лек] [Лаб]
    attendances = db.relationship('Attendance', backref='lesson', lazy=True)

# Таблица посещаемости
class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    lesson_id = db.Column(db.Integer, db.ForeignKey('lesson.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    status = db.Column(db.Boolean, default=True, nullable=False)  # По умолчанию True (присутствовал)



def create_empty_attendances():
    with app.app_context():
        # Получаем текущую дату
        today = datetime.now().date()
        
        # Получаем тип недели для текущей даты
        week_type = get_week_type(today)
        
        # Если тип недели не определен (например, каникулы), пропускаем
        if not week_type:
            print("Тип недели не определен. Сегодня, вероятно, каникулы.")
            return

        # Получаем все группы
        groups = Group.query.all()

        for group in groups:
            # Получаем все уроки для группы на текущий день и тип недели
            lessons = Lesson.query.filter(
                Lesson.group_id == group.id,
                Lesson.weekday == today.weekday() + 1,  # weekday в базе: 1 - Пн, 7 - Вс
                Lesson.week_type == week_type
            ).all()

            if not lessons: 
                continue 

            # Получаем всех студентов группы
            students = Student.query.filter_by(group_id=group.id).all()

            for student in students:
                for lesson in lessons:
                    # Проверяем, существует ли уже запись о посещении для этого студента, урока и даты
                    existing_attendance = Attendance.query.filter_by(
                        student_id=student.id,
                        lesson_id=lesson.id,
                        date=today
                    ).first()

                    # Если запись не существует, создаем новую
                    if not existing_attendance:
                        print('yes')
                        new_attendance = Attendance(
                            student_id=student.id,
                            lesson_id=lesson.id,
                            date=today,
                            status=False  # По умолчанию отсутствует
                        )
                        db.session.add(new_attendance)

        db.session.commit()
        print(f"Пустые посещения созданы для {today}.")

def parse_schedule(text, week_type, group_id):
    with app.app_context():
        days_mapping = {
            "понедельник": 1,
            "вторник": 2,
            "среду": 3,
            "четверг": 4,
            "пятницу": 5,
            "субботу": 6,
            "воскресенье": 7,
        }
        
        # Заменяем "Во вторник" на "В вторник"
        text = text.replace('Во вторник', 'В вторник')
        
        current_weekday = None
        subjects_set = set()
        lessons_list = []
        
        for line in text.split('\n'):
            line = line.strip()
            
            if not line or "военка" in line.lower():
                continue
            
            # Определяем день недели
            day_match = re.match(r'В\s(понедельник|вторник|среду|четверг|пятницу|субботу|воскресенье)', line, re.IGNORECASE)
            if day_match:
                current_weekday = days_mapping[day_match.group(1).lower()]
                continue
            
            # Парсим строку с парой
            lesson_match = re.match(r'(\d+)\.\s[^ ]+\s[А-Яа-яЁё\s]+\s[А-ЯЁа-я\.]+\s(.+?)(?:\s\[(.+)\])?$', line)
            if lesson_match:
                lesson_number = int(lesson_match.group(1))
                subject_name = lesson_match.group(2).strip()
                lesson_type = lesson_match.group(3) if lesson_match.group(3) else "Пр"  # Если тип занятия отсутствует, ставим "Пр"
                subjects_set.add(subject_name)
                lessons_list.append((subject_name, current_weekday, lesson_number, week_type, lesson_type))
        
        # Удаляем все существующие уроки для данной группы и типа недели
        Lesson.query.filter_by(group_id=group_id, week_type=week_type).delete()
        
        # Добавляем предметы в базу, если их нет
        existing_subjects = {s.name for s in Subject.query.all()}
        for subject_name in subjects_set:
            if subject_name not in existing_subjects:
                db.session.add(Subject(name=subject_name))
        db.session.commit()
        
        # Добавляем уроки
        subjects_dict = {s.name: s.id for s in Subject.query.all()}
        for subject_name, weekday, lesson_number, week_type, lesson_type in lessons_list:
            lesson = Lesson(
                subject_id=subjects_dict[subject_name],
                weekday=weekday,
                lesson_number=lesson_number,
                week_type=week_type,
                lesson_type=lesson_type,
                group_id=group_id
            )
            db.session.add(lesson)
        
        db.session.commit()


def commit_subjects(subjects):
    existing_subjects = {s.name for s in Subject.query.all()}
    for subject_name in subjects:
        if subject_name not in existing_subjects:
            db.session.add(Subject(name=subject_name))
    db.session.commit()

def commit_lessons(lessons):
    subjects_dict = {s.name: s.id for s in Subject.query.all()}
    group_dict = {s.name: s.id for s in Group.query.all()}
    for subject_name, weekday, lesson_number, week_type, lesson_type, group_name in lessons:
        lesson = Lesson(
            subject_id=subjects_dict[subject_name],
            weekday=weekday,
            lesson_number=lesson_number,
            week_type=week_type,
            lesson_type=lesson_type,
            group_id=group_dict[group_name]
        )
        db.session.add(lesson)
    db.session.commit()

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))  # Используем Session.get() вместо Query.get()

@app.route('/')
def index():
    if current_user.is_authenticated:
            if current_user.role in ['moderator']:
                return redirect(url_for('dashboard'))
            elif current_user.role in ['admin']:
                return redirect(url_for('admin'))
    else:
        return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        print(user)

        if user and user.check_password(password):
            login_user(user)
            flash('Вы успешно вошли в систему!', 'success')
            if current_user.role in ['moderator']:
                return redirect(url_for('dashboard'))
            elif current_user.role in ['admin']:
                return redirect(url_for('admin'))
        else:
            flash('Неверное имя пользователя или пароль.', 'danger')
            
    return render_template('login.html')

@app.route('/dashboard')
@login_required
@role_required(['moderator'])
def dashboard():
    if current_user.role == 'admin':
        return redirect(url_for('admin'))  

    # Получаем группу, связанную с текущим модератором
    group = Group.query.filter_by(moderator_id=current_user.id).first()
    if not group:
        flash('Группа не найдена.', 'danger')
        return redirect(url_for('index'))

    # Получаем выбранную дату из параметра запроса (если есть)
    selected_date_str = request.args.get('selected_date')
    if selected_date_str:
        selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
    else:
        selected_date = datetime.now().date()  # По умолчанию — сегодняшняя дата

    # Определяем тип недели
    week_type = get_week_type(selected_date)

    # Если тип недели не определен (дата раньше начала семестра), показываем сообщение
    if week_type is None:
        flash('Семестр еще не начался.', 'info')
        return redirect(url_for('index'))

    # Создаем список из 7 дней, где последний элемент — выбранный день
    days = [
        [(selected_date - timedelta(days=(6 - i))).strftime('%a'),  # День недели (Пн, Вт и т.д.)
         (selected_date - timedelta(days=(6 - i))).strftime('%d')]  # Число месяца
        for i in range(7)
    ]

    # Получаем студентов и занятия только для группы модератора
    students = Student.query.filter_by(group_id=group.id).all()
    lessons = Lesson.query.filter_by(group_id=group.id).all()

    # Передаем selected_date, week_type и timedelta в шаблон
    return render_template(
        'dashboard.html',
        students=students,
        lessons=lessons,
        days=days,
        today_index=6,  # Индекс выбранного дня (последний элемент в списке)
        today=selected_date,  # Передаем выбранную дату в шаблон
        week_type=week_type,  # Передаем тип недели в шаблон
        timedelta=timedelta  # Передаем timedelta в шаблон
    )

@app.route('/get_lessons_for_day', methods=['GET'])
@login_required
def get_lessons_for_day():
    # Получаем группу, связанную с текущим модератором
    group = Group.query.filter_by(moderator_id=current_user.id).first()
    if not group:
        return jsonify({"error": "Группа не найдена"}), 404

    # Получаем выбранную дату из запроса
    selected_date_str = request.args.get('date')
    if not selected_date_str:
        return jsonify({"error": "Дата не указана"}), 400

    # Преобразуем строку в объект datetime
    selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()

    # Определяем тип недели для выбранной даты
    week_type = get_week_type(selected_date)

    # Фильтруем уроки по дню недели, типу недели и группе модератора
    lessons = Lesson.query.filter(
        Lesson.weekday == selected_date.weekday() + 1,  # weekday в базе данных: 1 - Пн, 7 - Вс
        Lesson.week_type == week_type,
        Lesson.group_id == group.id  # Фильтруем по группе модератора
    ).all()

    # Формируем список уроков для ответа
    lessons_data = [
        {
            "id": lesson.id,  # Добавляем ID урока
            "subject_name": lesson.subject.name,
            "lesson_type": lesson.lesson_type,
            "lesson_number": lesson.lesson_number
        }
        for lesson in lessons
    ]

    return jsonify({
        "lessons": lessons_data,
        "week_type": week_type
    })





@app.route('/mark_attendance', methods=['POST'])
@login_required
@role_required(['admin', 'moderator'])
def mark_attendance():
    selected_date_str = request.form.get('selected_date')  # Получаем дату из формы
    if not selected_date_str:
        flash('Дата не выбрана.', 'danger')
        return redirect(url_for('dashboard'))

    selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()

    # Получаем группу, связанную с текущим пользователем (модератором)
    group = Group.query.filter_by(moderator_id=current_user.id).first()
    if not group:
        flash('Группа не найдена.', 'danger')
        return redirect(url_for('dashboard'))

    # Фильтруем студентов по группе, связанной с текущим пользователем
    for student in Student.query.filter_by(group_id=group.id).all():
        lesson_id = request.form.get(f'lesson_{student.id}')
        status = request.form.get(f'status_{student.id}') == '1'

        # Проверяем, что lesson_id не равен None
        if not lesson_id:
            flash(f'Не указан ID урока для студента {student.name}.', 'danger')
            continue  # Пропускаем этого студента

        # Проверяем, существует ли уже запись для данного студента, урока и даты
        attendance = Attendance.query.filter_by(
            student_id=student.id,
            lesson_id=lesson_id,
            date=selected_date
        ).first()

        if attendance:
            # Если запись существует, обновляем её статус
            attendance.status = status
        else:
            # Если записи нет, создаем новую
            attendance = Attendance(
                student_id=student.id,
                lesson_id=lesson_id,  # Убедимся, что lesson_id не None
                date=selected_date,
                status=status
            )
            db.session.add(attendance)

    db.session.commit()
    flash('Посещения успешно сохранены!', 'success')
    return redirect(url_for('dashboard'))


@app.route('/admin')
@login_required
@role_required(['admin'])
def admin():
    # Получаем список всех групп с рассчитанной посещаемостью
    groups_data = cache.get('groups_data')
    if not groups_data:
        groups = Group.query.all()
        groups_data = []
        for group in groups:
            # Рассчитываем общую посещаемость для каждой группы
            total_attended = 0
            total_classes = 0

            for lesson in group.lessons:
                attended_count = Attendance.query.filter_by(
                    lesson_id=lesson.id,
                    status=True
                ).count()

                total_lessons = Attendance.query.filter_by(
                    lesson_id=lesson.id
                ).count()

                total_attended += attended_count
                total_classes += total_lessons

            attendance_percentage = (total_attended / total_classes * 100) if total_classes > 0 else 0

            groups_data.append({
                'id': group.id,
                'name': group.name,
                'attendance_percentage': round(attendance_percentage, 2)  # Добавляем посещаемость
            })
        cache.set('groups_data', groups_data, timeout=300)  # Кэшируем на 5 минут

    # Остальной код остается без изменений
    group_id = request.args.get('group_id')
    selected_group_data = None
    attendance_stats = []
    subject_stats = []
    view_mode = request.args.get('view_mode', 'students')
    
    if group_id:
        selected_group_data = cache.get(f'selected_group_data_{group_id}')
        if not selected_group_data:
            selected_group = Group.query.get_or_404(group_id)
            selected_group_data = {
                'id': selected_group.id,
                'name': selected_group.name,
                'students': [{'id': student.id, 'name': student.name} for student in selected_group.students],
                'lessons': [{
                    'id': lesson.id,
                    'subject_id': lesson.subject_id,
                    'subject_name': lesson.subject.name,
                    'weekday': lesson.weekday,
                    'lesson_number': lesson.lesson_number,
                    'week_type': lesson.week_type,
                    'lesson_type': lesson.lesson_type
                } for lesson in selected_group.lessons]
            }
            cache.set(f'selected_group_data_{group_id}', selected_group_data, timeout=300)

        if view_mode == 'students':
            attendance_stats = cache.get(f'attendance_stats_{group_id}')
            if not attendance_stats:
                attendance_stats = []
                for student in selected_group_data['students']:
                    total_attended = 0
                    total_classes = 0

                    for lesson in selected_group_data['lessons']:
                        attended_count = Attendance.query.filter_by(
                            student_id=student['id'],
                            lesson_id=lesson['id'],
                            status=True
                        ).count()

                        total_lessons = Attendance.query.filter_by(
                            student_id=student['id'],
                            lesson_id=lesson['id']
                        ).count()

                        total_attended += attended_count
                        total_classes += total_lessons

                    attendance_percentage = (total_attended / total_classes * 100) if total_classes > 0 else 0

                    attendance_stats.append({
                        "student_id": student['id'],
                        "student_name": student['name'],
                        "attendance_percentage": round(attendance_percentage, 2)
                    })
                cache.set(f'attendance_stats_{group_id}', attendance_stats, timeout=300)

        elif view_mode == 'subjects':
            subject_stats = cache.get(f'subject_stats_{group_id}')
            if not subject_stats:
                subject_stats = []
                subject_dict = {}  # Словарь для хранения данных по каждому предмету

                for lesson in selected_group_data['lessons']:
                    subject_id = lesson['subject_id']
                    subject_name = lesson['subject_name']

                    # Если предмет еще не добавлен в словарь, добавляем его
                    if subject_id not in subject_dict:
                        subject_dict[subject_id] = {
                            "subject_id": subject_id,
                            "subject_name": subject_name,
                            "total_attended": 0,
                            "total_classes": 0
                        }

                    # Считаем посещаемость для текущего занятия
                    attended_count = Attendance.query.filter_by(
                        lesson_id=lesson['id'],
                        status=True
                    ).count()

                    total_lessons = Attendance.query.filter_by(
                        lesson_id=lesson['id']
                    ).count()

                    # Обновляем общее количество посещений и занятий для предмета
                    subject_dict[subject_id]['total_attended'] += attended_count
                    subject_dict[subject_id]['total_classes'] += total_lessons

                # Преобразуем словарь в список и рассчитываем процент посещаемости
                for subject_id, data in subject_dict.items():
                    total_attended = data['total_attended']
                    total_classes = data['total_classes']
                    attendance_percentage = (total_attended / total_classes * 100) if total_classes > 0 else 0

                    subject_stats.append({
                        "subject_id": subject_id,
                        "subject_name": data['subject_name'],
                        "attendance_percentage": round(attendance_percentage, 2)
                    })

                # Кэшируем результат
                cache.set(f'subject_stats_{group_id}', subject_stats, timeout=300)
    # pprint(subject_stats)
    return render_template(
        'admin.html',
        groups=groups_data,
        selected_group=selected_group_data,
        attendance_stats=attendance_stats,
        subject_stats=subject_stats,
        view_mode=view_mode
    )

@app.route('/edit_group_schedule/<int:group_id>', methods=['GET', 'POST'])
@login_required
@role_required(['admin'])
def edit_group_schedule(group_id):
    group = Group.query.get_or_404(group_id)
    lessons = Lesson.query.filter_by(group_id=group.id).all()

    if request.method == 'POST':
        # Обработка добавления нового расписания
        group_name = group.name

        if group_name:
            try:
                # Получаем расписание для группы
                raw_schedule = get_lessons_for_group(group_name)
                subjects = get_subjects(raw_schedule)
                lessons = get_lessons_for_group(group_name)

                # Удаляем все существующие уроки для данной группы и типа недели
                Lesson.query.filter_by(group_id=group_id).delete()

                # Добавляем предметы в базу, если их нет
                commit_subjects(subjects)

                # Добавляем уроки
                commit_lessons(lessons)

                flash('Расписание успешно добавлено.', 'success')
            except Exception as e:
                flash(f'Ошибка при добавлении расписания: {str(e)}', 'danger')

            return redirect(url_for('edit_group_schedule', group_id=group.id))

        # Обработка удаления урока
        delete_lesson_id = request.form.get('delete_lesson_id')
        if delete_lesson_id:
            lesson_to_delete = Lesson.query.get(delete_lesson_id)
            if lesson_to_delete:
                db.session.delete(lesson_to_delete)
                db.session.commit()
                flash('Урок успешно удален.', 'success')

                # Перезагружаем объект `group`, чтобы он не был "отсоединён"
                group = Group.query.get_or_404(group_id)

                return redirect(url_for('edit_group_schedule', group_id=group.id))

    # Получаем список всех предметов для выпадающего списка (если нужно)
    subjects = Subject.query.all()

    return render_template('edit_group_schedule.html', group=group, lessons=lessons, subjects=subjects)

@app.route('/manage_users')
@login_required
@role_required(['admin'])
def manage_users():
    # Получаем всех пользователей с информацией о группе (если есть)
    users = db.session.query(
        User,
        Group.name.label('group_name')  # Добавляем название группы
    ).outerjoin(  # Используем outerjoin, чтобы включить пользователей без группы
        Group, User.id == Group.moderator_id
    ).order_by(
        # User.role.desc()  ,  # Сначала админы, затем остальные
        User.username       # Сортировка по имени пользователя
    ).all()
    print(users)
    return render_template('manage_users.html', users=users)


@app.route('/update_user_credentials/<int:user_id>', methods=['POST'])
@login_required
@role_required(['admin'])
def update_user_credentials(user_id):
    user = User.query.get_or_404(user_id)

    
    # Генерация нового логина и пароля
    new_password = secrets.token_hex(8)  # Пример: 1a2b3c4d5e6f7g8h
    
    # Обновление данных пользователя
    user.set_password(new_password)
    db.session.commit()
    
    # Возвращаем новые данные для отображения
    return jsonify({
        "success": True,
        "username": user.username,
        "password": new_password
    })


@app.route('/add_group', methods=['GET', 'POST'])
@login_required
@role_required(['admin'])
def add_group():
    if request.method == 'POST':
        group_name = request.form['group_name']

        # Проверяем, существует ли группа с таким именем
        if Group.query.filter_by(name=group_name).first():
            flash('Группа с таким названием уже существует.', 'danger')
            return redirect(url_for('add_group'))

        # Генерируем username и пароль для старосты
        username = f"moderator_{group_name.lower()}"  # Пример: moderator_ivt_23
        password = secrets.token_hex(8)  # Генерация случайного пароля

        # Создаем нового пользователя (старосту)
        moderator = User(username=username, role='moderator')
        moderator.set_password(password)
        db.session.add(moderator)
        db.session.commit()

        # Создаем новую группу
        new_group = Group(name=group_name, moderator_id=moderator.id)
        db.session.add(new_group)
        db.session.commit()
        cache.delete('groups_data')  # Удаляем кэш данных о группах при создании новой группы.

        try:
            if group_name:
                # Получаем расписание для группы
                subjects = get_subjects(group_name)
                lessons = get_lessons_for_group(group_name)

                # Добавляем предметы в базу, если их нет
                commit_subjects(subjects)

                # Добавляем уроки
                commit_lessons(lessons)

                flash('Расписание успешно добавлено.', 'success')
        except Exception as e:
            # Если произошла ошибка, откатываем транзакцию и удаляем группу и модератора
            db.session.rollback()  # Откат транзакции
            db.session.delete(new_group)  # Удаляем группу
            db.session.delete(moderator)  # Удаляем модератора
            db.session.commit()  # Сохраняем изменения

            # Выводим сообщение об ошибке
            flash(f'Ошибка при добавлении расписания: {str(e)}', 'danger')
            flash('Группа не была создана из-за ошибки.', 'danger')
            return redirect(url_for('add_group'))

        return render_template(
            'add_group.html',
            moderators=User.query.filter_by(role='moderator').all(),
            created_group=group_name,
            created_username=username,
            created_password=password
        )

    # GET-запрос: отображаем форму
    return render_template(
        'add_group.html',
        moderators=User.query.filter_by(role='moderator').all(),
        created_group=None,
        created_username=None,
        created_password=None
    )


@app.route('/delete_user/<int:user_id>', methods=['POST'])
@login_required
@role_required(['admin'])
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()

    flash('Пользователь успешно удален.', 'success')
    return redirect(url_for('manage_users'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы вышли из системы.', 'success')
    return redirect(url_for('login'))

@app.route('/test_carousel', methods=['GET', 'POST'])
def test_carousel():
    return render_template('test_carousel.html')


@app.route('/students_attendance_list/<int:lesson_id>')
@login_required
def students_attendance_list(lesson_id):
    lesson = Lesson.query.get_or_404(lesson_id)
    students = Student.query.filter_by(group_id=lesson.group_id).all()
    selected_date_str = request.args.get('selected_date')  # Получаем selected_date из URL

    if not selected_date_str:
        flash('Дата не выбрана.', 'danger')
        return redirect(url_for('dashboard'))

    selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()

    # Собираем данные о посещаемости для каждого студента
    attendance_data = []
    for student in students:
        # Ищем запись о посещаемости для данного студента, урока и даты
        attendance = Attendance.query.filter_by(
            student_id=student.id,
            lesson_id=lesson.id,
            date=selected_date
        ).first()

        # Если запись найдена, берем её статус, иначе ставим False
        status = attendance.status if attendance else False
        attendance_data.append({
            "student_id": student.id,
            "status": status
        })

    return render_template(
        'students_attendance_list.html',
        lesson=lesson,
        students=students,
        attendance_data=attendance_data,  # Передаем данные о посещаемости
        selected_date=selected_date_str  # Передаем selected_date в шаблон
    )

@app.route('/propagate_attendance', methods=['POST'])
@login_required
def propagate_attendance():
    if current_user.role not in ['moderator', 'admin']:
        return jsonify({"success": False, "error": "Доступ запрещен"}), 403

    # Получаем данные из запроса
    data = request.get_json()
    selected_students = data.get('students', [])  # Список выбранных студентов (status_{{ student.id }})
    lesson_id = request.args.get('lesson_id')
    selected_date_str = request.args.get('selected_date')

    if not lesson_id or not selected_date_str:
        return jsonify({"success": False, "error": "Не указан ID урока или дата"}), 400

    selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
    lesson = Lesson.query.get_or_404(lesson_id)

    try:
        # Получаем все пары ниже текущей (по номеру пары)
        lessons_below = Lesson.query.filter(
            Lesson.group_id == lesson.group_id,
            Lesson.weekday == lesson.weekday,
            Lesson.lesson_number >= lesson.lesson_number,
            Lesson.week_type == lesson.week_type
        ).all()

        # Для каждого выбранного студента обновляем посещаемость на всех парах ниже
        for student_status in selected_students:
            student_id = int(student_status.replace('status_', ''))  # Извлекаем ID студента

            for lesson_below in lessons_below:
                # Проверяем, существует ли уже запись
                attendance = Attendance.query.filter_by(
                    student_id=student_id,
                    lesson_id=lesson_below.id,
                    date=selected_date
                ).first()

                if attendance:
                    # Если запись существует, обновляем её статус
                    attendance.status = True  # Устанавливаем присутствие
                else:
                    # Если записи нет, создаем новую
                    attendance = Attendance(
                        student_id=student_id,
                        lesson_id=lesson_below.id,
                        date=selected_date,
                        status=True  # Устанавливаем присутствие
                    )
                    db.session.add(attendance)

        db.session.commit()
        return jsonify({"success": True})

    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500



@app.route('/edit_group_members', methods=['GET', 'POST'])
@login_required
@role_required(['moderator'])
def edit_group_members():
    # Получаем группу, связанную с текущим модератором
    group = Group.query.filter_by(moderator_id=current_user.id).first()
    if not group:
        flash('Группа не найдена.', 'danger')
        return redirect(url_for('dashboard'))

    students = Student.query.filter_by(group_id=group.id).all()

    if request.method == 'POST':
        new_student_name = request.form.get('new_student_name')
        if new_student_name:
            new_student = Student(name=new_student_name, group_id=group.id)
            db.session.add(new_student)
            db.session.commit()

            # Очищаем кэш для студентов и статистики
            cache.delete(f'students_{group.id}')
            cache.delete(f'attendance_stats_{group.id}')
            cache.delete(f'subject_stats_{group.id}')

            flash(f'Студент {new_student_name} успешно добавлен.', 'success')
            return redirect(url_for('edit_group_members'))

        delete_student_id = request.form.get('delete_student_id')
        if delete_student_id:
            student_to_delete = Student.query.get(delete_student_id)
            if student_to_delete:
                # Удаляем связанные записи в attendance
                Attendance.query.filter_by(student_id=student_to_delete.id).delete()
                db.session.delete(student_to_delete)
                db.session.commit()

                # Очищаем кэш для студентов и статистики
                cache.delete(f'students_{group.id}')
                cache.delete(f'attendance_stats_{group.id}')
                cache.delete(f'subject_stats_{group.id}')

                flash(f'Студент {student_to_delete.name} успешно удален.', 'success')
                return redirect(url_for('edit_group_members'))

    return render_template('edit_group_members.html', students=students, group=group)

@app.route('/student_statistics/<int:student_id>')
@login_required
@role_required(['admin'])
def student_statistics(student_id):
    student = Student.query.get_or_404(student_id)
    attendances = Attendance.query.filter_by(student_id=student.id).all()

    # Словарь для хранения статистики по предметам
    subject_stats_dict = {}
    # Словарь для хранения статистики по типам занятий
    lesson_type_stats = {
        "Лек": {"attended": 0, "total": 0},
        "Пр": {"attended": 0, "total": 0},
        "Лаб": {"attended": 0, "total": 0},
    }
    # Словарь для хранения статистики по типам занятий для каждого предмета
    subject_lesson_type_stats = {}

    for attendance in attendances:
        lesson = Lesson.query.get(attendance.lesson_id)
        subject = Subject.query.get(lesson.subject_id)

        # Если предмет еще не добавлен в словарь, добавляем его
        if subject.name not in subject_stats_dict:
            subject_stats_dict[subject.name] = {
                "subject_name": subject.name,
                "attended_count": 0,
                "total_classes": 0,
                "attendance_percentage": 0
            }

        # Обновляем статистику по предмету
        subject_stats_dict[subject.name]["attended_count"] += 1 if attendance.status else 0
        subject_stats_dict[subject.name]["total_classes"] += 1

        # Обновляем статистику по типам занятий
        if lesson.lesson_type in lesson_type_stats:
            lesson_type_stats[lesson.lesson_type]["attended"] += 1 if attendance.status else 0
            lesson_type_stats[lesson.lesson_type]["total"] += 1

        # Обновляем статистику по типам занятий для каждого предмета
        if subject.name not in subject_lesson_type_stats:
            subject_lesson_type_stats[subject.name] = {
                "Лек": {"attended": 0, "total": 0},
                "Пр": {"attended": 0, "total": 0},
                "Лаб": {"attended": 0, "total": 0},
            }

        if lesson.lesson_type in subject_lesson_type_stats[subject.name]:
            subject_lesson_type_stats[subject.name][lesson.lesson_type]["attended"] += 1 if attendance.status else 0
            subject_lesson_type_stats[subject.name][lesson.lesson_type]["total"] += 1

    # Рассчитываем процент посещаемости для каждого предмета
    attendance_stats = []
    for subject_name, stats in subject_stats_dict.items():
        attendance_percentage = (stats["attended_count"] / stats["total_classes"] * 100) if stats["total_classes"] > 0 else 0
        attendance_stats.append({
            "subject_name": subject_name,
            "attended_count": stats["attended_count"],
            "total_classes": stats["total_classes"],
            "attendance_percentage": round(attendance_percentage, 2)
        })

    # Рассчитываем процент посещаемости для каждого типа занятий
    for lesson_type, stats in lesson_type_stats.items():
        if stats["total"] > 0:
            stats["percentage"] = round((stats["attended"] / stats["total"]) * 100, 2)
        else:
            stats["percentage"] = 0

    # Рассчитываем процент посещаемости для каждого типа занятий по предметам
    for subject_name, stats in subject_lesson_type_stats.items():
        for lesson_type, data in stats.items():
            if data["total"] > 0:
                data["percentage"] = round((data["attended"] / data["total"]) * 100, 2)
            else:
                data["percentage"] = 0

    return render_template(
        'student_statistics.html',
        student=student,
        attendance_stats=attendance_stats,
        lesson_type_stats=lesson_type_stats,
        subject_lesson_type_stats=subject_lesson_type_stats
    )


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # print(db.metadata.tables.keys())
        
        if not User.query.filter_by(username='moderator').first():
            moderator_user = User(username='moderator', role='moderator')
            moderator_user.set_password('moderator123')
            db.session.add(moderator_user)

        if not User.query.filter_by(username='1').first():
            moderator_user = User(username='1', role='admin')
            moderator_user.set_password('1')
            db.session.add(moderator_user)
        
        # if not User.query.filter_by(username='student1').first():
        #     student1 = User(username='student1', role='student')
        #     student1.set_password('student123')
        #     db.session.add(student1)
        if not Group.query.filter_by(name='IVT_13').first():
            groupIVT_13 = Group(name='IVT_13', moderator_id=1)
            db.session.add(groupIVT_13)

        if not Student.query.filter_by(name='kirill khabulinov').first():
            student2 = Student(
                name='kirill khabulinov',
                group_id=Group.query.filter(Group.name == "IVT_13").first().id)
            db.session.add(student2)


        if not Subject.query.first():
            math_class = Subject(name='Математика')
            physics_class = Subject(name='Физика')
            db.session.add(math_class)
            db.session.add(physics_class)
            db.session.commit()  # Сохраняем изменения в базе данных

        # Проверяем, есть ли уже записи в таблице Lesson
        if not Lesson.query.first():
            math_class = Subject.query.filter_by(name='Математика').first()
            physics_class = Subject.query.filter_by(name='Физика').first()
            group = Group.query.filter_by(name='IVT_13').first()

            if math_class and physics_class and group:
                math_class_10_10_10 = Lesson(
                    subject_id=math_class.id, 
                    group_id=group.id,
                    weekday=1,
                    lesson_number=1,
                    week_type=1,
                    lesson_type="Лек"

                )
                physics_class_10_10_10 = Lesson(
                    subject_id=physics_class.id, 
                    group_id=group.id,
                    weekday=1,
                    lesson_number=2,
                    week_type=1,
                    lesson_type="Лек"
                )
                db.session.add(math_class_10_10_10)
                db.session.add(physics_class_10_10_10)




                db.session.commit()  # Сохраняем изменения в базе данных
        
        if not Subject.query.filter_by(name='test_subject_name').first():
            test_subject = Subject(name='test_subject_name')
            db.session.add(test_subject)
            db.session.commit()

    scheduler.add_job(
        id='create_empty_attendances',
        func=create_empty_attendances,
        trigger=CronTrigger(hour=0, minute=1),  # Запуск каждый день в 00:01
        replace_existing=True
    )



    cache.delete('groups_data')
    app.run(debug=True)

