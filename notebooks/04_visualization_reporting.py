# %% [markdown]
# # 📊 Notebook 4: Visualisasi & Reporting
# ## Proyek Big Data - Analisis Performa Kampanye Marketing
#
# **Penanggung Jawab:** Project Manager & Documentation (Nikita Tsalis Akmalinda Yanisa - 235150401111041)
#
# **Tujuan:**
# 1. Dashboard visual komprehensif hasil analitik
# 2. Confusion Matrix & Classification Report
# 3. Feature Importance & Business Insights
# 4. Actual vs Predicted Revenue
# 5. Rekomendasi bisnis actionable (min. 3)
#
# ---

# %% [markdown]
# ## 1. Setup

# %%
import os, sys, json, warnings
warnings.filterwarnings('ignore')
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, avg, count, sum as spark_sum, round as spark_round, when
from pyspark.ml import PipelineModel
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.gridspec import GridSpec

plt.style.use('seaborn-v0_8-darkgrid')
plt.rcParams['figure.dpi'] = 150
plt.rcParams['font.size'] = 11
sns.set_palette("husl")
os.makedirs("output/plots", exist_ok=True)
os.makedirs("output/reports", exist_ok=True)
print("✅ Library berhasil diimport!")

# %%
LOCAL_PARQUET = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'processed', 'marketing_campaign_features.parquet')
MODELS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'models')
METRICS_PATH = os.path.join(MODELS_DIR, 'metrics.json')

spark = SparkSession.builder \
    .appName("Marketing_Campaign_Visualization") \
    .master("local[*]") \
    .config("spark.driver.memory", "4g") \
    .getOrCreate()
spark.sparkContext.setLogLevel("WARN")
print(f"✅ SparkSession aktif — Spark {spark.version}")

# %%
# Load data dan metrik
df = spark.read.parquet(LOCAL_PARQUET)
print(f"✅ Data dimuat: {df.count():,} records")

with open(METRICS_PATH, 'r') as f:
    metrics = json.load(f)
print(f"✅ Metrik model dimuat dari: {METRICS_PATH}")

# %% [markdown]
# ## 2. Dashboard Ringkasan Performa Model

# %%
clf = metrics["classification"]
reg = metrics["regression"]

fig = plt.figure(figsize=(18, 6))
gs = GridSpec(1, 3, figure=fig, wspace=0.3)

# Panel 1: Metrik Klasifikasi
ax1 = fig.add_subplot(gs[0, 0])
clf_metrics = ['Accuracy', 'F1-Score', 'Precision', 'Recall', 'AUC-ROC']
clf_values = [clf['accuracy'], clf['f1_score'], clf['precision'], clf['recall'], clf['auc_roc']]
clf_targets = [0.80, 0.78, None, None, None]
colors_clf = ['#2ecc71' if v >= 0.78 else '#e74c3c' for v in clf_values]
bars1 = ax1.barh(clf_metrics, clf_values, color=colors_clf, edgecolor='white', height=0.5)
ax1.axvline(x=0.80, color='navy', linestyle='--', alpha=0.7, label='Target 0.80')
ax1.set_xlim(0, 1.05)
ax1.set_title('🌲 Random Forest\nClassification Metrics', fontsize=13, fontweight='bold')
for bar, val in zip(bars1, clf_values):
    ax1.text(val + 0.01, bar.get_y() + bar.get_height()/2, f'{val:.3f}', va='center', fontsize=10)
ax1.legend(loc='lower right')

# Panel 2: Metrik Regresi
ax2 = fig.add_subplot(gs[0, 1])
reg_names = ['R²', 'RMSE (USD)', 'MAE (USD)']
reg_values = [reg['r2'], reg['rmse'], reg['mae']]
colors_reg = ['#2ecc71', '#3498db', '#9b59b6']
bars2 = ax2.barh(reg_names, reg_values, color=colors_reg, edgecolor='white', height=0.5)
ax2.set_title('📈 Linear Regression\nRegression Metrics', fontsize=13, fontweight='bold')
for bar, val in zip(bars2, reg_values):
    fmt = f'{val:.4f}' if val < 10 else f'{val:.2f}'
    ax2.text(val + max(reg_values)*0.01, bar.get_y() + bar.get_height()/2, fmt, va='center', fontsize=10)

