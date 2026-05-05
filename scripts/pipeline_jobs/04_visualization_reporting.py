# Auto-generated script from 04_visualization_reporting.ipynb
# This script is intended to be run by an orchestrator like Apache Airflow or GitHub Actions.

import os, sys, warnings, glob as _glob
warnings.filterwarnings('ignore')

os.environ["JAVA_HOME"]   = r"C:\Program Files\Java\jdk-21.0.10"
os.environ["SPARK_HOME"]  = r"C:\spark\spark-4.1.1-bin-hadoop3"
os.environ["HADOOP_HOME"] = r"C:\Users\muham\OneDrive\Dokumen\Dokumen\BigData\bigdata6-marketing-analytics\hadoop"
_py4j = _glob.glob(os.path.join(os.environ["SPARK_HOME"], "python", "lib", "py4j-*.zip"))
sys.path.insert(0, os.path.join(os.environ["SPARK_HOME"], "python"))
if _py4j: sys.path.insert(0, _py4j[0])

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
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

MINIO_ENDPOINT = "localhost:9000"
MINIO_ACCESS_KEY = "minioadmin"
MINIO_SECRET_KEY = "minioadmin123"
MINIO_BUCKET = "marketing-data"

GOLD_PREDICTIONS_PATH          = f"s3a://{MINIO_BUCKET}/gold/predictions"
GOLD_CHANNEL_SUMMARY_PATH      = f"s3a://{MINIO_BUCKET}/gold/channel_performance_summary"
GOLD_PROFITABILITY_REPORT_PATH = f"s3a://{MINIO_BUCKET}/gold/campaign_profitability_report"

spark = SparkSession.builder \
    .appName("Marketing_Visualization_Reporting") \
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

df_predictions = spark.read.parquet(GOLD_PREDICTIONS_PATH)

# Gunakan Data Gold untuk keseluruhan analisis
pdf = df_predictions.toPandas()
pdf_pred = pdf.copy()

print(f'[OK] Data dimuat dari Gold Layer!')
print(f'   Predictions (Gold)  : {len(pdf_pred):,} baris')
print(f'   Kolom pred          : {list(pdf_pred.columns)}')

# Agregasi: ROI & Revenue per Channel
channel_agg = pdf.groupby('Channel').agg(
    Jumlah_Kampanye  = ('CampaignID',  'count'),
    Avg_ROI          = ('ROI',          'mean'),
    Total_Revenue    = ('Revenue_USD',  'sum'),
    Avg_Revenue      = ('Revenue_USD',  'mean'),
    Total_Cost       = ('Cost_USD',     'sum'),
    Avg_Conversions  = ('Conversions',  'mean'),
    Avg_CTR          = ('CTR',          'mean'),
    Avg_CVR          = ('CVR',          'mean'),
).reset_index().round(3)

channel_agg = channel_agg.sort_values('Avg_ROI', ascending=False)
print('=== Performa per Channel ===')
print(channel_agg.to_string(index=False))

colors = sns.color_palette('husl', len(channel_agg))

fig, axes = plt.subplots(1, 3, figsize=(18, 6))

# Avg ROI
axes[0].bar(channel_agg['Channel'], channel_agg['Avg_ROI'], color=colors)
axes[0].set_title('Rata-rata ROI per Channel', fontweight='bold')
axes[0].set_xlabel('Channel')
axes[0].set_ylabel('Avg ROI')
for i, v in enumerate(channel_agg['Avg_ROI']):
    axes[0].text(i, v + 0.005, f'{v:.3f}', ha='center', fontsize=9, fontweight='bold')

# Total Revenue
axes[1].bar(channel_agg['Channel'], channel_agg['Total_Revenue'], color=colors)
axes[1].set_title('Total Revenue per Channel (USD)', fontweight='bold')
axes[1].set_xlabel('Channel')
axes[1].set_ylabel('Total Revenue (USD)')

# Avg CTR
axes[2].bar(channel_agg['Channel'], channel_agg['Avg_CTR'], color=colors)
axes[2].set_title('Rata-rata CTR per Channel', fontweight='bold')
axes[2].set_xlabel('Channel')
axes[2].set_ylabel('Avg CTR')

plt.tight_layout()
plt.show()

# Profitabilitas keseluruhan
profit_counts = pdf['is_profitable'].value_counts()
labels = ['Profitable (ROI>1)', 'Not Profitable (ROI≤1)']
values = [profit_counts.get(1, 0), profit_counts.get(0, 0)]

