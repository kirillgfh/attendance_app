    document.addEventListener('DOMContentLoaded', function () {
        const items = document.querySelectorAll('.scroll-content .item');
        const lessonsList = document.getElementById('lessons-list');
        const weekTypeSpan = document.getElementById('week-type');
        const contentDiv = document.getElementById('content');
        const selectedDateInput = document.getElementById('selected-date');

        // Восстановление выбранного дня из localStorage
        const savedDate = localStorage.getItem('selectedDate');
        if (savedDate) {
            const savedItem = document.querySelector(`.scroll-content .item[data-date="${savedDate}"]`);
            if (savedItem) {
                savedItem.click();
            }
        }

        items.forEach(item => {
            item.addEventListener('click', function () {
                // Убираем выделение у всех элементов
                items.forEach(i => i.classList.remove('selected'));
                // Выделяем выбранный элемент
                item.classList.add('selected');

                // Получаем выбранную дату
                const selectedDate = item.getAttribute('data-date');

                // Сохраняем выбранную дату в localStorage
                localStorage.setItem('selectedDate', selectedDate);

                // Устанавливаем значение скрытого поля для формы
                if (selectedDateInput) {
                    selectedDateInput.value = selectedDate;
                }

                // Отправляем запрос на сервер для получения уроков
                fetch(`/get_lessons_for_day?date=${selectedDate}`)
                    .then(response => response.json())
                    .then(data => {
                        if (data.error) {
                            console.error(data.error);
                            return;
                        }

                        // Обновляем тип недели
                        weekTypeSpan.textContent = data.week_type;

                        // Очищаем список уроков
                        lessonsList.innerHTML = '';

                        // Добавляем уроки в список
                        data.lessons.forEach(lesson => {
                            const li = document.createElement('li');
                            const button = document.createElement('button');
                            button.textContent = `${lesson.subject_name} (${lesson.lesson_type}) - ${lesson.lesson_number} пара`;
                            button.classList.add('btn', 'btn-primary', 'mb-2');  // Добавляем стили Bootstrap
                            button.onclick = () => {
                                // Переход на страницу students_attendance_list
                                if (lesson.id) {
                                    window.location.href = `/students_attendance_list/${lesson.id}?selected_date=${selectedDate}`;
                                } else {
                                    console.error('ID урока не определен:', lesson);
                                }
                            };
                            li.appendChild(button);
                            lessonsList.appendChild(li);
                        });

                        // Обновляем контент
                        contentDiv.textContent = `Выбран день: ${selectedDate}`;
                    })
                    .catch(error => {
                        console.error('Ошибка при загрузке уроков:', error);
                    });
            });
        });

        // По умолчанию выбираем сегодняшний день
        const todayItem = document.querySelector('.scroll-content .item.today');
        if (todayItem) {
            todayItem.click();
        }
    });
