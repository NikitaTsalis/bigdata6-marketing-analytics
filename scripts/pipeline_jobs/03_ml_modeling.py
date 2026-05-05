# Auto-generated script from 03_ml_modeling.ipynb
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
from pyspark.ml import Pipeline
from pyspark.ml.feature import StringIndexer, OneHotEncoder, VectorAssembler, StandardScaler
from pyspark.ml.classification import RandomForestClassifier
from pyspark.ml.regression import LinearRegression
from pyspark.ml.evaluation import MulticlassClassificationEvaluator, RegressionEvaluator, BinaryClassificationEvaluator
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
GOLD_PREDICTIONS_PATH          = f"s3a://{MINIO_BUCKET}/gold/predictions"
GOLD_CHANNEL_SUMMARY_PATH      = f"s3a://{MINIO_BUCKET}/gold/channel_performance_summary"
GOLD_PROFITABILITY_REPORT_PATH = f"s3a://{MINIO_BUCKET}/gold/campaign_profitability_report"
MODEL_RF_PATH = f"s3a://{MINIO_BUCKET}/models/random_forest_classifier"
MODEL_LR_PATH = f"s3a://{MINIO_BUCKET}/models/linear_regression"

spark = SparkSession.builder \
    .appName("Marketing_ML_Modeling") \
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

df = spark.read.parquet(SILVER_FEATURES_PATH)
print(f'[OK] Data dimuat dari Silver Layer: {df.count():,} baris, {len(df.columns)} kolom')
df.printSchema()

# Preview data Silver Layer
print('--- Preview 5 baris pertama ---')
df.show(5, truncate=False)

# Distribusi label target (is_profitable)
print('\n--- Distribusi Label is_profitable ---')
df.groupBy('is_profitable').count().orderBy('is_profitable').show()

# Statistik dasar
print('\n--- Statistik Deskriptif ---')
df.select(['Impressions','Clicks','Leads','Conversions','Cost_USD','Revenue_USD','ROI',
           'CTR','CPC','CPL','CVR','Campaign_Duration']).describe().show()

# Encoding Channel (kategorikal → numerik)
channel_indexer = StringIndexer(inputCol='Channel', outputCol='Channel_Index', handleInvalid='keep')
channel_encoder = OneHotEncoder(inputCols=['Channel_Index'], outputCols=['Channel_Vec'])

# Fitur numerik
numeric_features = ['Impressions', 'Clicks', 'Leads', 'Conversions',
                    'Cost_USD', 'CTR', 'CPC', 'CPL', 'CVR', 'Campaign_Duration']

all_features = numeric_features + ['Channel_Vec']
assembler = VectorAssembler(inputCols=all_features, outputCol='features_raw', handleInvalid='skip')

# Standarisasi fitur
scaler = StandardScaler(inputCol='features_raw', outputCol='features', withStd=True, withMean=True)

print('[OK] Komponen pipeline disiapkan')
print(f'   Fitur numerik   : {numeric_features}')
print(f'   Fitur kategorikal: [Channel → Channel_Vec (One-Hot)]')

SEED = 42
train_data, test_data = df.randomSplit([0.8, 0.2], seed=SEED)
print(f'[OK] Data split selesai')
print(f'   Train set: {train_data.count():,} baris')
print(f'   Test  set: {test_data.count():,} baris')

rf = RandomForestClassifier(
    labelCol='is_profitable',
    featuresCol='features',
    numTrees=50,
    maxDepth=5,
    seed=SEED
)
rf_pipeline = Pipeline(stages=[channel_indexer, channel_encoder, assembler, scaler, rf])

print('[...] Melatih Random Forest Classifier...')
rf_model = rf_pipeline.fit(train_data)
print('[OK] Training selesai!')

rf_predictions = rf_model.transform(test_data)

# Evaluasi
acc_eval  = MulticlassClassificationEvaluator(labelCol='is_profitable', predictionCol='prediction', metricName='accuracy')
f1_eval   = MulticlassClassificationEvaluator(labelCol='is_profitable', predictionCol='prediction', metricName='f1')
auc_eval  = BinaryClassificationEvaluator(labelCol='is_profitable', rawPredictionCol='rawPrediction', metricName='areaUnderROC')

rf_accuracy = acc_eval.evaluate(rf_predictions)
rf_f1       = f1_eval.evaluate(rf_predictions)
rf_auc      = auc_eval.evaluate(rf_predictions)

print('=== Evaluasi Random Forest Classifier ===')
print(f'   Accuracy : {rf_accuracy:.4f}')
print(f'   F1-Score : {rf_f1:.4f}')
print(f'   AUC-ROC  : {rf_auc:.4f}')

# Feature Importance (dari model RandomForest di tahap akhir pipeline)
rf_stage = rf_model.stages[-1]  # RandomForestClassificationModel
importances = rf_stage.featureImportances.toArray()

feature_names = numeric_features + [f'Channel_Vec_{i}' for i in range(len(importances) - len(numeric_features))]
fi_df = pd.DataFrame({'feature': feature_names, 'importance': importances})
fi_df = fi_df.sort_values('importance', ascending=False)

plt.figure(figsize=(10, 6))
sns.barplot(data=fi_df, x='importance', y='feature', palette='Blues_r')
plt.title('Feature Importance — Random Forest Classifier', fontweight='bold', fontsize=14)
plt.xlabel('Importance Score')
plt.ylabel('Feature')
plt.tight_layout()
plt.show()

