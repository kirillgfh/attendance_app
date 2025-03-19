from datetime import datetime
from flask_apscheduler import APScheduler
from apscheduler.triggers.cron import CronTrigger
from utils.get_week_type import get_week_type
from main2 import app, db, Group, Lesson, Student, Attendance


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
                        new_attendance = Attendance(
                            student_id=student.id,
                            lesson_id=lesson.id,
                            date=today,
                            status=False  # По умолчанию отсутствует
                        )
                        db.session.add(new_attendance)
                    
        db.session.commit()
        print(f"Пустые посещения созданы для {today}.")




create_empty_attendances()
# Настройка задачи для ежедневного выполнения в 00:01
# scheduler.add_job(
#     id='create_empty_attendances',
#     func=create_empty_attendances,
#     trigger=CronTrigger(hour=3, minute=20),  # Запуск каждый день в 00:01
#     replace_existing=True
# )