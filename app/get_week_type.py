from datetime import date

def get_week_type(target_date):
    semester_start = date(2025, 2, 5)  # Начало семестра (среда)
    week_types = ["1ч", "1з", "2ч", "2з"]  # Чередование недель
    
    # Вычисляем количество дней между датами
    delta_days = (target_date - semester_start).days
    
    # Определяем номер недели с учетом сдвига (недели считаем с понедельника)
    week_number = (delta_days + 3) // 7  # Сдвиг на 3 дня, чтобы понедельник был первым днем недели
    
    return week_types[week_number % 4]  # Определяем текущий тип недели

# Проверка
# print(get_week_type(date(2025, 3, 3)))  # Должно быть "1ч"
# print(get_week_type(date(2025, 3, 10))) # Должно быть "1з"
# print(get_week_type(date(2025, 3, 17))) # Должно быть "2ч"
# print(get_week_type(date(2025, 3, 24))) # Должно быть "2з"