# Panel 3: Summary card
ax3 = fig.add_subplot(gs[0, 2])
ax3.axis('off')
summary_text = f"""
━━━ MODEL SUMMARY ━━━

🌲 Random Forest Classifier
   Accuracy : {clf['accuracy']:.4f}
   F1-Score : {clf['f1_score']:.4f}
   Trees    : {clf.get('num_trees', 'N/A')}
   Depth    : {clf.get('max_depth', 'N/A')}

📈 Linear Regression
   R²       : {reg['r2']:.4f}
   RMSE     : {reg['rmse']:.2f} USD
   MAE      : {reg['mae']:.2f} USD

━━━━━━━━━━━━━━━━━━━
"""
ax3.text(0.1, 0.5, summary_text, transform=ax3.transAxes, fontsize=11,
         verticalalignment='center', fontfamily='monospace',
         bbox=dict(boxstyle='round,pad=0.8', facecolor='#ecf0f1', alpha=0.8))

plt.suptitle('Dashboard Performa Model — Marketing Campaign Analytics', fontsize=16, fontweight='bold', y=1.02)
plt.savefig("output/plots/dashboard_model_performance.png", dpi=150, bbox_inches='tight')
plt.show()
print("✅ Dashboard disimpan: output/plots/dashboard_model_performance.png")

# %% [markdown]
# ## 3. Analisis per Channel

# %%
channel_stats = df.groupBy("Channel").agg(
    count("*").alias("Total_Campaigns"),
    spark_round(avg("ROI"), 4).alias("Avg_ROI"),
    spark_round(avg("Revenue_USD"), 2).alias("Avg_Revenue"),
    spark_round(avg("Cost_USD"), 2).alias("Avg_Cost"),
    spark_round(spark_sum("Revenue_USD"), 2).alias("Total_Revenue"),
    spark_round(spark_sum("Cost_USD"), 2).alias("Total_Cost"),
    count(when(col("is_profitable") == 1, True)).alias("Profitable_Count"),
    spark_round(avg("CTR"), 6).alias("Avg_CTR"),
    spark_round(avg("CVR"), 6).alias("Avg_CVR"),
).orderBy("Avg_ROI", ascending=False)

ch_pd = channel_stats.toPandas()
ch_pd["Profitable_Rate"] = (ch_pd["Profitable_Count"] / ch_pd["Total_Campaigns"] * 100).round(1)

print("📊 Statistik per Channel:")
print(ch_pd.to_string(index=False))

# %%
fig, axes = plt.subplots(2, 2, figsize=(16, 12))

# 1. ROI per channel
ax = axes[0][0]
colors = ['#2ecc71' if x >= 1 else '#e74c3c' for x in ch_pd["Avg_ROI"]]
ax.bar(ch_pd["Channel"], ch_pd["Avg_ROI"], color=colors, edgecolor='white')
ax.axhline(y=1.0, color='black', linestyle='--', linewidth=1, label='Break-even (ROI=1)')
ax.set_title("Rata-rata ROI per Channel", fontsize=13, fontweight='bold')
ax.set_ylabel("ROI")
ax.legend()

# 2. Profitable rate per channel
ax = axes[0][1]
ax.bar(ch_pd["Channel"], ch_pd["Profitable_Rate"], color=sns.color_palette("Set2", 5), edgecolor='white')
ax.set_title("% Kampanye Profitable per Channel", fontsize=13, fontweight='bold')
ax.set_ylabel("Profitable Rate (%)")
for i, v in enumerate(ch_pd["Profitable_Rate"]):
    ax.text(i, v + 0.5, f'{v:.1f}%', ha='center', fontweight='bold')

# 3. Revenue vs Cost per channel
ax = axes[1][0]
x = np.arange(len(ch_pd))
w = 0.35
ax.bar(x - w/2, ch_pd["Total_Revenue"], w, label='Revenue', color='#2ecc71', edgecolor='white')
ax.bar(x + w/2, ch_pd["Total_Cost"], w, label='Cost', color='#e74c3c', edgecolor='white')
ax.set_xticks(x)
ax.set_xticklabels(ch_pd["Channel"])
ax.set_title("Total Revenue vs Cost per Channel", fontsize=13, fontweight='bold')
ax.set_ylabel("USD")
ax.legend()

# 4. CTR vs CVR
ax = axes[1][1]
ax.bar(x - w/2, ch_pd["Avg_CTR"]*100, w, label='CTR (%)', color='#3498db', edgecolor='white')
ax.bar(x + w/2, ch_pd["Avg_CVR"]*100, w, label='CVR (%)', color='#9b59b6', edgecolor='white')
ax.set_xticks(x)
ax.set_xticklabels(ch_pd["Channel"])
ax.set_title("Rata-rata CTR & CVR per Channel (%)", fontsize=13, fontweight='bold')
ax.set_ylabel("Rate (%)")
ax.legend()

