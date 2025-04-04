from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from app.models.group import Group
from app.models.attendance import Attendance
from app.models.lesson import Lesson
from app.utils.check_access import role_required
from app import db
from datetime import datetime

api_bp = Blueprint('api', __name__)

@api_bp.route('/groups', methods=['GET'])
@login_required
@role_required(['admin'])
def get_groups():
    groups = Group.query.all()
    return jsonify([
        {"id": g.id, "name": g.name, "attendance_percentage": g.attendance_percentage}
        for g in groups
    ])

@api_bp.route('/attendance', methods=['POST'])
@login_required
@role_required(['moderator', 'admin'])
def attendance():
    data = request.get_json()
    attendance = Attendance(
        student_id=data['student_id'],
        lesson_id=data['lesson_id'],
        date=datetime.strptime(data['date'], '%Y-%m-%d').date(),
        status=data['status']
    )
    db.session.add(attendance)
    db.session.commit()
    return jsonify({"message": "Посещение отмечено"}), 201

@api_bp.route('/propagate_attendance', methods=['POST'])
@login_required
@role_required(['moderator', 'admin'])
def propagate_attendance():
    data = request.get_json()
    selected_students = data.get('students', [])
    lesson_id = request.args.get('lesson_id')
    selected_date_str = request.args.get('selected_date')

    if not lesson_id or not selected_date_str:
        return jsonify({"success": False, "error": "Не указан ID урока или дата"}), 400

    selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
    lesson = Lesson.query.get_or_404(lesson_id)

    try:
        lessons_below = Lesson.query.filter(
            Lesson.group_id == lesson.group_id,
            Lesson.weekday == lesson.weekday,
            Lesson.lesson_number >= lesson.lesson_number,
            Lesson.week_type == lesson.week_type
        ).all()

        for student_status in selected_students:
            student_id = int(student_status.replace('status_', ''))
            for lesson_below in lessons_below:
                attendance = Attendance.query.filter_by(student_id=student_id, lesson_id=lesson_below.id, date=selected_date).first()
                if attendance:
                    attendance.status = True
                else:
                    attendance = Attendance(student_id=student_id, lesson_id=lesson_below.id, date=selected_date, status=True)
                    db.session.add(attendance)

        db.session.commit()
        return jsonify({"success": True})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500