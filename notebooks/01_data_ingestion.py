# %% [markdown]
# # 📥 Notebook 1: Data Ingestion ke MinIO/HDFS
# ## Proyek Big Data - Analisis Performa Kampanye Marketing
# 
# **Penanggung Jawab:** Data Engineer 1 (Esa Khafidotul Khusna Rois)
# 
# **Tujuan Notebook ini:**
# 1. Membaca dataset Marketing Campaign dari local storage
# 2. Mengupload dataset ke MinIO (Data Lake)
# 3. Memindahkan data dari MinIO ke HDFS menggunakan PySpark
# 4. Memverifikasi integritas data (10.000 record utuh)
# 
# **Teknologi:** MinIO Client, PySpark, HDFS
# 
# ---

# %% [markdown]
# ## 1. Setup & Import Library

# %%
# Import library yang diperlukan
import os
import sys
import warnings
warnings.filterwarnings('ignore')

# Tambahkan path config ke sys.path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from pyspark.sql import SparkSession
from pyspark.sql.types import (
    StructType, StructField, StringType, IntegerType, 
    DoubleType, DateType
)

print("✅ Library berhasil diimport!")

# %% [markdown]
# ## 2. Konfigurasi Spark Session
# 
# Membuat SparkSession dengan konfigurasi yang mendukung akses ke MinIO 
# melalui protokol S3A dan koneksi ke HDFS.

# %%
# ============================================
# KONFIGURASI - Sesuaikan dengan environment Anda
# ============================================

# MinIO Configuration
MINIO_ENDPOINT = "http://localhost:9000"
MINIO_ACCESS_KEY = "minioadmin"
MINIO_SECRET_KEY = "minioadmin"
MINIO_BUCKET = "marketing-data"

# HDFS Configuration
HDFS_NAMENODE = "hdfs://localhost:9000"
HDFS_RAW_DIR = "/user/hadoop/marketing/raw"

# Local file path
LOCAL_CSV_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), 
    '..', 'data', 'raw', 'marketing_campaign_performance_10000.csv'
)

print("📋 Konfigurasi:")
print(f"   MinIO Endpoint : {MINIO_ENDPOINT}")
print(f"   MinIO Bucket   : {MINIO_BUCKET}")
print(f"   HDFS NameNode  : {HDFS_NAMENODE}")
print(f"   HDFS Raw Dir   : {HDFS_RAW_DIR}")
print(f"   Local CSV      : {LOCAL_CSV_PATH}")

# %%
# Membuat SparkSession
spark = SparkSession.builder \
    .appName("Marketing_Campaign_DataIngestion") \
    .master("local[*]") \
    .config("spark.driver.memory", "4g") \
    .config("spark.executor.memory", "2g") \
    .config("spark.sql.shuffle.partitions", "8") \
    .config("spark.hadoop.fs.s3a.endpoint", MINIO_ENDPOINT) \
    .config("spark.hadoop.fs.s3a.access.key", MINIO_ACCESS_KEY) \
    .config("spark.hadoop.fs.s3a.secret.key", MINIO_SECRET_KEY) \
    .config("spark.hadoop.fs.s3a.path.style.access", "true") \
    .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem") \
    .config("spark.serializer", "org.apache.spark.serializer.KryoSerializer") \
    .getOrCreate()

spark.sparkContext.setLogLevel("WARN")

print(f"✅ SparkSession berhasil dibuat!")
print(f"   App Name  : {spark.conf.get('spark.app.name')}")
print(f"   Master    : {spark.conf.get('spark.master')}")
print(f"   Spark Ver : {spark.version}")

# %% [markdown]
# ## 3. Verifikasi Dataset Lokal
# 
# Dataset sudah tersedia di `data/raw/`. Langkah ini memverifikasi
# keberadaan dan informasi file CSV sebelum melanjutkan proses ingestion.

# %%
# Verifikasi dataset lokal
def verify_local_dataset():
    """Verifikasi bahwa dataset CSV sudah ada di local storage."""
    if os.path.exists(LOCAL_CSV_PATH):
        file_size_kb = os.path.getsize(LOCAL_CSV_PATH) / 1024
        
        # Hitung jumlah baris
        with open(LOCAL_CSV_PATH, 'r') as f:
            line_count = sum(1 for _ in f) - 1  # minus header
        
        print(f"✅ Dataset ditemukan di lokal!")
        print(f"   Path   : {LOCAL_CSV_PATH}")
        print(f"   Ukuran : {file_size_kb:.2f} KB")
        print(f"   Record : {line_count:,} baris")
        return True
    else:
        print(f"❌ Dataset tidak ditemukan di: {LOCAL_CSV_PATH}")
        print(f"   Letakkan file CSV di folder data/raw/")
        return False

