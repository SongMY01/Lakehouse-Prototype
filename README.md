Iceberg Prototype

# Frontend
React, next.js


# Backend
FAST API

uvicorn main:app --reload --port 8000


# Iceberg
pyiceberg


# Storage
MinIO

docker run -d --name minio \                                             
  -p 9000:9000 -p 9001:9001 \
  -e "MINIO_ROOT_USER=minioadmin" \
  -e "MINIO_ROOT_PASSWORD=minioadmin" \
  -v /Users/minyoung.song/projects/bmp/workspace/my-project/data:/data \
  minio/minio server /data --console-address ":9001"