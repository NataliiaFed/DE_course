import os
import requests
from typing import List, Dict, Any
from dotenv import load_dotenv

load_dotenv()

API_URL = 'https://fake-api-vycpfa6oca-uc.a.run.app/sales'


def get_sales(date: str) -> List[Dict[str, Any]]:
    """
    Get data from sales API for specified date.

    :param date: date to retrieve the data from
    :return: list of records
    """
    token = os.getenv('AUTH_TOKEN')  # Отримуємо токен доступу з environment змінної
    if not token:
        raise EnvironmentError("AUTH_TOKEN environment variable is not set in .env.")

    headers = {"Authorization": token"}
    all_sales: List[Dict[str, Any]] = []  # Сюди будемо накопичувати всі результати зі сторінок
    page = 1  # Починаємо з першої сторінки

    while True:
        # Запит з параметрами дати і сторінки
        params = {"date": date, "page": page}
        response = requests.get(API_URL, headers=headers, params=params)

        # Якщо запит не успішний — зупиняємо виконання з поясненням
        if response.status_code != 200:
            raise requests.HTTPError(f"API request failed with status {response.status_code}: {response.text}")

        # Отримуємо дані з поточної сторінки
        data = response.json()

        # Якщо сторінка порожня — зупиняємо цикл
        if not data:
            break

        # Додаємо отримані дані до загального списку
        all_sales.extend(data)

        page += 1  # Переходимо до наступної сторінки

    return all_sales
