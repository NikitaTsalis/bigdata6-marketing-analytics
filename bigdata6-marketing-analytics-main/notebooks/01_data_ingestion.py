# %% [1] Import
from minio import Minio
from minio.error import S3Error
from pyspark.sql import SparkSession
from pyspark.sql import functions as F

MINIO_ENDPOINT = "minilab-minio:9000"
MINIO_ACCESS_KEY = "minioadmin"
MINIO_SECRET_KEY = "minioadmin123"
BUCKET_NAME      = "marketing-analytics"
LOCAL_CSV = "/app/data/raw/marketing_campaign_performance_10000.csv"

# Path per layer
BRONZE_PATH = f"s3a://{BUCKET_NAME}/bronze/marketing_campaign_dataset.csv"
SILVER_PATH = f"s3a://{BUCKET_NAME}/silver/marketing_cleaned/"
GOLD_PATH   = f"s3a://{BUCKET_NAME}/gold/marketing_features/"

# %% [2] Upload CSV mentah ke Bronze (via MinIO client)
client = Minio(MINIO_ENDPOINT, access_key=MINIO_ACCESS_KEY,
               secret_key=MINIO_SECRET_KEY, secure=False)

if not client.bucket_exists(BUCKET_NAME):
    client.make_bucket(BUCKET_NAME)
    print(f"✅ Bucket '{BUCKET_NAME}' dibuat")

try:
    client.fput_object(BUCKET_NAME, "bronze/marketing_campaign_dataset.csv", LOCAL_CSV)
    print(f"✅ [BRONZE] CSV berhasil diupload ke MinIO")
except S3Error as e:
    print(f"❌ Error: {e}")

# %% [3] Spark Session
spark = SparkSession.builder \
    .appName("MarketingAnalytics-Medallion") \
    .config("spark.hadoop.fs.s3a.endpoint", "http://minilab-minio:9000") \
    .config("spark.hadoop.fs.s3a.access.key", MINIO_ACCESS_KEY) \
    .config("spark.hadoop.fs.s3a.secret.key", MINIO_SECRET_KEY) \
    .config("spark.hadoop.fs.s3a.path.style.access", "true") \
    .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem") \
    .getOrCreate()

# %% [4] Baca Bronze layer
df_bronze = spark.read \
    .option("header", "true") \
    .option("inferSchema", "true") \
    .csv(BRONZE_PATH)

print(f"🥉 [BRONZE] {df_bronze.count()} baris, {len(df_bronze.columns)} kolom")
df_bronze.printSchema()
df_bronze.show(5)