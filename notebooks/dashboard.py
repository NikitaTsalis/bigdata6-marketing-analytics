"""
Marketing Campaign Performance Dashboard
Membaca data dari MinIO Gold Layer (Parquet)
Run: streamlit run dashboard.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
import boto3
from io import BytesIO
import warnings
warnings.filterwarnings('ignore')

# ── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Marketing Campaign Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .metric-card {
        background: linear-gradient(135deg, #1e3a5f 0%, #2d6a9f 100%);
        border-radius: 12px;
        padding: 16px 20px;
        color: white;
        margin-bottom: 8px;
    }
    .metric-label { font-size: 12px; opacity: 0.8; margin-bottom: 4px; }
    .metric-value { font-size: 26px; font-weight: 700; }
    .metric-sub   { font-size: 11px; opacity: 0.7; margin-top: 2px; }
    .section-header {
        font-size: 18px; font-weight: 700;
        border-left: 4px solid #2d6a9f;
        padding-left: 10px; margin: 20px 0 12px 0;
        color: #1e3a5f;
    }
    [data-testid="stMetricValue"] { font-size: 28px !important; }
    .stTabs [data-baseweb="tab"] { font-weight: 600; }
</style>
""", unsafe_allow_html=True)

# ── MinIO Config ──────────────────────────────────────────────────────────────
MINIO_ENDPOINT    = "localhost:9000"
MINIO_ACCESS_KEY  = "minioadmin"
MINIO_SECRET_KEY  = "minioadmin123"
MINIO_BUCKET      = "marketing-data"

GOLD_PREDICTIONS_PATH     = "gold/predictions"
GOLD_CHANNEL_SUMMARY_PATH = "gold/channel_performance_summary"

# ── Load Data ─────────────────────────────────────────────────────────────────
@st.cache_data(ttl=300, show_spinner="Memuat data dari MinIO Gold Layer...")
def load_gold_data():
    """Baca parquet dari MinIO menggunakan boto3 + pandas."""
    s3 = boto3.client(
        "s3",
        endpoint_url=f"http://{MINIO_ENDPOINT}",
        aws_access_key_id=MINIO_ACCESS_KEY,
        aws_secret_access_key=MINIO_SECRET_KEY,
    )

    def read_parquet_from_minio(prefix):
        """List semua file .parquet di prefix, concat jadi 1 DataFrame."""
        paginator = s3.get_paginator("list_objects_v2")
        dfs = []
        for page in paginator.paginate(Bucket=MINIO_BUCKET, Prefix=prefix):
            for obj in page.get("Contents", []):
                key = obj["Key"]
                if key.endswith(".parquet"):
                    buf = BytesIO(s3.get_object(Bucket=MINIO_BUCKET, Key=key)["Body"].read())
                    dfs.append(pd.read_parquet(buf))
        return pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()

    df = read_parquet_from_minio(GOLD_PREDICTIONS_PATH)
    return df

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/combo-chart.png", width=60)
    st.title("Marketing Analytics")
    st.markdown("---")

    try:
        df_raw = load_gold_data()
        load_ok = not df_raw.empty
    except Exception as e:
        st.error(f"❌ Gagal konek MinIO:\n{e}")
        st.info("Pastikan MinIO berjalan di localhost:9000 dan Gold Layer sudah ada.")
        st.stop()

    if not load_ok:
        st.warning("Gold Layer kosong. Jalankan NB03 dulu.")
        st.stop()

    df = df_raw.copy()

    st.success(f"✅ {len(df):,} kampanye dimuat")
    st.markdown("---")

    st.markdown("### 🔍 Filter")
    all_channels = sorted(df["Channel"].unique().tolist())
    selected_channels = st.multiselect(
        "Channel", all_channels, default=all_channels
    )

    if "Start_Month" in df.columns:
        months = sorted(df["Start_Month"].dropna().unique().tolist())
        month_names = {1:"Jan",2:"Feb",3:"Mar",4:"Apr",5:"May",6:"Jun",
                       7:"Jul",8:"Aug",9:"Sep",10:"Oct",11:"Nov",12:"Dec"}
        selected_months = st.multiselect(
            "Bulan Launch",
            options=months,
            default=months,
            format_func=lambda x: month_names.get(int(x), str(x))
        )
    else:
        selected_months = None

    min_roi, max_roi = float(df["ROI"].min()), float(df["ROI"].max())
    roi_range = st.slider("ROI Range", min_roi, max_roi, (min_roi, max_roi), step=0.01)

    st.markdown("---")
    if st.button("🔄 Refresh Data"):
        st.cache_data.clear()
        st.rerun()

