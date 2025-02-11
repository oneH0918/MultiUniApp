import sqlite3
import os
from database.connection import get_db_connection

def has_column(cursor, table_name, column_name):
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [col[1] for col in cursor.fetchall()]
    return column_name in columns

# --- データベースの初期化 ---
def init_db():
    db_path = "tasks.db"

    # データベースファイルが存在しない場合に新規作成し、必要なテーブルを初期化する。
    if not os.path.exists(db_path):
        print(f"{db_path} が存在しないため、新規作成します...")

    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            # タスクテーブル
            c.execute('''CREATE TABLE IF NOT EXISTS tasks (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            name TEXT NOT NULL,
                            details TEXT,
                            due_date TEXT,
                            priority TEXT,
                            category TEXT,
                            tags TEXT
                        )''')

            # 既に作成済のテーブルに status カラムがあるか確認し、なければ追加する
            if not has_column(c, "tasks", "status"):
                c.execute("ALTER TABLE tasks ADD COLUMN status TEXT")

            # カテゴリテーブル
            c.execute('''CREATE TABLE IF NOT EXISTS categories (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            name TEXT NOT NULL UNIQUE
                        )''')

            # タグテーブル
            c.execute('''CREATE TABLE IF NOT EXISTS tags (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            name TEXT NOT NULL UNIQUE
                        )''')

            # タスク-タグ関連テーブル
            c.execute('''CREATE TABLE IF NOT EXISTS task_tags (
                            task_id INTEGER,
                            tag_id INTEGER,
                            FOREIGN KEY(task_id) REFERENCES tasks(id),
                            FOREIGN KEY(tag_id) REFERENCES tags(id)
                        )''')

            # 初期カテゴリの追加
            c.execute('''INSERT OR IGNORE INTO categories (name) VALUES 
                            ('仕事'), ('家庭'), ('個人')''')

            conn.commit()
            print("データベースの初期化が完了しました。")

    except sqlite3.Error as e:
        print(f"データベースの初期化中にエラーが発生しました: {e}")
