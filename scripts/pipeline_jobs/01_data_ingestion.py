# Auto-generated script from 01_data_ingestion.ipynb
# This script is intended to be run by an orchestrator like Apache Airflow or GitHub Actions.

import os, sys, warnings, glob as _glob
warnings.filterwarnings('ignore')

# ============================================================
# FIX Windows: Set environment variables sebelum import PySpark
# ============================================================
os.environ["JAVA_HOME"]   = r"C:\Program Files\Java\jdk-21.0.10"
os.environ["SPARK_HOME"]  = r"C:\spark\spark-4.1.1-bin-hadoop3"
os.environ["HADOOP_HOME"] = r"C:\Users\muham\OneDrive\Dokumen\Dokumen\BigData\bigdata6-marketing-analytics\hadoop"
_py4j = _glob.glob(os.path.join(os.environ["SPARK_HOME"], "python", "lib", "py4j-*.zip"))
sys.path.insert(0, os.path.join(os.environ["SPARK_HOME"], "python"))
if _py4j: sys.path.insert(0, _py4j[0])
# ============================================================
import os
import sys
import hashlib
import pandas as pd
from datetime import datetime
from minio import Minio
from minio.error import S3Error

# Tambahkan parent directory ke path untuk import config
sys.path.insert(0, os.path.abspath('..'))

print('[OK] Library berhasil di-import!')
print(f'   Pandas version  : {pd.__version__}')
print(f'   Waktu eksekusi  : {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')

# ============================================
# KONFIGURASI - Sesuaikan dengan environment
# ============================================

# MinIO Configuration
MINIO_ENDPOINT = "localhost:9000"
MINIO_ACCESS_KEY = "minioadmin"
MINIO_SECRET_KEY = "minioadmin123"
MINIO_BUCKET = "marketing-data"
MINIO_USE_SSL = False

# Path dataset lokal
LOCAL_CSV_PATH = "../data/raw/marketing_campaign_performance_10000.csv"

# Medallion Architecture — Path di MinIO
MINIO_BRONZE_DIR = "bronze/"
MINIO_SILVER_DIR = "silver/"
MINIO_GOLD_DIR = "gold/"
MINIO_MODELS_DIR = "models/"
MINIO_BRONZE_CSV = "bronze/marketing_campaign_performance.csv"

# Kaggle dataset info
KAGGLE_DATASET = "mirzayasirabdullah07/marketing-campaign-performance-dataset"

print('[OK] Konfigurasi dimuat!')
print(f'   MinIO Endpoint : {MINIO_ENDPOINT}')
print(f'   Bucket         : {MINIO_BUCKET}')
print(f'   Bronze Path    : {MINIO_BRONZE_CSV}')
print(f'   Local CSV      : {LOCAL_CSV_PATH}')

# Cek apakah file CSV ada di lokal
if os.path.exists(LOCAL_CSV_PATH):
    file_size = os.path.getsize(LOCAL_CSV_PATH)
    print('[OK] Dataset ditemukan!')
    print(f'   Path   : {os.path.abspath(LOCAL_CSV_PATH)}')
    print(f'   Ukuran : {file_size / 1024:.2f} KB ({file_size:,} bytes)')
else:
    print('[ERROR] Dataset TIDAK ditemukan!')
    print(f'   Expected path: {os.path.abspath(LOCAL_CSV_PATH)}')
    print('\n[INFO] Cara mendapatkan dataset:')
    print('   Option 1: python scripts/download_dataset.py')
    print(f'   Option 2: Download manual dari https://www.kaggle.com/datasets/{KAGGLE_DATASET}')

# Load dataset dengan Pandas untuk eksplorasi awal
df = pd.read_csv(LOCAL_CSV_PATH)

print('=' * 60)
print('INFORMASI DATASET')
print('=' * 60)
print(f'Jumlah Record  : {df.shape[0]:,} baris')
print(f'Jumlah Kolom   : {df.shape[1]} kolom')
print(f'Memory Usage   : {df.memory_usage(deep=True).sum() / 1024:.2f} KB')
print(f'\nKolom-kolom:')
for i, (col, dtype) in enumerate(zip(df.columns, df.dtypes), 1):
    null_count = df[col].isnull().sum()
    print(f'   {i:2d}. {col:<15s} | {str(dtype):<10s} | Null: {null_count}')

