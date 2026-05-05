# Auto-generated script from 02_data_processing_eda.ipynb
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

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import *
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

plt.rcParams["figure.figsize"] = (12, 6)
plt.rcParams["font.size"] = 12
sns.set_style("whitegrid")
sns.set_palette("husl")

print("[OK] Library berhasil di-import!")
print(f"   JAVA_HOME   : {os.environ['JAVA_HOME']}")
print(f"   SPARK_HOME  : {os.environ['SPARK_HOME']}")
print(f"   HADOOP_HOME : {os.environ['HADOOP_HOME']}")

# Konfigurasi MinIO
MINIO_ENDPOINT = "localhost:9000"
MINIO_ACCESS_KEY = "minioadmin"
MINIO_SECRET_KEY = "minioadmin123"
MINIO_BUCKET = "marketing-data"

BRONZE_CSV_PATH      = f"s3a://{MINIO_BUCKET}/bronze/marketing_campaign_performance.csv"
SILVER_CLEANED_PATH  = f"s3a://{MINIO_BUCKET}/silver/marketing_campaign_cleaned"
SILVER_FEATURES_PATH = f"s3a://{MINIO_BUCKET}/silver/marketing_campaign_features"

# hadoop-aws-3.3.1.jar & aws-java-sdk-bundle-1.11.901.jar
# sudah ada di C:/spark/spark-4.1.1-bin-hadoop3/jars/
#
# Override wajib: Hadoop 3.4.2 (bundled Spark 4.x) punya default config
# format duration string (60s, 200s, dll) yang tidak kompatibel dengan
# S3AFileSystem.initThreadPools() yang menggunakan getLong().
spark = SparkSession.builder \
    .appName("Marketing_Campaign_Processing_EDA") \
    .master("local[*]") \
    .config("spark.hadoop.fs.s3a.endpoint", f"http://{MINIO_ENDPOINT}") \
    .config("spark.hadoop.fs.s3a.access.key", MINIO_ACCESS_KEY) \
    .config("spark.hadoop.fs.s3a.secret.key", MINIO_SECRET_KEY) \
    .config("spark.hadoop.fs.s3a.path.style.access", "true") \
    .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem") \
    .config("spark.hadoop.fs.s3a.aws.credentials.provider",
            "org.apache.hadoop.fs.s3a.SimpleAWSCredentialsProvider") \
    .config("spark.hadoop.fs.s3a.connection.ssl.enabled", "false") \
    .config("spark.hadoop.fs.s3a.threads.keepalivetime", "60") \
    .config("spark.hadoop.fs.s3a.connection.timeout", "200000") \
    .config("spark.hadoop.fs.s3a.connection.establish.timeout", "30000") \
    .config("spark.hadoop.fs.s3a.connection.ttl", "300000") \
    .config("spark.hadoop.fs.s3a.multipart.purge.age", "86400") \
    .config("spark.hadoop.fs.s3a.assumed.role.session.duration", "1800") \
    .config("spark.driver.memory", "4g") \
    .config("spark.sql.shuffle.partitions", "8") \
    .getOrCreate()

spark.sparkContext.setLogLevel("WARN")
print(f'[OK] SparkSession dibuat! Versi: {spark.version}')

df_raw = spark.read.csv(BRONZE_CSV_PATH, header=True, inferSchema=True)

print(f'[OK] Data berhasil dimuat dari Bronze Layer!')
print(f'   Jumlah Record : {df_raw.count():,}')
print(f'   Jumlah Kolom  : {len(df_raw.columns)}')
df_raw.printSchema()

df_raw.show(5, truncate=False)

df_raw.describe().toPandas()

print('Statistik per Channel:')
df_raw.groupBy('Channel').agg(
    F.count('*').alias('Jumlah_Kampanye'),
    F.round(F.avg('ROI'), 3).alias('Avg_ROI'),
    F.round(F.avg('Revenue_USD'), 2).alias('Avg_Revenue'),
    F.round(F.avg('Cost_USD'), 2).alias('Avg_Cost'),
    F.round(F.avg('Conversions'), 1).alias('Avg_Conversions'),
    F.round(F.sum('Revenue_USD'), 2).alias('Total_Revenue')
).orderBy('Avg_ROI', ascending=False).show()

pdf = df_raw.toPandas()
colors = sns.color_palette('husl', 5)

fig, axes = plt.subplots(1, 2, figsize=(14, 5))
channel_counts = pdf['Channel'].value_counts()
axes[0].bar(channel_counts.index, channel_counts.values, color=colors, edgecolor='black')
axes[0].set_title('Distribusi Kampanye per Channel', fontweight='bold', fontsize=14)
axes[0].set_xlabel('Channel')
axes[0].set_ylabel('Jumlah Kampanye')
for i, v in enumerate(channel_counts.values):
    axes[0].text(i, v + 20, str(v), ha='center', fontweight='bold')

