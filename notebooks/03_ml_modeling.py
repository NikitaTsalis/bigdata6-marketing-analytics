# %% [markdown]
# # 🤖 Notebook 3: ML Modeling (Klasifikasi & Regresi)
# ## Proyek Big Data - Analisis Performa Kampanye Marketing
#
# **Penanggung Jawab:** ML Engineer (M Takhta Ali Sulthon - 235150400111055)
#
# **Tujuan:**
# 1. Membangun pipeline Spark MLlib (VectorAssembler + Model)
# 2. Random Forest Classifier → klasifikasi is_profitable
# 3. Linear Regression → prediksi Revenue_USD
# 4. Hyperparameter tuning (CrossValidator + ParamGridBuilder)
# 5. Evaluasi dan analisis feature importance
# 6. Menyimpan model terbaik ke HDFS
#
# ---

# %% [markdown]
# ## 1. Setup

# %%
import os, sys, warnings
warnings.filterwarnings('ignore')
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, count, when, round as spark_round
from pyspark.ml import Pipeline
from pyspark.ml.feature import VectorAssembler, StringIndexer, StandardScaler
from pyspark.ml.classification import RandomForestClassifier
from pyspark.ml.regression import LinearRegression
from pyspark.ml.evaluation import (
    BinaryClassificationEvaluator,
    MulticlassClassificationEvaluator,
    RegressionEvaluator
)
from pyspark.ml.tuning import CrossValidator, ParamGridBuilder
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import json

plt.style.use('seaborn-v0_8-darkgrid')
print("✅ Library berhasil diimport!")

# %%
HDFS_NAMENODE = "hdfs://localhost:9000"
HDFS_PROCESSED_DIR = "/user/hadoop/marketing/processed"
HDFS_MODEL_DIR = "/user/hadoop/marketing/model"
LOCAL_PARQUET = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'processed', 'marketing_campaign_features.parquet')
RANDOM_SEED = 42

spark = SparkSession.builder \
    .appName("Marketing_Campaign_ML_Modeling") \
    .master("local[*]") \
    .config("spark.driver.memory", "4g") \
    .config("spark.sql.shuffle.partitions", "8") \
    .getOrCreate()
spark.sparkContext.setLogLevel("WARN")
print(f"✅ SparkSession aktif — Spark {spark.version}")

# %% [markdown]
# ## 2. Memuat Data Processed

# %%
try:
    hdfs_path = f"{HDFS_NAMENODE}{HDFS_PROCESSED_DIR}/marketing_campaign_features.parquet"
    df = spark.read.parquet(hdfs_path)
    print(f"✅ Data dimuat dari HDFS: {df.count():,} records")
except:
    df = spark.read.parquet(LOCAL_PARQUET)
    print(f"✅ Data dimuat dari lokal: {df.count():,} records")

print(f"   Kolom: {df.columns}")

# %% [markdown]
# ## 3. Persiapan Fitur

# %%
# Fitur numerik yang akan digunakan
feature_cols = [
    "Impressions", "Clicks", "Leads", "Conversions", "Cost_USD",
    "CTR", "CPC", "CPL", "CVR", "Campaign_Duration", "Channel_Index"
]

# Pastikan tipe data benar
for c in feature_cols:
    df = df.withColumn(c, col(c).cast("double"))

# Hapus baris dengan null di kolom fitur
df_clean = df.dropna(subset=feature_cols + ["is_profitable", "Revenue_USD"])
print(f"✅ Data bersih: {df_clean.count():,} records (setelah drop null)")

# %% [markdown]
# ## 4. VectorAssembler & Train-Test Split

# %%
# Assembler untuk menggabungkan fitur
assembler = VectorAssembler(inputCols=feature_cols, outputCol="features", handleInvalid="skip")

# Scaler untuk normalisasi
scaler = StandardScaler(inputCol="features", outputCol="scaled_features", withStd=True, withMean=True)

# Train-test split (80-20)
train_data, test_data = df_clean.randomSplit([0.8, 0.2], seed=RANDOM_SEED)

print(f"📊 Split Data:")
print(f"   Training  : {train_data.count():,} records ({train_data.count()/df_clean.count()*100:.1f}%)")
print(f"   Testing   : {test_data.count():,} records ({test_data.count()/df_clean.count()*100:.1f}%)")