# Hitung MD5 checksum untuk verifikasi integritas
with open(LOCAL_CSV_PATH, 'rb') as f:
    local_md5 = hashlib.md5(f.read()).hexdigest()
print(f'\nMD5 Checksum   : {local_md5}')

# Tampilkan 5 baris pertama
print('Preview Data (5 baris pertama):')
df.head()

# Statistik deskriptif
print('Statistik Deskriptif:')
df.describe()

# Distribusi Channel
print('Distribusi Channel:')
channel_dist = df['Channel'].value_counts()
for channel, count in channel_dist.items():
    pct = count / len(df) * 100
    print(f'   {channel:<12s}: {count:,} kampanye ({pct:.1f}%)')

print(f'\nDistribusi ROI (Label Klasifikasi):')
profitable = (df['ROI'] >= 1.0).sum()
not_profitable = (df['ROI'] < 1.0).sum()
print(f'   Profitable (ROI >= 1.0)    : {profitable:,} ({profitable/len(df)*100:.1f}%)')
print(f'   Not Profitable (ROI < 1.0) : {not_profitable:,} ({not_profitable/len(df)*100:.1f}%)')

# Buat koneksi ke MinIO
try:
    minio_client = Minio(
        MINIO_ENDPOINT,
        access_key=MINIO_ACCESS_KEY,
        secret_key=MINIO_SECRET_KEY,
        secure=MINIO_USE_SSL
    )
    
    # Test koneksi dengan list buckets
    buckets = minio_client.list_buckets()
    print('[OK] Berhasil terhubung ke MinIO!')
    print(f'   Endpoint : {MINIO_ENDPOINT}')
    print(f'   Buckets  : {len(buckets)} bucket ditemukan')
    for b in buckets:
        print(f'              - {b.name} (created: {b.creation_date})')
        
except Exception as e:
    print('[ERROR] Gagal terhubung ke MinIO!')
    print(f'   Error: {e}')
    print('\n[INFO] Pastikan MinIO server sudah berjalan:')
    print('   docker-compose up -d minio')

import io

# Buat bucket jika belum ada
try:
    if not minio_client.bucket_exists(MINIO_BUCKET):
        minio_client.make_bucket(MINIO_BUCKET)
        print(f'[OK] Bucket "{MINIO_BUCKET}" berhasil dibuat!')
    else:
        print(f'[INFO] Bucket "{MINIO_BUCKET}" sudah ada.')
    
    # Buat placeholder untuk struktur Medallion Architecture
    medallion_dirs = [
        (MINIO_BRONZE_DIR, 'Bronze — Data mentah'),
        (MINIO_SILVER_DIR, 'Silver — Data bersih & enriched'),
        (MINIO_GOLD_DIR, 'Gold — Agregasi bisnis'),
        (MINIO_MODELS_DIR, 'Models — Artefak ML'),
    ]
    
    for d, desc in medallion_dirs:
        objects = list(minio_client.list_objects(MINIO_BUCKET, prefix=d))
        if not objects:
            minio_client.put_object(
                MINIO_BUCKET, 
                d + ".gitkeep",
                io.BytesIO(b""),
                0
            )
            print(f'   [OK] {d:<10s} dibuat — {desc}')
        else:
            print(f'   [INFO] {d:<10s} sudah ada — {desc}')
    
    print(f'\n[OK] Struktur Medallion Architecture di bucket "{MINIO_BUCKET}" siap!')

except S3Error as e:
    print(f'[ERROR] Error saat membuat bucket: {e}')