# ── Apply Filters ─────────────────────────────────────────────────────────────
df_f = df[df["Channel"].isin(selected_channels)]
df_f = df_f[(df_f["ROI"] >= roi_range[0]) & (df_f["ROI"] <= roi_range[1])]
if selected_months is not None and "Start_Month" in df_f.columns:
    df_f = df_f[df_f["Start_Month"].isin(selected_months)]

if df_f.empty:
    st.warning("Tidak ada data dengan filter tersebut.")
    st.stop()

# ── Header ────────────────────────────────────────────────────────────────────
st.title("📊 Marketing Campaign Performance Dashboard")
st.caption(f"Data: {len(df_f):,} kampanye • Filter aktif: {len(selected_channels)} channel")
st.markdown("---")

# ── KPI Cards ─────────────────────────────────────────────────────────────────
col1, col2, col3, col4, col5, col6 = st.columns(6)

total_rev   = df_f["Revenue_USD"].sum()
total_cost  = df_f["Cost_USD"].sum()
total_profit = df_f["Profit_USD"].sum() if "Profit_USD" in df_f.columns else total_rev - total_cost
profit_rate = df_f["is_profitable"].mean() * 100
avg_roi     = df_f["ROI"].mean()
avg_roas    = df_f["ROAS"].mean() if "ROAS" in df_f.columns else total_rev / total_cost

with col1:
    st.metric("💰 Total Revenue", f"${total_rev/1e6:.2f}M")
with col2:
    st.metric("💸 Total Cost", f"${total_cost/1e6:.2f}M")
with col3:
    st.metric("📈 Total Profit", f"${total_profit/1e6:.2f}M",
              delta=f"{total_profit/total_cost*100:.1f}% margin")
with col4:
    st.metric("🎯 Avg ROI", f"{avg_roi:.3f}",
              delta="≥1.0 profitable" if avg_roi >= 1.0 else "<1.0")
with col5:
    st.metric("📡 Avg ROAS", f"{avg_roas:.2f}x")
with col6:
    st.metric("✅ Profitable Rate", f"{profit_rate:.1f}%")

st.markdown("---")

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "📡 Channel Performance",
    "💰 Profitabilitas",
    "🤖 Model Predictions",
    "🔗 Correlation & Distribusi"
])

COLORS = sns.color_palette("husl", 8)
plt.style.use("seaborn-v0_8-whitegrid")

