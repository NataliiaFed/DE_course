from datetime import datetime, timedelta
from airflow.models.dag import DAG
from airflow.providers.amazon.aws.operators.redshift_data import RedshiftDataOperator

# 1. removed check_s3_for_files :
# S3KeySensor as suggested in the template checks for a single file only but we need to check for multiple files in the prefix
# but S3PrefixSensor which checks for any is not supported (ImportError)
# 2. replaced S3ToRedshiftOperator with RedshiftDataOperator as S3ToRedshiftOperator seems to not be working with Redshift Serverless

AWS_CONN_ID = "aws_default"
S3_BUCKET = "natafed-data-platform-data-lake-321711906247"
REDSHIFT_SCHEMA = "natafed_schema"
REDSHIFT_CLUSTER_IDENTIFIER = "natafed-data-platform-workgroup"
REDSHIFT_IAM_ROLE = "arn:aws:iam::321711906247:role/natafed-data-platform-redshift-service-role"

CUSTOMERS_S3_KEY = "silver/customers/"
USER_PROFILES_S3_KEY = "silver/user_profiles/"

CREATE_CUSTOMERS_SILVER_TABLE = f"""
CREATE TABLE IF NOT EXISTS {REDSHIFT_SCHEMA}.customers_silver (
    id INT,
    first_name VARCHAR(256),
    last_name VARCHAR(256),
    email VARCHAR(256),
    registration_date DATE,
    state VARCHAR(256)
);
"""

CREATE_USER_PROFILES_SILVER_TABLE = f"""
CREATE TABLE IF NOT EXISTS {REDSHIFT_SCHEMA}.user_profiles_silver (
    email VARCHAR(256),
    full_name VARCHAR(256),
    state VARCHAR(256),
    phone_number VARCHAR(256),
    birth_date DATE
);
"""

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

default_args = {
    'owner': 'natafed',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    dag_id="enrich_user_profiles_pipeline",
    default_args=default_args,
    schedule_interval=None,
    start_date=datetime(2023, 1, 1),
    catchup=False,
    tags=["gold", "redshift", "enrichment"],
) as dag:
    # Create silver tables
    create_customers_silver_table = RedshiftDataOperator(
        task_id="create_customers_silver_table",
        sql=CREATE_CUSTOMERS_SILVER_TABLE,
        cluster_identifier=REDSHIFT_CLUSTER_IDENTIFIER,
        database="dev",
        aws_conn_id=AWS_CONN_ID
    )
    create_user_profiles_silver_table = RedshiftDataOperator(
        task_id="create_user_profiles_silver_table",
        sql=CREATE_USER_PROFILES_SILVER_TABLE,
        cluster_identifier=REDSHIFT_CLUSTER_IDENTIFIER,
        database="dev",
        aws_conn_id=AWS_CONN_ID
    )
    # Load data from S3 to Redshift silver tables
    customers_load_s3_to_redshift = RedshiftDataOperator(
        task_id='customers_load_s3_to_redshift',
        sql=f"""
            COPY {REDSHIFT_SCHEMA}.customers_silver
            FROM 's3://{S3_BUCKET}/{CUSTOMERS_S3_KEY}'
            IAM_ROLE '{REDSHIFT_IAM_ROLE}'
            FORMAT AS PARQUET;
        """,
        cluster_identifier=REDSHIFT_CLUSTER_IDENTIFIER,
        database="dev",
        aws_conn_id=AWS_CONN_ID
    )
    user_profiles_load_s3_to_redshift = RedshiftDataOperator(
        task_id='user_profiles_load_s3_to_redshift',
        sql=f"""
            COPY {REDSHIFT_SCHEMA}.user_profiles_silver
            FROM 's3://{S3_BUCKET}/{USER_PROFILES_S3_KEY}'
            IAM_ROLE '{REDSHIFT_IAM_ROLE}'
            FORMAT AS PARQUET;
        """,
        cluster_identifier=REDSHIFT_CLUSTER_IDENTIFIER,
        database="dev",
        aws_conn_id=AWS_CONN_ID
    )

    # Create gold table
    create_gold_table = RedshiftDataOperator(
        task_id="create_gold_table",
        sql=CREATE_GOLD_TABLE,
        cluster_identifier=REDSHIFT_CLUSTER_IDENTIFIER,
        database="dev",
        aws_conn_id=AWS_CONN_ID
    )
    # Transform and merge
    create_staging_table = RedshiftDataOperator(
        task_id="create_staging_table",
        sql=STAGING_TABLE_SQL,
        cluster_identifier=REDSHIFT_CLUSTER_IDENTIFIER,
        database="dev",
        aws_conn_id=AWS_CONN_ID
    )
    merge_data_to_gold = RedshiftDataOperator(
        task_id="merge_data_to_gold",
        sql=MERGE_SQL,
        cluster_identifier=REDSHIFT_CLUSTER_IDENTIFIER,
        database="dev",
        aws_conn_id=AWS_CONN_ID
    )
    # Dependencies
    create_customers_silver_table >> customers_load_s3_to_redshift
    create_user_profiles_silver_table >> user_profiles_load_s3_to_redshift
    [customers_load_s3_to_redshift, user_profiles_load_s3_to_redshift, create_gold_table] >> create_staging_table
    create_staging_table >> merge_data_to_gold
