# 📊 Analisis Performa Kampanye Marketing
## Klasifikasi dan Regresi Berbasis Spark MLlib pada Ekosistem Big Data ERP CRM-Marketing

**Mata Kuliah:** Big Data dan Analitik (CSD60707)

### 👥 Anggota Tim
| No | Nama | NIM | Peran |
|----|------|-----|-------|
| 1 | Esa Khafidotul Khusna Rois | 245150407111069| Data Engineer 1 (Data Ingestion) |
| 2 | Naufal Zahdan Zulfakar | 245150401111003 | Data Engineer 2 (Spark Processing) |
| 3 | M Takhta Ali Sulthon | 235150400111055 | ML Engineer (Modeling & Analytics) |
| 4 | Nikita Tsalis Akmalinda Yanisa | 235150401111041 | Project Manager & Documentation |
 
---

## 📁 Struktur Proyek

```
bigdata6-marketing-analytics/
├── README.md
├── docker-compose.yml
├── requirements.txt
├── config/
│   └── spark_config.py
├── data/
│   └── raw/
│       └── marketing_campaign_performance_10000.csv
├── notebooks/
│   ├── 01_data_ingestion.ipynb
│   ├── 02_data_processing_eda.ipynb
│   ├── 03_ml_modeling.ipynb
│   └── 04_visualization_reporting.ipynb
├── scripts/
│   └── download_dataset.py
└── docs/
    ├── architecture.md
    ├── setup_guide.md
    └── laporan_teknis.md
```

---

## 🏗️ Arsitektur Sistem (Medallion Architecture)

```
┌─────────────┐      ┌───────────────────────── MinIO Data Lake ─────────────────────────┐
│   Kaggle    │────▶ │  [Bronze]      ▶  [Silver]        ▶  [Gold]         ▶  [Models]   │
│  (Dataset)  │      │  Raw CSV       │  Clean Parquet   │  Aggregations   │  ML Models  │
└─────────────┘      └───────────────────────────────────────────────────────────────────┘
                            ▲                │                   │               ▲
                            └─────── Apache Spark (ETL & MLlib) ─┴───────────────┘
```

Ekosistem ini menggunakan konsep **Medallion Architecture**:
- **Bronze Layer**: Data mentah (CSV) yang di-ingest apa adanya dari sumber.
- **Silver Layer**: Data yang sudah dibersihkan dan dilakukan feature engineering (Parquet).
- **Gold Layer**: Data prediksi dan agregasi level bisnis yang siap digunakan untuk reporting/dashboard.
- **Models**: Artefak model Machine Learning yang telah dilatih.

---

## 🚀 Quick Start

### Prasyarat
- Python 3.8+
- Java 8 atau 11 (untuk Spark)
- Apache Spark 3.3+
- MinIO Server
- Jupyter Notebook / JupyterLab

### Langkah-langkah

1. **Install dependensi Python:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Start MinIO Server:**
   ```bash
   docker-compose up -d minio
   # atau manual:
   minio server ./minio-data --console-address ":9001"
   ```

3. **Download dataset dari Kaggle (jika belum ada):**
   ```bash
   python scripts/download_dataset.py
   ```

4. **Jalankan Jupyter & buka notebook secara berurutan:**
   ```bash
   jupyter notebook
   ```
   ```
   notebooks/01_data_ingestion.ipynb        → Ingestion data ke MinIO
   notebooks/02_data_processing_eda.ipynb   → Preprocessing & EDA
   notebooks/03_ml_modeling.ipynb           → Training model ML
   notebooks/04_visualization_reporting.ipynb → Visualisasi hasil
   ```

---

## 📊 Model yang Dibangun

### 1. Random Forest Classifier (Klasifikasi)
- **Target:** `is_profitable` (1 = ROI ≥ 1.0, 0 = ROI < 1.0)
- **Fitur:** Impressions, Clicks, Leads, Conversions, Cost_USD, CTR, CPC, CPL, CVR, Campaign_Duration, Channel (encoded)
- **Metrik target:** Accuracy ≥ 80%, F1-Score ≥ 0.78

### 2. Linear Regression (Regresi)
- **Target:** `Revenue_USD`
- **Fitur:** Impressions, Clicks, Leads, Conversions, Cost_USD, CTR, CPC, CPL, CVR, Campaign_Duration, Channel (encoded)
- **Metrik target:** R² ≥ 0.75, RMSE ≤ 700 USD

---

## 📄 Lisensi Dataset
Apache 2.0 — Dataset dari [Kaggle](https://www.kaggle.com/datasets/mirzayasirabdullah07/marketing-campaign-performance-dataset)