print('\n--- Top 5 Fitur Paling Penting ---')
print(fi_df.head(5).to_string(index=False))

lr = LinearRegression(
    labelCol='Revenue_USD',
    featuresCol='features',
    maxIter=10,
    regParam=0.1,
    elasticNetParam=0.5
)
lr_pipeline = Pipeline(stages=[channel_indexer, channel_encoder, assembler, scaler, lr])

print('[...] Melatih Linear Regression...')
lr_model = lr_pipeline.fit(train_data)
print('[OK] Training selesai!')

lr_predictions = lr_model.transform(test_data)

r2_eval   = RegressionEvaluator(labelCol='Revenue_USD', predictionCol='prediction', metricName='r2')
mae_eval  = RegressionEvaluator(labelCol='Revenue_USD', predictionCol='prediction', metricName='mae')
rmse_eval = RegressionEvaluator(labelCol='Revenue_USD', predictionCol='prediction', metricName='rmse')

lr_r2   = r2_eval.evaluate(lr_predictions)
lr_mae  = mae_eval.evaluate(lr_predictions)
lr_rmse = rmse_eval.evaluate(lr_predictions)

print('=== Evaluasi Linear Regression ===')
print(f'   R²   : {lr_r2:.4f}')
print(f'   MAE  : {lr_mae:.2f}')
print(f'   RMSE : {lr_rmse:.2f}')

# Visualisasi Actual vs Predicted Revenue
lr_pdf = lr_predictions.select('Revenue_USD', 'prediction').toPandas()

plt.figure(figsize=(10, 6))
plt.scatter(lr_pdf['Revenue_USD'], lr_pdf['prediction'], alpha=0.3, color='steelblue')
lim_min = min(lr_pdf['Revenue_USD'].min(), lr_pdf['prediction'].min())
lim_max = max(lr_pdf['Revenue_USD'].max(), lr_pdf['prediction'].max())
plt.plot([lim_min, lim_max], [lim_min, lim_max], 'r--', label='Perfect Prediction')
plt.xlabel('Actual Revenue (USD)')
plt.ylabel('Predicted Revenue (USD)')
plt.title(f'Linear Regression: Actual vs Predicted Revenue  (R²={lr_r2:.4f})', fontweight='bold')
plt.legend()
plt.tight_layout()
plt.show()

print('[...] Menyimpan model dan prediksi ke MinIO...')

# Simpan model
rf_model.write().overwrite().save(MODEL_RF_PATH)
lr_model.write().overwrite().save(MODEL_LR_PATH)
print(f'[OK] Model RF disimpan di: {MODEL_RF_PATH}')
print(f'[OK] Model LR disimpan di: {MODEL_LR_PATH}')

# Gabungkan hasil prediksi RF + LR → Gold Layer
# Prediksi pada seluruh dataset (df) untuk Gold Layer
rf_full = rf_model.transform(df)
lr_full = lr_model.transform(df)

# Gabungkan hasil prediksi RF + LR → Gold Layer
rf_save = rf_full.select(
    'CampaignID', 'Channel', 'is_profitable', 'prediction',
    'Impressions', 'Clicks', 'Leads', 'Conversions',
    'Revenue_USD', 'Cost_USD', 'ROI', 'CTR', 'CPC', 'CPL', 'CVR', 'Campaign_Duration'
).withColumnRenamed('prediction', 'rf_prediction')

lr_save = lr_full.select(
    'CampaignID', 'prediction'
).withColumnRenamed('prediction', 'lr_predicted_revenue')

predictions_combined = rf_save.join(lr_save, on='CampaignID', how='inner')

# --- Data Governance: Schema Validation untuk Gold Layer ---
expected_columns = {'CampaignID', 'Channel', 'is_profitable', 'rf_prediction', \
                    'Impressions', 'Clicks', 'Leads', 'Conversions', \
                    'Revenue_USD', 'Cost_USD', 'ROI', 'CTR', 'CPC', 'CPL', 'CVR', 'Campaign_Duration', 'lr_predicted_revenue'}
actual_columns = set(predictions_combined.columns)
if not expected_columns.issubset(actual_columns):
    missing_cols = expected_columns - actual_columns
    raise ValueError(f'[ERROR] Schema Validation Failed: Missing columns {missing_cols}')
print('[OK] Data Governance: Schema validation passed. Semua kolom wajib tersedia.')

predictions_combined.write.mode('overwrite').parquet(GOLD_PREDICTIONS_PATH)
print(f'[OK] Gold Prediksi tersimpan di: {GOLD_PREDICTIONS_PATH}')
print(f'   Jumlah baris: {predictions_combined.count():,}')

summary = pd.DataFrame({
    'Model': ['Random Forest Classifier', 'Linear Regression'],
    'Task': ['Klasifikasi Profitabilitas (is_profitable)', 'Prediksi Revenue (Revenue_USD)'],
    'Metrik Utama': [
        f'Accuracy={rf_accuracy:.4f}, F1={rf_f1:.4f}, AUC={rf_auc:.4f}',
        f'R²={lr_r2:.4f}, MAE={lr_mae:.2f}, RMSE={lr_rmse:.2f}'
    ]
})

print('=== Ringkasan Performa Model ===')
print(summary.to_string(index=False))

spark.stop()
print('[OK] SparkSession dihentikan')