axes[1].pie(channel_counts.values, labels=channel_counts.index, autopct='%1.1f%%',
           colors=colors, startangle=90)
axes[1].set_title('Proporsi Channel', fontweight='bold', fontsize=14)
plt.tight_layout()
plt.show()

fig, axes = plt.subplots(2, 3, figsize=(18, 10))
metrics = ['Impressions', 'Clicks', 'Leads', 'Conversions', 'Cost_USD', 'Revenue_USD']
colors2 = sns.color_palette('husl', 6)

for idx, metric in enumerate(metrics):
    ax = axes[idx // 3][idx % 3]
    ax.hist(pdf[metric], bins=40, color=colors2[idx], edgecolor='black', alpha=0.7)
    ax.set_title(f'Distribusi {metric}', fontweight='bold')
    ax.set_xlabel(metric)
    ax.set_ylabel('Frekuensi')
    ax.axvline(pdf[metric].mean(), color='red', linestyle='--',
               label=f'Mean: {pdf[metric].mean():.0f}')
    ax.legend()

plt.suptitle('Distribusi Metrik Kampanye', fontsize=16, fontweight='bold', y=1.02)
plt.tight_layout()
plt.show()

fig, axes = plt.subplots(1, 2, figsize=(14, 5))

axes[0].hist(pdf['ROI'], bins=50, color='steelblue', edgecolor='black', alpha=0.7)
axes[0].axvline(x=1.0, color='red', linestyle='--', linewidth=2, label='Threshold (ROI=1.0)')
axes[0].set_title('Distribusi ROI', fontweight='bold', fontsize=14)
axes[0].set_xlabel('ROI')
axes[0].set_ylabel('Frekuensi')
axes[0].legend()

labels = ['Profitable (ROI >= 1.0)', 'Not Profitable (ROI < 1.0)']
sizes = [(pdf['ROI'] >= 1.0).sum(), (pdf['ROI'] < 1.0).sum()]
axes[1].pie(sizes, labels=labels, autopct='%1.1f%%',
           colors=['#2ecc71', '#e74c3c'], startangle=90)
axes[1].set_title('Profitable vs Not Profitable', fontweight='bold', fontsize=14)
plt.tight_layout()
plt.show()

numeric_cols = ['Impressions', 'Clicks', 'Leads', 'Conversions', 'Cost_USD', 'Revenue_USD', 'ROI']
corr_matrix = pdf[numeric_cols].corr()

fig, ax = plt.subplots(figsize=(10, 8))
mask = np.triu(np.ones_like(corr_matrix, dtype=bool))
sns.heatmap(corr_matrix, mask=mask, annot=True, fmt='.2f', cmap='RdYlBu_r',
            center=0, square=True, linewidths=1, ax=ax)
ax.set_title('Matriks Korelasi Antar Fitur', fontweight='bold', fontsize=14)
plt.tight_layout()
plt.show()

fig, axes = plt.subplots(1, 3, figsize=(18, 5))
for idx, metric in enumerate(['ROI', 'Revenue_USD', 'Cost_USD']):
    sns.boxplot(data=pdf, x='Channel', y=metric, ax=axes[idx], palette='husl')
    axes[idx].set_title(f'{metric} per Channel', fontweight='bold')
    axes[idx].tick_params(axis='x', rotation=45)
plt.tight_layout()
plt.show()

print('Pengecekan Missing Values:')
total_rows = df_raw.count()
for col_name in df_raw.columns:
    null_count = df_raw.filter(F.col(col_name).isNull()).count()
    pct = null_count / total_rows * 100
    status = '[OK]' if null_count == 0 else '[WARN]'
    print(f'   {status} {col_name:<15s}: {null_count:>5d} null ({pct:.2f}%)')

df_clean = df_raw.dropna()
dropped = total_rows - df_clean.count()
print(f'\nBaris dihapus karena null: {dropped}')

total = df_clean.count()
distinct = df_clean.select('CampaignID').distinct().count()
duplicates = total - distinct
print(f'Total record    : {total:,}')
print(f'CampaignID unik : {distinct:,}')
print(f'Duplikasi       : {duplicates}')

if duplicates > 0:
    df_clean = df_clean.dropDuplicates(['CampaignID'])
    print(f'[OK] {duplicates} duplikasi dihapus')
else:
    print('[OK] Tidak ada duplikasi')

df_clean = df_clean.withColumn('StartDate', F.to_date(F.col('StartDate'), 'yyyy-MM-dd'))
df_clean = df_clean.withColumn('EndDate', F.to_date(F.col('EndDate'), 'yyyy-MM-dd'))
print('[OK] Konversi tipe data selesai')
df_clean.printSchema()

print('Deteksi Outlier (IQR Method):')
outlier_cols = ['Impressions', 'Clicks', 'Leads', 'Conversions', 'Cost_USD', 'Revenue_USD']
for col_name in outlier_cols:
    quantiles = df_clean.approxQuantile(col_name, [0.25, 0.75], 0.01)
    Q1, Q3 = quantiles[0], quantiles[1]
    IQR = Q3 - Q1
    lower = Q1 - 1.5 * IQR
    upper = Q3 + 1.5 * IQR
    outlier_count = df_clean.filter(
        (F.col(col_name) < lower) | (F.col(col_name) > upper)
    ).count()
    pct = outlier_count / df_clean.count() * 100
    print(f'   {col_name:<15s}: {outlier_count:>4d} outliers ({pct:.1f}%)')

print('[INFO] Outlier dipertahankan - variasi natural kampanye marketing')

df_features = df_clean \
    .withColumn('CTR',
        F.when(F.col('Impressions') > 0, F.col('Clicks') / F.col('Impressions')).otherwise(0)) \
    .withColumn('CPC',
        F.when(F.col('Clicks') > 0, F.col('Cost_USD') / F.col('Clicks')).otherwise(0)) \
    .withColumn('CPL',
        F.when(F.col('Leads') > 0, F.col('Cost_USD') / F.col('Leads')).otherwise(0)) \
    .withColumn('CVR',
        F.when(F.col('Clicks') > 0, F.col('Conversions') / F.col('Clicks')).otherwise(0)) \
    .withColumn('Campaign_Duration',
        F.datediff(F.col('EndDate'), F.col('StartDate'))) \
    .withColumn('is_profitable',
        F.when(F.col('ROI') >= 1.0, 1).otherwise(0))

print(f'[OK] Feature engineering selesai! Total kolom: {len(df_features.columns)}')
df_features.select('CTR','CPC','CPL','CVR','Campaign_Duration','is_profitable').describe().show()

pdf_feat = df_features.toPandas()
fig, axes = plt.subplots(2, 3, figsize=(18, 10))
new_features = ['CTR', 'CPC', 'CPL', 'CVR', 'Campaign_Duration', 'is_profitable']
colors_feat = sns.color_palette('Set2', 6)

for idx, feat in enumerate(new_features):
    ax = axes[idx // 3][idx % 3]
    if feat == 'is_profitable':
        counts = pdf_feat[feat].value_counts().sort_index()
        ax.bar(['Not Profitable (0)', 'Profitable (1)'], counts.values,
               color=['#e74c3c', '#2ecc71'], edgecolor='black')
        for i, v in enumerate(counts.values):
            ax.text(i, v + 20, str(v), ha='center', fontweight='bold')
    else:
        ax.hist(pdf_feat[feat], bins=40, color=colors_feat[idx], edgecolor='black', alpha=0.7)
        ax.axvline(pdf_feat[feat].mean(), color='red', linestyle='--',
                  label=f'Mean: {pdf_feat[feat].mean():.4f}')
        ax.legend()
    ax.set_title(f'Distribusi {feat}', fontweight='bold')

plt.suptitle('Distribusi Fitur Engineering', fontsize=16, fontweight='bold', y=1.02)
plt.tight_layout()
plt.show()

print('[...] Menyimpan data Silver ke MinIO...')

df_clean.write.mode('overwrite').parquet(SILVER_CLEANED_PATH)
print(f'[OK] Silver Cleaned  : {SILVER_CLEANED_PATH}')

df_features.write.mode('overwrite').parquet(SILVER_FEATURES_PATH)
print(f'[OK] Silver Features : {SILVER_FEATURES_PATH}')

df_verify = spark.read.parquet(SILVER_FEATURES_PATH)
print(f'[OK] Verifikasi Silver Layer berhasil!')
print(f'   Record : {df_verify.count():,}')
print(f'   Kolom  : {len(df_verify.columns)}')
df_verify.printSchema()
df_verify.show(5)

print('=' * 60)
print('RINGKASAN: BRONZE --> SILVER')
print('=' * 60)
print(f"""
Input  (Bronze): {BRONZE_CSV_PATH}
Output (Silver):
   Cleaned  : {SILVER_CLEANED_PATH}
   Features : {SILVER_FEATURES_PATH}
   Format   : Apache Parquet

[OK] Status: SILVER LAYER SELESAI
--> Next: Notebook 03 (ML Modeling)
""")
print('=' * 60)

spark.stop()
print('[OK] SparkSession dihentikan')

