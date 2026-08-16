import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from pyspark.sql.functions import col, to_date
from awsglue.dynamicframe import DynamicFrame


glueContext = GlueContext(SparkContext.getOrCreate())

# read data from Glue Data Catalog
raw_dyf = glueContext.create_dynamic_frame.from_catalog(
    database="natafed-data-platform_database",
    table_name="user_profiles",
    transformation_ctx="raw_dyf"
)

# exit if the source is empty
if raw_dyf.count() == 0:
    print("Source table is empty. No data to process.")
    sys.exit(0)

# convert to Spark DataFrame for data manipulation
raw_df = raw_dyf.toDF()

# cleaning and transformation
cleaned_df = raw_df.select(
    col("email").cast("string").alias("email"),
    col("full_name").cast("string").alias("full_name"),
    col("state").cast("string").alias("state"),
    to_date(col("birth_date"), "yyyy-MM-dd").alias("birth_date"),
    col("phone_number").cast("string").alias("phone_number")
)

# convert back to a DynamicFrame
silver_dyf = DynamicFrame.fromDF(cleaned_df, glueContext, "silver_dyf")

# write data to silver tier
glueContext.write_dynamic_frame.from_options(
    frame=silver_dyf,
    connection_type="s3",
    connection_options={"path": "s3://natafed-data-platform-data-lake-321711906247/silver/user_profiles/"},
    format="parquet",
    transformation_ctx="write_silver_dyf"
) 