plt.suptitle("Analisis Performa Channel Marketing", fontsize=16, fontweight='bold')
plt.tight_layout()
plt.savefig("output/plots/channel_analysis.png", dpi=150, bbox_inches='tight')
plt.show()
print("✅ Plot disimpan: output/plots/channel_analysis.png")

# %% [markdown]
# ## 4. Feature Importance Analysis

# %%
fi_data = metrics.get("feature_importance", [])
fi_df = pd.DataFrame(fi_data).sort_values("Importance", ascending=True)

plt.figure(figsize=(10, 7))
colors = plt.cm.RdYlGn(np.linspace(0.2, 0.9, len(fi_df)))
plt.barh(fi_df["Feature"], fi_df["Importance"], color=colors, edgecolor='white')
plt.xlabel("Importance Score", fontsize=12)
plt.title("Feature Importance — Random Forest Classifier\n(Fitur Paling Berpengaruh terhadap Profitabilitas)", fontsize=14, fontweight='bold')
for i, (_, row) in enumerate(fi_df.iterrows()):
    plt.text(row["Importance"] + 0.002, i, f'{row["Importance"]:.4f}', va='center', fontsize=9)
plt.tight_layout()
plt.savefig("output/plots/feature_importance_detailed.png", dpi=150, bbox_inches='tight')
plt.show()
print("✅ Plot disimpan: output/plots/feature_importance_detailed.png")

# %% [markdown]
# ## 5. Distribusi Profitabilitas

# %%
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

# ROI distribution
roi_pd = df.select("ROI").toPandas()
ax = axes[0]
ax.hist(roi_pd["ROI"], bins=50, color='steelblue', edgecolor='white', alpha=0.8)
ax.axvline(x=1.0, color='red', linestyle='--', linewidth=2, label='Threshold (ROI=1.0)')
ax.set_title("Distribusi ROI Seluruh Kampanye", fontsize=13, fontweight='bold')
ax.set_xlabel("ROI")
ax.set_ylabel("Frekuensi")
ax.legend()

# Profitable vs Not
label_pd = df.groupBy("is_profitable").count().toPandas()
ax = axes[1]
labels = ['Not Profitable', 'Profitable']
sizes = [label_pd.loc[label_pd['is_profitable']==0, 'count'].values[0] if 0 in label_pd['is_profitable'].values else 0,
         label_pd.loc[label_pd['is_profitable']==1, 'count'].values[0] if 1 in label_pd['is_profitable'].values else 0]
colors_pie = ['#e74c3c', '#2ecc71']
explode = (0.05, 0.05)
ax.pie(sizes, explode=explode, labels=labels, colors=colors_pie, autopct='%1.1f%%',
       shadow=True, startangle=90, textprops={'fontsize': 12})
ax.set_title("Proporsi Profitable vs Not Profitable", fontsize=13, fontweight='bold')

plt.tight_layout()
plt.savefig("output/plots/profitability_distribution.png", dpi=150, bbox_inches='tight')
plt.show()
print("✅ Plot disimpan: output/plots/profitability_distribution.png")

# %% [markdown]
# ## 6. Rekomendasi Bisnis Actionable

# %%
print("=" * 70)
print("💡 REKOMENDASI BISNIS ACTIONABLE")
print("=" * 70)

# Analisis data untuk rekomendasi
best_channel = ch_pd.loc[ch_pd["Avg_ROI"].idxmax()]
worst_channel = ch_pd.loc[ch_pd["Avg_ROI"].idxmin()]
best_profitable = ch_pd.loc[ch_pd["Profitable_Rate"].idxmax()]

# Top features
top_features = pd.DataFrame(fi_data).sort_values("Importance", ascending=False).head(3)

