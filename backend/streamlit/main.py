# -*- coding: utf-8 -*-
# file: streamlit/main.py
# desc: Iceberg 데이터를 시각화하는 Streamlit 대시보드
# author: minyoung.song
# created: 2025-07-23

import logging
import streamlit as st
import pandas as pd
from pyiceberg.catalog import load_catalog
from pathlib import Path
import os

# 🔷 로거 설정
logger = logging.getLogger(__name__)

# 🔷 MinIO 및 Iceberg 설정
MINIO_ENDPOINT = "http://minio:9000"
ACCESS_KEY = "minioadmin"
SECRET_KEY = "minioadmin"
BUCKET_NAME = "user-events"

# 🔷 메타데이터 경로 설정 (backend/ 기준)
BASE_DIR = Path(__file__).resolve().parent.parent
WAREHOUSE_META_PATH = BASE_DIR / "db/warehouse"

# 🔷 Iceberg 카탈로그 설정
CATALOG_NAME = "user_catalog"
NAMESPACE = "user_events"

# 🔷 Iceberg 메타데이터 디렉토리 생성
logger.info("Ensuring warehouse metadata directory exists at %s", WAREHOUSE_META_PATH)
os.makedirs(WAREHOUSE_META_PATH, exist_ok=True)

# # 🔷 Iceberg 카탈로그 로드
# catalog = load_catalog(
#     CATALOG_NAME,
#     **{
#         "type": "sql",
#         "uri": f"sqlite:///{WAREHOUSE_META_PATH}/pyiceberg_catalog.db",
#         "warehouse": f"s3://{BUCKET_NAME}",
#         "s3.endpoint": MINIO_ENDPOINT,
#         "s3.access-key-id": ACCESS_KEY,
#         "s3.secret-access-key": SECRET_KEY,
#         "s3.region": "us-east-1",
#     }
# )

catalog = load_catalog(
    name="rest",
    uri="http://rest:8181",
    warehouse="s3://rest-bucket"
)

# --- Streamlit 앱 시작 ---
st.set_page_config(page_title="User Events Dashboard", layout="wide")

st.title("🎯 User Events Dashboard")

# 🔷 테이블 선택 (클릭/키다운)
table_choice = st.selectbox("📋 테이블 선택", options=["click_events", "keydown_events"])
TABLE_NAME = f"{NAMESPACE}.{table_choice}"

# 🔷 최신 데이터 갱신 버튼
if st.button("🔄 최신 데이터 불러오기"):
    st.rerun()

# 🔷 Iceberg 테이블 로드 및 시각화
try:
    # 테이블 로드
    table = catalog.load_table(TABLE_NAME)
    arrow_table = table.scan().to_arrow()
    df = arrow_table.to_pandas()

    # timestamp 컬럼 처리 (서울 시간대로 변환 후 최신순 정렬)
    if 'timestamp' in df.columns:
        df["timestamp"] = (
            pd.to_datetime(df["timestamp"], unit="ms", utc=True)
            .dt.tz_convert("Asia/Seoul")
        )
        df = df.sort_values("timestamp", ascending=False)

    # 🔷 Raw Data 출력
    st.subheader("📋 Raw Data")
    st.dataframe(df, use_container_width=True)

    # 🔷 타임스탬프 분포 차트
    st.subheader("🕒 Timestamp Distribution")
    if not df.empty:
        df.set_index("timestamp", inplace=True)
        st.line_chart(df.resample("1min").size())
    else:
        st.info("데이터가 없습니다.")

except Exception as e:
    # 🔷 에러 처리
    st.error(f"🚨 테이블 로드 실패: {e}")