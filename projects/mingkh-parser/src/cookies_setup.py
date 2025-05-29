# Импорт необходимых библиотек
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
import time
import pickle

# ===== НАСТРОЙКА БРАУЗЕРА =====
# Создание опций для Chrome
options = webdriver.ChromeOptions()
# Отключение автоматических признаков WebDriver
options.add_argument("--disable-blink-features=AutomationControlled")

# Инициализация сервиса с указанием пути к драйверу
service = Service(executable_path="chromedriver.exe")
# Создание экземпляра драйвера с настройками
driver = webdriver.Chrome(service=service, options=options)

# ===== ОБХОД ЗАЩИТЫ ОТ БОТОВ =====
# Удаление специфических свойств окна, которые используются для детекции
driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
    'source': '''
        delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;
        delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
        delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;
        delete window.cdc_adoQpoasnfa76pfcZLmcfl_JSON;
  '''
})

# ===== ОСНОВНОЙ БЛОК РАБОТЫ =====
try:
    # Открытие целевого сайта
    driver.get("https://mingkh.ru/kemerovskaya-oblast/kemerovo/")
    
    # Ожидание ручной аутентификации (20 секунд)
    time.sleep(20)
    
    # СОХРАНЕНИЕ КУКИ
    # Получение текущих кук и сохранение в файл
    pickle.dump(driver.get_cookies(), open("cookies.pkl", "wb"))
    print("Куки успешно сохранены!")

# ===== ОБРАБОТКА ОШИБОК =====
except Exception as ex:
    print(f"Произошла ошибка: {ex}")

# ===== ЗАВЕРШЕНИЕ РАБОТЫ =====
finally:
    # Закрытие браузера независимо от результата
    driver.close()
    driver.quit()