# ════════════════════════════════════════════════════════════════
# TAB 1: Channel Performance
# ════════════════════════════════════════════════════════════════
with tab1:
    st.markdown('<div class="section-header">Performa per Channel</div>', unsafe_allow_html=True)

    ch_agg = df_f.groupby("Channel").agg(
        Jumlah=("CampaignID","count"),
        Avg_ROI=("ROI","mean"),
        Total_Revenue=("Revenue_USD","sum"),
        Total_Cost=("Cost_USD","sum"),
        Avg_CTR=("CTR","mean"),
        Avg_CVR=("CVR","mean"),
    ).reset_index().sort_values("Avg_ROI", ascending=False)

    # ── Row 1: Revenue/Cost/Profit + ROI ──────────────────────────────────────
    c1, c2 = st.columns(2)

    with c1:
        fig, ax = plt.subplots(figsize=(7, 4))
        ch_fin = df_f.groupby("Channel").agg(
            Revenue=("Revenue_USD","sum"),
            Cost=("Cost_USD","sum"),
        ).reset_index()
        if "Profit_USD" in df_f.columns:
            ch_fin["Profit"] = df_f.groupby("Channel")["Profit_USD"].sum().values
        else:
            ch_fin["Profit"] = ch_fin["Revenue"] - ch_fin["Cost"]
        x = np.arange(len(ch_fin)); w = 0.27
        ax.bar(x - w, ch_fin["Revenue"]/1e6, w, label="Revenue", color="#3498db", edgecolor="white")
        ax.bar(x,     ch_fin["Cost"]/1e6,    w, label="Cost",    color="#e74c3c", edgecolor="white")
        ax.bar(x + w, ch_fin["Profit"]/1e6,  w, label="Profit",  color="#2ecc71", edgecolor="white")
        ax.set_xticks(x); ax.set_xticklabels(ch_fin["Channel"], rotation=15)
        ax.set_title("Revenue vs Cost vs Profit per Channel ($M)", fontweight="bold")
        ax.set_ylabel("USD (Millions)"); ax.legend(fontsize=9)
        plt.tight_layout(); st.pyplot(fig); plt.close()

    with c2:
        fig, ax = plt.subplots(figsize=(7, 4))
        colors_bar = sns.color_palette("husl", len(ch_agg))
        bars = ax.bar(ch_agg["Channel"], ch_agg["Avg_ROI"], color=colors_bar, edgecolor="white")
        ax.axhline(y=1.0, color="red", linestyle="--", linewidth=1.5, label="ROI = 1.0")
        ax.set_title("Rata-rata ROI per Channel", fontweight="bold")
        ax.set_ylabel("Avg ROI"); ax.legend()
        for i, v in enumerate(ch_agg["Avg_ROI"]):
            ax.text(i, v + 0.005, f"{v:.3f}", ha="center", fontsize=9, fontweight="bold")
        plt.tight_layout(); st.pyplot(fig); plt.close()

    # ── Row 2: CTR + CVR ──────────────────────────────────────────────────────
    c3, c4 = st.columns(2)
    with c3:
        fig, ax = plt.subplots(figsize=(7, 4))
        ax.bar(ch_agg["Channel"], ch_agg["Avg_CTR"], color=colors_bar, edgecolor="white")
        ax.set_title("Rata-rata CTR per Channel", fontweight="bold"); ax.set_ylabel("Avg CTR")
        for i, v in enumerate(ch_agg["Avg_CTR"]):
            ax.text(i, v + 0.0001, f"{v:.4f}", ha="center", fontsize=9)
        plt.tight_layout(); st.pyplot(fig); plt.close()

    with c4:
        fig, ax = plt.subplots(figsize=(7, 4))
        ax.bar(ch_agg["Channel"], ch_agg["Avg_CVR"], color=colors_bar, edgecolor="white")
        ax.set_title("Rata-rata CVR per Channel", fontweight="bold"); ax.set_ylabel("Avg CVR")
        for i, v in enumerate(ch_agg["Avg_CVR"]):
            ax.text(i, v + 0.0001, f"{v:.4f}", ha="center", fontsize=9)
        plt.tight_layout(); st.pyplot(fig); plt.close()

    # ── Table ─────────────────────────────────────────────────────────────────
    st.markdown("##### 📋 Tabel Ringkasan Channel")
    st.dataframe(
        ch_agg.style.format({
            "Avg_ROI": "{:.3f}", "Total_Revenue": "${:,.0f}",
            "Total_Cost": "${:,.0f}", "Avg_CTR": "{:.4f}", "Avg_CVR": "{:.4f}"
        }).background_gradient(subset=["Avg_ROI"], cmap="RdYlGn"),
        use_container_width=True
    )

    # ── ROAS vs ROI scatter ───────────────────────────────────────────────────
    if "ROAS" in df_f.columns:
        st.markdown('<div class="section-header">ROAS vs ROI per Channel</div>', unsafe_allow_html=True)
        fig, ax = plt.subplots(figsize=(10, 5))
        channels_u = df_f["Channel"].unique()
        colors_ch = sns.color_palette("husl", len(channels_u))
        for ch, c in zip(channels_u, colors_ch):
            sub = df_f[df_f["Channel"] == ch]
            ax.scatter(sub["ROAS"].clip(upper=sub["ROAS"].quantile(0.99)),
                       sub["ROI"].clip(upper=sub["ROI"].quantile(0.99)),
                       alpha=0.35, label=ch, s=15, color=c)
        ax.axhline(y=1.0, color="red", linestyle="--", linewidth=1.5, label="ROI = 1.0 (break-even)")
        ax.set_xlabel("ROAS"); ax.set_ylabel("ROI")
        ax.set_title("ROAS vs ROI per Channel", fontweight="bold")
        ax.legend(fontsize=9)
        plt.tight_layout(); st.pyplot(fig); plt.close()

