import os
import json
import shutil
from typing import List, Dict, Any


def save_to_disk(json_content: List[Dict[str, Any]], path: str) -> None:
    """
    Save JSON content to local disk, overwriting existing files.

    :param json_content: list of records
    :param path: directory path to save file
    """
    # Якщо директорія існує, видаляємо її та її вміст
    if os.path.exists(path):
        shutil.rmtree(path)

    # Створити директорію заново
    os.makedirs(path, exist_ok=True)

    # Визначити шлях до файлу
    file_name = os.path.basename(path.rstrip("/"))  # Наприклад: 2022-08-09
    file_path = os.path.join(path, f"sales_{file_name}.json")

    # Записуємо дані у файл у форматі JSON
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(json_content, f, ensure_ascii=False, indent=2)