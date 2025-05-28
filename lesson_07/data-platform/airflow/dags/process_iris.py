from airflow import DAG
from datetime import timedelta
from datetime import datetime
from airflow.operators.python import PythonOperator
from airflow.utils.email import send_email
import os
import sys

# Add the plugins directory to Python path
sys.path.append(os.path.join(os.getenv('AIRFLOW_HOME'), 'plugins'))
from dbt_operator import DbtOperator

# Import the training function
from python_scripts.train_model import process_iris_data

# Get environment variables
ANALYTICS_DB = os.getenv('ANALYTICS_DB', 'analytics')
PROJECT_DIR = os.getenv('AIRFLOW_HOME')+"/dags/dbt/homework"
PROFILE = 'homework'

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email': ['nataliiafedorets@gmail.com'],
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'process_iris',
    default_args=default_args,
    description='Process Iris dataset and train ML model',
    schedule_interval='0 1 * * *',  # 1 AM Kyiv time (GMT+3)
    start_date=datetime(2025,4,22),
    end_date=datetime(2025,4,24),
    catchup=True,
    tags=['iris', 'ml', 'dbt'],
)

# Function to send success email
def send_success_email(**context):
    execution_date = context['execution_date']
    send_email(
        to=default_args['email'],
        subject=f'Success: Iris Processing DAG - {execution_date}',
        html_content=f"""
        <h3>Iris Processing DAG completed successfully</h3>
        """,
        mime_charset='utf-8'
    )

# Environment variables to pass to dbt
env_vars = {
    'ANALYTICS_DB': ANALYTICS_DB,
    'DBT_PROFILE': PROFILE
}

# Variables to pass to dbt
dbt_vars = {
    'is_test': False,
    'data_date': '{{ ds }}',  # Uses Airflow's ds (execution date) macro
}

# Task 1: Run dbt seed to load CSV data
dbt_seed = DbtOperator(
    task_id='dbt_seed',
    command='seed',
    profile=PROFILE,
    project_dir=PROJECT_DIR,
    env_vars=env_vars,
    vars=dbt_vars,
    dag=dag,
)

# Task 2: Run dbt transformation
dbt_transform = DbtOperator(
    task_id='dbt_transform',
    command='run',
    profile=PROFILE,
    project_dir=PROJECT_DIR,
    models=['mart.iris_processed'],
    fail_fast=True,
    env_vars=env_vars,
    vars=dbt_vars,
    dag=dag,
)

# Task 3: Train the model
train_model = PythonOperator(
    task_id='train_model',
    python_callable=process_iris_data,
    provide_context=True,
    dag=dag,
)

# Task 4: Send success email
send_email = PythonOperator(
    task_id='send_success_email',
    python_callable=send_success_email,
    provide_context=True,
    dag=dag,
)

# Set task dependencies
dbt_seed >> dbt_transform >> train_model >> send_email