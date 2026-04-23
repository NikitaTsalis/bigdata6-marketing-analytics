"""
Konfigurasi Spark Session untuk Proyek Big Data Marketing Analytics
==================================================================
File ini berisi konfigurasi yang digunakan di seluruh notebook.
Sesuaikan parameter sesuai dengan environment yang digunakan.
"""

# ============================================
# KONFIGURASI UMUM
# ============================================

# Nama aplikasi Spark
APP_NAME = "Marketing_Campaign_BigData_Analytics"

# Mode Spark: "local" untuk development, "yarn" untuk cluster
SPARK_MASTER = "local[*]"  # Gunakan semua core yang tersedia
# SPARK_MASTER = "yarn"    # Uncomment jika menggunakan YARN cluster

# ============================================
# KONFIGURASI HDFS
# ============================================

HDFS_NAMENODE = "hdfs://localhost:9000"  # Sesuaikan dengan NameNode address

# Direktori HDFS
HDFS_BASE_DIR = "/user/hadoop/marketing"
HDFS_RAW_DIR = f"{HDFS_BASE_DIR}/raw"
HDFS_PROCESSED_DIR = f"{HDFS_BASE_DIR}/processed"
HDFS_MODEL_DIR = f"{HDFS_BASE_DIR}/model"

# Path file di HDFS
HDFS_RAW_CSV = f"{HDFS_RAW_DIR}/marketing_campaign_performance.csv"
HDFS_PROCESSED_PARQUET = f"{HDFS_PROCESSED_DIR}/marketing_campaign_cleaned.parquet"
HDFS_FEATURE_ENGINEERED_PARQUET = f"{HDFS_PROCESSED_DIR}/marketing_campaign_features.parquet"

# ============================================
# KONFIGURASI MINIO (Object Storage / Data Lake)
# ============================================

MINIO_ENDPOINT = "localhost:9000"       # Endpoint MinIO
MINIO_ACCESS_KEY = "minioadmin"          # Access key (default)
MINIO_SECRET_KEY = "minioadmin"          # Secret key (default)
MINIO_BUCKET = "marketing-data"          # Nama bucket
MINIO_USE_SSL = False                    # SSL (False untuk development)

# Path di MinIO
MINIO_RAW_PATH = "raw/marketing_campaign_performance.csv"
MINIO_PROCESSED_PATH = "processed/"

# ============================================
# KONFIGURASI SPARK SESSION
# ============================================

SPARK_CONFIG = {
    "spark.app.name": APP_NAME,
    "spark.master": SPARK_MASTER,
    
    # Memory Configuration
    "spark.driver.memory": "4g",
    "spark.executor.memory": "2g",
    "spark.executor.cores": "2",
    
    # Serialization
    "spark.serializer": "org.apache.spark.serializer.KryoSerializer",
    
    # SQL Configuration
    "spark.sql.shuffle.partitions": "8",
    "spark.sql.adaptive.enabled": "true",
    
    # Hadoop/S3A Configuration untuk MinIO
    "spark.hadoop.fs.s3a.endpoint": f"http://{MINIO_ENDPOINT}",
    "spark.hadoop.fs.s3a.access.key": MINIO_ACCESS_KEY,
    "spark.hadoop.fs.s3a.secret.key": MINIO_SECRET_KEY,
    "spark.hadoop.fs.s3a.path.style.access": "true",
    "spark.hadoop.fs.s3a.impl": "org.apache.hadoop.fs.s3a.S3AFileSystem",
}

# ============================================
# KONFIGURASI DATASET
# ============================================

# Skema kolom dataset
DATASET_COLUMNS = [
    "CampaignID",    # STRING - Identifier
    "StartDate",     # STRING/DATE - Temporal
    "EndDate",       # STRING/DATE - Temporal
    "Channel",       # STRING (Categorical) - Feature
    "Impressions",   # INT64 - Feature
    "Clicks",        # INT64 - Feature
    "Leads",         # INT64 - Feature
    "Conversions",   # INT64 - Feature
    "Cost_USD",      # FLOAT64 - Feature
    "Revenue_USD",   # FLOAT64 - Label (Regresi)
    "ROI",           # FLOAT64 - Label (Klasifikasi)
]

# Channel yang tersedia
CHANNELS = ["Search", "Email", "Display", "Social", "Influencer"]

# Threshold profitabilitas
PROFITABLE_THRESHOLD = 1.0  # ROI >= 1.0 = Profitable

# ============================================
# KONFIGURASI MODEL
# ============================================

# Train-test split ratio
TEST_SIZE = 0.2
TRAIN_SIZE = 0.8
RANDOM_SEED = 42

# Random Forest Classifier
RF_CONFIG = {
    "numTrees": [50, 100, 150],
    "maxDepth": [5, 10, 15],
    "maxBins": 32,
    "seed": RANDOM_SEED,
}

# Linear Regression
LR_CONFIG = {
    "maxIter": [50, 100],
    "regParam": [0.01, 0.1, 0.3],
    "elasticNetParam": [0.0, 0.5, 1.0],
}

# Cross Validation
CV_NUM_FOLDS = 5

# ============================================
# KONFIGURASI OUTPUT
# ============================================

# Direktori output lokal untuk visualisasi
LOCAL_OUTPUT_DIR = "output"
LOCAL_PLOTS_DIR = f"{LOCAL_OUTPUT_DIR}/plots"
LOCAL_REPORTS_DIR = f"{LOCAL_OUTPUT_DIR}/reports"

# ============================================
# KONFIGURASI KAGGLE (untuk download dataset)
# ============================================

KAGGLE_DATASET = "mirzayasirabdullah07/marketing-campaign-performance-dataset"
KAGGLE_FILENAME = "marketing_campaign_performance_10000.csv"
LOCAL_DATA_DIR = "data/raw"


def get_spark_session():
    """
    Membuat dan mengembalikan SparkSession dengan konfigurasi yang sudah ditentukan.
    
    Returns:
        SparkSession: Instance SparkSession yang sudah dikonfigurasi
    """
    from pyspark.sql import SparkSession
    
    builder = SparkSession.builder
    
    for key, value in SPARK_CONFIG.items():
        builder = builder.config(key, value)
    
    spark = builder.getOrCreate()
    
    # Set log level
    spark.sparkContext.setLogLevel("WARN")
    
    print(f"✅ SparkSession berhasil dibuat!")
    print(f"   App Name : {spark.conf.get('spark.app.name')}")
    print(f"   Master   : {spark.conf.get('spark.master')}")
    print(f"   Version  : {spark.version}")
    
    return spark
