# %% [markdown]
# # 🔧 Notebook 2: Data Processing & Exploratory Data Analysis (EDA)
# ## Proyek Big Data - Analisis Performa Kampanye Marketing
#
# **Penanggung Jawab:** Data Engineer 2 (Naufal Zahdan Zulfakar - 245150401111003)
#
# **Tujuan:**
# 1. Memuat data dari HDFS ke Spark DataFrame
# 2. Eksplorasi Data Awal (EDA): statistik deskriptif, distribusi, korelasi
# 3. Pembersihan data: missing values, outlier
# 4. Feature Engineering: CTR, CPC, CPL, CVR, Campaign Duration, is_profitable
# 5. Encoding variabel kategorikal (Channel)
# 6. Menyimpan data bersih ke HDFS dalam format Parquet
#
# ---

# %% [markdown]
# ## 1. Setup & Import Library

# %%
import os, sys, warnings
warnings.filterwarnings('ignore')
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, count, when, isnan, isnull, lit, round as spark_round,
    mean, stddev, min as spark_min, max as spark_max,
    datediff, to_date, avg, sum as spark_sum, expr, corr
)
from pyspark.sql.types import DoubleType, IntegerType
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")
print("✅ Library berhasil diimport!")

# %% [markdown]
# ## 2. Membuat Spark Session

# %%
HDFS_NAMENODE = "hdfs://localhost:9000"
HDFS_RAW_DIR = "/user/hadoop/marketing/raw"
HDFS_PROCESSED_DIR = "/user/hadoop/marketing/processed"
LOCAL_CSV = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'raw', 'marketing_campaign_performance_10000.csv')

spark = SparkSession.builder \
    .appName("Marketing_Campaign_DataProcessing_EDA") \
    .master("local[*]") \
    .config("spark.driver.memory", "4g") \
    .config("spark.sql.shuffle.partitions", "8") \
    .getOrCreate()
spark.sparkContext.setLogLevel("WARN")
print(f"✅ SparkSession aktif — Spark {spark.version}")

# %% [markdown]
# ## 3. Memuat Data dari HDFS
# Memuat data yang telah di-ingest pada Notebook 1.

# %%
# Coba baca dari HDFS, fallback ke lokal
try:
    hdfs_path = f"{HDFS_NAMENODE}{HDFS_RAW_DIR}/marketing_campaign_raw.parquet"
    df = spark.read.parquet(hdfs_path)
    print(f"✅ Data dimuat dari HDFS (Parquet): {df.count():,} records")
except Exception as e:
    print(f"⚠️ HDFS tidak tersedia ({e}), membaca dari lokal...")
    df = spark.read.csv(LOCAL_CSV, header=True, inferSchema=True)
    print(f"✅ Data dimuat dari lokal: {df.count():,} records")

print(f"   Kolom: {len(df.columns)}")
df.printSchema()

# %% [markdown]
# ## 4. Eksplorasi Data Awal (EDA)
# ### 4.1 Statistik Deskriptif

# %%
print("📊 Statistik Deskriptif Kolom Numerik:")
df.describe().show()

# %%
# Statistik detail per kolom numerik
numeric_cols = ["Impressions", "Clicks", "Leads", "Conversions", "Cost_USD", "Revenue_USD", "ROI"]
print("📊 Statistik Detail:")
for c in numeric_cols:
    stats = df.select(
        lit(c).alias("Column"),
        spark_min(col(c)).alias("Min"),
        spark_max(col(c)).alias("Max"),
        spark_round(avg(col(c)), 2).alias("Mean"),
        spark_round(stddev(col(c)), 2).alias("StdDev")
    )
    stats.show(truncate=False)

# %% [markdown]
# ### 4.2 Distribusi Channel

# %%
print("📊 Distribusi Kampanye per Channel:")
channel_dist = df.groupBy("Channel").agg(
    count("*").alias("Jumlah_Kampanye"),
    spark_round(avg("ROI"), 4).alias("Avg_ROI"),
    spark_round(avg("Revenue_USD"), 2).alias("Avg_Revenue"),
    spark_round(avg("Cost_USD"), 2).alias("Avg_Cost"),
    spark_round(spark_sum("Revenue_USD"), 2).alias("Total_Revenue")
).orderBy("Jumlah_Kampanye", ascending=False)
channel_dist.show(truncate=False)

# %%
# Visualisasi distribusi channel
channel_pd = channel_dist.toPandas()

