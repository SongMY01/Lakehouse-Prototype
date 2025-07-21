import os
import redis
import pyarrow as pa
import threading
import time
import logging
from database.redis import r
from database.iceberg import catalog, NAMESPACE_NAME
from schemas.click_event import click_arrow_fields
from schemas.keydown_event import keydown_arrow_fields
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=log_level,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

GROUP_NAME = "worker-group"
CONSUMER_NAME = "worker-1"
BATCH_SIZE = 10
TIMEOUT_SEC = 5

SCHEMAS = {
    "click": click_arrow_fields(),
    "keydown": keydown_arrow_fields(),
}


def delete_from_stream(stream_name, ids):
    time.sleep(5)
    for msg_id in ids:
        r.xdel(stream_name, msg_id)
    logger.info(f"🗑️ [{stream_name}] Stream에서 {len(ids)}건 삭제")


def process_stream(stream_name):
    try:
        r.xgroup_create(stream_name, GROUP_NAME, id='0', mkstream=True)
        logger.info(f"✅ 컨슈머 그룹 생성: {stream_name}:{GROUP_NAME}")
    except redis.exceptions.ResponseError as e: # type: ignore
        if "BUSYGROUP" in str(e):
            logger.info(f"✅ 컨슈머 그룹 이미 존재: {stream_name}:{GROUP_NAME}")
        else:
            raise e

    batch = []
    ids = []
    last_flush = time.time()

    while True:
        msgs = r.xreadgroup(
            groupname=GROUP_NAME,
            consumername=CONSUMER_NAME,
            streams={stream_name: '>'},
            count=BATCH_SIZE,
            block=2000
        )

        now = time.time()

        if msgs:
            for _, messages in msgs: # type: ignore
                for msg_id, fields in messages:
                    event_type = stream_name.replace("_events", "")
                    table_name = f"{NAMESPACE_NAME}.{event_type}_events"
                    schema_fields = SCHEMAS[event_type]

                    record = {}
                    for k, typ in schema_fields:
                        v = fields.get(k)

                        # 안전한 타입 변환
                        if typ == pa.bool_():
                            record[k] = True if v == "True" else False
                        elif typ == pa.int32():
                            try:
                                record[k] = int(v) if v not in [None, ""] else 0
                            except (ValueError, TypeError):
                                record[k] = 0
                        elif typ == pa.timestamp("ms"):
                            try:
                                record[k] = int(v) if v not in [None, ""] else 0
                            except (ValueError, TypeError):
                                record[k] = 0
                        else:
                            record[k] = v if v is not None else ""

                    batch.append(record)
                    ids.append(msg_id)
                    r.xack(stream_name, GROUP_NAME, msg_id)

        if len(batch) >= BATCH_SIZE or (batch and now - last_flush >= TIMEOUT_SEC):
            logger.info(f"📋 [{stream_name}] 배치 적재 시작: {len(batch)}건")

            columns, names = [], []
            for name, typ in schema_fields:
                col = []
                for r_ in batch:
                    val = r_.get(name)
                    if typ == pa.int32():
                        if val in [None, ""]:
                            val = 0
                        elif not isinstance(val, int):
                            try:
                                val = int(val)
                            except (ValueError, TypeError):
                                val = 0
                    if typ == pa.bool_():
                        val = bool(val) if val not in [None, ""] else False
                    if typ == pa.string() and val is None:
                        val = ""
                    if typ == pa.timestamp("ms"):
                        if val in [None, ""]:
                            val = 0
                        elif not isinstance(val, int):
                            try:
                                val = int(val)
                            except (ValueError, TypeError):
                                val = 0
                    col.append(val)
                columns.append(pa.array(col, type=typ))
                names.append(name)

            record_batch = pa.record_batch(columns, names=names)

            try:
                table = catalog.load_table(table_name)
                table.append(pa.Table.from_batches([record_batch]))
                logger.info(f"✅ [{stream_name}] Iceberg 적재 완료: {len(batch)}건")
            except Exception as e:
                logger.error(f"🚨 Iceberg 테이블 로드 실패: {table_name}\n{e}")

            threading.Thread(
                target=delete_from_stream,
                args=(stream_name, ids.copy(),)
            ).start()
            batch.clear()
            ids.clear()
            last_flush = now


if __name__ == "__main__":
    streams = ["click_events", "keydown_events"]
    threads = []
    for stream in streams:
        t = threading.Thread(target=process_stream, args=(stream,))
        t.start()
        threads.append(t)

    for t in threads:
        t.join()