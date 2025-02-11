import sqlite3

def process_tags(conn, task_id, tags):
    """
    タグを処理し、関連付けを登録する。
    - タグを一括登録。
    - タグIDとタスクIDの関連付けを一括登録。
    """
    if not tags:
        return

    try:
        # タグをカンマ区切りで分割し、空白や空タグを除外
        tag_names = [tag.strip() for tag in tags.split(",") if tag.strip()]

        if not tag_names:
            # 有効なタグがない場合は処理を終了
            return

        c = conn.cursor()

        # タグを一括登録
        c.executemany("INSERT OR IGNORE INTO tags (name) VALUES (?)", [(tag,) for tag in tag_names])

        # タグIDを一括取得
        placeholders = ", ".join(["?"] * len(tag_names))
        c.execute(f"SELECT id, name FROM tags WHERE name IN ({placeholders})", tag_names)
        tag_ids = dict(c.fetchall())

        # タスクとタグの関連付けを取得して、既存の関連付けを確認
        c.execute("SELECT tag_id FROM task_tags WHERE task_id = ?", (task_id,))
        existing_tag_ids = {row[0] for row in c.fetchall()}

        # 新規の関連付けのみ挿入
        task_tags = [(task_id, tag_id) for name in tag_names if (tag_id := tag_ids.get(name)) and tag_id not in existing_tag_ids]
        if task_tags:  # 新規の関連付けがある場合のみクエリ実行
            c.executemany("INSERT INTO task_tags (task_id, tag_id) VALUES (?, ?)", task_tags)

        conn.commit()

    except sqlite3.Error as e:
        print(f"タグの処理中にエラーが発生しました: {e}")
