from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
# from app.models.group import Group
# from app.models.student import Student
# from app.models.lesson import Lesson
from app.models.attendance import Attendance
from app.repositories.attendance_repository import AttendanceRepository
from app.repositories.group_repository import GroupRepository
from app.repositories.lesson_repository import LessonRepository
from app.repositories.student_repository import StudentRepository
from app.utils.check_access import role_required
from app.utils.get_week_type import get_week_type
from datetime import datetime, timedelta
from app import cache

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/dashboard')
@login_required
@role_required(['moderator'])
def dashboard():
    group = GroupRepository.get_by_moderator_id(current_user.id)
    # group = Group.query.filter_by(moderator_id=current_user.id).first()
    if not group:
        flash('Группа не найдена.', 'danger')
        return redirect(url_for('auth.index'))

    selected_date_str = request.args.get('selected_date')
    selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date() if selected_date_str else datetime.now().date()
    week_type = get_week_type(selected_date)

    if week_type is None:
        flash('Семестр еще не начался.', 'info')
        return redirect(url_for('auth.index'))

    days = [
        [(selected_date - timedelta(days=(6 - i))).strftime('%a'), (selected_date - timedelta(days=(6 - i))).strftime('%d')]
        for i in range(7)
    ]

    students = StudentRepository.get_by_group_id(group.id)
    lessons = LessonRepository.get_by_group_id(group.id)

    return render_template(
        'dashboard.html',
        students=students,
        lessons=lessons,
        days=days,
        today_index=6,
        today=selected_date,
        week_type=week_type,
        timedelta=timedelta
    )

@dashboard_bp.route('/get_lessons_for_day', methods=['GET'])
@login_required
@role_required(['moderator'])
def get_lessons_for_day():
    group = GroupRepository.get_by_moderator_id(current_user.id)
    if not group:
        return jsonify({"error": "Группа не найдена"}), 404

    selected_date_str = request.args.get('date')
    if not selected_date_str:
        return jsonify({"error": "Дата не указана"}), 400

    selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
    week_type = get_week_type(selected_date)
    week_type_fullname = get_week_type(selected_date, full_name=True)
    lessons = LessonRepository.get_by_day_and_type(
        group_id=group.id,
        weekday= selected_date.weekday()+1,
        week_type=week_type
    )
    
    # lessons = Lesson.query.filter(
    #     Lesson.weekday == selected_date.weekday() + 1,
    #     Lesson.week_type == week_type,
    #     Lesson.group_id == group.id
    # ).all()

    lessons_data = [
        {"id": lesson.id, "subject_name": lesson.subject.name, "lesson_type": lesson.lesson_type, "lesson_number": lesson.lesson_number}
        for lesson in lessons
    ]

    return jsonify({"lessons": lessons_data, "week_type": week_type_fullname})

@dashboard_bp.route('/mark_attendance', methods=['POST'])
@login_required
@role_required(['moderator'])
def mark_attendance():
    selected_date_str = request.form.get('selected_date')
    if not selected_date_str:
        flash('Дата не выбрана.', 'danger')
        return redirect(url_for('dashboard.dashboard'))

    selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
    group = GroupRepository.get_by_moderator_id(current_user.id)
    if not group:
        flash('Группа не найдена.', 'danger')
        return redirect(url_for('dashboard.dashboard'))

    for student in StudentRepository.get_by_group_id(group.id):
        lesson_id = request.form.get(f'lesson_{student.id}')
        status = request.form.get(f'status_{student.id}') == '1'

        if not lesson_id:
            flash(f'Не указан ID урока для студента {student.name}.', 'danger')
            continue

        attendance = AttendanceRepository.get_by_student_lesson_date(student.id, lesson_id, selected_date)
        if attendance:
            AttendanceRepository.update(student.id, lesson_id, selected_date, status)
        else:
            AttendanceRepository.create(student.id, lesson_id, selected_date, status)

    # db.session.commit()
    flash('Посещения успешно сохранены!', 'success')
    cache.delete('groups_data')
    return redirect(url_for('dashboard.dashboard'))

@dashboard_bp.route('/edit_group_members', methods=['GET', 'POST'])
@login_required
@role_required(['moderator'])
def edit_group_members():
    group = GroupRepository.get_by_moderator_id(current_user.id)
    if not group:
        flash('Группа не найдена.', 'danger')
        return redirect(url_for('dashboard.dashboard'))

    # students = Student.query.filter_by(group_id=group.id).all()
    students = StudentRepository.get_by_group_id(group_id = group.id)

    if request.method == 'POST':
        new_student_name = request.form.get('new_student_name')
        if new_student_name:

            new_student = StudentRepository.create(name=new_student_name, group_id=group.id)
            flash(f'Студент {new_student_name} успешно добавлен.', 'success')
            return redirect(url_for('dashboard.edit_group_members'))

        delete_student_id = request.form.get('delete_student_id')
        if delete_student_id:
            try: 
                student_to_delete = StudentRepository.delete(delete_student_id)
                Attendance.query.filter_by(student_id=student_to_delete.id).delete()
                flash(f'Студент {student_to_delete.name} успешно удален.', 'success')
            except:
                return redirect(url_for('dashboard.edit_group_members'))
        return redirect(url_for('dashboard.edit_group_members'))


    return render_template('edit_group_members.html', students=students, group=group)


@dashboard_bp.route('/students_attendance_list/<int:lesson_id>')
@login_required
def students_attendance_list(lesson_id):
    lesson = LessonRepository.get_by_id(lesson_id = lesson_id)
    # lesson = Lesson.query.get_or_404(lesson_id)
    students = StudentRepository.get_by_group_id(group_id=lesson.group_id)
    # students = Student.query.filter_by(group_id=lesson.group_id).all()
    selected_date_str = request.args.get('selected_date')  # Получаем selected_date из URL

    if not selected_date_str:
        flash('Дата не выбрана.', 'danger')
        return redirect(url_for('dashboard'))

    selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()

    # Собираем данные о посещаемости для каждого студента
    attendance_data = []
    for student in students:
        # Ищем запись о посещаемости для данного студента, урока и даты
        attendance = AttendanceRepository.get_by_student_lesson_date(            
            student_id=student.id,
            lesson_id=lesson.id,
            date=selected_date)


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