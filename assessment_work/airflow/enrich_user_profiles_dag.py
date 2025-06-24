from datetime import datetime, timedelta
from airflow.models.dag import DAG
from airflow.providers.amazon.aws.operators.redshift_sql import RedshiftSQLOperator
from airflow.providers.amazon.aws.transfers.s3_to_redshift import S3ToRedshiftOperator
from airflow.providers.amazon.aws.sensors.s3 import S3KeySensor

AWS_CONN_ID = "aws_default"
REDSHIFT_CONN_ID = "redshift_default"
S3_BUCKET = "natafed-data-platform-data-lake-321711906247"
REDSHIFT_SCHEMA = "natafed_schema"

CUSTOMERS_S3_KEY = "silver/customers/"
USER_PROFILES_S3_KEY = "silver/user_profiles/"

default_args = {
    'owner': 'natafed',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

CREATE_GOLD_TABLE = f"""
CREATE TABLE IF NOT EXISTS {REDSHIFT_SCHEMA}.user_profiles_enriched (
    client_id INT PRIMARY KEY,
    first_name VARCHAR(256),
    last_name VARCHAR(256),
    email VARCHAR(256),
    registration_date DATE,
    state VARCHAR(256),
    phone_number VARCHAR(256),
    birth_date DATE
);
"""

STAGING_TABLE_SQL = f"""
DROP TABLE IF EXISTS {REDSHIFT_SCHEMA}.user_profiles_enriched_staging;
CREATE TABLE {REDSHIFT_SCHEMA}.user_profiles_enriched_staging AS
SELECT
    c.id AS client_id,
    COALESCE(c.first_name, 
             CASE 
                 WHEN p.full_name IS NOT NULL THEN 
                     TRIM(SPLIT_PART(p.full_name, ' ', 0))
                 ELSE NULL 
             END) AS first_name,
    COALESCE(c.last_name, 
             CASE 
                 WHEN p.full_name IS NOT NULL THEN 
                     TRIM(SPLIT_PART(p.full_name, ' ', 1))
                 ELSE NULL 
             END) AS last_name,
    c.email,
    c.registration_date,
    COALESCE(c.state, p.state) AS state,
    p.phone_number,
    p.birth_date
FROM {REDSHIFT_SCHEMA}.customers_silver c
LEFT JOIN {REDSHIFT_SCHEMA}.user_profiles_silver p ON c.email = p.email;
"""

MERGE_SQL = f"""
MERGE INTO {REDSHIFT_SCHEMA}.user_profiles_enriched AS target
USING {REDSHIFT_SCHEMA}.user_profiles_enriched_staging AS source
ON target.client_id = source.client_id
WHEN MATCHED THEN
    UPDATE SET
        first_name = source.first_name,
        last_name = source.last_name,
        email = source.email,
        registration_date = source.registration_date,
        state = source.state,
        phone_number = source.phone_number,
        birth_date = source.birth_date
WHEN NOT MATCHED THEN
    INSERT (client_id, first_name, last_name, email, registration_date, state, phone_number, birth_date) 
    VALUES (source.client_id, source.first_name, source.last_name, source.email, source.registration_date, source.state, source.phone_number, source.birth_date);
"""

with DAG(
    dag_id="enrich_user_profiles_pipeline",
    default_args=default_args,
    schedule_interval=None,
    start_date=datetime(2023, 1, 1),
    catchup=False,
    tags=["gold", "redshift", "enrichment"],
) as dag:
    
    # check if silver data is available
    check_customers_silver_data = S3KeySensor(
        task_id='check_customers_silver_data',
        bucket_name=S3_BUCKET,
        bucket_key=CUSTOMERS_S3_KEY,
        aws_conn_id=AWS_CONN_ID,
    )

    check_user_profiles_silver_data = S3KeySensor(
        task_id='check_user_profiles_silver_data',
        bucket_name=S3_BUCKET,
        bucket_key=USER_PROFILES_S3_KEY,
        aws_conn_id=AWS_CONN_ID,
    )

    # create gold table
    create_gold_table = RedshiftSQLOperator(
        task_id="create_gold_table", 
        sql=CREATE_GOLD_TABLE, 
        redshift_conn_id=REDSHIFT_CONN_ID
    )

    # load data from S3 to Redshift
    customers_load_s3_to_redshift = S3ToRedshiftOperator(
        task_id='customers_load_s3_to_redshift',
        s3_bucket=S3_BUCKET,
        s3_key=CUSTOMERS_S3_KEY,
        schema=REDSHIFT_SCHEMA,
        table='customers_silver',
        copy_options=["FORMAT AS PARQUET"],
        redshift_conn_id=REDSHIFT_CONN_ID,
    )

    user_profiles_load_s3_to_redshift = S3ToRedshiftOperator(
        task_id='user_profiles_load_s3_to_redshift',
        s3_bucket=S3_BUCKET,
        s3_key=USER_PROFILES_S3_KEY,
        schema=REDSHIFT_SCHEMA,
        table='user_profiles_silver',
        copy_options=["FORMAT AS PARQUET"],
        redshift_conn_id=REDSHIFT_CONN_ID,
    )

    # transform and merge
    create_staging_table = RedshiftSQLOperator(
        task_id="create_staging_table", 
        sql=STAGING_TABLE_SQL, 
        redshift_conn_id=REDSHIFT_CONN_ID
    )

    merge_data_to_gold = RedshiftSQLOperator(
        task_id="merge_data_to_gold", 
        sql=MERGE_SQL, 
        redshift_conn_id=REDSHIFT_CONN_ID
    )

    # dependencies
    check_customers_silver_data >> customers_load_s3_to_redshift
    check_user_profiles_silver_data >> user_profiles_load_s3_to_redshift
    
    [customers_load_s3_to_redshift, user_profiles_load_s3_to_redshift, create_gold_table] >> create_staging_table
    
    create_staging_table >> merge_data_to_gold
