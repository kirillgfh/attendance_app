    // Функция для сортировки по алфавиту (кириллице)
    function sortByName(rows, isAscending) {
        rows.sort((rowA, rowB) => {
            const nameA = rowA.querySelector('td:nth-child(1)').textContent.trim().toLowerCase();
            const nameB = rowB.querySelector('td:nth-child(1)').textContent.trim().toLowerCase();
            return isAscending ? nameA.localeCompare(nameB, 'ru') : nameB.localeCompare(nameA, 'ru');
        });
    }

    // Функция для сортировки по проценту посещаемости
    function sortByPercent(rows, isAscending) {
        rows.sort((rowA, rowB) => {
            const percentA = parseFloat(rowA.querySelector('td:nth-child(2)').textContent);
            const percentB = parseFloat(rowB.querySelector('td:nth-child(2)').textContent);
            return isAscending ? percentA - percentB : percentB - percentA;
        });
    }

    // Функция для обновления иконки сортировки
    function updateSortIcon(button, isAscending) {
        const icon = button.querySelector('i');
        icon.className = isAscending ? 'fas fa-sort-up' : 'fas fa-sort-down';
    }

    // Обработчик для сортировки по имени (студенты)
    document.getElementById('sort-name-button')?.addEventListener('click', function() {
        const table = document.getElementById('attendance-table');
        const tbody = table.querySelector('tbody');
        const rows = Array.from(tbody.querySelectorAll('tr'));

        // Определяем текущее направление сортировки
        const isAscending = table.getAttribute('data-sort-name') !== 'asc';

        // Сортируем строки по имени
        sortByName(rows, isAscending);

        // Обновляем направление сортировки
        table.setAttribute('data-sort-name', isAscending ? 'asc' : 'desc');

        // Очищаем tbody и добавляем отсортированные строки
        tbody.innerHTML = '';
        rows.forEach(row => tbody.appendChild(row));

        // Обновляем иконку сортировки
        updateSortIcon(this, isAscending);

        // Сбрасываем иконку сортировки для другого столбца
        const percentButton = document.getElementById('sort-percent-button');
        percentButton.querySelector('i').className = 'fas fa-sort';
    });

    // Обработчик для сортировки по проценту (студенты)
    document.getElementById('sort-percent-button')?.addEventListener('click', function() {
        const table = document.getElementById('attendance-table');
        const tbody = table.querySelector('tbody');
        const rows = Array.from(tbody.querySelectorAll('tr'));

        // Определяем текущее направление сортировки
        const isAscending = table.getAttribute('data-sort-percent') !== 'asc';

        // Сортируем строки по проценту
        sortByPercent(rows, isAscending);

        // Обновляем направление сортировки
        table.setAttribute('data-sort-percent', isAscending ? 'asc' : 'desc');

        // Очищаем tbody и добавляем отсортированные строки
        tbody.innerHTML = '';
        rows.forEach(row => tbody.appendChild(row));

        // Обновляем иконку сортировки
        updateSortIcon(this, isAscending);

        // Сбрасываем иконку сортировки для другого столбца
        const nameButton = document.getElementById('sort-name-button');
        nameButton.querySelector('i').className = 'fas fa-sort';
    });

    // Обработчик для сортировки по предмету (предметы)
    document.getElementById('sort-subject-button')?.addEventListener('click', function() {
        const table = document.getElementById('subject-table');
        const tbody = table.querySelector('tbody');
        const rows = Array.from(tbody.querySelectorAll('tr'));

        // Определяем текущее направление сортировки
        const isAscending = table.getAttribute('data-sort-subject') !== 'asc';

        // Сортируем строки по имени предмета
        sortByName(rows, isAscending);

        // Обновляем направление сортировки
        table.setAttribute('data-sort-subject', isAscending ? 'asc' : 'desc');

        // Очищаем tbody и добавляем отсортированные строки
        tbody.innerHTML = '';
        rows.forEach(row => tbody.appendChild(row));

        // Обновляем иконку сортировки
        updateSortIcon(this, isAscending);

        // Сбрасываем иконку сортировки для другого столбца
        const percentButton = document.getElementById('sort-subject-percent-button');
        percentButton.querySelector('i').className = 'fas fa-sort';
    });

    // Обработчик для сортировки по проценту (предметы)
    document.getElementById('sort-subject-percent-button')?.addEventListener('click', function() {
        const table = document.getElementById('subject-table');
        const tbody = table.querySelector('tbody');
        const rows = Array.from(tbody.querySelectorAll('tr'));

        // Определяем текущее направление сортировки
        const isAscending = table.getAttribute('data-sort-subject-percent') !== 'asc';

        // Сортируем строки по проценту
        sortByPercent(rows, isAscending);

        // Обновляем направление сортировки
        table.setAttribute('data-sort-subject-percent', isAscending ? 'asc' : 'desc');

        // Очищаем tbody и добавляем отсортированные строки
        tbody.innerHTML = '';
        rows.forEach(row => tbody.appendChild(row));

        // Обновляем иконку сортировки
        updateSortIcon(this, isAscending);

        // Сбрасываем иконку сортировки для другого столбца
        const subjectButton = document.getElementById('sort-subject-button');
        subjectButton.querySelector('i').className = 'fas fa-sort';
    });