# ════════════════════════════════════════════════════════════════
# TAB 2: Profitabilitas
# ════════════════════════════════════════════════════════════════
with tab2:
    st.markdown('<div class="section-header">Analisis Profitabilitas Kampanye</div>', unsafe_allow_html=True)

    profit_counts = df_f["is_profitable"].value_counts()
    labels_pie = ["Profitable (ROI≥1)", "Not Profitable (ROI<1)"]
    values_pie = [profit_counts.get(1, 0), profit_counts.get(0, 0)]

    c1, c2 = st.columns(2)
    with c1:
        fig, ax = plt.subplots(figsize=(6, 5))
        ax.pie(values_pie, labels=labels_pie, autopct="%1.1f%%",
               colors=["#2ecc71","#e74c3c"], startangle=90,
               wedgeprops={"edgecolor":"white","linewidth":2})
        ax.set_title("Distribusi Profitabilitas Kampanye", fontweight="bold")
        plt.tight_layout(); st.pyplot(fig); plt.close()

    with c2:
        fig, ax = plt.subplots(figsize=(7, 5))
        profit_ch = df_f.groupby(["Channel","is_profitable"]).size().unstack(fill_value=0)
        profit_ch.columns = ["Not Profitable","Profitable"] if 0 in profit_ch.columns else ["Profitable"]
        profit_ch.plot(kind="bar", ax=ax, color=["#e74c3c","#2ecc71"], edgecolor="black")
        ax.set_title("Profitabilitas per Channel", fontweight="bold")
        ax.set_xlabel("Channel"); ax.set_ylabel("Jumlah Kampanye")
        ax.tick_params(axis="x", rotation=0); ax.legend()
        plt.tight_layout(); st.pyplot(fig); plt.close()

    # ── ROI & Profit Distribution ─────────────────────────────────────────────
    c3, c4 = st.columns(2)
    with c3:
        fig, ax = plt.subplots(figsize=(7, 4))
        channels_s = ch_agg["Channel"].tolist()
        data_by_ch = [df_f[df_f["Channel"] == ch]["ROI"].values for ch in channels_s]
        bp = ax.boxplot(data_by_ch, labels=channels_s, patch_artist=True,
                        boxprops=dict(facecolor="lightblue", alpha=0.8))
        ax.axhline(y=1.0, color="red", linestyle="--", label="ROI = 1.0")
        ax.set_title("Distribusi ROI per Channel", fontweight="bold")
        ax.set_xlabel("Channel"); ax.set_ylabel("ROI"); ax.legend()
        plt.tight_layout(); st.pyplot(fig); plt.close()

    with c4:
        if "Profit_USD" in df_f.columns:
            fig, ax = plt.subplots(figsize=(7, 4))
            sns.boxplot(data=df_f, x="Channel", y="Profit_USD",
                        palette="husl", ax=ax, order=channels_s)
            ax.axhline(y=0, color="red", linestyle="--", linewidth=1.5, label="Break-even")
            ax.set_title("Distribusi Profit per Channel", fontweight="bold")
            ax.set_xlabel("Channel"); ax.set_ylabel("Profit (USD)"); ax.legend()
            plt.tight_layout(); st.pyplot(fig); plt.close()

    # ── Timing Analysis ───────────────────────────────────────────────────────
    if "Start_Month" in df_f.columns:
        st.markdown('<div class="section-header">Timing Analysis — Kapan Kampanye Paling Profitable?</div>', unsafe_allow_html=True)
        month_names_list = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
        monthly = df_f.groupby("Start_Month")["ROI"].mean()

        c5, c6 = st.columns(2)
        with c5:
            fig, ax = plt.subplots(figsize=(7, 4))
            vals = [monthly.get(i, 0) for i in range(1, 13)]
            bar_colors = ["gold" if v == max(vals) else "#3498db" for v in vals]
            ax.bar(month_names_list, vals, color=bar_colors, edgecolor="white")
            ax.set_title("Rata-rata ROI per Bulan Launch", fontweight="bold")
            ax.set_ylabel("Avg ROI"); ax.set_xlabel("Bulan")
            best_m = month_names_list[np.argmax(vals)]
            ax.set_title(f"Rata-rata ROI per Bulan Launch\n🏆 Best: {best_m}", fontweight="bold")
            plt.tight_layout(); st.pyplot(fig); plt.close()

        with c6:
            if "Start_DayOfWeek" in df_f.columns:
                day_names = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]
                dow = df_f.groupby("Start_DayOfWeek")["ROI"].mean()
                vals_d = [dow.get(i, 0) for i in range(0, 7)]
                bar_colors_d = ["gold" if v == max(vals_d) else "#9b59b6" for v in vals_d]
                fig, ax = plt.subplots(figsize=(7, 4))
                ax.bar(day_names, vals_d, color=bar_colors_d, edgecolor="white")
                best_d = day_names[np.argmax(vals_d)]
                ax.set_title(f"Rata-rata ROI per Hari Launch\n🏆 Best: {best_d}", fontweight="bold")
                ax.set_ylabel("Avg ROI"); ax.set_xlabel("Hari")
                plt.tight_layout(); st.pyplot(fig); plt.close()

