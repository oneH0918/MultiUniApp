#!/bin/bash

# データベースの初期化
python database/init_db.py

# GunicornでFlaskを起動（環境変数 PORT を取得して Gunicorn を起動）
PORT=${PORT:-10000}  # デフォルト値 10000
exec gunicorn -b 0.0.0.0:$PORT main:app