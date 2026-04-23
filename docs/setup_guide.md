# 📘 Panduan Instalasi & Konfigurasi
## Ekosistem Big Data untuk Marketing Analytics

---

## Daftar Isi
1. [Prasyarat](#1-prasyarat)
2. [Instalasi Java JDK](#2-instalasi-java-jdk)
3. [Instalasi Apache Hadoop](#3-instalasi-apache-hadoop)
4. [Instalasi Apache Spark](#4-instalasi-apache-spark)
5. [Instalasi MinIO](#5-instalasi-minio)
6. [Instalasi Python & Dependencies](#6-instalasi-python--dependencies)
7. [Konfigurasi Jupyter Notebook](#7-konfigurasi-jupyter-notebook)
8. [Verifikasi Seluruh Komponen](#8-verifikasi-seluruh-komponen)
9. [Menjalankan Pipeline](#9-menjalankan-pipeline)
10. [Troubleshooting](#10-troubleshooting)

---

## 1. Prasyarat

### Sistem Operasi
- **Windows 10/11** (dengan WSL2 direkomendasikan) atau
- **Ubuntu 20.04+** (native Linux)

### Hardware Minimum
- RAM: 8 GB (16 GB direkomendasikan)
- CPU: 4 cores
- Storage: 20 GB free space

### Software yang Harus Diinstal
- Git
- Text Editor (VS Code direkomendasikan)

---

## 2. Instalasi Java JDK

Apache Spark dan Hadoop memerlukan Java 8 atau 11.

### Windows
```powershell
# Download OpenJDK 11 dari https://adoptium.net/
# Atau gunakan winget:
winget install EclipseAdoptium.Temurin.11.JDK

# Set JAVA_HOME
# System Properties > Environment Variables > System Variables
# JAVA_HOME = C:\Program Files\Eclipse Adoptium\jdk-11.x.x.x-hotspot
# Path += %JAVA_HOME%\bin
```

### Linux (Ubuntu)
```bash
sudo apt update
sudo apt install openjdk-11-jdk -y

# Verifikasi
java -version

# Set JAVA_HOME di ~/.bashrc
echo 'export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64' >> ~/.bashrc
source ~/.bashrc
```

### Verifikasi
```bash
java -version
# Output: openjdk version "11.x.x"
echo $JAVA_HOME
```

---

## 3. Instalasi Apache Hadoop

### 3.1 Download Hadoop
```bash
# Download Hadoop 3.3.6
wget https://dlcdn.apache.org/hadoop/common/hadoop-3.3.6/hadoop-3.3.6.tar.gz
tar -xzf hadoop-3.3.6.tar.gz
sudo mv hadoop-3.3.6 /opt/hadoop
```

### 3.2 Konfigurasi Environment Variables
Tambahkan ke `~/.bashrc` (Linux) atau System Environment Variables (Windows):
```bash
export HADOOP_HOME=/opt/hadoop
export HADOOP_CONF_DIR=$HADOOP_HOME/etc/hadoop
export PATH=$PATH:$HADOOP_HOME/bin:$HADOOP_HOME/sbin
export HDFS_NAMENODE_USER=root
export HDFS_DATANODE_USER=root
export HDFS_SECONDARYNAMENODE_USER=root
export YARN_RESOURCEMANAGER_USER=root
export YARN_NODEMANAGER_USER=root
```

### 3.3 Konfigurasi core-site.xml
Edit `$HADOOP_HOME/etc/hadoop/core-site.xml`:
```xml
<configuration>
    <property>
        <name>fs.defaultFS</name>
        <value>hdfs://localhost:9000</value>
    </property>
    <property>
        <name>hadoop.tmp.dir</name>
        <value>/tmp/hadoop-data</value>
    </property>
</configuration>
```

### 3.4 Konfigurasi hdfs-site.xml
Edit `$HADOOP_HOME/etc/hadoop/hdfs-site.xml`:
```xml
<configuration>
    <property>
        <name>dfs.replication</name>
        <value>2</value>
    </property>
    <property>
        <name>dfs.namenode.name.dir</name>
        <value>file:///tmp/hadoop-data/namenode</value>
    </property>
    <property>
        <name>dfs.datanode.data.dir</name>
        <value>file:///tmp/hadoop-data/datanode</value>
    </property>
</configuration>
```

### 3.5 Format dan Start HDFS
```bash
# Format NameNode (hanya pertama kali)
hdfs namenode -format

# Start HDFS
start-dfs.sh

# Verifikasi
hdfs dfsadmin -report
jps  # Harus muncul: NameNode, DataNode, SecondaryNameNode
```

### 3.6 Verifikasi HDFS Web UI
- NameNode UI: http://localhost:9870

---

## 4. Instalasi Apache Spark

### 4.1 Download Spark
```bash
# Download Spark 3.5.0 (pre-built for Hadoop 3)
wget https://dlcdn.apache.org/spark/spark-3.5.0/spark-3.5.0-bin-hadoop3.tgz
tar -xzf spark-3.5.0-bin-hadoop3.tgz
sudo mv spark-3.5.0-bin-hadoop3 /opt/spark
```

### 4.2 Konfigurasi Environment Variables
```bash
export SPARK_HOME=/opt/spark
export PATH=$PATH:$SPARK_HOME/bin:$SPARK_HOME/sbin
export PYSPARK_PYTHON=python3
export PYSPARK_DRIVER_PYTHON=python3
```

### 4.3 Konfigurasi Spark untuk S3A (MinIO)
Download JAR tambahan untuk akses MinIO via S3A:
```bash
cd $SPARK_HOME/jars/

# Download hadoop-aws dan aws-java-sdk-bundle
wget https://repo1.maven.org/maven2/org/apache/hadoop/hadoop-aws/3.3.4/hadoop-aws-3.3.4.jar
wget https://repo1.maven.org/maven2/com/amazonaws/aws-java-sdk-bundle/1.12.262/aws-java-sdk-bundle-1.12.262.jar
```

### 4.4 Verifikasi
```bash
spark-shell --version
pyspark --version

# Test PySpark
pyspark
>>> spark.version
>>> spark.stop()
```

---

## 5. Instalasi MinIO

### 5.1 Download dan Install MinIO

#### Linux
```bash
wget https://dl.min.io/server/minio/release/linux-amd64/minio
chmod +x minio
sudo mv minio /usr/local/bin/

# Download MinIO Client
wget https://dl.min.io/client/mc/release/linux-amd64/mc
chmod +x mc
sudo mv mc /usr/local/bin/
```

#### Windows
```powershell
# Download dari https://dl.min.io/server/minio/release/windows-amd64/minio.exe
# Download MC dari https://dl.min.io/client/mc/release/windows-amd64/mc.exe
# Tambahkan ke PATH
```

### 5.2 Jalankan MinIO Server
```bash
# Buat direktori data
mkdir -p /data/minio

# Jalankan MinIO
minio server /data/minio --console-address ":9001"
```

MinIO akan berjalan di:
- **API:** http://localhost:9000
- **Console:** http://localhost:9001
- **Default credentials:** minioadmin / minioadmin

### 5.3 Setup Bucket
```bash
# Jalankan script setup
bash scripts/setup_minio.sh
```

---

## 6. Instalasi Python & Dependencies

### 6.1 Virtual Environment (Opsional tapi Direkomendasikan)
```bash
# Buat virtual environment
python -m venv bigdata_env

# Aktivasi
# Linux:
source bigdata_env/bin/activate
# Windows:
bigdata_env\Scripts\activate
```

### 6.2 Install Dependencies
```bash
pip install -r requirements.txt
```

### 6.3 Setup Kaggle API
1. Buka https://www.kaggle.com/settings
2. Scroll ke bagian **API**
3. Klik **"Create New Token"**
4. File `kaggle.json` akan terunduh otomatis
5. Letakkan di:
   - **Windows:** `C:\Users\<username>\.kaggle\kaggle.json`
   - **Linux:** `~/.kaggle/kaggle.json`
6. Set permission (Linux): `chmod 600 ~/.kaggle/kaggle.json`

---

## 7. Konfigurasi Jupyter Notebook

### 7.1 Install Jupyter
```bash
pip install jupyter jupyterlab jupytext
```

### 7.2 Konfigurasi PySpark di Jupyter
```bash
# Set environment variables
export PYSPARK_DRIVER_PYTHON=jupyter
export PYSPARK_DRIVER_PYTHON_OPTS="notebook"
```

### 7.3 Jalankan Jupyter
```bash
# Dari root direktori proyek
cd BigData/
jupyter notebook
# atau
jupyter lab
```

### 7.4 Konversi File .py ke .ipynb (Opsional)
Jika ingin menggunakan format notebook tradisional:
```bash
# Konversi satu file
jupytext --to notebook notebooks/01_data_ingestion.py

# Konversi semua file
for f in notebooks/*.py; do jupytext --to notebook "$f"; done
```

---

## 8. Verifikasi Seluruh Komponen

Jalankan checklist berikut untuk memastikan semua komponen berjalan:

```bash
echo "=== VERIFIKASI KOMPONEN ==="

# 1. Java
echo "--- Java ---"
java -version

# 2. Hadoop
echo "--- Hadoop ---"
hadoop version
hdfs dfs -ls /

# 3. Spark
echo "--- Spark ---"
spark-submit --version

# 4. MinIO
echo "--- MinIO ---"
mc alias list

# 5. Python
echo "--- Python ---"
python --version
pip list | grep -E "pyspark|pandas|matplotlib|minio"

# 6. Jupyter
echo "--- Jupyter ---"
jupyter --version
```

---

## 9. Menjalankan Pipeline

### Urutan Eksekusi

```
Step 1: Download dataset
$ python scripts/download_dataset.py

Step 2: Setup MinIO bucket
$ bash scripts/setup_minio.sh

Step 3: Setup HDFS directories
$ bash scripts/setup_hdfs.sh

Step 4: Jalankan notebook secara berurutan
$ jupyter notebook notebooks/01_data_ingestion.py
$ jupyter notebook notebooks/02_data_processing_eda.py
$ jupyter notebook notebooks/03_ml_modeling.py
$ jupyter notebook notebooks/04_visualization_reporting.py
```

### Atau jalankan sebagai script Python
```bash
python notebooks/01_data_ingestion.py
python notebooks/02_data_processing_eda.py
python notebooks/03_ml_modeling.py
python notebooks/04_visualization_reporting.py
```

---

## 10. Troubleshooting

### Problem: HDFS tidak bisa start
```bash
# Solusi: Format ulang namenode
stop-dfs.sh
rm -rf /tmp/hadoop-data/*
hdfs namenode -format
start-dfs.sh
```

### Problem: Spark tidak bisa connect ke HDFS
```bash
# Pastikan HADOOP_CONF_DIR sudah di-set
echo $HADOOP_CONF_DIR
# Pastikan core-site.xml bisa diakses
cat $HADOOP_CONF_DIR/core-site.xml
```

### Problem: MinIO connection refused
```bash
# Pastikan MinIO server berjalan
ps aux | grep minio
# Restart MinIO
minio server /data/minio --console-address ":9001"
```

### Problem: PySpark import error
```bash
# Pastikan SPARK_HOME sudah diset
echo $SPARK_HOME
# Pastikan findspark atau pyspark terinstall
pip install pyspark findspark
```

### Problem: Kaggle API error
```bash
# Pastikan kaggle.json ada di lokasi yang benar
ls ~/.kaggle/kaggle.json
# Set permission
chmod 600 ~/.kaggle/kaggle.json
```

### Problem: Memory error saat Spark processing
```python
# Tambah memory di spark_config.py
SPARK_CONFIG["spark.driver.memory"] = "8g"
SPARK_CONFIG["spark.executor.memory"] = "4g"
```
