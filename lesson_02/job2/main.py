"""
This file contains the controller for transforming JSON to AVRO
"""

from flask import Flask, request
from flask import typing as flask_typing

from lesson_02.job2.bll.transform import transform_json_to_avro

app = Flask(__name__)


@app.route('/', methods=['POST'])
def main() -> flask_typing.ResponseReturnValue:
    """
    Controller for transforming JSON to AVRO.

    Proposed POST body in JSON:
    {
      "raw_dir": "/path/to/my_dir/raw/sales/2022-08-09",
      "stg_dir": "/path/to/my_dir/stg/sales/2022-08-09"
    }
    """
    input_data = request.json
    if not input_data:
        return {"message": "Missing JSON body."}, 400

    raw_dir = input_data.get("raw_dir")
    stg_dir = input_data.get("stg_dir")

    if not raw_dir or not stg_dir:
        return {"message": "raw_dir and stg_dir are required."}, 400

    try:
        transform_json_to_avro(raw_dir=raw_dir, stg_dir=stg_dir)
    except Exception as e:
        return {"message": f"Error occurred: {str(e)}"}, 500

    return {"message": "Files transformed successfully."}, 201


if __name__ == "__main__":
    app.run(debug=True, host="localhost", port=8082)