# ════════════════════════════════════════════════════════════════
# TAB 3: Model Predictions
# ════════════════════════════════════════════════════════════════
with tab3:
    st.markdown('<div class="section-header">Evaluasi Model Random Forest & Linear Regression</div>', unsafe_allow_html=True)

    # RF Accuracy
    df_f2 = df_f.copy()
    df_f2["rf_correct"] = (df_f2["rf_prediction"] == df_f2["is_profitable"]).astype(int)
    overall_acc = df_f2["rf_correct"].mean()
    rf_per_ch = df_f2.groupby("Channel")["rf_correct"].mean().reset_index()
    rf_per_ch.columns = ["Channel","RF_Accuracy"]

    # LR Error
    df_f2["lr_error"] = df_f2["Revenue_USD"] - df_f2["lr_predicted_revenue"]
    lr_mae = df_f2["lr_error"].abs().mean()

    kc1, kc2, kc3 = st.columns(3)
    with kc1:
        st.metric("🎯 RF Accuracy (Overall)", f"{overall_acc:.4f}", f"{overall_acc*100:.1f}%")
    with kc2:
        st.metric("📉 LR MAE", f"${lr_mae:,.0f}")
    with kc3:
        lr_r2 = 1 - (df_f2["lr_error"]**2).sum() / ((df_f2["Revenue_USD"] - df_f2["Revenue_USD"].mean())**2).sum()
        st.metric("📊 LR R² (approx)", f"{lr_r2:.4f}")

    c1, c2 = st.columns(2)
    with c1:
        fig, ax = plt.subplots(figsize=(7, 4))
        colors_acc = sns.color_palette("Blues_r", len(rf_per_ch))
        ax.bar(rf_per_ch["Channel"], rf_per_ch["RF_Accuracy"], color=colors_acc, edgecolor="white")
        ax.set_ylim(0, 1.1)
        ax.axhline(y=0.9, color="red", linestyle="--", alpha=0.7, label="0.9 threshold")
        ax.set_title("RF Classifier Accuracy per Channel", fontweight="bold")
        ax.set_ylabel("Accuracy"); ax.legend()
        for i, v in enumerate(rf_per_ch["RF_Accuracy"]):
            ax.text(i, v + 0.01, f"{v:.3f}", ha="center", fontsize=9, fontweight="bold")
        plt.tight_layout(); st.pyplot(fig); plt.close()

    with c2:
        rev_per_ch = df_f2.groupby("Channel").agg(
            Actual=("Revenue_USD","mean"),
            Predicted=("lr_predicted_revenue","mean")
        ).reset_index()
        fig, ax = plt.subplots(figsize=(7, 4))
        x_r = np.arange(len(rev_per_ch)); w_r = 0.35
        ax.bar(x_r - w_r/2, rev_per_ch["Actual"],    w_r, label="Actual",    color="steelblue",  edgecolor="white")
        ax.bar(x_r + w_r/2, rev_per_ch["Predicted"], w_r, label="Predicted", color="darkorange", edgecolor="white")
        ax.set_xticks(x_r); ax.set_xticklabels(rev_per_ch["Channel"])
        ax.set_title("Actual vs Predicted Revenue per Channel", fontweight="bold")
        ax.set_ylabel("Avg Revenue (USD)"); ax.legend()
        plt.tight_layout(); st.pyplot(fig); plt.close()

    # LR Error Distribution + Actual vs Predicted scatter
    c3, c4 = st.columns(2)
    with c3:
        fig, ax = plt.subplots(figsize=(7, 4))
        err_clipped = df_f2["lr_error"].clip(
            lower=df_f2["lr_error"].quantile(0.01),
            upper=df_f2["lr_error"].quantile(0.99)
        )
        ax.hist(err_clipped, bins=50, color="#9b59b6", edgecolor="white", alpha=0.85)
        ax.axvline(x=0, color="red", linestyle="--", linewidth=2, label="Perfect Prediction")
        ax.axvline(x=df_f2["lr_error"].mean(), color="orange", linestyle="--",
                   linewidth=1.5, label=f"Mean Error: ${df_f2['lr_error'].mean():.0f}")
        ax.set_title("Distribusi Error Prediksi Revenue (LR)", fontweight="bold")
        ax.set_xlabel("Actual − Predicted (USD)"); ax.set_ylabel("Frekuensi"); ax.legend(fontsize=9)
        plt.tight_layout(); st.pyplot(fig); plt.close()

    with c4:
        fig, ax = plt.subplots(figsize=(7, 4))
        ax.scatter(df_f2["Revenue_USD"], df_f2["lr_predicted_revenue"],
                   alpha=0.25, s=8, color="steelblue")
        lim = max(df_f2["Revenue_USD"].max(), df_f2["lr_predicted_revenue"].max())
        ax.plot([0, lim], [0, lim], "r--", linewidth=1.5, label="Perfect Prediction")
        ax.set_title(f"LR: Actual vs Predicted Revenue (R²≈{lr_r2:.4f})", fontweight="bold")
        ax.set_xlabel("Actual Revenue (USD)"); ax.set_ylabel("Predicted Revenue (USD)")
        ax.legend()
        plt.tight_layout(); st.pyplot(fig); plt.close()

