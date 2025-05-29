# Импорт необходимых библиотек
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup
import pickle
import time
import csv
import random
import os

# ===== НАСТРОЙКА ДРАЙВЕРА =====
service = Service(executable_path="chromedriver.exe")
driver = webdriver.Chrome(service=service)

# ===== ПОДГОТОВКА CSV-ФАЙЛА =====
# Создаем/очищаем CSV-файл с заданными заголовками
csv_filename = "kemerovo_companies.csv"
headers = [
    "Компания", "Город", "Домов", "Адрес", "Телефон", 
    "Наименование", "Руководитель", "Юридический адрес",
    "Диспетчерская служба", "Телефоны", "Дома в управлении", 
    "ИНН", "ОГРН", "E-mail"
]

with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
    writer = csv.writer(csvfile, quoting=csv.QUOTE_ALL, quotechar='"')
    writer.writerow(headers)

# ===== ФУНКЦИЯ ЗАГРУЗКИ КУКИ =====
def load_cookies():
    """Загружаем сохраненные cookies для авторизации"""
    try:
        driver.get("https://mingkh.ru/")
        cookies = pickle.load(open("cookies.pkl", "rb"))
        for cookie in cookies:
            driver.add_cookie(cookie)
        print("Куки успешно загружены")
    except Exception as e:
        print(f"Ошибка загрузки куков: {str(e)}")

# ===== ФУНКЦИЯ ПАРСИНГА ДЕТАЛЕЙ КОМПАНИИ =====
def parse_company_page(url):
    """Парсим детальную страницу компании с повторами при ошибках"""
    max_attempts = 3
    for attempt in range(max_attempts):
        try:
            driver.get(url)
            # Увеличиваем задержку с каждой попыткой
            time.sleep(5 + 5 * attempt)
            
            soup = BeautifulSoup(driver.page_source, 'lxml')
            data = {}
            
            # ===== ИЗВЛЕЧЕНИЕ ДАННЫХ ИЗ КАРТОЧКИ =====
            # Сопоставление элементов интерфейса с названиями полей
            fields = {
                "Наименование": "Наименование",
                "Руководитель": "Руководитель",
                "Адрес": "Юридический адрес",
                "Диспетчерская служба": "Диспетчерская служба",
                "Телефон (ы)": "Телефоны",
                "Дома в управлении": "Дома в управлении",
                "ИНН": "ИНН",
                "ОГРН": "ОГРН",
                "E-mail": "E-mail"
            }
            
            # Обработка каждого поля на странице
            for dt_text, field_name in fields.items():
                try:
                    dt = soup.find('dt', text=dt_text)
                    if not dt:
                        data[field_name] = ""
                        continue
                        
                    dd = dt.find_next_sibling('dd')
                    if not dd:
                        data[field_name] = ""
                        continue
                     
                    # Специальная обработка для полей с лишними элементами
                    if field_name in ["Юридический адрес", "Дома в управлении"]:
                        for child in dd.find_all():
                            child.decompose()
                        data[field_name] = dd.get_text(strip=True)
                    else:
                        data[field_name] = dd.get_text(strip=True)
                        
                except Exception as e:
                    print(f"Ошибка при извлечении {field_name}: {str(e)}")
                    data[field_name] = ""
            
            return data
        
        except Exception as e:
            print(f"Попытка {attempt+1}/{max_attempts} не удалась для {url}: {str(e)}")
            if attempt < max_attempts - 1:
                # Увеличиваем задержку перед следующей попыткой
                delay = 5 * (2 ** attempt)
                print(f"Повторная попытка через {delay} сек...")
                time.sleep(delay)
    
    print(f"Не удалось загрузить страницу после {max_attempts} попыток: {url}")
    return {}

