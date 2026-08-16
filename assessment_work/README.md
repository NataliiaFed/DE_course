# Final Project

## Project Description

This project implements a modern data pipeline for a company engaged in consumer electronics sales. The goal is to build a platform for integrating, cleaning, transforming, and enriching data from various sources for subsequent analytics. The project is built on AWS (S3, Glue, Redshift, Airflow).

## Solution Architecture

- **S3** — storage for raw, bronze, and silver data
- **Glue** — ETL data processing (raw → bronze → silver)
- **Redshift** — storage and processing of analytical (gold) data
- **Airflow** — orchestration of pipelines (DAGs)

## Data Sources
- **customers** — CSV, daily dump (full dump for each day)
- **sales** — CSV, partitioned by date
- **user_profiles** — JSONLines, high quality data

## Pipeline Structure (DAGs)

1. **process_sales_pipeline** — ETL for sales (raw → bronze → silver, Glue)
2. **process_customers_pipeline** — ETL for customers (raw → bronze → silver, Glue)
3. **process_user_profiles_pipeline** — ETL for user_profiles (raw → silver, Glue)
4. **enrich_user_profiles_pipeline** — enrichment of customers with user_profiles data, write to gold (Redshift)

### Why This DAG Structure?
- **Modularity**: Each pipeline is responsible for a separate source/stage, which simplifies maintenance, debugging, and reuse.
- **Flexibility**: Some pipelines (e.g., user_profiles, enrichment) are triggered manually, others run on schedule. This prevents blocking updates to one data source due to another.
- **Transparency**: It's easy to track the status of each stage separately and quickly identify issues.
- **Scalability**: When adding new sources, you only need to add a new DAG without modifying existing ones.

> Combining pipelines into fewer DAGs would complicate monitoring, reuse, and the flexibility of running individual stages.

## Table Structure

- **Bronze**: maximally similar to raw (original column names, all types are STRING). This simplifies auditing and error detection in raw data.
- **Silver**: cleaned, normalized data with correct types, renamed columns, partitioning (for sales). This optimizes analytics and preparation for enrichment.
- **Gold**: enriched data (user_profiles_enriched) — result of integrating customers and user_profiles, with full names, states, age, phone numbers, etc. Designed for analytics.

### Why This Approach?
- **Bronze** — for transparency and reproducibility (raw → bronze — minimum transformations)
- **Silver** — for analytics (clean, convenient for BI/SQL)
- **Gold** — for business queries, enriched with all available attributes

## Orchestration and Automation
- All ETL and enrichment processes are managed through Apache Airflow (AWS MWAA)
- DAGs use GlueJobOperator (for Glue) and RedshiftDataOperator (for Redshift)
- Data automatically flows between layers (raw → bronze → silver → gold)

## How to Deploy
1. Deploy CloudFormation stack from assessment_work/DataPlatform.yml
2. Upload data to S3 bucket (raw)
3. Run Glue Crawler to create tables in Data Catalog
4. Airflow DAGs automatically pick up new data and run ETL

## Author
- Nataliia Fedorets