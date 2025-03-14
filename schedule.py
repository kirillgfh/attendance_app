from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import time
from webdriver_manager.chrome import ChromeDriverManager
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# Настройка ChromeOptions
options = Options()
options.add_argument('--headless')  # Безголовый режим (без графического интерфейса)
options.add_argument('--disable-gpu')  # Отключение GPU ускорения

# Запуск Chrome
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

# Открытие страницы с расписанием
url = "https://www.miet.ru/schedule/#%D0%98%D0%92%D0%A2-23"
driver.get(url)

# Ждем, пока страница полностью загрузится (можно увеличить время, если страница медленно загружается)
time.sleep(5)

# Находим все элементы, которые содержат расписание
# Используем правильный CSS-селектор, который нужно будет подогнать под структуру страницы
schedule_elements = driver.find_elements(By.CSS_SELECTOR, ".schedule-item")

# Выводим информацию о расписании
for element in schedule_elements:
    print(element.text)

# Закрываем браузер
driver.quit()