# ===== ОСНОВНАЯ ФУНКЦИЯ =====
def main():
    # Загрузка авторизационных cookies
    load_cookies()
    base_url = "https://mingkh.ru/kemerovskaya-oblast/kemerovo/"
    
    page_num = 1
    company_count = 0
    
    try:
        # ===== ЦИКЛ ПО СТРАНИЦАМ =====
        while True:
            url = f"{base_url}?page={page_num}" if page_num > 1 else base_url
            print(f"Обработка страницы #{page_num}: {url}")
            
            # ===== ЗАГРУЗКА СТРАНИЦЫ СО СПИСКОМ КОМПАНИЙ =====
            table = None
            for attempt in range(3):
                try:
                    driver.get(url)
                    # Увеличиваем задержку с каждой попыткой
                    time.sleep(10 + 10 * attempt)
                    
                    soup = BeautifulSoup(driver.page_source, 'lxml')
                    table = soup.find("table", class_="table table-bordered table-striped")
                    
                    if table:
                        break
                    else:
                        print(f"Таблица не найдена, попытка {attempt+1}/3")
                except Exception as e:
                    print(f"Ошибка загрузки страницы: {str(e)}, попытка {attempt+1}/3")
                
                if attempt < 2:
                    retry_delay = 10 * (attempt + 1)
                    print(f"Повторная попытка через {retry_delay} сек...")
                    time.sleep(retry_delay)
            
            # Если таблица не загрузилась - пропускаем страницу
            if not table:
                print(f"Не удалось загрузить таблицу после 3 попыток. Пропускаем страницу #{page_num}")
                page_num += 1
                continue
                
            # ===== ОБРАБОТКА СПИСКА КОМПАНИЙ =====
            rows = table.find("tbody").find_all("tr")
            if not rows:
                print("Строки в таблице не найдены. Парсинг завершен.")
                break
                
            for row in rows:
                # Проверка наличия всех столбцов
                if len(row.find_all('td')) >= 6:
                    cols = row.find_all('td')
                    
                    # Извлечение базовой информации
                    try:
                        company_link_element = cols[1].find("a")
                        company_url = f"https://mingkh.ru{company_link_element.get('href')}" if company_link_element else None
                    except Exception as e:
                        print(f"Ошибка при получении URL компании: {e}")
                        company_url = None
                        
                    company_name = cols[1].text.strip() if cols[1] else ""
                    company_city = cols[2].text.strip() if cols[2] else ""
                    houses = cols[3].text.strip() if cols[3] else ""
                    address = cols[4].text.strip() if cols[4] else ""
                    phone = cols[5].text.strip() if cols[5] else ""

                    base_data = {
                        "Компания": company_name,
                        "Город": company_city,
                        "Домов": houses,
                        "Адрес": address,
                        "Телефон": phone
                    }

                    print("_____________________________________________________________")
                    
                    # ===== ПАРСИНГ ДЕТАЛЬНОЙ СТРАНИЦЫ КОМПАНИИ =====
                    details = {}
                    if company_url:
                        try:
                            details = parse_company_page(company_url)
                            time.sleep(random.uniform(3, 7))  # Случайная задержка
                        except Exception as e:
                            print(f"Критическая ошибка при парсинге {company_url}: {str(e)}")
                    
                    # Объединение базовых данных и деталей
                    company_data = {**base_data, **details}
                    
                    # ===== ЗАПИСЬ ДАННЫХ В CSV =====
                    with open(csv_filename, 'a', newline='', encoding='utf-8') as csvfile:
                        writer = csv.writer(csvfile, quoting=csv.QUOTE_ALL, quotechar='"')
                        writer.writerow([
                            company_data.get("Компания", ""),
                            company_data.get("Город", ""),
                            company_data.get("Домов", ""),
                            company_data.get("Адрес", ""),
                            company_data.get("Телефон", ""),
                            company_data.get("Наименование", ""),
                            company_data.get("Руководитель", ""),
                            company_data.get("Юридический адрес", ""),
                            company_data.get("Диспетчерская служба", ""),
                            company_data.get("Телефоны", ""),
                            company_data.get("Дома в управлении", ""),
                            company_data.get("ИНН", ""),
                            company_data.get("ОГРН", ""),
                            company_data.get("E-mail", "")
                        ])
                    
                    company_count += 1
                    print(f"Обработано компаний: {company_count} | Текущая: {company_name}")
            
            # ===== ПРОВЕРКА НАЛИЧИЯ СЛЕДУЮЩЕЙ СТРАНИЦЫ =====
            next_btn = soup.find("a", rel="next")
            if not next_btn:
                print("Достигнута последняя страница")
                break
                
            page_num += 1
            time.sleep(random.uniform(2, 5))  # Случайная задержка между страницами
            
    except Exception as e:
        print(f"Критическая ошибка: {str(e)}")
    finally:
        # ===== ЗАВЕРШЕНИЕ РАБОТЫ =====
        driver.quit()
        print(f"Парсинг завершен. Обработано компаний: {company_count}")
        print(f"Файл сохранен: {os.path.abspath(csv_filename)}")

if __name__ == "__main__":
    main()
