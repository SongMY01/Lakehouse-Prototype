./bin/sql-client.sh
-- =========================================
-- 0) 세션/전역 옵션
-- =========================================

SET 'table.local-time-zone' = 'Asia/Seoul';

-- =========================================
-- 1) Kafka 소스 테이블 (default_catalog)
--    - 이벤트타임(ts) + 워터마크 포함
--    - group.id는 새 값으로(오프셋 충돌 방지)
-- =========================================
USE CATALOG default_catalog;
USE default_database;

CREATE TEMPORARY TABLE mouse_events_src (
  shape STRING,
  event_type STRING,
  altKey BOOLEAN,
  ctrlKey BOOLEAN,
  metaKey BOOLEAN,
  shiftKey BOOLEAN,
  button INT,
  buttons INT,
  clientX INT,
  clientY INT,
  pageX INT,
  pageY INT,
  screenX INT,
  screenY INT,
  `timestamp`  BIGINT,                          -- 원본 ms
  canvasX DOUBLE,
  canvasY DOUBLE,
  movementX DOUBLE,
  movementY DOUBLE,
  isTrusted BOOLEAN,
  ts AS TO_TIMESTAMP_LTZ(`timestamp`, 3),       -- 이벤트타임
  WATERMARK FOR ts AS ts - INTERVAL '3' SECOND  -- 지연 허용 3초
) WITH (
  'connector' = 'kafka',
  'topic' = 'mouse_events',
  'properties.bootstrap.servers' = 'sv_kafka:29092',
  'properties.group.id' = 'flink-consumer-mouse-p8',
  'scan.startup.mode' = 'latest-offset',                 -- 필요시 earliest-offset
  'scan.topic-partition-discovery.interval' = '60 s',
  'format' = 'json',
  'json.ignore-parse-errors' = 'true',
  -- 소형 이벤트 벌크 fetch 튜닝
  'properties.fetch.min.bytes' = '1048576',
  'properties.fetch.max.wait.ms' = '100',
  'properties.max.partition.fetch.bytes' = '8388608'
);

CREATE TEMPORARY TABLE keydown_events_src (
  altKey BOOLEAN,
  ctrlKey BOOLEAN,
  metaKey BOOLEAN,
  shiftKey BOOLEAN,
  `key` STRING,
  `code` STRING,
  `timestamp`  BIGINT,
  `type` STRING,
  ts AS TO_TIMESTAMP_LTZ(`timestamp`, 3),
  WATERMARK FOR ts AS ts - INTERVAL '3' SECOND
) WITH (
  'connector' = 'kafka',
  'topic' = 'keydown_events',
  'properties.bootstrap.servers' = 'sv_kafka:29092',
  'properties.group.id' = 'flink-consumer-key-p8',
  'scan.startup.mode' = 'latest-offset',
  'scan.topic-partition-discovery.interval' = '60 s',
  'format' = 'json',
  'json.ignore-parse-errors' = 'true',
  'properties.fetch.min.bytes' = '1048576',
  'properties.fetch.max.wait.ms' = '100',
  'properties.max.partition.fetch.bytes' = '8388608'
);

-- =========================================
-- 2) Iceberg 카탈로그/DB/싱크 테이블
--    - 시간 파티션(ts_hour) + 파일/압축 옵션
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

-- (스키마 맞춤을 위해 필요시 드롭)
DROP TABLE IF EXISTS user_events.mouse_events;
DROP TABLE IF EXISTS user_events.keydown_events;

CREATE TABLE user_events.mouse_events (
  shape STRING,
  event_type STRING,
  altKey BOOLEAN,
  ctrlKey BOOLEAN,
  metaKey BOOLEAN,
  shiftKey BOOLEAN,
  button INT,
  buttons INT,
  clientX INT,
  clientY INT,
  pageX INT,
  pageY INT,
  screenX INT,
  screenY INT,
  `timestamp`  BIGINT,                  -- 원본 이벤트 ms
  canvasX DOUBLE,
  canvasY DOUBLE,
  movementX DOUBLE,
  movementY DOUBLE,
  isTrusted BOOLEAN,
  ts TIMESTAMP_LTZ(3),                  -- 이벤트타임
  ts_hour TIMESTAMP_LTZ(3)              -- 시간 파티션 키
)
PARTITIONED BY (ts_hour)
WITH (
  'write.target-file-size-bytes' = '134217728',       -- 128MB
  'write.distribution-mode'      = 'hash',
  'write.parquet.compression-codec' = 'zstd'
);

CREATE TABLE user_events.keydown_events (
  altKey BOOLEAN,
  ctrlKey BOOLEAN,
  metaKey BOOLEAN,
  shiftKey BOOLEAN,
  `key` STRING,
  `code` STRING,
  `timestamp`  BIGINT,
  `type` STRING,
  ts TIMESTAMP_LTZ(3),
  ts_hour TIMESTAMP_LTZ(3)
)
PARTITIONED BY (ts_hour)
WITH (
  'write.target-file-size-bytes' = '134217728',
  'write.distribution-mode'      = 'hash',
  'write.parquet.compression-codec' = 'zstd'
);

-- =========================================
-- 3) Kafka → Iceberg 적재 (Exactly-Once)
--    - ts_hour = FLOOR(ts TO HOUR)
-- =========================================
INSERT INTO iceberg.user_events.mouse_events
SELECT
  shape, event_type, altKey, ctrlKey, metaKey, shiftKey,
  button, buttons,
  clientX, clientY, pageX, pageY, screenX, screenY,
  `timestamp`, 
  canvasX, canvasY, movementX, movementY,
  isTrusted, ts,
  CAST(FLOOR(ts TO HOUR) AS TIMESTAMP_LTZ(3)) AS ts_hour
FROM default_catalog.default_database.mouse_events_src;

INSERT INTO iceberg.user_events.keydown_events
SELECT
  altKey, ctrlKey, metaKey, shiftKey,
  `key`, `code`,
  `timestamp`, `type`,
  ts,
  CAST(FLOOR(ts TO HOUR) AS TIMESTAMP_LTZ(3)) AS ts_hour
FROM default_catalog.default_database.keydown_events_src;
