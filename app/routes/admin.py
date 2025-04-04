from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from app.models.group import Group
from app.models.user import User
from app.models.student import Student
from app.models.lesson import Lesson
from app.models.attendance import Attendance
from app.models.subject import Subject
from app.utils.check_access import role_required
from app.utils.get_week_type import get_week_type
from app import db, cache
from datetime import datetime, timedelta
import secrets

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/admin')
@login_required
@role_required(['admin'])
def admin():
    groups_data = cache.get('groups_data')
    if not groups_data:
        groups = Group.query.all()
        groups_data = [
            {
                'id': group.id,
                'name': group.name,
                'attendance_percentage': group.attendance_percentage
            } for group in groups
        ]
        cache.set('groups_data', groups_data, timeout=300)

    group_id = request.args.get('group_id')
    selected_group_data = None
    attendance_stats = []
    subject_stats = []
    weekly_attendance = []
    dates = []
    view_mode = request.args.get('view_mode', 'students')

    if group_id:
        selected_group_data = cache.get(f'selected_group_data_{group_id}')
        if not selected_group_data:
            selected_group = Group.query.get_or_404(group_id)
            selected_group_data = {
                'id': selected_group.id,
                'name': selected_group.name,
                'students': [{'id': s.id, 'name': s.name} for s in selected_group.students],
                'lessons': [{'id': l.id, 'subject_name': l.subject.name, 'weekday': l.weekday, 'lesson_number': l.lesson_number, 'week_type': l.week_type, 'lesson_type': l.lesson_type} for l in selected_group.lessons]
            }
            cache.set(f'selected_group_data_{group_id}', selected_group_data, timeout=300)

        for i in range(6, -1, -1):
            date = datetime.now().date() - timedelta(days=i)
            dates.append(date)
            total_attended = sum(
                Attendance.query.filter_by(lesson_id=lesson['id'], date=date, status=True).count()
                for lesson in selected_group_data['lessons'] if lesson['weekday'] == date.weekday() + 1 and lesson['week_type'] == get_week_type(date)
            )
            total_classes = sum(
                Attendance.query.filter_by(lesson_id=lesson['id'], date=date).count()
                for lesson in selected_group_data['lessons'] if lesson['weekday'] == date.weekday() + 1 and lesson['week_type'] == get_week_type(date)
            )
            weekly_attendance.append(round((total_attended / total_classes * 100), 2) if total_classes > 0 else 0)

        if view_mode == 'students':
            attendance_stats = [
                {
                    "student_id": s['id'],
                    "student_name": s['name'],
                    "attendance_percentage": round(
                        sum(Attendance.query.filter_by(student_id=s['id'], lesson_id=l['id'], status=True).count() for l in selected_group_data['lessons']) /
                        sum(Attendance.query.filter_by(student_id=s['id'], lesson_id=l['id']).count() for l in selected_group_data['lessons']) * 100, 2
                    ) if sum(Attendance.query.filter_by(student_id=s['id'], lesson_id=l['id']).count() for l in selected_group_data['lessons']) > 0 else 0
                } for s in selected_group_data['students']
            ]
        elif view_mode == 'subjects':
            subject_dict = {}
            for lesson in selected_group_data['lessons']:
                subject_name = lesson['subject_name']
                if subject_name not in subject_dict:
                    subject_dict[subject_name] = {"total_attended": 0, "total_classes": 0}
                subject_dict[subject_name]['total_attended'] += Attendance.query.filter_by(lesson_id=lesson['id'], status=True).count()
                subject_dict[subject_name]['total_classes'] += Attendance.query.filter_by(lesson_id=lesson['id']).count()
            subject_stats = [
                {"subject_name": name, "attendance_percentage": round(data['total_attended'] / data['total_classes'] * 100, 2) if data['total_classes'] > 0 else 0}
                for name, data in subject_dict.items()
            ]

    return render_template(
        'admin.html',
        groups=groups_data,
        selected_group=selected_group_data,
        attendance_stats=attendance_stats,
        subject_stats=subject_stats,
        view_mode=view_mode,
        weekly_attendance=weekly_attendance,
        weekly_dates=[date.strftime('%a %d') for date in dates]
    )

