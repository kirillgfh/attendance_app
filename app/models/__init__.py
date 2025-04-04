# app/models/__init__.py
from .user import User
from .group import Group
from .student import Student
from .subject import Subject
from .lesson import Lesson
from .attendance import Attendance  

# Список всех моделей для удобного доступа
__all__ = [
    'User',
    'Group',
    'Student',
    'Subject',
    'Lesson',
    'Attendance'
]