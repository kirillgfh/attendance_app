document.addEventListener('DOMContentLoaded', function () {
    const items = document.querySelectorAll('.scroll-content .item');
    const selectedDateInput = document.getElementById('selected-date');

    items.forEach(item => {
        item.addEventListener('click', function () {
            // Убираем выделение у всех элементов
            items.forEach(i => i.classList.remove('selected'));
            // Выделяем выбранный элемент
            item.classList.add('selected');
            // Устанавливаем значение скрытого поля
            selectedDateInput.value = item.getAttribute('data-date');
            console.log('Selected date:', selectedDateInput.value);  // Для отладки
        });
    });

    // По умолчанию выбираем сегодняшний день
    const todayItem = document.querySelector('.scroll-content .item.today');
    if (todayItem) {
        todayItem.click();
    }
});


document.addEventListener('DOMContentLoaded', () => {
    const scrollContainer = document.querySelector('.scroll-container');
    const scrollContent = document.querySelector('.scroll-content');
    const items = document.querySelectorAll('.item');
    const content = document.getElementById('content');

    if (!scrollContainer || !scrollContent) {
        console.error('Элементы .scroll-container или .scroll-content не найдены!');
        return;
    }

    // Проверяем, нужна ли прокрутка
    const checkScroll = () => {
        if (scrollContent.scrollWidth <= scrollContainer.offsetWidth) {
            // Если прокрутка не нужна, заменяем контейнер на центрированный div
            scrollContainer.classList.add('center');
        } else {
            // Если прокрутка нужна, возвращаем исходное состояние
            scrollContainer.classList.remove('center');
        }
    };

    // Проверяем при загрузке страницы
    checkScroll();

    // Проверяем при изменении размера окна
    window.addEventListener('resize', checkScroll);

    // Логика для перетаскивания (если прокрутка активна)
    let isDragging = false;
    let startX, scrollLeft;

    scrollContainer.addEventListener('mousedown', (e) => {
        if (scrollContainer.classList.contains('center')) return; // Не перетаскиваем, если контейнер центрирован
        isDragging = true;
        startX = e.pageX - scrollContainer.offsetLeft;
        scrollLeft = scrollContainer.scrollLeft;
        scrollContainer.style.cursor = 'grabbing';
    });

    scrollContainer.addEventListener('mouseleave', () => {
        if (isDragging) {
            isDragging = false;
            scrollContainer.style.cursor = 'grab';
        }
    });

    scrollContainer.addEventListener('mouseup', () => {
        if (isDragging) {
            isDragging = false;
            scrollContainer.style.cursor = 'grab';
        }
    });

    scrollContainer.addEventListener('mousemove', (e) => {
        if (!isDragging || scrollContainer.classList.contains('center')) return;
        e.preventDefault();
        const x = e.pageX - scrollContainer.offsetLeft;
        const walk = (x - startX) * 2; // Увеличиваем скорость прокрутки
        scrollContainer.scrollLeft = scrollLeft - walk;
    });

    // Отключаем выделение текста при перетаскивании
    scrollContainer.addEventListener('dragstart', (e) => {
        e.preventDefault();
    });

    // Логика для выбора элемента
    let selectedItem = null;

    items.forEach(item => {
        item.addEventListener('click', () => {
            // Убираем выделение с предыдущего элемента
            if (selectedItem) {
                selectedItem.classList.remove('selected');
            }

            // Выделяем текущий элемент
            item.classList.add('selected');
            selectedItem = item;

            // Меняем контент страницы
            const day = item.querySelector('li:first-child').textContent;
            const date = item.querySelector('li:last-child').textContent;
            // content.textContent = `Выбран день: ${day}, дата: ${date}`;
            console.log( `Выбран день: ${day}, дата: ${date}`);  // Для отладки

        });
    });
});