fig, axes = plt.subplots(1, 2, figsize=(14, 6))

# Pie Chart
axes[0].pie(values, labels=labels, autopct='%1.1f%%',
            colors=['#2ecc71', '#e74c3c'], startangle=90)
axes[0].set_title('Distribusi Profitabilitas Kampanye', fontweight='bold')

# Profitabilitas per Channel
profit_channel = pdf.groupby(['Channel', 'is_profitable']).size().unstack(fill_value=0)
profit_channel.columns = ['Not Profitable', 'Profitable']
profit_channel.plot(kind='bar', ax=axes[1], color=['#e74c3c', '#2ecc71'], edgecolor='black')
axes[1].set_title('Profitabilitas per Channel', fontweight='bold')
axes[1].set_xlabel('Channel')
axes[1].set_ylabel('Jumlah Kampanye')
axes[1].tick_params(axis='x', rotation=0)
axes[1].legend()

plt.tight_layout()
plt.show()

print(f'Total kampanye profitable     : {values[0]:,} ({values[0]/sum(values)*100:.1f}%)')
print(f'Total kampanye not profitable : {values[1]:,} ({values[1]/sum(values)*100:.1f}%)')

# Akurasi RF per channel
pdf_pred['rf_correct'] = (pdf_pred['rf_prediction'] == pdf_pred['is_profitable']).astype(int)
rf_acc_per_channel = pdf_pred.groupby('Channel')['rf_correct'].mean().reset_index()
rf_acc_per_channel.columns = ['Channel', 'RF_Accuracy']

# Revenue: Actual vs Predicted per channel
rev_per_channel = pdf_pred.groupby('Channel').agg(
    Actual_Revenue    = ('Revenue_USD', 'mean'),
    Predicted_Revenue = ('lr_predicted_revenue', 'mean')
).reset_index()

fig, axes = plt.subplots(1, 2, figsize=(16, 6))

# RF Accuracy per Channel
colors = sns.color_palette('Blues_r', len(rf_acc_per_channel))
axes[0].bar(rf_acc_per_channel['Channel'], rf_acc_per_channel['RF_Accuracy'], color=colors)
axes[0].set_ylim(0, 1)
axes[0].set_title('RF Classifier Accuracy per Channel', fontweight='bold')
axes[0].set_xlabel('Channel')
axes[0].set_ylabel('Accuracy')
for i, v in enumerate(rf_acc_per_channel['RF_Accuracy']):
    axes[0].text(i, v + 0.01, f'{v:.3f}', ha='center', fontsize=9)

# Actual vs Predicted Revenue per Channel
x = range(len(rev_per_channel))
w = 0.35
axes[1].bar([i - w/2 for i in x], rev_per_channel['Actual_Revenue'],    w, label='Actual',    color='steelblue')
axes[1].bar([i + w/2 for i in x], rev_per_channel['Predicted_Revenue'], w, label='Predicted', color='orange')
axes[1].set_xticks(list(x))
axes[1].set_xticklabels(rev_per_channel['Channel'])
axes[1].set_title('Actual vs Predicted Revenue per Channel', fontweight='bold')
axes[1].set_xlabel('Channel')
axes[1].set_ylabel('Avg Revenue (USD)')
axes[1].legend()

plt.tight_layout()
plt.show()

total_revenue   = pdf['Revenue_USD'].sum()
total_cost      = pdf['Cost_USD'].sum()
overall_roi     = pdf['ROI'].mean()
profit_rate     = pdf['is_profitable'].mean() * 100
total_campaigns = len(pdf)
avg_ctr         = pdf['CTR'].mean()
avg_cvr         = pdf['CVR'].mean()

print('='*55)
print('         MARKETING CAMPAIGN PERFORMANCE DASHBOARD')
print('='*55)
print(f'  Total Kampanye       : {total_campaigns:>10,}')
print(f'  Total Revenue (USD)  : {total_revenue:>10,.2f}')
print(f'  Total Cost (USD)     : {total_cost:>10,.2f}')
print(f'  Overall ROI (avg)    : {overall_roi:>10.4f}')
print(f'  Profitability Rate   : {profit_rate:>9.1f}%')
print(f'  Avg CTR              : {avg_ctr:>10.4f}')
print(f'  Avg CVR              : {avg_cvr:>10.4f}')
print('='*55)

