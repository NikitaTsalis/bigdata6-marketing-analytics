# %% [1] Import
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.ml.feature import StringIndexer, VectorAssembler, StandardScaler

MINIO_ENDPOINT = "minilab-minio:9000"
MINIO_ACCESS_KEY = "minioadmin"
MINIO_SECRET_KEY = "minioadmin123"
BUCKET_NAME      = "marketing-analytics"

BRONZE_PATH = f"s3a://{BUCKET_NAME}/bronze/marketing_campaign_dataset.csv"
SILVER_PATH = f"s3a://{BUCKET_NAME}/silver/marketing_cleaned/"
GOLD_PATH   = f"s3a://{BUCKET_NAME}/gold/marketing_features/"

spark = SparkSession.builder \
    .appName("MarketingAnalytics-Medallion") \
    .config("spark.hadoop.fs.s3a.endpoint", "http://minilab-minio:9000") \
    .config("spark.hadoop.fs.s3a.access.key", MINIO_ACCESS_KEY) \
    .config("spark.hadoop.fs.s3a.secret.key", MINIO_SECRET_KEY) \
    .config("spark.hadoop.fs.s3a.path.style.access", "true") \
    .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem") \
    .getOrCreate()

# ============================================================
# 🥉 BRONZE → baca raw data
# ============================================================
# %% [2] Load Bronze
df_bronze = spark.read \
    .option("header", "true") \
    .option("inferSchema", "true") \
    .csv(BRONZE_PATH)

print(f"🥉 [BRONZE] Raw data: {df_bronze.count()} baris")

# ============================================================
# 🥈 SILVER → cleaning & validasi
# ============================================================
# %% [3] Drop duplicates & null
important_cols = ["Impressions", "Clicks", "Leads", "Conversions",
                  "Cost_USD", "Revenue_USD", "Channel"]

df_silver = df_bronze \
    .dropDuplicates() \
    .dropna(subset=important_cols)

# Pastikan tipe data numerik benar
numeric_cols = ["Impressions", "Clicks", "Leads", "Conversions", "Cost_USD", "Revenue_USD"]
for col in numeric_cols:
    df_silver = df_silver.withColumn(col, F.col(col).cast("double"))

# Filter data yang tidak masuk akal (validasi bisnis)
df_silver = df_silver \
    .filter(F.col("Impressions") > 0) \
    .filter(F.col("Cost_USD") > 0) \
    .filter(F.col("Clicks") <= F.col("Impressions"))  # clicks gak mungkin > impressions

print(f"🥈 [SILVER] Setelah cleaning: {df_silver.count()} baris")

# Simpan Silver layer sebagai Parquet
df_silver.write.mode("overwrite").parquet(SILVER_PATH)
print(f"✅ [SILVER] Tersimpan di MinIO: {SILVER_PATH}")

# ============================================================
# 🥇 GOLD → feature engineering, siap ML
# ============================================================
# %% [4] Load Silver & Feature Engineering
df_silver = spark.read.parquet(SILVER_PATH)

df_gold = df_silver \
    .withColumn("CTR", F.col("Clicks") / F.col("Impressions")) \
    .withColumn("CVR", F.col("Conversions") / F.col("Clicks")) \
    .withColumn("CPC", F.col("Cost_USD") / F.col("Clicks")) \
    .withColumn("CPL", F.col("Cost_USD") / F.col("Leads")) \
    .withColumn("ROI", F.col("Revenue_USD") / F.col("Cost_USD")) \
    .withColumn("is_profitable", (F.col("ROI") >= 1.0).cast("int"))

# Handle inf & NaN dari pembagian
for c in ["CTR", "CVR", "CPC", "CPL"]:
    df_gold = df_gold.withColumn(
        c, F.when(F.col(c).isNull() | F.isnan(c), 0.0).otherwise(F.col(c))
    )

# %% [5] Encode & Scale
indexer = StringIndexer(inputCol="Channel", outputCol="Channel_Index")
df_gold = indexer.fit(df_gold).transform(df_gold)

feature_cols = ["Impressions", "Clicks", "Leads", "Conversions",
                "Cost_USD", "CTR", "CPC", "CPL", "CVR", "Channel_Index"]

assembler = VectorAssembler(inputCols=feature_cols, outputCol="features_raw")
df_gold = assembler.transform(df_gold)

scaler = StandardScaler(inputCol="features_raw", outputCol="features",
                        withMean=True, withStd=True)
df_gold = scaler.fit(df_gold).transform(df_gold)

print(f"🥇 [GOLD] Feature engineered: {df_gold.count()} baris")

# Simpan Gold layer
df_gold.write.mode("overwrite").parquet(GOLD_PATH)
print(f"✅ [GOLD] Tersimpan di MinIO: {GOLD_PATH}")

# %% [6] Train/Test split dari Gold
train_df, test_df = df_gold.randomSplit([0.8, 0.2], seed=42)
train_df.write.mode("overwrite").parquet(f"s3a://{BUCKET_NAME}/gold/train/")
test_df.write.mode("overwrite").parquet(f"s3a://{BUCKET_NAME}/gold/test/")

print(f"✅ Train: {train_df.count()} | Test: {test_df.count()}")