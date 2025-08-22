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
from config.iceberg import catalog

# 🔷 로거 설정
logger = logging.getLogger(__name__)

# 🔷 MinIO 및 Iceberg 설정
MINIO_ENDPOINT = "http://minio:9000"
ACCESS_KEY = "minioadmin"
SECRET_KEY = "minioadmin"
BUCKET_NAME = "warehouse"

# 🔷 Iceberg 카탈로그 설정
CATALOG_NAME = "default"
NAMESPACE = "user_events"

# --- Streamlit 앱 시작 ---
st.set_page_config(page_title="User Events Dashboard", layout="wide")

st.title("🎯 User Events Dashboard")

# 🔷 테이블 선택 (클릭/키다운)
table_choice = st.selectbox("📋 테이블 선택", options=["events_bronze"])
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

    # timeStamp 컬럼 처리 (서울 시간대로 변환 후 최신순 정렬)
    if 'timeStamp' in df.columns:
        df["timeStamp"] = (
            pd.to_datetime(df["timeStamp"], unit="ms", utc=True)
            .dt.tz_convert("Asia/Seoul")
        )
        df = df.sort_values("timeStamp", ascending=False)

    # ts, ts_hour도 서울 시간대로 변환 (UTC → Asia/Seoul)
    if 'ts' in df.columns:
        df["ts"] = df["ts"].dt.tz_convert("Asia/Seoul")

    if 'ts_hour' in df.columns:
        df["ts_hour"] = df["ts_hour"].dt.tz_convert("Asia/Seoul")

    # 🔷 Raw Data 출력
    st.subheader("📋 Raw Data")
    st.dataframe(df.head(1000), use_container_width=True)

    # 🔷 타임스탬프 분포 차트
    st.subheader("🕒 timeStamp Distribution")
    if not df.empty:
        df.set_index("timeStamp", inplace=True)
        st.line_chart(df.resample("1min").size().tail(180))
    else:
        st.info("데이터가 없습니다.")

except Exception as e:
    # 🔷 에러 처리
    st.error(f"🚨 테이블 로드 실패: {e}")