print(f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📌 REKOMENDASI 1: Optimasi Alokasi Anggaran berdasarkan Channel
   Channel dengan ROI tertinggi : {best_channel['Channel']} (Avg ROI = {best_channel['Avg_ROI']:.4f})
   Channel dengan ROI terendah  : {worst_channel['Channel']} (Avg ROI = {worst_channel['Avg_ROI']:.4f})
   
   ➡️  AKSI: Alokasikan 40-50% anggaran marketing ke channel {best_channel['Channel']}
       yang menunjukkan ROI tertinggi. Kurangi investasi di channel 
       {worst_channel['Channel']} atau lakukan optimasi konten/targeting.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📌 REKOMENDASI 2: Fokus pada Fitur Kunci untuk Profitabilitas
   Fitur paling berpengaruh:
""")
for _, row in top_features.iterrows():
    print(f"      - {row['Feature']:20s} (importance: {row['Importance']:.4f})")

print(f"""
   ➡️  AKSI: Tingkatkan monitoring dan optimasi pada metrik 
       {top_features.iloc[0]['Feature']} karena memiliki pengaruh terbesar
       terhadap profitabilitas kampanye.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📌 REKOMENDASI 3: Profil Kampanye Profitable
   Channel dengan tingkat profitabilitas tertinggi: {best_profitable['Channel']} ({best_profitable['Profitable_Rate']:.1f}%)
   
   ➡️  AKSI: Replikasi karakteristik kampanye profitable di channel 
       {best_profitable['Channel']}. Gunakan model prediktif sebelum meluncurkan
       kampanye baru — estimasi revenue dengan Linear Regression (R²={reg['r2']:.4f})
       dan cek probabilitas profitabilitas dengan Random Forest 
       (Accuracy={clf['accuracy']:.4f}).

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📌 REKOMENDASI 4: Implementasi Early Warning System
   ➡️  AKSI: Integrasikan model klasifikasi ke dalam modul CRM ERP untuk 
       memberikan peringatan dini (early warning) saat sebuah kampanye
       diprediksi menghasilkan ROI < 1.0. Tim marketing dapat segera
       melakukan penyesuaian strategi (budget reallocation, creative change,
       audience retargeting) sebelum kerugian membesar.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""")

# %% [markdown]
# ## 7. Generate Report File

# %%
report = f"""
================================================================================
        LAPORAN ANALITIK - MARKETING CAMPAIGN PERFORMANCE
        Proyek Akhir Big Data dan Analitik (CSD60707)
================================================================================

Tanggal Generate: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}

1. RINGKASAN DATASET
   Total Kampanye   : {df.count():,}
   Jumlah Channel   : 5 (Search, Email, Display, Social, Influencer)
   Periode Data     : 2025
   Jumlah Fitur     : {len(df.columns)} kolom

2. HASIL MODEL KLASIFIKASI (Random Forest)
   Accuracy         : {clf['accuracy']:.4f}
   F1-Score         : {clf['f1_score']:.4f}
   Precision        : {clf['precision']:.4f}
   Recall           : {clf['recall']:.4f}
   AUC-ROC          : {clf['auc_roc']:.4f}

3. HASIL MODEL REGRESI (Linear Regression)
   R²               : {reg['r2']:.4f}
   RMSE             : {reg['rmse']:.2f} USD
   MAE              : {reg['mae']:.2f} USD

4. CHANNEL PERFORMANCE
{ch_pd[['Channel', 'Total_Campaigns', 'Avg_ROI', 'Avg_Revenue', 'Profitable_Rate']].to_string(index=False)}

5. FEATURE IMPORTANCE (Top 5)
{pd.DataFrame(fi_data).sort_values('Importance', ascending=False).head(5).to_string(index=False)}

6. REKOMENDASI BISNIS
   1) Alokasikan anggaran lebih besar ke channel {best_channel['Channel']} (ROI tertinggi)
   2) Monitor dan optimalkan metrik {top_features.iloc[0]['Feature']} sebagai driver utama profit
   3) Replikasi profil kampanye profitable dari channel {best_profitable['Channel']}
   4) Integrasikan model prediktif ke CRM ERP sebagai early warning system

================================================================================
"""

report_path = "output/reports/analytics_report.txt"
with open(report_path, 'w') as f:
    f.write(report)
print(f"✅ Laporan disimpan: {report_path}")

# %% [markdown]
# ## 8. Daftar Semua Plot yang Dihasilkan

# %%
print("📁 DAFTAR OUTPUT YANG DIHASILKAN:")
print("=" * 50)
plots_dir = "output/plots"
for f in sorted(os.listdir(plots_dir)):
    size = os.path.getsize(os.path.join(plots_dir, f)) / 1024
    print(f"   📊 {f} ({size:.1f} KB)")
print()
reports_dir = "output/reports"
for f in sorted(os.listdir(reports_dir)):
    size = os.path.getsize(os.path.join(reports_dir, f)) / 1024
    print(f"   📄 {f} ({size:.1f} KB)")

# %%
spark.stop()
print("\n✅ SparkSession dihentikan. Notebook 4 selesai!")
print("🎉 SELURUH PIPELINE ANALITIK SELESAI!")