# Distribusi label pada train & test
print(f"\n📊 Distribusi is_profitable:")
print("   Training:")
train_data.groupBy("is_profitable").count().show()
print("   Testing:")
test_data.groupBy("is_profitable").count().show()

# %% [markdown]
# ---
# ## 5. MODEL 1: Random Forest Classifier (Klasifikasi)
# **Target:** `is_profitable` (0 = Not Profitable, 1 = Profitable)
# **Metrik Target:** Accuracy >= 80%, F1-Score >= 0.78

# %% [markdown]
# ### 5.1 Baseline Random Forest

# %%
print("=" * 60)
print("🌲 RANDOM FOREST CLASSIFIER")
print("=" * 60)

# Pipeline: Assembler -> RF
rf = RandomForestClassifier(
    labelCol="is_profitable",
    featuresCol="features",
    numTrees=100,
    maxDepth=10,
    seed=RANDOM_SEED
)

rf_pipeline = Pipeline(stages=[assembler, rf])

# Training
print("⏳ Training Random Forest Classifier...")
rf_model = rf_pipeline.fit(train_data)
print("✅ Training selesai!")

# Prediksi pada test set
rf_predictions = rf_model.transform(test_data)

# %% [markdown]
# ### 5.2 Evaluasi Baseline

# %%
# Evaluasi metrik klasifikasi
accuracy_eval = MulticlassClassificationEvaluator(
    labelCol="is_profitable", predictionCol="prediction", metricName="accuracy")
f1_eval = MulticlassClassificationEvaluator(
    labelCol="is_profitable", predictionCol="prediction", metricName="f1")
precision_eval = MulticlassClassificationEvaluator(
    labelCol="is_profitable", predictionCol="prediction", metricName="weightedPrecision")
recall_eval = MulticlassClassificationEvaluator(
    labelCol="is_profitable", predictionCol="prediction", metricName="weightedRecall")
auc_eval = BinaryClassificationEvaluator(
    labelCol="is_profitable", rawPredictionCol="rawPrediction", metricName="areaUnderROC")

accuracy = accuracy_eval.evaluate(rf_predictions)
f1 = f1_eval.evaluate(rf_predictions)
precision = precision_eval.evaluate(rf_predictions)
recall = recall_eval.evaluate(rf_predictions)
auc = auc_eval.evaluate(rf_predictions)

print("📊 EVALUASI BASELINE RANDOM FOREST:")
print(f"   Accuracy  : {accuracy:.4f} {'✅' if accuracy >= 0.80 else '❌'} (target >= 0.80)")
print(f"   F1-Score  : {f1:.4f} {'✅' if f1 >= 0.78 else '❌'} (target >= 0.78)")
print(f"   Precision : {precision:.4f}")
print(f"   Recall    : {recall:.4f}")
print(f"   AUC-ROC   : {auc:.4f}")

# %% [markdown]
# ### 5.3 Confusion Matrix

# %%
# Hitung confusion matrix
cm_data = rf_predictions.select("is_profitable", "prediction") \
    .groupBy("is_profitable", "prediction").count().toPandas()

# Buat matriks
cm = np.zeros((2, 2), dtype=int)
for _, row in cm_data.iterrows():
    cm[int(row["is_profitable"])][int(row["prediction"])] = int(row["count"])

print("📊 Confusion Matrix:")
print(f"                    Predicted")
print(f"                  Not Prof.  Prof.")
print(f"   Actual Not Prof.  {cm[0][0]:5d}   {cm[0][1]:5d}")
print(f"   Actual Prof.      {cm[1][0]:5d}   {cm[1][1]:5d}")

# Visualisasi
plt.figure(figsize=(8, 6))
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
            xticklabels=['Not Profitable', 'Profitable'],
            yticklabels=['Not Profitable', 'Profitable'],
            annot_kws={"size": 16})
plt.title('Confusion Matrix - Random Forest Classifier', fontsize=14, fontweight='bold')
plt.ylabel('Actual Label', fontsize=12)
plt.xlabel('Predicted Label', fontsize=12)
plt.tight_layout()
os.makedirs("output/plots", exist_ok=True)
plt.savefig("output/plots/confusion_matrix_rf.png", dpi=150, bbox_inches='tight')
plt.show()
print("✅ Plot disimpan: output/plots/confusion_matrix_rf.png")

