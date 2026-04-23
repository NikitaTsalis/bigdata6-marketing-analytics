#!/bin/bash
# ============================================
# Script Setup MinIO Bucket untuk Marketing Data
# ============================================
# Pastikan MinIO Server sudah berjalan sebelum menjalankan script ini.
#
# Cara menjalankan MinIO Server:
#   minio server /data --console-address ":9001"
#
# Cara menjalankan script ini:
#   bash scripts/setup_minio.sh
# ============================================

echo "============================================"
echo "🗄️  SETUP MINIO BUCKET"
echo "============================================"

# Konfigurasi MinIO
MINIO_ALIAS="myminio"
MINIO_ENDPOINT="http://localhost:9000"
MINIO_ACCESS_KEY="minioadmin"
MINIO_SECRET_KEY="minioadmin"
BUCKET_NAME="marketing-data"

# 1. Set alias MinIO
echo ""
echo "📌 Step 1: Menambahkan alias MinIO..."
mc alias set $MINIO_ALIAS $MINIO_ENDPOINT $MINIO_ACCESS_KEY $MINIO_SECRET_KEY

if [ $? -ne 0 ]; then
    echo "❌ Gagal menambahkan alias. Pastikan MinIO server sudah berjalan!"
    echo "   Jalankan: minio server /data --console-address ':9001'"
    exit 1
fi
echo "✅ Alias '$MINIO_ALIAS' berhasil ditambahkan"

# 2. Buat bucket
echo ""
echo "📌 Step 2: Membuat bucket '$BUCKET_NAME'..."
mc mb $MINIO_ALIAS/$BUCKET_NAME --ignore-existing
echo "✅ Bucket '$BUCKET_NAME' siap digunakan"

# 3. Buat struktur direktori
echo ""
echo "📌 Step 3: Membuat struktur direktori..."

# Upload placeholder untuk membuat struktur folder
echo "placeholder" | mc pipe $MINIO_ALIAS/$BUCKET_NAME/raw/.keep
echo "placeholder" | mc pipe $MINIO_ALIAS/$BUCKET_NAME/processed/.keep
echo "placeholder" | mc pipe $MINIO_ALIAS/$BUCKET_NAME/model/.keep

echo "✅ Struktur direktori berhasil dibuat:"
echo "   📁 $BUCKET_NAME/"
echo "   ├── 📁 raw/          (data mentah CSV)"
echo "   ├── 📁 processed/    (data yang sudah diproses)"
echo "   └── 📁 model/        (model ML yang disimpan)"

# 4. Upload dataset CSV ke MinIO (jika file ada)
echo ""
echo "📌 Step 4: Mengupload dataset ke MinIO..."
CSV_FILE="data/raw/marketing_campaign_performance_10000.csv"

if [ -f "$CSV_FILE" ]; then
    mc cp $CSV_FILE $MINIO_ALIAS/$BUCKET_NAME/raw/marketing_campaign_performance.csv
    echo "✅ Dataset berhasil diupload ke MinIO"
else
    echo "⚠️  File CSV tidak ditemukan di '$CSV_FILE'"
    echo "   Jalankan terlebih dahulu: python scripts/download_dataset.py"
fi

# 5. Verifikasi
echo ""
echo "📌 Step 5: Verifikasi isi bucket..."
mc ls $MINIO_ALIAS/$BUCKET_NAME/ --recursive

echo ""
echo "============================================"
echo "✅ SETUP MINIO SELESAI!"
echo "============================================"
echo ""
echo "📋 Info akses MinIO:"
echo "   Console : http://localhost:9001"
echo "   API     : http://localhost:9000"
echo "   User    : $MINIO_ACCESS_KEY"
echo "   Password: $MINIO_SECRET_KEY"
echo "   Bucket  : $BUCKET_NAME"
