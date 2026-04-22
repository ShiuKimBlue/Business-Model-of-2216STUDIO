#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import pandas as pd
from datetime import datetime, timedelta


def load_json_data(json_path):
    if not os.path.exists(json_path):
        raise FileNotFoundError(
            f"找不到数据文件：{json_path}\n"
            "请从微信云开发控制台导出 bookings.json 放入 data/ 目录"
        )
    
    with open(json_path, 'r', encoding='utf-8') as f:
        raw = json.load(f)
    
    if isinstance(raw, dict) and 'data' in raw:
        records = raw['data']
    elif isinstance(raw, list):
        records = raw
    else:
        raise ValueError("无法识别的JSON格式")
    
    return pd.DataFrame(records)


def parse_date_range(days=7, start_date=None, end_date=None):
    if end_date is None:
        end = datetime.now().date()
    else:
        end = datetime.strptime(end_date, '%Y-%m-%d').date()
    
    if start_date is None:
        start = end - timedelta(days=days)
    else:
        start = datetime.strptime(start_date, '%Y-%m-%d').date()
    
    return str(start), str(end)


def ensure_dir(path):
    os.makedirs(path, exist_ok=True)
    return path