fig, axes = plt.subplots(1, 3, figsize=(18, 5))

# Bar plot - jumlah kampanye per channel
axes[0].bar(channel_pd["Channel"], channel_pd["Jumlah_Kampanye"], color=sns.color_palette("husl", 5))
axes[0].set_title("Jumlah Kampanye per Channel", fontsize=13, fontweight='bold')
axes[0].set_ylabel("Jumlah")
axes[0].tick_params(axis='x', rotation=30)

# Bar plot - avg ROI per channel
colors_roi = ['green' if x >= 1 else 'red' for x in channel_pd["Avg_ROI"]]
axes[1].bar(channel_pd["Channel"], channel_pd["Avg_ROI"], color=colors_roi)
axes[1].axhline(y=1.0, color='black', linestyle='--', label='ROI = 1.0')
axes[1].set_title("Rata-rata ROI per Channel", fontsize=13, fontweight='bold')
axes[1].set_ylabel("ROI")
axes[1].legend()
axes[1].tick_params(axis='x', rotation=30)

# Bar plot - total revenue per channel
axes[2].bar(channel_pd["Channel"], channel_pd["Total_Revenue"], color=sns.color_palette("viridis", 5))
axes[2].set_title("Total Revenue per Channel (USD)", fontsize=13, fontweight='bold')
axes[2].set_ylabel("Revenue (USD)")
axes[2].tick_params(axis='x', rotation=30)

plt.tight_layout()
os.makedirs("output/plots", exist_ok=True)
plt.savefig("output/plots/channel_distribution.png", dpi=150, bbox_inches='tight')
plt.show()
print("✅ Plot disimpan: output/plots/channel_distribution.png")

# %% [markdown]
# ### 4.3 Distribusi Kolom Numerik

# %%
df_pd = df.select(numeric_cols).toPandas()

fig, axes = plt.subplots(2, 4, figsize=(20, 10))
axes = axes.flatten()

for i, c in enumerate(numeric_cols):
    axes[i].hist(df_pd[c], bins=40, color=sns.color_palette("husl", 7)[i], edgecolor='white', alpha=0.8)
    axes[i].set_title(f"Distribusi {c}", fontsize=11, fontweight='bold')
    axes[i].set_xlabel(c)
    axes[i].set_ylabel("Frekuensi")

axes[-1].axis('off')
plt.tight_layout()
plt.savefig("output/plots/numeric_distributions.png", dpi=150, bbox_inches='tight')
plt.show()
print("✅ Plot disimpan: output/plots/numeric_distributions.png")

# %% [markdown]
# ### 4.4 Matriks Korelasi

# %%
corr_pd = df_pd[numeric_cols].corr()

plt.figure(figsize=(10, 8))
mask = [[False]*len(numeric_cols) for _ in range(len(numeric_cols))]
for i in range(len(numeric_cols)):
    for j in range(i):
        mask[i][j] = True
sns.heatmap(corr_pd, annot=True, fmt=".2f", cmap="RdYlBu_r", center=0,
            square=True, linewidths=0.5, vmin=-1, vmax=1)
