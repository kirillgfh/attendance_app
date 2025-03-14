# from flask import Flask
# from flask_sqlalchemy import SQLAlchemy
# import re
# app = Flask(__name__)
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///university.db'
# app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# db = SQLAlchemy(app)

# # Определение моделей базы данных
# class Group(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     name = db.Column(db.String(100), unique=True, nullable=False)
#     moderator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
#     students = db.relationship('Student', backref='group', lazy=True)
#     lessons = db.relationship('Lesson', backref='group', lazy=True)

# class Student(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     name = db.Column(db.String(100), nullable=False)
#     group_id = db.Column(db.Integer, db.ForeignKey('group.id'), nullable=False)
#     attendances = db.relationship('Attendance', backref='student', lazy=True)

# class Subject(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     name = db.Column(db.String(255), unique=True, nullable=False)
#     lessons = db.relationship('Lesson', backref='subject', lazy=True)

# class Lesson(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
#     group_id = db.Column(db.Integer, db.ForeignKey('group.id'), nullable=False)
#     weekday = db.Column(db.Integer, nullable=False)  # 1 - Пн, 7 - Вс
#     lesson_number = db.Column(db.Integer, nullable=False)  # Номер пары
#     week_type = db.Column(db.String(100), nullable=False)  # Тип недели (числитель 1,2 /знаменатель) ч1 ч2 з1 з2
#     lesson_type = db.Column(db.String(100), nullable=False)  # Тип недели (числитель 1,2 /знаменатель) [Пр] [Лек] [Лаб]
#     attendances = db.relationship('Attendance', backref='lesson', lazy=True)

# class Attendance(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
#     lesson_id = db.Column(db.Integer, db.ForeignKey('lesson.id'), nullable=False)
#     date = db.Column(db.Date, nullable=False)
#     status = db.Column(db.Boolean, default=True, nullable=False)  # По умолчанию True (присутствовал)

# def parse_schedule(text, week_type, group_id):
#     with app.app_context():
#         days_mapping = {
#             "понедельник": 1,
#             "вторник": 2,
#             "среду": 3,
#             "четверг": 4,
#             "пятницу": 5,
#             "субботу": 6,
#             "воскресенье": 7,
#         }
        
#         current_weekday = None
#         subjects_set = set()
#         lessons_list = []
        
#         for line in text.split('\n'):
#             line = line.strip()
            
#             if not line or "военка" in line.lower():
#                 continue
            
#             # Определяем день недели
#             day_match = re.match(r'В\s(понедельник|вторник|среду|четверг|пятницу|субботу|воскресенье)', line, re.IGNORECASE)
#             if day_match:
#                 current_weekday = days_mapping[day_match.group(1).lower()]
#                 continue
            
#             # Парсим строку с парой
#             lesson_match = re.match(r'(\d+)\.\s[^ ]+\s[А-Яа-яЁё\s]+\s[А-ЯЁа-я\.]+\s(.+?)(?:\s\[(.+)\])?$', line)
#             if lesson_match:
#                 lesson_number = int(lesson_match.group(1))
#                 subject_name = lesson_match.group(2).strip()
#                 lesson_type = lesson_match.group(3) if lesson_match.group(3) else "Лек"  # Если тип занятия отсутствует, ставим "Лек"
                
#                 subjects_set.add(subject_name)
#                 lessons_list.append((subject_name, current_weekday, lesson_number, week_type, lesson_type))
        
#         # Удаляем все существующие уроки для данной группы и типа недели
#         Lesson.query.filter_by(group_id=group_id, week_type=week_type).delete()
        
#         # Добавляем предметы в базу, если их нет
#         existing_subjects = {s.name for s in Subject.query.all()}
#         for subject_name in subjects_set:
#             if subject_name not in existing_subjects:
#                 db.session.add(Subject(name=subject_name))
#         db.session.commit()
        
#         # Добавляем уроки
#         subjects_dict = {s.name: s.id for s in Subject.query.all()}
#         for subject_name, weekday, lesson_number, week_type, lesson_type in lessons_list:
#             lesson = Lesson(
#                 subject_id=subjects_dict[subject_name],
#                 weekday=weekday,
#                 lesson_number=lesson_number,
#                 week_type=week_type,
#                 lesson_type=lesson_type,
#                 group_id=group_id
#             )
#             db.session.add(lesson)
        
#         db.session.commit()

# # Пример использования
# schedule_text = """
# В понедельник
# 3. 3201л МПСУ Хисамов В.Т. Электроника и импульсная техника [Пр]
# 4. 3116 м Орлов А.Н. Объектно-ориентированное программирование [Пр]
# -----
# Во вторник
# 1. 1204 м Гудкова Т.А. Инженерная и компьютерная графика [Лек]
# 2. 3304 Епихин В.Н. Теория вероятностей и математическая статистика [Пр]
# 3. 3104 м Беклемишев Д.Н. Программируемые логические интегральные схемы [Лек]
# 4. 5101 Преподаватель К.Ф. Индивидуальные виды спорта / Командные виды спорта
# 5. 4338у МПСУ Балабаев С.А. [ФТД] Углубленное изучение языка С [Лаб]
# 6. 4338у МПСУ Балабаев С.А. [ФТД] Углубленное изучение языка С [Лаб]
# -----
# В среду
# 2. 3105  Герасина Е.В. Инженерная и компьютерная графика [Пр]
# 3. 3102 м Михайлина С.А. Философия [Пр]
# 4. 1205 м Хисамов В.Т. Электроника и импульсная техника/Электроника [Лек]
# -----
# В четверг военка
# -----
# В пятницу
# 1. 1205 м Ярошевич В.А. Численные методы [Лек]
# 2. 5101 Преподаватель К.Ф. Индивидуальные виды спорта / Командные виды спорта
# 3. 1203 м Пирогов А.И. Философия [Лек]
# -----
# В субботу
# 1. 1202 м Петриков А.О. Теория вероятностей и математическая статистика [Лек]
# 2. 3229 Сахно А.В. Численные методы [Пр]"""

