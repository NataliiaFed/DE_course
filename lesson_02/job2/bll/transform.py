import os
import json
import shutil
from typing import List, Dict
from fastavro import writer, parse_schema


def transform_json_to_avro(raw_dir: str, stg_dir: str) -> None:
    """
    Transform JSON files from raw_dir to AVRO format in stg_dir.

    :param raw_dir: source directory with JSON files
    :param stg_dir: destination directory to save AVRO files
    """
    # Очищення директорії
    if os.path.exists(stg_dir):
        shutil.rmtree(stg_dir)
    os.makedirs(stg_dir, exist_ok=True)

    for file_name in os.listdir(raw_dir):
        # Ігноруємо все, що не .json
        if not file_name.endswith('.json'):
            continue

        # Читаємо JSON файл
        raw_path = os.path.join(raw_dir, file_name)
        with open(raw_path, "r", encoding="utf-8") as f:
            records: List[Dict] = json.load(f)

        # Якщо файл порожній — пропускаємо
        if not records:
            continue

        # Автоматично будуємо Avro-схему
        schema_fields = [{"name": key, "type": "string"} for key in records[0].keys()]
        avro_schema = {
            "doc": "Auto-generated sales schema",
            "name": "Sale",
            "namespace": "sales",
            "type": "record",
            "fields": schema_fields
        }

        # спершу розпарсити схему
        parsed_schema = parse_schema(avro_schema)

        # cтворюємо шлях до нового .avro файлу
        avro_file_name = file_name.replace('.json', '.avro')
        avro_path = os.path.join(stg_dir, avro_file_name)

        # pаписуємо Avro-файл
        with open(avro_path, "wb") as out:
            writer(out, parsed_schema, records)