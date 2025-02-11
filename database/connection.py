import sqlite3
import traceback

# --- データベース接続 ---
def get_db_connection():
    try:
        conn = sqlite3.connect("tasks.db", check_same_thread=False)
        conn.row_factory = sqlite3.Row  # カラム名でアクセス可能に
        return conn
    except sqlite3.Error as e:
        print(f"データベース接続エラー: {e}")
        print(traceback.format_exc())
        raise