# # parse_schedule(schedule_text, "1ч",)


# import re


# def parse_schedule(text, week_type, group_id):
#         days_mapping = {
#             "понедельник": 1,
#             "вторник": 2,
#             "среду": 3,
#             "четверг": 4,
#             "пятницу": 5,
#             "субботу": 6,
#             "воскресенье": 7,
#         }
#         text.replace('Во вторник', "В вторник")
#         current_weekday = None
#         subjects_set = set()
#         lessons_list = []
        
#         for line in text.split('\n'):
#             line = line.strip()
            
#             if not line or "военка" in line.lower():
#                 continue
            
#             # Определяем день недели
#             day_match = re.match(r'В\s(понедельник|вторник|среду|четверг|пятницу|субботу|воскресенье)', line, re.IGNORECASE)
#             if day_match:
#                 current_weekday = days_mapping[day_match.group(1).lower()]
#                 continue
            
#             # Парсим строку с парой
#             lesson_match = re.match(r'(\d+)\.\s[^ ]+\s[А-Яа-яЁё\s]+\s[А-ЯЁа-я\.]+\s(.+?)(?:\s\[(.+)\])?$', line)
#             if lesson_match:
#                 lesson_number = int(lesson_match.group(1))
#                 subject_name = lesson_match.group(2).strip()
#                 lesson_type = lesson_match.group(3) if lesson_match.group(3) else "Лек"  # Если тип занятия отсутствует, ставим "Лек"
                
#                 subjects_set.add(subject_name)
#                 lessons_list.append((subject_name, current_weekday, lesson_number, week_type, lesson_type))
        
#         # Удаляем все существующие уроки для данной группы и типа недели
#         # Lesson.query.filter_by(group_id=group_id, week_type=week_type).delete()
        
#         # Добавляем предметы в базу, если их нет
#         # existing_subjects = {s.name for s in Subject.query.all()}
#         # for subject_name in subjects_set:
#         #     if subject_name not in existing_subjects:
#         #         db.session.add(Subject(name=subject_name))
#         # db.session.commit()
        
#         # Добавляем уроки
#         # subjects_dict = {s.name: s.id for s in Subject.query.all()}
#         for subject_name, weekday, lesson_number, week_type, lesson_type in lessons_list:
#              print (subject_name, weekday, lesson_number, week_type, lesson_type)
#         #     lesson = Lesson(
#         #         subject_id=subjects_dict[subject_name],
#         #         weekday=weekday,
#         #         lesson_number=lesson_number,
#         #         week_type=week_type,
#         #         lesson_type=lesson_type,
#         #         group_id=group_id
#         #     )
#         #     db.session.add(lesson)
        
#         # db.session.commit()
# txt = """
# В понедельник
# 3. 3201л МПСУ Хисамов В.Т. Электроника и импульсная техника [Пр]
# 4. 3116 м Орлов А.Н. Объектно-ориентированное программирование [Пр]
# -----
# Во вторник
# 1. 1204 м Гудкова Т.А. Инженерная и компьютерная графика [Лек]
# 2. 3304 Епихин В.Н. Теория вероятностей и математическая статистика [Пр]
# 3. 3104 м Беклемишев Д.Н. Программируемые логические интегральные схемы [Лек]
# 4. 5101 Преподаватель К.Ф. Индивидуальные виды спорта / Командные виды спорта
# 5. 4338у МПСУ Балабаев С.А. [ФТД] Углубленное изучение языка С [Лаб]
# 6. 4338у МПСУ Балабаев С.А. [ФТД] Углубленное изучение языка С [Лаб]
# -----
# В среду
# 2. 3105  Герасина Е.В. Инженерная и компьютерная графика [Пр]
# 3. 3102 м Михайлина С.А. Философия [Пр]
# 4. 1205 м Хисамов В.Т. Электроника и импульсная техника/Электроника [Лек]
# -----
# В четверг военка
# -----
# В пятницу
# 1. 1205 м Ярошевич В.А. Численные методы [Лек]
# 2. 5101 Преподаватель К.Ф. Индивидуальные виды спорта / Командные виды спорта
# 3. 1203 м Пирогов А.И. Философия [Лек]
# -----
# В субботу
# 1. 1202 м Петриков А.О. Теория вероятностей и математическая статистика [Лек]
# 2. 3229 Сахно А.В. Численные методы [Пр]"""
# print(parse_schedule(txt, '1ч', 1))