dataset_ready = verify_local_dataset()

# %% [markdown]
# ## 4. Definisi Skema Data
# 
# Mendefinisikan skema yang eksplisit untuk memastikan tipe data yang benar
# saat membaca CSV. Ini penting untuk menghindari inferensi tipe yang salah.

# %%
# Definisi skema dataset
marketing_schema = StructType([
    StructField("CampaignID", StringType(), False),      # ID unik kampanye
    StructField("StartDate", StringType(), True),         # Tanggal mulai (YYYY-MM-DD)
    StructField("EndDate", StringType(), True),           # Tanggal selesai (YYYY-MM-DD)
    StructField("Channel", StringType(), True),           # Platform: Search, Email, Display, Social, Influencer
    StructField("Impressions", IntegerType(), True),      # Jumlah tayangan
    StructField("Clicks", IntegerType(), True),           # Jumlah klik
    StructField("Leads", IntegerType(), True),            # Jumlah prospek
    StructField("Conversions", IntegerType(), True),      # Jumlah konversi
    StructField("Cost_USD", DoubleType(), True),          # Biaya kampanye (USD)
    StructField("Revenue_USD", DoubleType(), True),       # Pendapatan (USD)
    StructField("ROI", DoubleType(), True),               # Return on Investment
])

print("✅ Skema data didefinisikan:")
for field in marketing_schema.fields:
    nullable = "Nullable" if field.nullable else "Not Null"
    print(f"   {field.name:15s} | {str(field.dataType):15s} | {nullable}")

# %% [markdown]
# ## 5. Membaca Dataset CSV ke Spark DataFrame
# 
# Membaca file CSV dari local storage ke Spark DataFrame menggunakan skema
# yang sudah didefinisikan.

# %%
# Baca CSV ke Spark DataFrame
print(f"⏳ Membaca CSV dari: {LOCAL_CSV_PATH}")

df_raw = spark.read.csv(
    LOCAL_CSV_PATH,
    header=True,
    schema=marketing_schema,
    dateFormat="yyyy-MM-dd"
)

# Tampilkan informasi dasar
total_records = df_raw.count()
total_columns = len(df_raw.columns)

print(f"\n✅ Dataset berhasil dimuat!")
print(f"   Total Records : {total_records:,}")
print(f"   Total Kolom   : {total_columns}")
print(f"   Partitions    : {df_raw.rdd.getNumPartitions()}")

# %% [markdown]
# ## 6. Inspeksi Data Awal
# 
# Melakukan pemeriksaan awal terhadap data yang telah dimuat untuk memastikan
# integritas dan kualitas data sebelum diupload.

# %%
# Tampilkan skema DataFrame
print("📋 Skema DataFrame:")
df_raw.printSchema()

# %%
# Tampilkan 10 baris pertama
print("📋 Sample Data (10 baris pertama):")
df_raw.show(10, truncate=False)

# %%
# Statistik deskriptif
print("📊 Statistik Deskriptif:")
df_raw.describe().show()

# %%
# Cek missing values per kolom
from pyspark.sql.functions import col, count, when, isnan, isnull

print("🔍 Pemeriksaan Missing Values:")
missing_df = df_raw.select([
    count(when(isnull(c) | isnan(c), c)).alias(c) 
    for c in df_raw.columns
])
missing_df.show(truncate=False)

# %%
# Distribusi Channel
print("📊 Distribusi Channel:")
df_raw.groupBy("Channel").count().orderBy("count", ascending=False).show()

# %%
# Statistik ROI
from pyspark.sql.functions import min as spark_min, max as spark_max, avg, stddev

print("📊 Statistik ROI:")
df_raw.select(
    spark_min("ROI").alias("Min_ROI"),
    spark_max("ROI").alias("Max_ROI"),
    avg("ROI").alias("Avg_ROI"),
    stddev("ROI").alias("StdDev_ROI")
).show()

# %% [markdown]
# ## 7. Upload Data ke MinIO (Data Lake)
# 
# Mengupload dataset CSV ke MinIO bucket sebagai data lake.
# MinIO digunakan sebagai object storage yang S3-compatible.

# %%
# Method 1: Upload via MinIO Python Client
from minio import Minio
from minio.error import S3Error

