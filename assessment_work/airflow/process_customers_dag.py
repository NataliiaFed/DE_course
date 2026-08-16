from datetime import datetime
from airflow.models.dag import DAG
from airflow.providers.amazon.aws.operators.glue import GlueJobOperator

PROJECT_NAME = "natafed"
DL_BUCKET_NAME = "natafed-data-platform-data-lake-321711906247"
GLUE_SCRIPT_LOCATION_PREFIX = "scripts/glue/"
RAW_TO_BRONZE_SCRIPT_PATH = f"s3://{DL_BUCKET_NAME}/{GLUE_SCRIPT_LOCATION_PREFIX}customers_raw_to_bronze.py"
BRONZE_TO_SILVER_SCRIPT_PATH = f"s3://{DL_BUCKET_NAME}/{GLUE_SCRIPT_LOCATION_PREFIX}customers_bronze_to_silver.py"

default_args = {
    'owner': 'airflow',
    'start_date': datetime(2023, 1, 1),
    'retries': 1,
    'aws_conn_id': 'aws_default'
}

with DAG(
    dag_id="process_customers_pipeline",
    default_args=default_args,
    schedule_interval='@daily',
    catchup=False,
    tags=["data_processing", "glue", "sales"],
) as dag:
    
    raw_to_bronze = GlueJobOperator(
        task_id="customers_raw_to_bronze",
        job_name="natafed-customers-raw-to-bronze",
        script_location=RAW_TO_BRONZE_SCRIPT_PATH,
        s3_bucket=DL_BUCKET_NAME,
        iam_role_name="natafed-data-platform-glue-service-role",
        region_name="eu-north-1",
        create_job_kwargs={"GlueVersion": "3.0", "WorkerType": "G.1X", "NumberOfWorkers": 4},
    )

    bronze_to_silver = GlueJobOperator(
        task_id="customers_bronze_to_silver",
        job_name="natafed-customers-bronze-to-silver",
        script_location=BRONZE_TO_SILVER_SCRIPT_PATH,
        s3_bucket=DL_BUCKET_NAME,
        iam_role_name="natafed-data-platform-glue-service-role",
        region_name="eu-north-1",
        create_job_kwargs={"GlueVersion": "3.0", "WorkerType": "G.1X", "NumberOfWorkers": 4},
    )

    raw_to_bronze >> bronze_to_silver