# ════════════════════════════════════════════════════════════════
# TAB 4: Correlation & Distribusi
# ════════════════════════════════════════════════════════════════
with tab4:
    st.markdown('<div class="section-header">Correlation Matrix</div>', unsafe_allow_html=True)

    base_cols = ["Impressions","Clicks","Leads","Conversions","Cost_USD","Revenue_USD","ROI","CTR","CPC","CPL","CVR","Campaign_Duration"]
    extra_cols = [c for c in ["ROAS","Profit_USD"] if c in df_f.columns]
    corr_cols = base_cols + extra_cols
    corr_cols = [c for c in corr_cols if c in df_f.columns]
    corr_m = df_f[corr_cols].corr()

    fig, ax = plt.subplots(figsize=(13, 9))
    mask = np.triu(np.ones_like(corr_m, dtype=bool))
    sns.heatmap(corr_m, mask=mask, annot=True, fmt=".2f", cmap="RdYlGn",
                center=0, vmin=-1, vmax=1, square=True, linewidths=0.5,
                annot_kws={"size": 8}, cbar_kws={"shrink": 0.8}, ax=ax)
    ax.set_title("Correlation Matrix — Marketing Campaign Metrics", fontweight="bold", fontsize=13)
    plt.tight_layout(); st.pyplot(fig); plt.close()

    st.markdown('<div class="section-header">Distribusi Metrik Utama</div>', unsafe_allow_html=True)
    dist_cols = ["ROI","Revenue_USD","Cost_USD","CTR","CVR"]
    if "ROAS" in df_f.columns:
        dist_cols.append("ROAS")

    fig, axes = plt.subplots(2, 3, figsize=(16, 9))
    axes = axes.flatten()
    for i, col in enumerate(dist_cols):
        if col not in df_f.columns:
            continue
        data = df_f[col].clip(lower=df_f[col].quantile(0.01), upper=df_f[col].quantile(0.99))
        axes[i].hist(data, bins=50, color=COLORS[i], edgecolor="white", alpha=0.85)
        axes[i].axvline(data.mean(),   color="red",    linestyle="--", linewidth=1.5,
                        label=f"Mean: {data.mean():.3f}")
        axes[i].axvline(data.median(), color="orange", linestyle=":",  linewidth=1.5,
                        label=f"Median: {data.median():.3f}")
        axes[i].set_title(f"Distribusi {col}", fontweight="bold")
        axes[i].legend(fontsize=8)
    plt.suptitle("Distribusi Metrik Utama Kampanye", fontsize=14, fontweight="bold")
    plt.tight_layout(); st.pyplot(fig); plt.close()

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("---")
st.caption("📦 Data source: MinIO Gold Layer (Parquet) · Model: Spark MLlib Random Forest + Linear Regression")