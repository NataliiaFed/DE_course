import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from pyspark.sql.functions import col, to_date, year, month, dayofmonth, regexp_replace
from awsglue.dynamicframe import DynamicFrame


glueContext = GlueContext(SparkContext.getOrCreate())

# read data from bronze tier
bronze_dyf = glueContext.create_dynamic_frame.from_options(
    connection_type="s3",
    connection_options={
        "paths": ["s3://natafed-data-platform-data-lake-321711906247/bronze/sales/"],
        "groupFiles": "inPartition"
    },
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
cleaned_df = (
    bronze_df.withColumn("price", regexp_replace(col("price"), "[^0-9.]", "").cast("decimal(10, 2)"))
    .withColumn("purchase_date", to_date(col("purchasedate"), "yyyy-M-d"))
    .withColumn("customer_id", col("customerid").cast("int"))
    .select("customer_id", "purchase_date", "product", "price")
)

# partitioning
partitioned_df = cleaned_df.withColumn("year", year(col("purchase_date"))) \
                           .withColumn("month", month(col("purchase_date"))) \
                           .withColumn("day", dayofmonth(col("purchase_date")))

# convert back to a DynamicFrame
silver_dyf = DynamicFrame.fromDF(partitioned_df, glueContext, "silver_dyf")

# write data to silver tier
glueContext.write_dynamic_frame.from_options(
    frame=silver_dyf,
    connection_type="s3",
    connection_options={
        "path": "s3://natafed-data-platform-data-lake-321711906247/silver/sales/",
        "partitionKeys": ["year", "month", "day"]
    },
    format="parquet",
    transformation_ctx="write_silver_dyf"
)