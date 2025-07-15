import os
from pyiceberg.catalog import load_catalog

# 📁 베이스 디렉토리 설정
BASE_DIR = "/Users/minyoung.song/projects/bmp/workspace/my-project"
WAREHOUSE_META_PATH = os.path.join(BASE_DIR, "warehouse", "pyiceberg_catalog.db")
CATALOG_NAME = "mouse_catalog"                # 카탈로그 이름
NAMESPACE_NAME = "mouse_events"              # 네임스페이스 이름

# 📄 카탈로그 로드
catalog = load_catalog(
    CATALOG_NAME,
    **{
        "type": "sql",
        "uri": f"sqlite:///{WAREHOUSE_META_PATH}",  # Iceberg 메타데이터가 저장된 sqlite
        "warehouse": "s3://mouse-click",  # 실제 데이터는 MinIO의 my-bucket에 저장
        "s3.endpoint": "http://localhost:9000",
        "s3.access-key-id": "minioadmin",
        "s3.secret-access-key": "minioadmin",
        "s3.region": "us-east-1",
    }
)

# 📋 테이블 로드
table = catalog.load_table("mouse_events.click_events")

# 🔷 테이블 스키마 출력
print("📄 테이블 스키마:")
print(table.schema())

# 🔷 현재 스냅샷 ID와 버전 출력
print("\n📄 현재 스냅샷:")
print(f"Snapshot ID: {table.current_snapshot().snapshot_id}")
print(f"Timestamp: {table.current_snapshot().timestamp_ms}")

# 🔷 모든 스냅샷 목록 출력
print("\n📄 스냅샷 목록:")
for snapshot in table.snapshots():
    print(f"- ID: {snapshot.snapshot_id}, Timestamp: {snapshot.timestamp_ms}")

# 🔷 테이블 데이터를 Arrow → pandas로 로드
df = table.scan().to_arrow().to_pandas()
print("\n📋 테이블 데이터:")
print(df.head())

# 🔷 테이블의 메타데이터 파일 경로 출력
print("\n📄 메타데이터 파일 경로:")
print(table.metadata_location)