# %% [markdown]
# ### 5.4 Hyperparameter Tuning (CrossValidator)

# %%
print("⏳ Hyperparameter Tuning dengan CrossValidator...")

rf_tuning = RandomForestClassifier(
    labelCol="is_profitable", featuresCol="features", seed=RANDOM_SEED)

# ParamGrid
paramGrid_rf = ParamGridBuilder() \
    .addGrid(rf_tuning.numTrees, [50, 100, 150]) \
    .addGrid(rf_tuning.maxDepth, [5, 10, 15]) \
    .build()

rf_pipeline_tune = Pipeline(stages=[assembler, rf_tuning])

cv_rf = CrossValidator(
    estimator=rf_pipeline_tune,
    estimatorParamMaps=paramGrid_rf,
    evaluator=f1_eval,
    numFolds=5,
    seed=RANDOM_SEED
)

cv_rf_model = cv_rf.fit(train_data)
print("✅ CrossValidation selesai!")

# Prediksi dengan model terbaik
rf_best_predictions = cv_rf_model.transform(test_data)

# Evaluasi model terbaik
best_accuracy = accuracy_eval.evaluate(rf_best_predictions)
best_f1 = f1_eval.evaluate(rf_best_predictions)
best_precision = precision_eval.evaluate(rf_best_predictions)
best_recall = recall_eval.evaluate(rf_best_predictions)
best_auc = auc_eval.evaluate(rf_best_predictions)

print(f"\n📊 EVALUASI BEST MODEL (setelah tuning):")
print(f"   Accuracy  : {best_accuracy:.4f} {'✅' if best_accuracy >= 0.80 else '❌'}")
print(f"   F1-Score  : {best_f1:.4f} {'✅' if best_f1 >= 0.78 else '❌'}")
print(f"   Precision : {best_precision:.4f}")
print(f"   Recall    : {best_recall:.4f}")
print(f"   AUC-ROC   : {best_auc:.4f}")

# Best parameters
best_rf = cv_rf_model.bestModel.stages[-1]
print(f"\n📋 Best Hyperparameters:")
print(f"   numTrees : {best_rf.getNumTrees}")
print(f"   maxDepth : {best_rf.getOrDefault('maxDepth')}")

# %% [markdown]
# ### 5.5 Feature Importance

# %%
# Feature importance dari model terbaik
importances = best_rf.featureImportances.toArray()
fi_df = pd.DataFrame({
    'Feature': feature_cols,
    'Importance': importances
}).sort_values('Importance', ascending=False)

print("📊 Feature Importance (Random Forest):")
for _, row in fi_df.iterrows():
    bar = '█' * int(row['Importance'] * 50)
    print(f"   {row['Feature']:20s} : {row['Importance']:.4f} {bar}")

# Visualisasi
plt.figure(figsize=(10, 6))
colors = plt.cm.viridis(np.linspace(0.3, 0.9, len(fi_df)))
plt.barh(fi_df['Feature'], fi_df['Importance'], color=colors)
plt.xlabel('Importance', fontsize=12)
plt.title('Feature Importance - Random Forest Classifier', fontsize=14, fontweight='bold')
plt.gca().invert_yaxis()
plt.tight_layout()
plt.savefig("output/plots/feature_importance_rf.png", dpi=150, bbox_inches='tight')
plt.show()
print("✅ Plot disimpan: output/plots/feature_importance_rf.png")

# %% [markdown]
# ---
# ## 6. MODEL 2: Linear Regression (Regresi)
# **Target:** `Revenue_USD`
# **Metrik Target:** R² >= 0.75, RMSE <= 700 USD

# %% [markdown]
# ### 6.1 Baseline Linear Regression

# %%
print("=" * 60)
print("📈 LINEAR REGRESSION")
print("=" * 60)

lr = LinearRegression(
    labelCol="Revenue_USD",
    featuresCol="features",
    maxIter=100,
    regParam=0.1,
    elasticNetParam=0.5
)

lr_pipeline = Pipeline(stages=[assembler, lr])

print("⏳ Training Linear Regression...")
lr_model = lr_pipeline.fit(train_data)
print("✅ Training selesai!")