best_channel = channel_agg.iloc[0]['Channel']
print(f'\n  Best Channel (by ROI): {best_channel}')
print(f'  → Avg ROI: {channel_agg.iloc[0]["Avg_ROI"]:.4f}')
print(f'  → Total Revenue: ${channel_agg.iloc[0]["Total_Revenue"]:,.2f}')

# Heatmap Korelasi antar Metrik
corr_cols = ['Impressions','Clicks','Leads','Conversions','Cost_USD','Revenue_USD',
             'ROI','CTR','CPC','CPL','CVR','Campaign_Duration']
corr_matrix = pdf[corr_cols].corr()

plt.figure(figsize=(12, 9))
sns.heatmap(corr_matrix, annot=True, fmt='.2f', cmap='coolwarm',
            center=0, linewidths=0.5, annot_kws={'size': 8})
plt.title('Correlation Matrix — Marketing Campaign Metrics', fontweight='bold', fontsize=14)
plt.tight_layout()
plt.show()

# Distribusi ROI per Channel (Box Plot)
fig, axes = plt.subplots(1, 2, figsize=(16, 6))

channels_sorted = channel_agg['Channel'].tolist()
data_by_channel = [pdf[pdf['Channel'] == ch]['ROI'].values for ch in channels_sorted]

axes[0].boxplot(data_by_channel, labels=channels_sorted, patch_artist=True,
                boxprops=dict(facecolor='lightblue'))
axes[0].set_title('Distribusi ROI per Channel', fontweight='bold')
axes[0].set_xlabel('Channel')
axes[0].set_ylabel('ROI')
axes[0].axhline(y=1.0, color='red', linestyle='--', label='ROI=1 (Break-even)')
axes[0].legend()

# Revenue Distribution
axes[1].hist(pdf['Revenue_USD'], bins=50, color='steelblue', edgecolor='black', alpha=0.7)
axes[1].set_title('Distribusi Revenue per Kampanye', fontweight='bold')
axes[1].set_xlabel('Revenue (USD)')
axes[1].set_ylabel('Frekuensi')
axes[1].axvline(pdf['Revenue_USD'].mean(), color='red', linestyle='--',
                label=f'Mean: ${pdf["Revenue_USD"].mean():.2f}')
axes[1].legend()

plt.tight_layout()
plt.show()

# --- Gold: Channel Performance Summary ---
df_channel_summary = df_predictions.groupBy('Channel').agg(
    F.count('*').alias('Jumlah_Kampanye'),
    F.round(F.avg('ROI'), 4).alias('Avg_ROI'),
    F.round(F.avg('Revenue_USD'), 2).alias('Avg_Revenue'),
    F.round(F.sum('Revenue_USD'), 2).alias('Total_Revenue'),
    F.round(F.avg('Cost_USD'), 2).alias('Avg_Cost'),
    F.round(F.avg('Conversions'), 2).alias('Avg_Conversions'),
    F.round(F.avg('CTR'), 4).alias('Avg_CTR'),
    F.round(F.avg('CVR'), 4).alias('Avg_CVR')
).orderBy('Avg_ROI', ascending=False)

df_channel_summary.write.mode('overwrite').parquet(GOLD_CHANNEL_SUMMARY_PATH)
print(f'[OK] Gold Channel Summary disimpan: {GOLD_CHANNEL_SUMMARY_PATH}')
df_channel_summary.show()

# --- Gold: Campaign Profitability Report ---
df_profit_report = df_predictions.groupBy('Channel', 'is_profitable').agg(
    F.count('*').alias('Jumlah'),
    F.round(F.avg('ROI'), 4).alias('Avg_ROI'),
    F.round(F.sum('Revenue_USD'), 2).alias('Total_Revenue'),
    F.round(F.avg('Cost_USD'), 2).alias('Avg_Cost')
).orderBy('Channel', 'is_profitable')

df_profit_report.write.mode('overwrite').parquet(GOLD_PROFITABILITY_REPORT_PATH)
print(f'[OK] Gold Profitability Report disimpan: {GOLD_PROFITABILITY_REPORT_PATH}')
df_profit_report.show()

spark.stop()
print('[OK] SparkSession dihentikan')
print('[OK] Gold Layer selesai dibuat! Semua output tersimpan di MinIO.')

