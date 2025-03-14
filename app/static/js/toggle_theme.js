// Функция для переключения темы
function toggleTheme() {
    const body = document.body;
    const themeToggleButton = document.getElementById('theme-toggle');
    const themeToggleDesktopButton = document.getElementById('theme-toggle-desktop');

    if (body.classList.contains('dark-theme')) {
        body.classList.remove('dark-theme');
        body.classList.add('light-theme');
        if (themeToggleButton) themeToggleButton.innerHTML = '<i class="fas fa-sun"></i>';
        if (themeToggleDesktopButton) themeToggleDesktopButton.innerHTML = '<i class="fas fa-sun"></i>';
        localStorage.setItem('theme', 'light');
    } else {
        body.classList.remove('light-theme');
        body.classList.add('dark-theme');
        if (themeToggleButton) themeToggleButton.innerHTML = '<i class="fas fa-moon"></i>';
        if (themeToggleDesktopButton) themeToggleDesktopButton.innerHTML = '<i class="fas fa-moon"></i>';
        localStorage.setItem('theme', 'dark');
    }
}

// Загрузка сохраненной темы при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
    const savedTheme = localStorage.getItem('theme') || 'dark';
    const body = document.body;
    const themeToggleButton = document.getElementById('theme-toggle');
    const themeToggleDesktopButton = document.getElementById('theme-toggle-desktop');

    if (savedTheme === 'light') {
        body.classList.add('light-theme');
        if (themeToggleButton) themeToggleButton.innerHTML = '<i class="fas fa-sun"></i>';
        if (themeToggleDesktopButton) themeToggleDesktopButton.innerHTML = '<i class="fas fa-sun"></i>';
    } else {
        body.classList.add('dark-theme');
        if (themeToggleButton) themeToggleButton.innerHTML = '<i class="fas fa-moon"></i>';
        if (themeToggleDesktopButton) themeToggleDesktopButton.innerHTML = '<i class="fas fa-moon"></i>';
    }

    // Назначение обработчика события для кнопки смены темы (мобильная версия)
    if (themeToggleButton) {
        themeToggleButton.addEventListener('click', toggleTheme);
    }

    // Назначение обработчика события для кнопки смены темы (десктопная версия)
    if (themeToggleDesktopButton) {
        themeToggleDesktopButton.addEventListener('click', toggleTheme);
    }
});