lr_predictions = lr_model.transform(test_data)

# %% [markdown]
# ### 6.2 Evaluasi Baseline

# %%
rmse_eval = RegressionEvaluator(labelCol="Revenue_USD", predictionCol="prediction", metricName="rmse")
r2_eval = RegressionEvaluator(labelCol="Revenue_USD", predictionCol="prediction", metricName="r2")
mae_eval = RegressionEvaluator(labelCol="Revenue_USD", predictionCol="prediction", metricName="mae")

rmse = rmse_eval.evaluate(lr_predictions)
r2 = r2_eval.evaluate(lr_predictions)
mae = mae_eval.evaluate(lr_predictions)

print("📊 EVALUASI BASELINE LINEAR REGRESSION:")
print(f"   R²   : {r2:.4f} {'✅' if r2 >= 0.75 else '❌'} (target >= 0.75)")
print(f"   RMSE : {rmse:.2f} USD {'✅' if rmse <= 700 else '❌'} (target <= 700)")
print(f"   MAE  : {mae:.2f} USD")

# Koefisien model
lr_fitted = lr_model.stages[-1]
print(f"\n📋 Model Summary:")
print(f"   Intercept    : {lr_fitted.intercept:.4f}")
print(f"   Coefficients :")
for feat, coef in zip(feature_cols, lr_fitted.coefficients.toArray()):
    print(f"      {feat:20s} : {coef:12.4f}")

# %% [markdown]
# ### 6.3 Hyperparameter Tuning

# %%
print("⏳ Hyperparameter Tuning Linear Regression...")

lr_tuning = LinearRegression(labelCol="Revenue_USD", featuresCol="features")

paramGrid_lr = ParamGridBuilder() \
    .addGrid(lr_tuning.maxIter, [50, 100]) \
    .addGrid(lr_tuning.regParam, [0.01, 0.1, 0.3]) \
    .addGrid(lr_tuning.elasticNetParam, [0.0, 0.5, 1.0]) \
    .build()

lr_pipeline_tune = Pipeline(stages=[assembler, lr_tuning])

cv_lr = CrossValidator(
    estimator=lr_pipeline_tune,
    estimatorParamMaps=paramGrid_lr,
    evaluator=r2_eval,
    numFolds=5,
    seed=RANDOM_SEED
)

cv_lr_model = cv_lr.fit(train_data)
print("✅ CrossValidation selesai!")

lr_best_predictions = cv_lr_model.transform(test_data)

best_rmse = rmse_eval.evaluate(lr_best_predictions)
best_r2 = r2_eval.evaluate(lr_best_predictions)
best_mae = mae_eval.evaluate(lr_best_predictions)

print(f"\n📊 EVALUASI BEST MODEL (setelah tuning):")
print(f"   R²   : {best_r2:.4f} {'✅' if best_r2 >= 0.75 else '❌'}")
print(f"   RMSE : {best_rmse:.2f} USD {'✅' if best_rmse <= 700 else '❌'}")
print(f"   MAE  : {best_mae:.2f} USD")

best_lr = cv_lr_model.bestModel.stages[-1]
print(f"\n📋 Best Hyperparameters:")
print(f"   maxIter         : {best_lr.getOrDefault('maxIter')}")
print(f"   regParam        : {best_lr.getOrDefault('regParam')}")
print(f"   elasticNetParam : {best_lr.getOrDefault('elasticNetParam')}")

# %% [markdown]
# ### 6.4 Actual vs Predicted Scatter Plot

# %%
pred_pd = lr_best_predictions.select("Revenue_USD", "prediction").toPandas()

plt.figure(figsize=(10, 8))
plt.scatter(pred_pd["Revenue_USD"], pred_pd["prediction"], alpha=0.4, s=15, c='steelblue', edgecolors='navy', linewidths=0.3)
max_val = max(pred_pd["Revenue_USD"].max(), pred_pd["prediction"].max())
min_val = min(pred_pd["Revenue_USD"].min(), pred_pd["prediction"].min())
plt.plot([min_val, max_val], [min_val, max_val], 'r--', linewidth=2, label='Ideal (y=x)')
plt.xlabel('Actual Revenue (USD)', fontsize=12)
plt.ylabel('Predicted Revenue (USD)', fontsize=12)
plt.title(f'Actual vs Predicted Revenue — R²={best_r2:.4f}, RMSE={best_rmse:.2f}',
          fontsize=14, fontweight='bold')
