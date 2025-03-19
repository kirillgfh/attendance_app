import re
import requests
from collections import Counter
from pprint import pprint

# Параметры запроса
url = "https://miet.ru/schedule/data"


def preprocess_subject_frequencies(raw_schedule):
    """Создает словарь с частотой встречаемости полных и раздельных названий предметов."""
    subject_counter = Counter()

    for entry in raw_schedule:
        full_name = entry["Class"]["Name"]
        full_name = re.sub(r"\[.*?\]", "", full_name).strip()

        subject_counter[full_name] += 1  # Считаем полное название

        if "/" in full_name:  # Разделяем названия и учитываем их частоту
            part1, part2 = full_name.split("/")
            subject_counter[part1] += 1
            subject_counter[part2] += 1

    return subject_counter

def clean_subject_name(subject_name, subject_counter):
    """Заменяет сложные названия на наиболее часто встречающееся."""
    if subject_name == "Индивидуальные виды спорта / Командные виды спорта":
        return subject_name  # Исключение, оставляем как есть

    if "/" in subject_name:
        part1, part2 = subject_name.split("/")
        count_part1 = subject_counter.get(part1, 0)
        count_part2 = subject_counter.get(part2, 0)

        if count_part1 >= count_part2 and count_part1 > 0:
            return part1
        elif count_part2 > 0:
            return part2

    return subject_name  # Если нет изменений, возвращаем исходное название

def determine_subject_type(subject_name):
    """Определяет тип предмета (лекция, практика, лабораторная)."""
    if "Лек" in subject_name:
        return "Лек"
    elif "Пр" in subject_name:
        return "Пр"
    elif "Лаб" in subject_name:
        return "Лаб"
    return "Пр"  # По умолчанию






def get_lessons_for_group(group_name):
    args = {"group": group_name.upper()}

    # Получаем данные
    response = requests.get(url=url, params=args, headers=None)
    raw_schedule = response.json()["Data"]
    # Предварительно считаем частоту встречаемости предметов
    subject_counter = preprocess_subject_frequencies(raw_schedule)

    lessons = []

    # Парсим данные
    for entry in raw_schedule:
        day_number = entry["Day"]
        week_type_number = entry["DayNumber"]
        subject_name = entry["Class"]["Name"]
        subject_type = determine_subject_type(subject_name)
        subject_name = re.sub(r"\[.*?\]", "", subject_name).strip()
        lesson_number = entry["Time"]["Code"]

        # Очистка и нормализация названия предмета
        if subject_name != 'Военная подготовка':
            subject_name_clean = clean_subject_name(subject_name, subject_counter)

            # Определяем тип предмета
            list_week_type = ['1ч', '1з', '2ч', '2з']
            
            lessons.append([subject_name_clean, day_number, lesson_number, list_week_type[week_type_number], subject_type, group_name])

    # Сортируем уроки по дню недели и номеру пары
    lessons.sort(key=lambda x: (x[1], x[2]))  # Сначала по дню недели, затем по номеру пары

    # Выводим результат
    return lessons

def get_subjects(group_name):
    args = {"group": group_name.upper()}
    # Получаем данные
    response = requests.get(url=url, params=args, headers=None)
    raw_schedule = response.json()["Data"]
    
    subjects = set()  # Используем множество для автоматического удаления дубликатов
    for entry in raw_schedule:
        subject_name = entry["Class"]["Name"]
        subject_name_clean = re.sub(r"\[.*?\]", "", subject_name).strip()
        # Игнорируем "Военная подготовка"
        if subject_name_clean == "Военная подготовка":
            continue
        if '/' in subject_name_clean and subject_name_clean != 'Индивидуальные виды спорта / Командные виды спорта':
            continue
        # Добавляем очищенное название в множество
        subjects.add(subject_name_clean)
    # Преобразуем множество обратно в список (если нужен именно список)
    subjects = list(subjects)
    # Выводим результат
    return subjects

