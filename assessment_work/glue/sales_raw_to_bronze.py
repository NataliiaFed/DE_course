import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from pyspark.sql.functions import col
from awsglue.dynamicframe import DynamicFrame


glueContext = GlueContext(SparkContext.getOrCreate())

# read data from Glue Data Catalog
raw_dyf = glueContext.create_dynamic_frame.from_catalog(
    database="natafed-data-platform_database",
    table_name="sales",
    transformation_ctx="raw_dyf"
)

# exit if the source is empty
if raw_dyf.count() == 0:
    print("Source table is empty. No data to process.")
    sys.exit(0)

# convert to Spark DataFrame to manipulate columns and types
raw_df = raw_dyf.toDF()

# cast all columns to STRING type
string_casted_df = raw_df.select(
    [col(c).cast("string") for c in raw_df.columns]
)

# convert back to a DynamicFrame
bronze_dyf = DynamicFrame.fromDF(
    string_casted_df, 
    glueContext, 
    "bronze_dyf"
)

# write data to bronze tier
glueContext.write_dynamic_frame.from_options(
    frame=bronze_dyf,
    connection_type="s3",
    connection_options={"path": "s3://natafed-data-platform-data-lake-321711906247/bronze/sales/"},
    format="parquet",
    transformation_ctx="write_bronze_dyf"
)