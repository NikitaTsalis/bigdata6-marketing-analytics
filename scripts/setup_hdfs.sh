#!/bin/bash
# ============================================
# Script Setup Direktori HDFS untuk Marketing Data
# ============================================
# Pastikan Hadoop cluster sudah berjalan sebelum menjalankan script ini.
#
# Cara menjalankan:
#   bash scripts/setup_hdfs.sh
# ============================================

echo "============================================"
echo "📂 SETUP DIREKTORI HDFS"
echo "============================================"

# Konfigurasi
BASE_DIR="/user/hadoop/marketing"

# 1. Buat direktori utama
echo ""
echo "📌 Step 1: Membuat struktur direktori HDFS..."

hadoop fs -mkdir -p $BASE_DIR/raw
hadoop fs -mkdir -p $BASE_DIR/processed
hadoop fs -mkdir -p $BASE_DIR/model
hadoop fs -mkdir -p $BASE_DIR/model/rf_classifier
hadoop fs -mkdir -p $BASE_DIR/model/linear_regression

echo "✅ Struktur direktori HDFS berhasil dibuat:"
echo "   📁 $BASE_DIR/"
echo "   ├── 📁 raw/                (data mentah CSV)"
echo "   ├── 📁 processed/          (data Parquet yang sudah diproses)"
echo "   └── 📁 model/"
echo "       ├── 📁 rf_classifier/   (model Random Forest)"
echo "       └── 📁 linear_regression/ (model Linear Regression)"

# 2. Upload dataset CSV ke HDFS (jika file ada)
echo ""
echo "📌 Step 2: Mengupload dataset ke HDFS..."
CSV_FILE="data/raw/marketing_campaign_performance_10000.csv"

if [ -f "$CSV_FILE" ]; then
    hadoop fs -put -f $CSV_FILE $BASE_DIR/raw/marketing_campaign_performance.csv
    echo "✅ Dataset berhasil diupload ke HDFS"
else
    echo "⚠️  File CSV tidak ditemukan di '$CSV_FILE'"
    echo "   Jalankan terlebih dahulu: python scripts/download_dataset.py"
fi

# 3. Verifikasi
echo ""
echo "📌 Step 3: Verifikasi..."
echo ""
echo "--- Struktur Direktori ---"
hadoop fs -ls -R $BASE_DIR/

echo ""
echo "--- Statistik File ---"
hadoop fs -count $BASE_DIR/

echo ""
echo "============================================"
echo "✅ SETUP HDFS SELESAI!"
echo "============================================"
echo ""
echo "📋 Direktori HDFS yang tersedia:"
echo "   Raw Data   : $BASE_DIR/raw/"
echo "   Processed  : $BASE_DIR/processed/"
echo "   Models     : $BASE_DIR/model/"