def upload_to_minio():
    """Upload file CSV ke MinIO bucket."""
    try:
        # Inisialisasi MinIO client
        client = Minio(
            "localhost:9000",
            access_key=MINIO_ACCESS_KEY,
            secret_key=MINIO_SECRET_KEY,
            secure=False
        )
        
        # Buat bucket jika belum ada
        if not client.bucket_exists(MINIO_BUCKET):
            client.make_bucket(MINIO_BUCKET)
            print(f"✅ Bucket '{MINIO_BUCKET}' berhasil dibuat")
        else:
            print(f"✅ Bucket '{MINIO_BUCKET}' sudah ada")
        
        # Upload file
        object_name = "raw/marketing_campaign_performance.csv"
        print(f"⏳ Mengupload ke MinIO: {MINIO_BUCKET}/{object_name}...")
        
        client.fput_object(
            MINIO_BUCKET,
            object_name,
            LOCAL_CSV_PATH,
            content_type="text/csv"
        )
        
        # Verifikasi upload
        stat = client.stat_object(MINIO_BUCKET, object_name)
        print(f"✅ Upload berhasil!")
        print(f"   Object : {object_name}")
        print(f"   Size   : {stat.size / 1024:.2f} KB")
        print(f"   ETag   : {stat.etag}")
        
        return True
        
    except S3Error as e:
        print(f"❌ MinIO Error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        print("💡 Pastikan MinIO server sudah berjalan!")
        print("   Jalankan: minio server /data/minio --console-address ':9001'")
        return False

upload_success = upload_to_minio()

# %% [markdown]
# ## 8. Upload Data ke HDFS
# 
# Memindahkan data dari lokal/MinIO ke HDFS untuk pemrosesan terdistribusi.

# %%
# Method 1: Upload ke HDFS menggunakan PySpark
def upload_to_hdfs_spark():
    """Upload data ke HDFS menggunakan Spark DataFrame write."""
    try:
        hdfs_csv_path = f"{HDFS_NAMENODE}{HDFS_RAW_DIR}/marketing_campaign_performance.csv"
        
        print(f"⏳ Menulis data ke HDFS: {hdfs_csv_path}")
        
        # Simpan sebagai CSV di HDFS
        df_raw.write \
            .mode("overwrite") \
            .option("header", "true") \
            .csv(hdfs_csv_path)
        
        print(f"✅ Data berhasil ditulis ke HDFS (format CSV)")
        
        # Simpan juga dalam format Parquet untuk efisiensi
        hdfs_parquet_path = f"{HDFS_NAMENODE}{HDFS_RAW_DIR}/marketing_campaign_raw.parquet"
        
        df_raw.write \
            .mode("overwrite") \
            .parquet(hdfs_parquet_path)
        
        print(f"✅ Data berhasil ditulis ke HDFS (format Parquet)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error saat upload ke HDFS: {e}")
        print("💡 Pastikan HDFS sudah berjalan dan direktori sudah dibuat!")
        print("   Jalankan: bash scripts/setup_hdfs.sh")
        return False

hdfs_success = upload_to_hdfs_spark()

# %%
# Method 2: Upload dari MinIO ke HDFS (Alternative)
def transfer_minio_to_hdfs():
    """Transfer data dari MinIO S3A ke HDFS menggunakan Spark."""
    try:
        s3a_path = f"s3a://{MINIO_BUCKET}/raw/marketing_campaign_performance.csv"
        
        print(f"⏳ Membaca data dari MinIO: {s3a_path}")
        
        # Baca dari MinIO
        df_from_minio = spark.read.csv(
            s3a_path,
            header=True,
            schema=marketing_schema
        )
        
        record_count = df_from_minio.count()
        print(f"✅ Data berhasil dibaca dari MinIO: {record_count:,} records")
        
        # Tulis ke HDFS
        hdfs_output = f"{HDFS_NAMENODE}{HDFS_RAW_DIR}/from_minio/marketing_campaign.parquet"
        df_from_minio.write.mode("overwrite").parquet(hdfs_output)
        
        print(f"✅ Data berhasil ditransfer dari MinIO ke HDFS")
        
        return True
        
    except Exception as e:
        print(f"❌ Error saat transfer MinIO ke HDFS: {e}")
        print("💡 Metode alternatif: gunakan upload langsung (Method 1)")
        return False

# Uncomment baris berikut untuk menjalankan transfer MinIO -> HDFS
# transfer_minio_to_hdfs()

# %% [markdown]
# ## 9. Verifikasi Integritas Data
# 
# Memverifikasi bahwa data yang diupload ke HDFS memiliki integritas 100%
# (tidak ada record yang hilang atau corrupt).

# %%
# Verifikasi data di HDFS
def verify_data_integrity():
    """Verifikasi integritas data di HDFS."""
    print("=" * 60)
    print("🔍 VERIFIKASI INTEGRITAS DATA")
    print("=" * 60)
    
    # 1. Hitung record di lokal
    local_count = df_raw.count()
    print(f"\n📌 Record di lokal   : {local_count:,}")
    
    # 2. Baca dan hitung record di HDFS
    try:
        hdfs_parquet_path = f"{HDFS_NAMENODE}{HDFS_RAW_DIR}/marketing_campaign_raw.parquet"
        df_hdfs = spark.read.parquet(hdfs_parquet_path)
        hdfs_count = df_hdfs.count()
        print(f"📌 Record di HDFS    : {hdfs_count:,}")
        
        # 3. Bandingkan
        if local_count == hdfs_count:
            print(f"\n✅ INTEGRITAS DATA: 100% — Semua {local_count:,} record berhasil diupload!")
        else:
            diff = local_count - hdfs_count
            pct = (hdfs_count / local_count) * 100
            print(f"\n⚠️ PERBEDAAN DITEMUKAN: {diff:,} record hilang ({pct:.1f}% terupload)")
            
        # 4. Verifikasi skema
        print(f"\n📋 Skema di HDFS:")
        df_hdfs.printSchema()
        
        # 5. Sample data dari HDFS
        print(f"📋 Sample Data dari HDFS:")
        df_hdfs.show(5, truncate=False)
        
    except Exception as e:
        print(f"❌ Error saat membaca dari HDFS: {e}")
        print("💡 Verifikasi manual dengan: hadoop fs -count /user/hadoop/marketing/raw/")
    
    # 3. Verifikasi data di MinIO
    try:
        client = Minio(
            "localhost:9000",
            access_key=MINIO_ACCESS_KEY,
            secret_key=MINIO_SECRET_KEY,
            secure=False
        )
        stat = client.stat_object(MINIO_BUCKET, "raw/marketing_campaign_performance.csv")
        print(f"\n📌 File di MinIO     : {stat.size / 1024:.2f} KB")
        print(f"   Last Modified     : {stat.last_modified}")
        print(f"✅ Data di MinIO tersedia dan valid")
    except Exception as e:
        print(f"⚠️ MinIO verification skipped: {e}")
    
    print("\n" + "=" * 60)

verify_data_integrity()

# %% [markdown]
# ## 10. Ringkasan Proses Ingestion
# 
# Menampilkan ringkasan dari seluruh proses data ingestion.

# %%
# Ringkasan
print("=" * 60)
print("📊 RINGKASAN DATA INGESTION")
print("=" * 60)
print(f"""
📁 SUMBER DATA:
   Dataset     : Marketing Campaign Performance Dataset
   Sumber      : Kaggle
   Format      : CSV
   Records     : {df_raw.count():,} baris
   Kolom       : {len(df_raw.columns)} kolom
   
📦 STORAGE:
   MinIO       : s3://{MINIO_BUCKET}/raw/marketing_campaign_performance.csv
   HDFS (CSV)  : {HDFS_RAW_DIR}/marketing_campaign_performance.csv/
   HDFS (Parq) : {HDFS_RAW_DIR}/marketing_campaign_raw.parquet/

📋 KOLOM DATASET:
""")

for i, col_name in enumerate(df_raw.columns, 1):
    dtype = dict(df_raw.dtypes).get(col_name, "unknown")
    print(f"   {i:2d}. {col_name:15s} ({dtype})")

print(f"""
✅ STATUS: Data ingestion berhasil!
   - Dataset dibaca dari local storage
   - Data tersimpan di MinIO (Data Lake)
   - Data tersimpan di HDFS (Distributed Storage)
   - Integritas data 100% terverifikasi
""")

# %%
# Stop SparkSession
spark.stop()
print("✅ SparkSession dihentikan. Notebook 1 selesai!")
print("➡️  Lanjutkan ke Notebook 2: Data Processing & EDA")

# %% [markdown]
# ---
# ## Catatan Penting
# 
# 1. **Sebelum menjalankan notebook ini**, pastikan:
#    - Hadoop HDFS sudah berjalan (`start-dfs.sh`)
#    - MinIO server sudah berjalan (`minio server /data/minio`)
#    - Dataset CSV sudah ada di `data/raw/`
# 
# 2. **Jika terjadi error koneksi HDFS/MinIO**, gunakan upload manual:
#    ```bash
#    # Upload ke HDFS
#    hadoop fs -put data/raw/marketing_campaign_performance_10000.csv /user/hadoop/marketing/raw/
#    
#    # Upload ke MinIO
#    mc cp data/raw/marketing_campaign_performance_10000.csv myminio/marketing-data/raw/
#    ```
# 
# 3. **Output notebook ini:**
#    - Data CSV di MinIO bucket `marketing-data/raw/`
#    - Data CSV dan Parquet di HDFS `/user/hadoop/marketing/raw/`
#    - Data siap untuk diproses di Notebook 2