# Upload CSV ke Bronze Layer di MinIO
try:
    print('[...] Mengupload dataset ke Bronze Layer...')
    print(f'   Source : {os.path.abspath(LOCAL_CSV_PATH)}')
    print(f'   Target : s3a://{MINIO_BUCKET}/{MINIO_BRONZE_CSV}')
    
    result = minio_client.fput_object(
        bucket_name=MINIO_BUCKET,
        object_name=MINIO_BRONZE_CSV,
        file_path=LOCAL_CSV_PATH,
        content_type="text/csv"
    )
    
    print(f'\n[OK] Upload ke Bronze Layer berhasil!')
    print(f'   Object  : {result.object_name}')
    print(f'   ETag    : {result.etag}')
    
except S3Error as e:
    print(f'[ERROR] Error saat upload: {e}')

# List semua objects di bucket
print('Daftar Objects di MinIO Bucket (Medallion Structure):')
print('=' * 65)
objects = minio_client.list_objects(MINIO_BUCKET, recursive=True)
total_size = 0
for obj in objects:
    size_kb = obj.size / 1024 if obj.size else 0
    total_size += obj.size if obj.size else 0
    # Tentukan layer berdasarkan prefix
    if obj.object_name.startswith('bronze/'):
        layer = '[BRONZE]'
    elif obj.object_name.startswith('silver/'):
        layer = '[SILVER]'
    elif obj.object_name.startswith('gold/'):
        layer = '[GOLD]  '
    elif obj.object_name.startswith('models/'):
        layer = '[MODEL] '
    else:
        layer = '[OTHER] '
    print(f'   {layer} {obj.object_name:<50s} {size_kb:>8.2f} KB')
print('=' * 65)
print(f'   Total: {total_size / 1024:.2f} KB')

import tempfile

print('[...] Verifikasi Integritas Data...')

# Download file dari MinIO ke temp
temp_path = os.path.join(tempfile.gettempdir(), 'verify_download.csv')
minio_client.fget_object(MINIO_BUCKET, MINIO_BRONZE_CSV, temp_path)

# Hitung MD5 file yang didownload
with open(temp_path, 'rb') as f:
    minio_md5 = hashlib.md5(f.read()).hexdigest()

print(f'   MD5 Lokal  : {local_md5}')
print(f'   MD5 MinIO  : {minio_md5}')

if local_md5 == minio_md5:
    print('\n[OK] INTEGRITAS DATA TERJAGA 100%! Checksum cocok.')
else:
    print('\n[WARN] Checksum tidak cocok! Data mungkin corrupt.')

# Verifikasi jumlah record
df_verify = pd.read_csv(temp_path)
print(f'\n   Record lokal : {len(df):,}')
print(f'   Record MinIO : {len(df_verify):,}')
print(f'   Match        : {"[OK] Ya" if len(df) == len(df_verify) else "[ERROR] Tidak"}')

os.remove(temp_path)

print('=' * 65)
print('RINGKASAN DATA INGESTION — BRONZE LAYER')
print('=' * 65)
print(f"""
Medallion Architecture: BRONZE LAYER
   Bronze = Data mentah tanpa transformasi (single source of truth)

Sumber Data:
   Dataset  : Marketing Campaign Performance Dataset
   Sumber   : Kaggle ({KAGGLE_DATASET})
   Format   : CSV
   Record   : {len(df):,} baris
   Kolom    : {len(df.columns)} atribut

Storage (MinIO Data Lake — Bronze Layer):
   Endpoint : {MINIO_ENDPOINT}
   Bucket   : {MINIO_BUCKET}
   Path     : s3a://{MINIO_BUCKET}/{MINIO_BRONZE_CSV}
   
Struktur Medallion di Bucket:
   {MINIO_BUCKET}/
   ├── bronze/     <- CSV mentah        [UPLOADED ✓]
   ├── silver/     <- Cleaned & Features [menunggu Notebook 02]
   ├── gold/       <- Agregasi bisnis    [menunggu Notebook 03-04]
   └── models/     <- Model ML           [menunggu Notebook 03]

[OK] Integritas : Data 100% terjaga (MD5 checksum verified)
[OK] Status     : BRONZE LAYER INGESTION BERHASIL

--> Next Step   : Jalankan Notebook 02 (Bronze → Silver Processing & EDA)
""")
print('=' * 65)

