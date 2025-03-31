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
                    console.log(weekTypeSpan.textContent, weekTypeSpan);
                    // Очищаем список уроков
                    lessonsList.innerHTML = '';

                    // Добавляем уроки в виде карточек
                    data.lessons.forEach(lesson => {
                        const card = document.createElement('div');
                        card.classList.add('lesson-card');
                        card.classList.add('clickable-card');
                        card.innerHTML = `
                            <h4>${lesson.subject_name}</h4>
                            <div class="lesson-info">
                                <p class="lesson-type">${lesson.lesson_type}</p>
                                <p class="lesson-number">${lesson.lesson_number} пара</p>
                            </div>
                        `;
                        card.onclick = () => {
                            if (lesson.id) {
                                window.location.href = `/students_attendance_list/${lesson.id}?selected_date=${selectedDate}`;
                            } else {
                                console.error('ID урока не определен:', lesson);
                            }
                        };
                        lessonsList.appendChild(card);
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