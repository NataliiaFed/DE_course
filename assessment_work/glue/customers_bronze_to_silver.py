import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from pyspark.sql.functions import col, to_date
from awsglue.dynamicframe import DynamicFrame


glueContext = GlueContext(SparkContext.getOrCreate())

# read data from bronze tier
bronze_dyf = glueContext.create_dynamic_frame.from_options(
    connection_type="s3",
    connection_options={"paths": ["s3://natafed-data-platform-data-lake-321711906247/bronze/customers/"]},
    format="parquet",
    transformation_ctx="bronze_dyf"
)

# exit if the source is empty
if bronze_dyf.count() == 0:
    print("No data in bronze zone. Exiting.")
    sys.exit(0)

# convert to Spark DataFrame for data manipulation
bronze_df = bronze_dyf.toDF()

# cleaning and transformation
cleaned_df = bronze_df.dropDuplicates(["Id"]).select(
    col("Id").cast("int").alias("id"),
    col("FirstName").cast("string").alias("first_name"),
    col("LastName").cast("string").alias("last_name"),
    col("Email").cast("string").alias("email"),
    to_date(col("RegistrationDate"), "yyyy-M-d").alias("registration_date"),
    col("State").cast("string").alias("state"),
)

# convert back to a DynamicFrame
silver_dyf = DynamicFrame.fromDF(cleaned_df, glueContext, "silver_dyf")

# write data to silver tier
glueContext.write_dynamic_frame.from_options(
    frame=silver_dyf,
    connection_type="s3",
    connection_options={"path": "s3://natafed-data-platform-data-lake-321711906247/silver/customers/"},
    format="parquet",
    transformation_ctx="write_silver_dyf",
)