plt.legend(fontsize=11)
plt.tight_layout()
plt.savefig("output/plots/actual_vs_predicted_revenue.png", dpi=150, bbox_inches='tight')
plt.show()
print("✅ Plot disimpan: output/plots/actual_vs_predicted_revenue.png")

# %% [markdown]
# ## 7. Simpan Model ke HDFS

# %%
# Simpan model
local_model_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'models')
os.makedirs(local_model_dir, exist_ok=True)

# Simpan RF model
rf_local = os.path.join(local_model_dir, "rf_classifier")
cv_rf_model.bestModel.write().overwrite().save(rf_local)
print(f"✅ RF model disimpan: {rf_local}")

# Simpan LR model
lr_local = os.path.join(local_model_dir, "linear_regression")
cv_lr_model.bestModel.write().overwrite().save(lr_local)
print(f"✅ LR model disimpan: {lr_local}")

# Simpan ke HDFS (jika tersedia)
try:
    rf_hdfs = f"{HDFS_NAMENODE}{HDFS_MODEL_DIR}/rf_classifier"
    cv_rf_model.bestModel.write().overwrite().save(rf_hdfs)
    lr_hdfs = f"{HDFS_NAMENODE}{HDFS_MODEL_DIR}/linear_regression"
    cv_lr_model.bestModel.write().overwrite().save(lr_hdfs)
    print(f"✅ Model disimpan ke HDFS: {HDFS_MODEL_DIR}/")
except Exception as e:
    print(f"⚠️ HDFS tidak tersedia, model hanya disimpan lokal: {e}")

# Simpan metrik evaluasi
metrics = {
    "classification": {
        "model": "Random Forest Classifier",
        "accuracy": round(best_accuracy, 4),
        "f1_score": round(best_f1, 4),
        "precision": round(best_precision, 4),
        "recall": round(best_recall, 4),
        "auc_roc": round(best_auc, 4),
        "num_trees": best_rf.getNumTrees,
        "max_depth": best_rf.getOrDefault('maxDepth'),
    },
    "regression": {
        "model": "Linear Regression",
        "r2": round(best_r2, 4),
        "rmse": round(best_rmse, 2),
        "mae": round(best_mae, 2),
    },
    "feature_importance": fi_df.to_dict(orient='records')
}

metrics_path = os.path.join(local_model_dir, "metrics.json")
with open(metrics_path, 'w') as f:
    json.dump(metrics, f, indent=2)
print(f"✅ Metrik disimpan: {metrics_path}")

# %% [markdown]
# ## 8. Ringkasan

# %%
print("=" * 60)
print("📊 RINGKASAN ML MODELING")
print("=" * 60)
print(f"""
🌲 RANDOM FOREST CLASSIFIER (Klasifikasi Profitabilitas):
   Target     : is_profitable (ROI >= 1.0)
   Accuracy   : {best_accuracy:.4f} {'✅' if best_accuracy >= 0.80 else '❌'}
   F1-Score   : {best_f1:.4f} {'✅' if best_f1 >= 0.78 else '❌'}
   AUC-ROC    : {best_auc:.4f}
   Top Feature: {fi_df.iloc[0]['Feature']} ({fi_df.iloc[0]['Importance']:.4f})

📈 LINEAR REGRESSION (Prediksi Revenue):
   Target     : Revenue_USD
   R²         : {best_r2:.4f} {'✅' if best_r2 >= 0.75 else '❌'}
   RMSE       : {best_rmse:.2f} USD {'✅' if best_rmse <= 700 else '❌'}
   MAE        : {best_mae:.2f} USD

📁 MODEL TERSIMPAN:
   RF Local   : models/rf_classifier/
   LR Local   : models/linear_regression/
   Metrics    : models/metrics.json

✅ Modeling selesai! Lanjut ke Notebook 4 untuk Visualisasi.
""")

# %%
spark.stop()
print("✅ SparkSession dihentikan. Notebook 3 selesai!")
print("➡️  Lanjutkan ke Notebook 4: Visualization & Reporting")
