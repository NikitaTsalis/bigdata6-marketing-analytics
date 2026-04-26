"""
Script untuk mengunduh dataset Marketing Campaign dari Kaggle.
==============================================================
Pastikan Kaggle API sudah dikonfigurasi sebelum menjalankan script ini.

Cara setup Kaggle API:
1. Buka https://www.kaggle.com/settings
2. Klik "Create New Token" di bagian API
3. File kaggle.json akan terunduh
4. Letakkan file tersebut di:
   - Windows: C:\\Users\\<username>\\.kaggle\\kaggle.json
   - Linux/Mac: ~/.kaggle/kaggle.json
5. Jalankan script ini: python scripts/download_dataset.py
"""

import os
import sys

def download_dataset():
    """Download dataset dari Kaggle menggunakan Kaggle API."""
    
    # Konfigurasi
    KAGGLE_DATASET = "mirzayasirabdullah07/marketing-campaign-performance-dataset"
    OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "raw")
    
    # Buat direktori output jika belum ada
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    print("=" * 60)
    print("📥 DOWNLOAD DATASET MARKETING CAMPAIGN")
    print("=" * 60)
    print(f"Dataset : {KAGGLE_DATASET}")
    print(f"Output  : {OUTPUT_DIR}")
    print()
    
    try:
        from kaggle.api.kaggle_api_extended import KaggleApi
        
        # Inisialisasi API
        api = KaggleApi()
        api.authenticate()
        print("✅ Kaggle API berhasil terautentikasi")
        
        # Download dataset
        print(f"⏳ Mengunduh dataset...")
        api.dataset_download_files(
            KAGGLE_DATASET,
            path=OUTPUT_DIR,
            unzip=True
        )
        
        # Verifikasi file yang diunduh
        files = os.listdir(OUTPUT_DIR)
        csv_files = [f for f in files if f.endswith('.csv')]
        
        if csv_files:
            for f in csv_files:
                filepath = os.path.join(OUTPUT_DIR, f)
                size_mb = os.path.getsize(filepath) / (1024 * 1024)
                
                # Hitung jumlah baris
                with open(filepath, 'r') as file:
                    line_count = sum(1 for _ in file) - 1  # minus header
                
                print(f"✅ File berhasil diunduh: {f}")
                print(f"   Ukuran : {size_mb:.2f} MB")
                print(f"   Record : {line_count:,} baris")
        else:
            print("⚠️ Tidak ada file CSV yang ditemukan setelah download!")
            
    except ImportError:
        print("❌ Error: Package 'kaggle' belum terinstall!")
        print("   Jalankan: pip install kaggle")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error saat mengunduh dataset: {e}")
        print()
        print("💡 Alternatif: Download manual dari URL berikut:")
        print(f"   https://www.kaggle.com/datasets/{KAGGLE_DATASET}")
        print(f"   Lalu letakkan file CSV di: {OUTPUT_DIR}")
        sys.exit(1)
    
    print()
    print("=" * 60)
    print("✅ DOWNLOAD SELESAI!")
    print("=" * 60)


if __name__ == "__main__":
    download_dataset()
