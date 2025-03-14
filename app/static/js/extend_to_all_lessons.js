document.addEventListener('DOMContentLoaded', function () {
    const propagateButton = document.getElementById('propagate-button');
    const checkboxes = document.querySelectorAll('input[type="checkbox"]');

    propagateButton.addEventListener('click', function () {
        const selectedStudents = [];
        checkboxes.forEach(checkbox => {
            if (checkbox.checked) {
                const studentId = checkbox.name.replace('status_', '');
                selectedStudents.push(studentId);
            }
        });

        if (selectedStudents.length === 0) {
            alert('Выберите хотя бы одного студента.');
            return;
        }

        if (confirm('Вы уверены, что хотите распространить данные пары на все пары ниже?')) {
            // Получаем lesson_id и selected_date из DOM
            const lessonId = document.getElementById('selected-date').dataset.lessonId;
            const selectedDate = document.getElementById('selected-date').value;

            // Отправляем запрос на сервер
            fetch(`/propagate_attendance?lesson_id=${lessonId}&selected_date=${selectedDate}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ students: selectedStudents }),
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert('Данные успешно распространены на все пары ниже.');
                } else {
                    alert('Произошла ошибка: ' + data.error);
                }
            })
            .catch(error => {
                console.error('Ошибка:', error);
                alert('Произошла ошибка при распространении данных.');
            });
        }
    });
});