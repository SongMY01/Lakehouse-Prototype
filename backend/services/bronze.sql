./bin/sql-client.sh
-- =========================================
-- 0) 세션 옵션
-- =========================================
SET 'table.local-time-zone' = 'Asia/Seoul';

-- =========================================
-- 1) Kafka Source (raw string)
--    - JSON 전체를 payload로 읽음
-- =========================================
USE CATALOG default_catalog;
USE default_database;

CREATE TEMPORARY TABLE raw_events_src (
  payload STRING   -- Kafka 메시지 한 줄 전체
) WITH (
  'connector' = 'kafka',
  'topic' = 'user_events',
  'properties.bootstrap.servers' = 'broker-1:19092,broker-2:19092,broker-3:19092',
  'properties.group.id' = 'flink-consumer-bronze-raw',
  'scan.startup.mode' = 'latest-offset',
  'scan.topic-partition-discovery.interval' = '60 s',
  'format' = 'raw'
);

-- =========================================
-- 2) Iceberg Catalog + Bronze Table
-- =========================================
CREATE CATALOG iceberg WITH (
  'type' = 'iceberg',
  'catalog-type' = 'rest',
  'uri' = 'http://iceberg-rest:8181',
  'warehouse' = 's3://warehouse/',
  'io-impl' = 'org.apache.iceberg.aws.s3.S3FileIO',
  's3.endpoint' = 'http://minio:9000',
  's3.access-key-id' = 'admin',
  's3.secret-access-key' = 'password',
  'aws.region' = 'us-east-1'
);

USE CATALOG iceberg;
CREATE DATABASE IF NOT EXISTS user_events;

DROP TABLE IF EXISTS user_events.events_bronze;

CREATE TABLE user_events.events_bronze (
  `type` STRING,
  `timeStamp` BIGINT,
  `payload` STRING,                -- 원본 JSON 전체
  ts TIMESTAMP_LTZ(3),
  ts_hour TIMESTAMP_LTZ(3)
)
PARTITIONED BY (ts_hour, type)
WITH (
  'write.target-file-size-bytes' = '134217728',
  'write.distribution-mode' = 'hash',
  'write.parquet.compression-codec' = 'zstd'
);

-- =========================================
-- 3) Kafka → Iceberg Bronze Insert
--    - JSON_VALUE 함수로 필드 추출
-- =========================================
INSERT INTO iceberg.user_events.events_bronze
SELECT
  JSON_VALUE(payload, '$.type') AS `type`,
  CAST(JSON_VALUE(payload, '$.timeStamp') AS BIGINT) AS `timeStamp`,
  payload,
  TO_TIMESTAMP_LTZ(CAST(JSON_VALUE(payload, '$.timeStamp') AS BIGINT), 3) AS ts,
  CAST(
    FLOOR(
      TO_TIMESTAMP_LTZ(CAST(JSON_VALUE(payload, '$.timeStamp') AS BIGINT), 3) 
      TO HOUR
    ) AS TIMESTAMP_LTZ(3)
  ) AS ts_hour
FROM default_catalog.default_database.raw_events_src;
