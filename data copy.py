import streamlit as st
import pandas as pd
from pyiceberg.catalog import load_catalog


# 📌 Iceberg 카탈로그 설정
CATALOG_NAME = "mouse_catalog"
NAMESPACE = "mouse_events"
TABLE_NAME = f"{NAMESPACE}.click_events"

warehouse_meta_path = "/Users/minyoung.song/projects/bmp/workspace/my-project/warehouse"
MINIO_ENDPOINT = "http://localhost:9000"
ACCESS_KEY = "minioadmin"
SECRET_KEY = "minioadmin"
BUCKET_NAME = "mouse-click"

# 카탈로그 로드
catalog = load_catalog(
    CATALOG_NAME,
    **{
        "type": "sql",
        "uri": f"sqlite:///{warehouse_meta_path}/pyiceberg_catalog.db",
        "warehouse": f"s3://{BUCKET_NAME}",
        "s3.endpoint": MINIO_ENDPOINT,
        "s3.access-key-id": ACCESS_KEY,
        "s3.secret-access-key": SECRET_KEY,
        "s3.region": "us-east-1",
    }
)

# 테이블 로드
table = catalog.load_table(TABLE_NAME)

# 데이터 로드 (PyArrow Table → pandas)
arrow_table = table.scan().to_arrow()
df = arrow_table.to_pandas()
if 'timestamp' in df.columns:
    df["timestamp"] = (
        pd.to_datetime(df["timestamp"], unit="ms", utc=True)
        .dt.tz_convert("Asia/Seoul")
    )
    df = df.sort_values("timestamp", ascending=False)

# --- Streamlit 앱 시작 ---
st.set_page_config(page_title="Mouse Click Events Dashboard", layout="wide")

st.title("🖱️ Mouse Click Events Dashboard")

if st.button("🔄 최신 데이터 불러오기"):
    st.rerun()
st.subheader("📋 Raw Data")
st.dataframe(df, use_container_width=True)

st.subheader("🕒 Timestamp Distribution")
df.set_index("timestamp", inplace=True)
st.line_chart(df.resample("1min").size())