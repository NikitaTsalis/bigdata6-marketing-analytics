<<<<<<< HEAD
# 📊 Analisis Performa Kampanye Marketing
## Klasifikasi dan Regresi Berbasis Spark MLlib pada Ekosistem Big Data ERP CRM-Marketing

**Mata Kuliah:** Big Data dan Analitik (CSD60707)

### 👥 Anggota Tim
| No | Nama | NIM | Peran |
|----|------|-----|-------|
| 1 | Esa Khafidotul Khusna Rois | 245150407111069| Data Engineer 1 (Hadoop/Ingestion) |
| 2 | Naufal Zahdan Zulfakar | 245150401111003 | Data Engineer 2 (Spark Processing) |
| 3 | M Takhta Ali Sulthon | 235150400111055 | ML Engineer (Modeling & Analytics) |
| 4 | Nikita Tsalis Akmalinda Yanisa | 235150401111041 | Project Manager & Documentation |
 
---

## 📁 Struktur Proyek

```
BigData/
├── README.md                              # Dokumentasi utama proyek
├── docs/
│   ├── architecture.md                    # Dokumentasi arsitektur sistem
│   ├── setup_guide.md                     # Panduan instalasi & konfigurasi
│   └── laporan_teknis.md                  # Template laporan teknis akhir
├── config/
│   └── spark_config.py                    # Konfigurasi Spark Session
├── data/
│   └── raw/                               # Tempat menyimpan dataset CSV (lokal)
│       └── .gitkeep
├── notebooks/
│   ├── 01_data_ingestion.py               # Notebook 1: Data Ingestion ke MinIO/HDFS
│   ├── 02_data_processing_eda.py          # Notebook 2: Processing & EDA dengan Spark
│   ├── 03_ml_modeling.py                  # Notebook 3: ML Modeling (RF + LR)
│   └── 04_visualization_reporting.py      # Notebook 4: Visualisasi & Reporting
├── scripts/
│   ├── download_dataset.py                # Script download dataset dari Kaggle
│   ├── setup_minio.sh                     # Script setup MinIO bucket
│   └── setup_hdfs.sh                      # Script setup direktori HDFS
└── requirements.txt                       # Dependensi Python
```

---

## 🏗️ Arsitektur Sistem

```
┌─────────────┐      ┌──────────┐     ┌───────────────┐     ┌────────────┐     ┌──────────────┐
│   Kaggle    │────▶ │  MinIO   │────▶│ Apache Spark  │────▶│ Spark MLlib│────▶│   Jupyter  │
│  (Dataset)  │      │(Data Lake)│    │ (Processing)  │     │ (Modeling) │    │(Visualization)│
└─────────────┘      └──────────┘     └───────────────┘     └────────────┘     └──────────────┘
                         │                    │                    │
                    Raw CSV Data      Clean Parquet Data    Trained Models
                    di bucket         di HDFS/MinIO         di HDFS/MinIO
```

---

## 🚀 Quick Start

### Prasyarat
- Python 3.8+
- Java 8 atau 11 (untuk Spark)
- Apache Spark 3.x
- Hadoop 3.x (HDFS)
- MinIO Server
- Jupyter Notebook / JupyterLab

### Langkah-langkah

1. **Install dependensi Python:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Download dataset dari Kaggle:**
   ```bash
   python scripts/download_dataset.py
   ```

3. **Setup MinIO dan HDFS:**
   ```bash
   bash scripts/setup_minio.sh
   bash scripts/setup_hdfs.sh
   ```

4. **Jalankan notebook secara berurutan:**
   ```
   notebooks/01_data_ingestion.py        → Ingestion data ke MinIO/HDFS
   notebooks/02_data_processing_eda.py   → Preprocessing & EDA
   notebooks/03_ml_modeling.py           → Training model ML
   notebooks/04_visualization_reporting.py → Visualisasi hasil
   ```

> **Catatan:** File `.py` menggunakan format `# %%` (cell markers) yang dapat dibuka langsung di:
> - **VS Code** sebagai Interactive Python (Jupyter cells)
> - **Jupyter Notebook** setelah di-convert: `jupytext --to notebook file.py`
> - Atau langsung jalankan sebagai script Python biasa

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
=======
# bigdata6-marketing-analytics
Analisis Performa Kampanye Marketing menggunakan Spark MLlib
>>>>>>> 42da6ae4ad0f95a8f0addd5090a8552986ecb26c
