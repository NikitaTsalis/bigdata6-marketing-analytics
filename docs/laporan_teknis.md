# LAPORAN TEKNIS PROYEK AKHIR
## Big Data dan Analitik (CSD60707)

### Analisis Performa Kampanye Marketing menggunakan Klasifikasi dan Regresi Berbasis Spark MLlib pada Ekosistem Big Data ERP CRM-Marketing

---

**Anggota Tim:**

| No | Nama | NIM | Peran |
|----|------|-----|-------|
| 1 | Esa Khafidotul Khusna Rois | - | Data Engineer 1 (Hadoop/Ingestion) |
| 2 | Naufal Zahdan Zulfakar | 245150401111003 | Data Engineer 2 (Spark Processing) |
| 3 | M Takhta Ali Sulthon | 235150400111055 | ML Engineer (Modeling & Analytics) |
| 4 | Nikita Tsalis Akmalinda Yanisa | 235150401111041 | Project Manager & Documentation |

---

## 1. Pendahuluan

### 1.1 Latar Belakang
Dalam sistem Enterprise Resource Planning (ERP) modern, modul CRM mengelola seluruh siklus interaksi perusahaan dengan pelanggan. Salah satu fungsi kritis adalah pengelolaan kampanye marketing yang mencakup saluran digital (Search, Email, Social Media, Display, Influencer). Proyek ini mengimplementasikan Big Data Analytics berbasis Spark MLlib untuk membangun model prediktif yang mampu mengklasifikasikan profitabilitas kampanye dan memprediksi revenue.

### 1.2 Tujuan
1. **Klasifikasi:** Random Forest Classifier untuk mengklasifikasikan kampanye sebagai Profitable (ROI ≥ 1.0) atau Not Profitable
2. **Regresi:** Linear Regression untuk memprediksi Revenue_USD

### 1.3 Dataset
- **Sumber:** Kaggle - Marketing Campaign Performance Dataset
- **Records:** 10.000 kampanye marketing
- **Atribut:** 11 kolom
- **Periode:** 2025

---

## 2. Arsitektur Sistem

### 2.1 Teknologi yang Digunakan
| Komponen | Teknologi | Fungsi |
|----------|-----------|--------|
| Data Ingestion | Kaggle API, MinIO Client | Download & upload data |
| Storage | MinIO, HDFS | Data lake & distributed storage |
| Processing | Apache Spark | ETL & feature engineering |
| Analytics | Spark MLlib | Machine learning |
| Visualization | Jupyter, Matplotlib, Seaborn | Dashboard & reporting |

### 2.2 Alur Data (Data Pipeline)
```
Kaggle CSV → MinIO (raw/) → Spark DataFrame → Cleaning & Feature Engineering → Parquet (processed/) → Spark MLlib → Model → Predictions → Visualization
```

---

## 3. Implementasi

### 3.1 Data Ingestion (Tugas 1 — Data Engineer 1)
- Download dataset dari Kaggle menggunakan Kaggle API
- Upload ke MinIO bucket `marketing-data/raw/`
- Transfer ke HDFS `/user/hadoop/marketing/raw/`
- Verifikasi integritas: 10.000 records, 0% data loss

### 3.2 Data Processing (Tugas 2 — Data Engineer 2)
**EDA:**
- Statistik deskriptif seluruh kolom numerik
- Distribusi kampanye per channel
- Matriks korelasi antar fitur

**Preprocessing:**
- Penanganan missing values (median/modus imputation)
- Deteksi & penanganan outlier (IQR Winsorization)

**Feature Engineering:**
| Fitur Baru | Formula | Deskripsi |
|------------|---------|-----------|
| CTR | Clicks / Impressions | Click-Through Rate |
| CPC | Cost_USD / Clicks | Cost Per Click |
| CPL | Cost_USD / Leads | Cost Per Lead |
| CVR | Conversions / Clicks | Conversion Rate |
| Campaign_Duration | EndDate - StartDate | Durasi (hari) |
| is_profitable | 1 if ROI ≥ 1.0 else 0 | Label klasifikasi |

**Encoding:**
- StringIndexer: Channel → Channel_Index
- OneHotEncoder: Channel_Index → Channel_Vec

### 3.3 Machine Learning Modeling (Tugas 3 — ML Engineer)

#### Model 1: Random Forest Classifier
- **Target:** is_profitable (binary)
- **Fitur:** Impressions, Clicks, Leads, Conversions, Cost_USD, CTR, CPC, CPL, CVR, Campaign_Duration, Channel_Index
- **Split:** 80% training, 20% testing
- **Tuning:** CrossValidator (5-fold) dengan ParamGridBuilder
  - numTrees: [50, 100, 150]
  - maxDepth: [5, 10, 15]

**Hasil Evaluasi:**
| Metrik | Nilai | Target | Status |
|--------|-------|--------|--------|
| Accuracy | _[isi setelah run]_ | ≥ 0.80 | ✅/❌ |
| F1-Score | _[isi setelah run]_ | ≥ 0.78 | ✅/❌ |
| Precision | _[isi setelah run]_ | - | - |
| Recall | _[isi setelah run]_ | - | - |
| AUC-ROC | _[isi setelah run]_ | - | - |

#### Model 2: Linear Regression
- **Target:** Revenue_USD (continuous)
- **Tuning:** CrossValidator (5-fold)
  - maxIter: [50, 100]
  - regParam: [0.01, 0.1, 0.3]
  - elasticNetParam: [0.0, 0.5, 1.0]

**Hasil Evaluasi:**
| Metrik | Nilai | Target | Status |
|--------|-------|--------|--------|
| R² | _[isi setelah run]_ | ≥ 0.75 | ✅/❌ |
| RMSE | _[isi setelah run]_ | ≤ 700 USD | ✅/❌ |
| MAE | _[isi setelah run]_ | - | - |

---

## 4. Visualisasi Hasil
*(Sertakan screenshot dari output Notebook 4)*

1. **Dashboard Model Performance** - Ringkasan metrik kedua model
2. **Confusion Matrix** - Visualisasi hasil klasifikasi
3. **Feature Importance** - Fitur paling berpengaruh terhadap profitabilitas
4. **Actual vs Predicted Revenue** - Scatter plot regresi
5. **Channel Analysis** - Performa per channel marketing
6. **Profitability Distribution** - Distribusi ROI dan proporsi profitable

---

## 5. Rekomendasi Bisnis
*(Isi berdasarkan output analitik — minimal 3 rekomendasi)*

1. **Optimasi Alokasi Anggaran:** _(channel dengan ROI tertinggi)_
2. **Fokus pada Metrik Kunci:** _(fitur dengan importance tertinggi)_
3. **Profil Kampanye Profitable:** _(karakteristik kampanye sukses)_
4. **Early Warning System:** Integrasi model prediktif ke CRM ERP

---

## 6. Kesimpulan
_(Isi setelah seluruh pipeline dijalankan)_

---

## 7. Referensi
1. Dataset: https://www.kaggle.com/datasets/mirzayasirabdullah07/marketing-campaign-performance-dataset
2. Apache Spark MLlib Documentation: https://spark.apache.org/docs/latest/ml-guide.html
3. MinIO Documentation: https://min.io/docs/minio/linux/index.html
4. Hadoop HDFS: https://hadoop.apache.org/docs/current/hadoop-project-dist/hadoop-hdfs/HdfsDesign.html
