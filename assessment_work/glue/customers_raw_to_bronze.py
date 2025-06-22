import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext


glueContext = GlueContext(SparkContext.getOrCreate())

# # read data from Glue Data Catalog
# raw_dyf = glueContext.create_dynamic_frame.from_catalog(
#     database="natafed-data-platform_database",
#     table_name="customers",
#     transformation_ctx="raw_dyf"
# )

# DEBUGGING: Read directly from S3 to isolate catalog issues
raw_dyf = glueContext.create_dynamic_frame.from_options(
    connection_type="s3",
    connection_options={
        "paths": ["s3://natafed-data-platform-data-lake-321711906247/raw/customers/"],
        "recurse": True,
    },
    format="csv",
    format_options={"withHeader": True},
    transformation_ctx="raw_dyf_from_s3",
)

# exit if the source is empty
if raw_dyf.count() == 0:
    print("Source table is empty. No data to process.")
    sys.exit(0)

# write data to bronze tier
glueContext.write_dynamic_frame.from_options(
    frame=raw_dyf,
    connection_type="s3",
    connection_options={"path": "s3://natafed-data-platform-data-lake-321711906247/bronze/customers/"},
    format="parquet",
    transformation_ctx="write_bronze_dyf"
)