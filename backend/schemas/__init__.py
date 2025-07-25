# -*- coding: utf-8 -*-
# file: schemas/__init__.py
# desc: schemas 디렉토리의 *_event.py 파일을 자동 로딩하여 SCHEMAS, schema_files 제공
# author: 송민영
# created: 2025-07-25

import os
import glob
import importlib

import pyarrow as pa

SCHEMAS = {}
schema_files = []

# 현재 파일 기준 상대경로로 schemas 디렉토리 탐색
schemas_path = os.path.dirname(__file__)
schema_files = glob.glob(os.path.join(schemas_path, "*_event.py"))

for f in schema_files:
    basename = os.path.basename(f).replace(".py", "")
    event_type = basename.replace("_event", "")
    module_name = f"schemas.{basename}"

    try:
        mod = importlib.import_module(module_name)
        arrow_func = getattr(mod, f"{event_type}_arrow_fields")
        SCHEMAS[event_type] = arrow_func()
    except Exception as e:
        raise ImportError(f"❌ {module_name} 모듈 로딩 실패: {e}")