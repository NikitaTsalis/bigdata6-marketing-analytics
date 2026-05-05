# 🏗️ Arsitektur Ekosistem Big Data
## Proyek Analisis Performa Kampanye Marketing

---

## 1. Diagram Arsitektur

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        EKOSISTEM BIG DATA                                   │
│                                                                             │
│  ┌─────────────┐                                                            │
│  │   KAGGLE     │  Dataset CSV                                              │
│  │  (Sumber)    │──────────┐                                                │
│  └─────────────┘           │                                                │
│                            ▼                                                │
│  ┌─────────────────────────────────────┐                                    │
│  │         DATA LAKE (MinIO)           │                                    │
│  │                                     │                                    │
│  │  📁 marketing-data/                 │                                    │
│  │  ├── bronze/      ← CSV mentah      │                                    │
│  │  ├── silver/      ← Parquet bersih  │                                    │
│  │  ├── gold/        ← Agregasi bisnis │                                    │
│  │  └── models/      ← Model ML        │                                    │
│  └──────────────┬──────────────────────┘                                    │
│                 │                                                            │
│                 ▼                                                            │
│  ┌─────────────────────────────────────┐                                    │
│  │      HDFS (Distributed Storage)     │                                    │
│  │                                     │                                    │
│  │  /user/hadoop/marketing/            │                                    │
│  │  ├── bronze/      ← CSV dari MinIO  │                                    │
│  │  ├── silver/      ← Parquet         │                                    │
│  │  ├── gold/        ← Prediksi        │                                    │
│  │  └── models/      ← Model tersimpan │                                    │
│  │                                     │                                    │
│  │  NameNode (1) + DataNode (2+)       │                                    │
│  └──────────────┬──────────────────────┘                                    │
│                 │                                                            │
│                 ▼                                                            │
│  ┌─────────────────────────────────────┐                                    │
│  │      APACHE SPARK (Processing)      │                                    │
│  │                                     │                                    │
│  │  ┌───────────────┐  ┌────────────┐  │                                    │
│  │  │  Spark SQL    │  │ DataFrame  │  │                                    │
│  │  │  (Query)      │  │ API (ETL)  │  │                                    │
│  │  └───────────────┘  └────────────┘  │                                    │
│  │                                     │                                    │
│  │  ┌───────────────────────────────┐  │                                    │
│  │  │        SPARK MLLIB            │  │                                    │
│  │  │                               │  │                                    │
│  │  │  ┌─────────────────────────┐  │  │                                    │
│  │  │  │ Random Forest Classifier│  │  │                                    │
│  │  │  │ (Klasifikasi ROI)       │  │  │                                    │
│  │  │  └─────────────────────────┘  │  │                                    │
│  │  │                               │  │                                    │
│  │  │  ┌─────────────────────────┐  │  │                                    │
│  │  │  │ Linear Regression       │  │  │                                    │
│  │  │  │ (Prediksi Revenue)      │  │  │                                    │
│  │  │  └─────────────────────────┘  │  │                                    │
│  │  └───────────────────────────────┘  │                                    │
│  └──────────────┬──────────────────────┘                                    │
│                 │                                                            │
│                 ▼                                                            │
│  ┌─────────────────────────────────────┐                                    │
│  │   JUPYTER NOTEBOOK (Visualization)  │                                    │
│  │                                     │                                    │
│  │  📊 Matplotlib + Seaborn + Plotly   │                                    │
│  │  📈 Confusion Matrix               │                                    │
│  │  📉 Feature Importance             │                                    │
│  │  📋 Actual vs Predicted            │                                    │
│  └─────────────────────────────────────┘                                    │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Komponen Teknologi

### 2.1 Data Ingestion Layer
| Komponen | Teknologi | Deskripsi |
|----------|-----------|-----------|
| Sumber Data | Kaggle API | Download dataset CSV dari Kaggle |
| Upload ke Data Lake | MinIO Client (mc) | Upload CSV ke MinIO bucket |
| Upload ke HDFS | PySpark / hadoop fs | Transfer data dari MinIO ke HDFS |

### 2.2 Storage Layer (Medallion Architecture)
| Komponen | Layer | Format | Deskripsi |
|----------|-------|--------|-----------|
| Data Lake / HDFS | Bronze | CSV | Data mentah, tanpa modifikasi (*Single Source of Truth*) |
| Data Lake / HDFS | Silver | Parquet | Data yang telah dibersihkan, di-filter, dan *feature engineered* |
| Data Lake / HDFS | Gold | Parquet | Data teragregasi untuk bisnis, dan hasil prediksi ML |
| Data Lake / HDFS | Models | Spark ML | Artefak model ML yang sudah di-train |

### 2.3 Processing Layer
| Komponen | Teknologi | Deskripsi |
|----------|-----------|-----------|
| ETL Engine | Apache Spark | Pembersihan, transformasi, dan feature engineering |
| Query Engine | Spark SQL | Analisis data menggunakan SQL |
| DataFrame API | PySpark | Manipulasi data terdistribusi |

### 2.4 Analytics Layer
| Komponen | Teknologi | Deskripsi |
|----------|-----------|-----------|
| ML Framework | Spark MLlib | Library ML terdistribusi |
| Klasifikasi | Random Forest | Prediksi profitabilitas kampanye |
| Regresi | Linear Regression | Prediksi Revenue_USD |
| Tuning | CrossValidator | Hyperparameter optimization |

### 2.5 Visualization Layer
| Komponen | Teknologi | Deskripsi |
|----------|-----------|-----------|
| Notebook | Jupyter / JupyterLab | Interactive computing environment |
| Charting | Matplotlib + Seaborn | Static visualization |
| Interactive | Plotly | Interactive charts |

---

## 3. Data Flow Pipeline

```mermaid
graph TD
    A[Kaggle Dataset CSV] -->|download| B[Local Storage]
    B -->|Ingestion| C[MinIO - Bronze Layer]
    C -->|PySpark Read| D[Spark Processing]
    D -->|Clean & Engineer| E[Silver DataFrame]
    E -->|write parquet| F[MinIO - Silver Layer]
    F -->|train/test split| G{Split Data}
    G -->|80%| H[Training Set]
    G -->|20%| I[Test Set]
    H -->|fit| J[Random Forest Classifier]
    H -->|fit| K[Linear Regression]
    J -->|save| L[MinIO - Models Layer]
    K -->|save| L
    I -->|predict| M[Predictions DataFrame]
    M -->|write| N[MinIO - Gold Layer]
    N -->|read & aggregate| O[Visualization & Reporting]
    O -->|write aggregates| N
```

---

## 4. Environment Requirements

### Hardware Minimum
- **RAM:** 8 GB (16 GB recommended)
- **CPU:** 4 cores
- **Storage:** 20 GB free space

### Software Stack
| Software | Version | Purpose |
|----------|---------|---------|
| Java JDK | 8 atau 11 | Runtime untuk Spark & Hadoop |
| Python | 3.8+ | Bahasa pemrograman utama |
| Apache Spark | 3.3+ | Processing engine |
| Apache Hadoop | 3.3+ | Distributed storage (HDFS) |
| MinIO | Latest | Object storage (Data Lake) |
| Jupyter | 1.0+ | Notebook environment |

### Python Libraries
| Library | Purpose |
|---------|---------|
| pyspark | Spark Python API |
| pandas | Data manipulation |
| numpy | Numerical computing |
| matplotlib | Static visualization |
| seaborn | Statistical visualization |
| plotly | Interactive visualization |
| minio | MinIO Python client |
