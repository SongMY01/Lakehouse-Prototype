import streamlit as st
import pandas as pd
import boto3
import json
import io
import pyarrow.parquet as pq
from fastavro import reader
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

# 📌 카탈로그 로드
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

# 📌 테이블 로드
table = catalog.load_table(TABLE_NAME)

# 📌 S3 클라이언트
s3 = boto3.client(
    "s3",
    endpoint_url=MINIO_ENDPOINT,
    aws_access_key_id=ACCESS_KEY,
    aws_secret_access_key=SECRET_KEY,
    region_name="us-east-1"
)

# 📌 경로
metadata_prefix = "mouse_events.db/click_events/metadata/"
data_prefix = "mouse_events.db/click_events/data/"

st.set_page_config(page_title="Iceberg Latest Metadata Explorer", layout="wide")
st.title("🧊 Iceberg Table Explorer")

def get_latest_file(bucket, prefix, filter_fn):
    objs = s3.list_objects_v2(Bucket=bucket, Prefix=prefix).get("Contents", [])
    filtered = [o for o in objs if filter_fn(o["Key"])]
    if not filtered:
        return None
    # 최신 파일 = 마지막 수정 시각 기준
    latest = max(filtered, key=lambda x: x["LastModified"])
    return latest["Key"]

def show_json_file(key):
    content = s3.get_object(Bucket=BUCKET_NAME, Key=key)["Body"].read()
    st.json(json.loads(content))

def show_avro_file(key):
    body = s3.get_object(Bucket=BUCKET_NAME, Key=key)["Body"].read()
    with io.BytesIO(body) as f:
        avro_reader = reader(f)
        records = list(avro_reader)
        df = pd.DataFrame(records)
        st.dataframe(df)

def show_parquet_file(key):
    body = s3.get_object(Bucket=BUCKET_NAME, Key=key)["Body"].read()
    table = pq.read_table(io.BytesIO(body))
    df = table.to_pandas()
    st.dataframe(df.head())

# --- Metadata file ---
st.header("📑 Metadata file")
meta_key = get_latest_file(BUCKET_NAME, metadata_prefix, lambda k: k.endswith(".metadata.json"))
if meta_key:
    st.subheader(f"📄 {meta_key}")
    show_json_file(meta_key)

# --- Manifest list ---
st.header("📑 Manifest List file")
ml_key = get_latest_file(BUCKET_NAME, metadata_prefix, lambda k: "snap-" in k and k.endswith(".avro"))
if ml_key:
    st.subheader(f"📄 {ml_key}")
    show_avro_file(ml_key)

# --- Manifest file ---
st.header("📑 Manifest file")
mf_key = get_latest_file(BUCKET_NAME, metadata_prefix, lambda k: k.endswith("-m0.avro"))
if mf_key:
    st.subheader(f"📄 {mf_key}")
    show_avro_file(mf_key)

# --- Data file ---
st.header("📄 Data file")

df_key = get_latest_file(BUCKET_NAME, data_prefix, lambda k: k.endswith(".parquet"))

if df_key:
    st.subheader(f"📄 {df_key}")
    body = s3.get_object(Bucket=BUCKET_NAME, Key=df_key)["Body"].read()
    table = pq.read_table(io.BytesIO(body))
    df = table.to_pandas()
    
    # KST로 timestamp 컬럼 변환
    if 'timestamp' in df.columns:
        df['timestamp'] = (
            pd.to_datetime(df['timestamp'], unit='ms', utc=True)
            .dt.tz_convert('Asia/Seoul')
        )
        # 보기 좋게 정렬
        df = df.sort_values('timestamp', ascending=False)

    st.dataframe(df.head(50))  # 최신 50건만 보여주기