@admin_bp.route('/edit_group_schedule/<int:group_id>', methods=['GET', 'POST'])
@login_required
@role_required(['admin'])
def edit_group_schedule(group_id):
    group = Group.query.get_or_404(group_id)
    lessons = Lesson.query.filter_by(group_id=group.id).all()
    subjects = Subject.query.all()
    week_types = {'1ч': '1 числитель', '1з': '1 знаменатель', '2ч': '2 числитель', '2з': '2 знаменатель'}

    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add_lesson':
            new_lesson = Lesson(
                subject_id=request.form.get('subject_id'),
                group_id=group_id,
                weekday=int(request.form.get('weekday')),
                lesson_number=int(request.form.get('lesson_number')),
                week_type=request.form.get('week_type'),
                lesson_type=request.form.get('lesson_type')
            )
            db.session.add(new_lesson)
            db.session.commit()
            flash('Урок успешно добавлен.', 'success')
        elif action == 'edit_lesson':
            lesson = Lesson.query.get_or_404(request.form.get('lesson_id'))
            lesson.subject_id = request.form.get('subject_id')
            lesson.weekday = int(request.form.get('weekday'))
            lesson.lesson_number = int(request.form.get('lesson_number'))
            lesson.week_type = request.form.get('week_type')
            lesson.lesson_type = request.form.get('lesson_type')
            db.session.commit()
            flash('Урок успешно отредактирован.', 'success')
        elif 'delete_lesson_id' in request.form:
            lesson_to_delete = Lesson.query.get(request.form.get('delete_lesson_id'))
            if lesson_to_delete:
                db.session.delete(lesson_to_delete)
                db.session.commit()
                flash('Урок успешно удален.', 'success')
        return redirect(url_for('admin.edit_group_schedule', group_id=group_id))

    return render_template('edit_group_schedule.html', group=group, lessons=lessons, subjects=subjects, week_types=week_types)

@admin_bp.route('/manage_users')
@login_required
@role_required(['admin'])
def manage_users():
    users = db.session.query(User, Group.name.label('group_name')).outerjoin(Group, User.id == Group.moderator_id).order_by(User.username).all()
    return render_template('manage_users.html', users=users)

@admin_bp.route('/update_user_credentials/<int:user_id>', methods=['POST'])
@login_required
@role_required(['admin'])
def update_user_credentials(user_id):
    user = User.query.get_or_404(user_id)
    new_password = secrets.token_hex(6)
    user.set_password(new_password)
    db.session.commit()
    return jsonify({"success": True, "username": user.username, "password": new_password})

@admin_bp.route('/add_group', methods=['GET', 'POST'])
@login_required
@role_required(['admin'])
def add_group():
    if request.method == 'POST':
        group_name = request.form['group_name']
        if Group.query.filter_by(name=group_name).first():
            flash('Группа с таким названием уже существует.', 'danger')
            return redirect(url_for('admin.add_group'))

        username = f"moderator_{group_name.lower()}"
        password = secrets.token_hex(8)
        moderator = User(username=username, role='moderator')
        moderator.set_password(password)
        db.session.add(moderator)
        db.session.commit()

        new_group = Group(name=group_name, moderator_id=moderator.id)
        db.session.add(new_group)
        db.session.commit()
        cache.delete('groups_data')

        return render_template(
            'add_group.html',
            moderators=User.query.filter_by(role='moderator').all(),
            created_group=group_name,
            created_username=username,
            created_password=password
        )

    return render_template(
        'add_group.html',
        moderators=User.query.filter_by(role='moderator').all(),
        created_group=None,
        created_username=None,
        created_password=None
    )

@admin_bp.route('/delete_user/<int:user_id>', methods=['POST'])
@login_required
@role_required(['admin'])
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash('Пользователь успешно удален.', 'success')
    return redirect(url_for('admin.manage_users'))


@admin_bp.route('/student_statistics/<int:student_id>')
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

