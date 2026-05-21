# 📊 Analisis Performa Kampanye Marketing
## Klasifikasi dan Regresi Berbasis Spark MLlib pada Ekosistem Big Data ERP CRM-Marketing
### Proyek Akhir Mata Kuliah Big Data dan Analitik (CSD60707)

[![GitHub Repository](https://img.shields.io/badge/GitHub-Repository-blue?logo=github&style=flat-square)](https://github.com/NikitaTsalis/bigdata6-marketing-analytics)
[![Python Version](https://img.shields.io/badge/Python-3.14.3-green?logo=python&style=flat-square)](https://www.python.org/)
[![Apache Spark](https://img.shields.io/badge/Apache%20Spark-3.3%2B-orange?logo=apachespark&logoColor=white&style=flat-square)](https://spark.apache.org/)
[![MinIO](https://img.shields.io/badge/MinIO-Object%20Storage-red?style=flat-square)](https://min.io/)
[![Hadoop HDFS](https://img.shields.io/badge/Hadoop%20HDFS-3.3%2B-blue?logo=apachehadoop&logoColor=white&style=flat-square)](https://hadoop.apache.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-Dashboard-red?logo=streamlit&style=flat-square)](https://streamlit.io/)

---

## 🔗 Repository GitHub Resmi
Seluruh kode sumber, dokumentasi arsitektur, laporan teknis, dan file konfigurasi dapat diakses secara publik melalui link di bawah ini:
👉 **[https://github.com/NikitaTsalis/bigdata6-marketing-analytics](https://github.com/NikitaTsalis/bigdata6-marketing-analytics)**

---

## 👥 Anggota Tim & Peran
Kami dari **Kelompok 6** bertanggung jawab atas perancangan pipeline data dan pemodelan analitik ini:

| No | Nama | NIM | Peran Utama |
|----|------|-----|-------------|
| 1 | **Esa Khafidotul Khusna Rois** | 245150407111069 | **Data Engineer 1** (Data Ingestion & HDFS Sync) |
| 2 | **Naufal Zahdan Zulfakar** | 245150401111003 | **Data Engineer 2** (Spark Processing, Clean & ETL) |
| 3 | **M Takhta Ali Sulthon** | 235150400111055 | **ML Engineer** (Spark MLlib Modeling, Tuning & Eval) |
| 4 | **Nikita Tsalis Akmalinda Yanisa** | 235150401111041 | **Project Manager & Documentation** (Business Analysis) |

---

## 📁 Struktur Proyek
```
bigdata6-marketing-analytics/
├── README.md                 <- Laporan & Panduan Utama (Dokumen Ini)
├── docker-compose.yml        <- Orkestrasi container MinIO Object Storage
├── requirements.txt          <- Dependensi library Python proyek
├── spark_conf.txt            <- Pengaturan SparkSession & S3A connector
├── data/
│   └── raw/                  <- Dataset pemasaran lokal (10.000 records)
├── notebooks/
│   ├── 01_data_ingestion.ipynb          <- Ingestion ke MinIO & sinkronisasi HDFS
│   ├── 02_data_processing_eda.ipynb     <- Pembersihan data, Winsorization & EDA
│   ├── 03_ml_modeling.ipynb             <- Pelatihan, CrossValidation & Ekstraksi Model ML
│   ├── 04_visualization_reporting.ipynb <- Verifikasi visualisasi hasil & metrik
│   └── dashboard.py                     <- File dasbor utama berbasis Streamlit
└── docs/
    ├── architecture.md       <- Dokumentasi detail arsitektur ekosistem
    ├── setup_guide.md        <- Panduan setup lingkungan & troubleshooting
    └── laporan_teknis.md     <- Laporan teknis lengkap proyek akhir
```

---

## 🏗️ Arsitektur Sistem (Medallion Architecture)

Proyek ini mengadopsi **Medallion Architecture** untuk menjamin data kualitas tinggi yang siap dikonsumsi oleh aplikasi bisnis CRM-Marketing ERP:

```
┌──────────────────┐      ┌───────────────────────── MinIO Data Lake ─────────────────────────┐
│    Kaggle API    │ ───> │  📁 bronze/      📁 silver/       📁 gold/         📁 models/     │
│ (Source Dataset) │      │  (Raw CSV)  ──>  (Parquet Clean)  (Predictions)    (Spark ML)     │
└──────────────────┘      └───────────────────────────────────────────────────────────────────┘
                                   │               │               │                ▲
                                   ▼               ▼               ▼                │
                          ┌─────────────────────────────────────────────────────────┐
                          │         Apache Spark Engine (PySpark & MLlib)           │
                          └─────────────────────────────────────────────────────────┘
                                                   │
                                                   ▼
                                      ┌────────────────────────┐
                                      │   Streamlit Dashboard  │
                                      │  (Reporting / BI App)  │
                                      └────────────────────────┘
```

1. **Bronze Layer:** Data CSV mentah asli diunggah apa adanya dari Kaggle API ke MinIO (`s3a://marketing-data/bronze/`) dan disinkronisasikan ke HDFS (`/user/hadoop/marketing/bronze/`) untuk menjamin integritas.
2. **Silver Layer:** Data dibersihkan (median imputation untuk *missing values*, IQR Winsorization untuk *outliers*), kolom kategorikal di-encode dengan `OneHotEncoder`, dan dilakukan *feature engineering* (CTR, CPC, CPL, CVR, Durasi Kampanye, `is_profitable`). Disimpan dalam format **Parquet** kolumnar terkompresi.
3. **Gold Layer:** Menyimpan hasil prediksi akhir dari model Klasifikasi & Regresi serta tabel agregasi bisnis yang siap dibaca secara *real-time* oleh dasbor eksekutif.
4. **Models Layer:** Menyimpan objek model biner Spark MLlib (`random_forest_classifier` & `linear_regression`) yang telah dituning agar dapat di-load kembali sewaktu-waktu.

---

## 📥 Alur Data Ingestion (Tugas DE-1)
- Pipeline diawali dengan memicu Kaggle API untuk mengunduh dataset secara aman.
- Mengunggah file CSV secara terprogram menggunakan PySpark & library S3A ke bucket MinIO.
- Melakukan replikasi data mentah ke sistem berkas terdistribusi HDFS menggunakan perintah filesystem terdistribusi.
- **Verifikasi:** Mengecek kesesuaian total records sebanyak **10.000 baris** di lokal, MinIO, dan HDFS (*0% data loss*).

---

## 📊 Hasil Evaluasi Model Machine Learning (Tugas MLE)

Model dibangun di atas dataframe terdistribusi menggunakan library **Spark MLlib** dengan pembagian data **80% Training Set** dan **20% Test Set** serta dioptimalkan menggunakan **5-Fold CrossValidator**.

### 1. Klasifikasi Profitabilitas (Random Forest Classifier)
- **Tujuan:** Memprediksi apakah kampanye pemasaran menghasilkan ROI $\ge$ 1.0 (`is_profitable = 1`) atau tidak (`is_profitable = 0`).
- **Fitur Input:** `Impressions`, `Clicks`, `Leads`, `Conversions`, `Cost_USD`, `CTR`, `CPC`, `CPL`, `CVR`, `Campaign_Duration`, `Channel_Index`.
- **Hasil Evaluasi Akhir:**
  - 🎯 **Accuracy:** **99.53%** (Klasifikasi yang sangat presisi)
  - ⚖️ **F1-Score:** **99.53%**
  - 📈 **AUC-ROC:** **0.9998**

### 2. Prediksi Pendapatan (Linear Regression)
- **Tujuan:** Memprediksi nominal pendapatan berkelanjutan (`Revenue_USD`) dari suatu kampanye pemasaran.
- **Hasil Evaluasi Akhir:**
  - 📊 **Koefisien Determinasi ($R^2$):** **0.9998** (Model menjelaskan 99.98% variansi pendapatan kampanye)
  - 📉 **MAE (Mean Absolute Error):** **36.15 USD**
  - 📉 **RMSE (Root Mean Squared Error):** **47.58 USD** (Jauh di bawah batas toleransi $\le$ 700 USD)

---

## 🚀 Panduan Memulai Cepat (Quick Start)

### ⚙️ Prasyarat System
- **OS:** Windows / Linux / macOS
- **Python:** Versi 3.8 s.d. 3.14.3
- **Java Runtime:** JDK 8 atau JDK 11 (Diperlukan oleh Apache Spark)
- **Container Engine:** Docker & Docker Compose (Untuk instansiasi MinIO)

### 🛠️ Langkah Instalasi & Menjalankan Dashboard

1. **Clone repository ini ke lokal:**
   ```bash
   git clone https://github.com/NikitaTsalis/bigdata6-marketing-analytics.git
   cd bigdata6-marketing-analytics
   ```

2. **Install dependensi Python:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Jalankan container MinIO Data Lake via Docker:**
   ```bash
   docker compose up -d minio
   ```
   *MinIO Console akan aktif di `http://localhost:9001` (username: `minioadmin`, password: `minioadmin123`)*

4. **Jalankan pipeline Jupyter Notebook secara berurutan:**
   Jalankan Jupyter Notebook:
   ```bash
   jupyter notebook
   ```
   Eksekusi notebook di folder `notebooks/` dengan urutan sebagai berikut:
   - `01_data_ingestion.ipynb` -> Melakukan ingestion dataset mentah ke MinIO & HDFS.
   - `02_data_processing_eda.ipynb` -> Melakukan pembersihan data, Winsorization, dan EDA.
   - `03_ml_modeling.ipynb` -> Melatih model klasifikasi & regresi Spark MLlib dan menyimpan hasilnya ke Gold Layer.
   - `04_visualization_reporting.ipynb` -> Memverifikasi visualisasi hasil dan metrik model.

5. **Jalankan Dasbor Streamlit Interaktif:**
   Buka terminal baru di root folder proyek, kemudian jalankan:
   ```bash
   streamlit run notebooks/dashboard.py
   ```
   Aplikasi Streamlit otomatis terbuka di browser Anda pada alamat `http://localhost:8501`. Dasbor ini menampilkan:
   - **Dashboard Ringkasan Eksekutif:** Total biaya kampanye, total revenue, ROI rata-rata, dan proporsi profitabilitas kampanye.
   - **Metrik Kinerja Machine Learning:** Akurasi Random Forest Classifier, matriks konfusi, performa Linear Regression ($R^2$, MAE, RMSE), dan visualisasi *Actual vs Predicted Revenue*.
   - **Analisis Fitur (Feature Importance):** Memberikan informasi fitur yang paling berdampak bagi profit kampanye (seperti Conversion Rate & CTR).

---

## 💡 Rekomendasi Bisnis Utama (Modul CRM/Marketing ERP)

### 1. Optimasi Alokasi Budget per Channel
Berdasarkan analisis Avg ROI per channel:
- **Search (ROI = 1.0134)** dan **Email (ROI = 1.0100)** adalah satu-satunya channel
  yang secara rata-rata profitable (ROI > 1.0) → jadikan **backbone kampanye utama**
- Display (0.9993), Influencer (0.9975), dan Social (0.9880) masih di bawah break-even
  → perlu audit mendalam untuk identifikasi strategi yang bisa dorong ROI > 1.0
- Revenue share antar channel merata (~19–21%) → pertahankan diversifikasi
  karena tiap channel memiliki basis audiens yang berbeda

### 2. Pre-screening Kampanye dengan Random Forest Classifier
Model RF (Accuracy 99.53%) dapat diimplementasikan sebagai sistem pre-screening sebelum
kampanye diluncurkan:
- Masukkan karakteristik kampanye (channel, budget, target impressions) ke model
- Kampanye yang diprediksi **Not Profitable** → revisi strategi atau batalkan
  sebelum anggaran dikeluarkan
- **Potensi penghematan hingga 50.1%** dari anggaran yang saat ini terbuang
  pada kampanye tidak profitable

### 3. Proyeksi Revenue untuk Perencanaan Keuangan
Model Linear Regression (R² = 0.9998, MAE = $36.15) siap digunakan tim finance untuk:
- Memproyeksikan estimasi Revenue_USD dari kampanye yang direncanakan
  berdasarkan input budget dan target metrik
- Membantu perencanaan arus kas — total revenue aktual $51.0M, profit $25.3M
- Berpotensi diintegrasikan langsung ke sistem **ERP sebagai modul proyeksi revenue otomatis**

### 4. Fokus pada KPI dengan Feature Importance Tinggi
Berdasarkan analisis feature importance, **ROAS adalah prediktor terkuat profitabilitas**
(importance score 69.8%):
- Prioritaskan monitoring **ROAS secara real-time** sebagai early warning system
- Kampanye dengan ROAS rendah → hampir dipastikan ROI di bawah break-even
- Tetapkan **minimum threshold ROAS** sebagai KPI wajib sebelum kampanye dilanjutkan
- Overall Avg ROI hanya **1.0016** → margin sangat tipis, sensitif terhadap
  perubahan kecil pada biaya maupun revenue

---
*Proyek ini dikembangkan oleh Kelompok 6 Big Data & Analitik, Teknik Komputer Universitas Brawijaya 2026.*