plt.title("Matriks Korelasi Fitur Numerik", fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig("output/plots/correlation_matrix.png", dpi=150, bbox_inches='tight')
plt.show()
print("✅ Plot disimpan: output/plots/correlation_matrix.png")

# %% [markdown]
# ## 5. Pembersihan Data
# ### 5.1 Penanganan Missing Values

# %%
print("🔍 Pemeriksaan Missing Values:")
null_counts = []
for c in df.columns:
    nc = df.filter(col(c).isNull() | (col(c).cast("string") == "")).count()
    null_counts.append((c, nc))
    
null_df = spark.createDataFrame(null_counts, ["Column", "Null_Count"])
null_df.show(truncate=False)

total_nulls = sum(n for _, n in null_counts)
print(f"Total Missing Values: {total_nulls}")

# %%
# Isi missing values jika ada
if total_nulls > 0:
    print("⏳ Mengisi missing values...")
    # Numerik: isi dengan median
    for c in numeric_cols:
        median_val = df.approxQuantile(c, [0.5], 0.01)[0]
        df = df.fillna({c: median_val})
    # Kategorikal: isi dengan modus
    df = df.fillna({"Channel": "Unknown"})
    print("✅ Missing values berhasil diisi")
else:
    print("✅ Tidak ada missing values — data bersih!")

# %% [markdown]
# ### 5.2 Deteksi & Penanganan Outlier (IQR Method)

# %%
print("🔍 Deteksi Outlier menggunakan IQR Method:")
outlier_summary = []

for c in numeric_cols:
    q1, q3 = df.approxQuantile(c, [0.25, 0.75], 0.01)
    iqr = q3 - q1
    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr
    outlier_count = df.filter((col(c) < lower) | (col(c) > upper)).count()
    pct = (outlier_count / df.count()) * 100
    outlier_summary.append((c, round(q1, 2), round(q3, 2), round(iqr, 2),
                            round(lower, 2), round(upper, 2), outlier_count, round(pct, 2)))

outlier_df = spark.createDataFrame(
    outlier_summary,
    ["Column", "Q1", "Q3", "IQR", "Lower_Bound", "Upper_Bound", "Outlier_Count", "Pct"]
)
outlier_df.show(truncate=False)

# %%
# Capping outlier (Winsorization) — batas ke batas IQR
print("⏳ Melakukan capping outlier (Winsorization)...")
for c in numeric_cols:
    q1, q3 = df.approxQuantile(c, [0.25, 0.75], 0.01)
    iqr = q3 - q1
    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr
    df = df.withColumn(c,
        when(col(c) < lower, lower)
        .when(col(c) > upper, upper)
        .otherwise(col(c))
    )

print(f"✅ Outlier berhasil di-cap. Total records: {df.count():,}")

# %% [markdown]
# ## 6. Feature Engineering
# Membuat fitur baru yang relevan untuk analitik:
# - **CTR** (Click-Through Rate) = Clicks / Impressions
# - **CPC** (Cost Per Click) = Cost_USD / Clicks
# - **CPL** (Cost Per Lead) = Cost_USD / Leads
# - **CVR** (Conversion Rate) = Conversions / Clicks
# - **Campaign_Duration** = EndDate - StartDate (hari)
# - **is_profitable** = 1 jika ROI >= 1.0, 0 jika tidak

# %%
print("⏳ Membuat fitur baru...")

# Konversi tanggal
df = df.withColumn("StartDate", to_date(col("StartDate"), "yyyy-MM-dd"))
df = df.withColumn("EndDate", to_date(col("EndDate"), "yyyy-MM-dd"))

# Feature engineering
df = df.withColumn("CTR",
    when(col("Impressions") > 0, spark_round(col("Clicks") / col("Impressions"), 6)).otherwise(0.0)
)
df = df.withColumn("CPC",
    when(col("Clicks") > 0, spark_round(col("Cost_USD") / col("Clicks"), 4)).otherwise(0.0)
)
df = df.withColumn("CPL",
    when(col("Leads") > 0, spark_round(col("Cost_USD") / col("Leads"), 4)).otherwise(0.0)
)
df = df.withColumn("CVR",
    when(col("Clicks") > 0, spark_round(col("Conversions").cast("double") / col("Clicks"), 6)).otherwise(0.0)
)
df = df.withColumn("Campaign_Duration",
    datediff(col("EndDate"), col("StartDate")).cast("double")
)
# Label biner untuk klasifikasi
PROFITABLE_THRESHOLD = 1.0
df = df.withColumn("is_profitable",
    when(col("ROI") >= PROFITABLE_THRESHOLD, 1).otherwise(0)
)

print("✅ Fitur baru berhasil dibuat!")
print("\n📋 Skema DataFrame setelah Feature Engineering:")
df.printSchema()

# %%
# Tampilkan sample data dengan fitur baru
print("📋 Sample Data dengan Fitur Baru:")
df.select("CampaignID", "Channel", "CTR", "CPC", "CPL", "CVR",
          "Campaign_Duration", "ROI", "is_profitable").show(10, truncate=False)

# %%
# Distribusi label is_profitable
print("📊 Distribusi Label is_profitable:")
label_dist = df.groupBy("is_profitable").count().orderBy("is_profitable")
label_dist.show()

label_pd = label_dist.toPandas()
total = label_pd["count"].sum()
for _, row in label_pd.iterrows():
    label = "Profitable" if row["is_profitable"] == 1 else "Not Profitable"
    pct = (row["count"] / total) * 100
    print(f"   {label}: {row['count']:,} ({pct:.1f}%)")

# %%
# Visualisasi fitur baru
fig, axes = plt.subplots(2, 3, figsize=(18, 10))

new_features = ["CTR", "CPC", "CPL", "CVR", "Campaign_Duration", "is_profitable"]
colors = sns.color_palette("Set2", 6)

for i, feat in enumerate(new_features):
    ax = axes[i // 3][i % 3]
    data = df.select(feat).toPandas()
    if feat == "is_profitable":
        data[feat].value_counts().plot(kind='bar', ax=ax, color=["#e74c3c", "#2ecc71"])
        ax.set_xticklabels(["Not Profitable", "Profitable"], rotation=0)
    else:
        ax.hist(data[feat].dropna(), bins=40, color=colors[i], edgecolor='white', alpha=0.8)
    ax.set_title(f"Distribusi {feat}", fontsize=12, fontweight='bold')
    ax.set_xlabel(feat)
    ax.set_ylabel("Frekuensi")

plt.tight_layout()
plt.savefig("output/plots/feature_engineering_distributions.png", dpi=150, bbox_inches='tight')
plt.show()
print("✅ Plot disimpan: output/plots/feature_engineering_distributions.png")

# %% [markdown]
# ## 7. Encoding Variabel Kategorikal (Channel)
# Menggunakan StringIndexer dan OneHotEncoder dari Spark MLlib.

# %%
from pyspark.ml.feature import StringIndexer, OneHotEncoder

# StringIndexer: Channel -> Channel_Index
indexer = StringIndexer(inputCol="Channel", outputCol="Channel_Index")
df = indexer.fit(df).transform(df)

# OneHotEncoder: Channel_Index -> Channel_Vec
encoder = OneHotEncoder(inputCol="Channel_Index", outputCol="Channel_Vec")
df = encoder.fit(df).transform(df)

print("✅ Encoding Channel berhasil!")
print("\n📋 Mapping Channel -> Index:")
df.select("Channel", "Channel_Index").distinct().orderBy("Channel_Index").show()

# %% [markdown]
# ## 8. Menyimpan Data yang Telah Diproses ke HDFS (Parquet)

# %%
# Simpan ke HDFS
try:
    output_path = f"{HDFS_NAMENODE}{HDFS_PROCESSED_DIR}/marketing_campaign_features.parquet"
    print(f"⏳ Menyimpan data ke HDFS: {output_path}")
    df.write.mode("overwrite").parquet(output_path)
    print(f"✅ Data berhasil disimpan ke HDFS (Parquet)")
except Exception as e:
    print(f"⚠️ HDFS tidak tersedia: {e}")

# Simpan juga ke lokal sebagai backup
local_output = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'processed')
os.makedirs(local_output, exist_ok=True)
local_parquet = os.path.join(local_output, "marketing_campaign_features.parquet")
df.write.mode("overwrite").parquet(local_parquet)
print(f"✅ Backup lokal disimpan: {local_parquet}")

# %%
# Verifikasi data yang disimpan
df_verify = spark.read.parquet(local_parquet)
print(f"\n🔍 VERIFIKASI DATA PROCESSED:")
print(f"   Records   : {df_verify.count():,}")
print(f"   Columns   : {len(df_verify.columns)}")
print(f"   Kolom     : {df_verify.columns}")

# %% [markdown]
# ## 9. Ringkasan

# %%
print("=" * 60)
print("📊 RINGKASAN DATA PROCESSING & EDA")
print("=" * 60)
print(f"""
📌 DATA AWAL:
   Records          : 10,000
   Kolom            : 11

📌 SETELAH PROCESSING:
   Records          : {df.count():,}
   Kolom            : {len(df.columns)}

📌 FITUR BARU (Feature Engineering):
   1. CTR              = Clicks / Impressions
   2. CPC              = Cost_USD / Clicks
   3. CPL              = Cost_USD / Leads
   4. CVR              = Conversions / Clicks
   5. Campaign_Duration = EndDate - StartDate (hari)
   6. is_profitable    = 1 if ROI >= 1.0 else 0
   7. Channel_Index    = StringIndexer(Channel)
   8. Channel_Vec      = OneHotEncoder(Channel_Index)

📌 OUTPUT:
   HDFS  : {HDFS_PROCESSED_DIR}/marketing_campaign_features.parquet
   Lokal : data/processed/marketing_campaign_features.parquet
   Plots : output/plots/

✅ Data siap untuk modeling di Notebook 3!
""")

# %%
spark.stop()
print("✅ SparkSession dihentikan. Notebook 2 selesai!")
print("➡️  Lanjutkan ke Notebook 3: ML Modeling")
