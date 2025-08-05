CREATE TABLE mouse_events_src (
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
  `timestamp`  BIGINT,
  event_type STRING,
  canvasId STRING,
  canvasX DOUBLE,
  canvasY DOUBLE,
  movementX DOUBLE,
  movementY DOUBLE,
  isTrusted BOOLEAN,
  shape STRING
) WITH (
  'connector' = 'kafka',
  'topic' = 'mouse_events',
  'properties.bootstrap.servers' = 'sv_kafka:29092',
  'properties.group.id' = 'flink-consumer',
  'format' = 'json',
  'scan.startup.mode' = 'earliest-offset'
);

CREATE TABLE keydown_events_src (
  altKey BOOLEAN,
  ctrlKey BOOLEAN,
  metaKey BOOLEAN,
  shiftKey BOOLEAN,
  key STRING,
  code STRING,
  `timestamp`  BIGINT,
  `type` STRING
) WITH (
  'connector' = 'kafka',
  'topic' = 'keydown_events',
  'properties.bootstrap.servers' = 'sv_kafka:29092',
  'properties.group.id' = 'flink-consumer',
  'format' = 'json',
  'scan.startup.mode' = 'earliest-offset'
);

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

CREATE TABLE IF NOT EXISTS user_events.mouse_events (
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
  `timestamp`  BIGINT,
  event_type STRING,
  canvasId STRING,
  canvasX DOUBLE,
  canvasY DOUBLE,
  movementX DOUBLE,
  movementY DOUBLE,
  isTrusted BOOLEAN,
  shape STRING
);

CREATE TABLE IF NOT EXISTS user_events.keydown_events (
  altKey BOOLEAN,
  ctrlKey BOOLEAN,
  metaKey BOOLEAN,
  shiftKey BOOLEAN,
  key STRING,
  code STRING,
  `timestamp`  BIGINT,
  `type` STRING
);

SET 'execution.checkpointing.interval' = '10s';

INSERT INTO user_events.mouse_events
SELECT
  altKey,
  ctrlKey,
  metaKey,
  shiftKey,
  button,
  buttons,
  clientX,
  clientY,
  pageX,
  pageY,
  screenX,
  screenY,
  TO_TIMESTAMP_LTZ(`timestamp`, 3) AS `timestamp`,
  event_type,
  canvasId,
  canvasX,
  canvasY,
  movementX,
  movementY,
  isTrusted,
  shape
FROM default_catalog.default_database.mouse_events_src;



INSERT INTO user_events.keydown_events
SELECT
  altKey,
  ctrlKey,
  metaKey,
  shiftKey,
  key,
  code,
  TO_TIMESTAMP_LTZ(`timestamp`, 3) AS `timestamp`,
  `type`
FROM default_catalog.default_database.keydown_events_src;