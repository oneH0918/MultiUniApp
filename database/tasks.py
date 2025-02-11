import sqlite3
from flask import request, redirect, url_for, render_template
from database.utils import format_date
from database.tags import process_tags


# --- タスクの取得 ---
def get_filtered_tasks(conn, status_filter=None, priority_filter=None, category_filter=None, tag_filter=None, sort_by="due_date", sort_order="ASC"):
    """
    指定されたフィルタ条件でタスクを取得する汎用関数。

    - status_filter: ステータス条件 ('完了済み', '未着手' など)
    - priority_filter: 優先度フィルタ ('低', '中', '高', など)
    - category_filter: カテゴリ名フィルタ
    - tag_filter: タグ名フィルタ
    - sort_by: ソート対象の列名 (既定値: "due_date")
    - sort_order: ソート順 ("ASC" または "DESC")
    """

    # ホワイトリストを使用して安全な値を設定
    valid_sort_by = {"due_date", "priority", "name", "category"}
    valid_sort_order = {"ASC", "DESC"}
    
    # 安全な値を選択
    if sort_by not in valid_sort_by:
        sort_by = "due_date"
    if sort_order not in valid_sort_order:
        sort_order = "ASC"

    # ベースクエリ
    query = "SELECT * FROM tasks WHERE 1=1"
    params = []

    # 各フィルタ条件をクエリに追加
    if status_filter:
        query += " AND status = ?"
        params.append(status_filter)
    if priority_filter and priority_filter != "すべて":
        query += " AND priority = ?"
        params.append(priority_filter)
    if category_filter:
        query += " AND category = ?"
        params.append(category_filter)
    if tag_filter:
        query += '''
            AND id IN (
                SELECT task_id FROM task_tags
                INNER JOIN tags ON task_tags.tag_id = tags.id
                WHERE tags.name = ?
            )
        '''
        params.append(tag_filter)

    # ソートを安全に組み込む
    query += f" ORDER BY {sort_by} {sort_order}"

    try:
        c = conn.cursor()
        c.execute(query, params)
        return c.fetchall()
    except sqlite3.Error as e:
        print(f"タスク取得中にエラーが発生しました: {e}")
        return []


def fetch_tasks_data(c, conn):
    sort_by = request.args.get("sort_by", "due_date")
    sort_order = request.args.get("sort_order", "asc")

    all_tasks = get_filtered_tasks(
        conn,
        status_filter=None,
        priority_filter=request.args.get("incomplete_filter_priority"),
        category_filter=request.args.get("incomplete_filter_category"),
        tag_filter=request.args.get("incomplete_filter_tag"),
        sort_by=sort_by,
        sort_order=sort_order,
    )

    incomplete_tasks = [task for task in all_tasks if task["status"] != "完了済み"]
    completed_tasks = [task for task in all_tasks if task["status"] == "完了済み"]

    c.execute("SELECT name FROM categories")
    categories = [row[0] for row in c.fetchall()]

    c.execute("SELECT id, name FROM tags")
    tags = c.fetchall()

    task_tags_map = {}
    for task in all_tasks:
        task_id = task["id"]
        c.execute(
            '''
            SELECT tags.name FROM tags
            INNER JOIN task_tags ON tags.id = task_tags.tag_id
            WHERE task_tags.task_id = ?
            ''',
            (task_id,)
        )
        task_tags_map[task_id] = [row[0] for row in c.fetchall()]

    return {
        "incomplete_tasks": incomplete_tasks,
        "completed_tasks": completed_tasks,
        "categories": categories,
        "tags": tags,
        "task_tags_map": task_tags_map,
        "sort_by": sort_by,
        "sort_order": sort_order,
        "incomplete_filter_priority": request.args.get("incomplete_filter_priority"),
        "incomplete_filter_category": request.args.get("incomplete_filter_category"),
        "incomplete_filter_tag": request.args.get("incomplete_filter_tag"),
        "complete_filter_priority": request.args.get("complete_filter_priority"),
        "complete_filter_category": request.args.get("complete_filter_category"),
        "complete_filter_tag": request.args.get("complete_filter_tag"),
    }


# --- タスク処理 ---
def handle_task_creation(c, conn):
    task_name = request.form.get("task_name")
    new_category = request.form.get("new_category")

    if new_category:
        c.execute("INSERT OR IGNORE INTO categories (name) VALUES (?)", (new_category,))

    if task_name:
        task_id = add_task(c, conn, task_name, new_category)
        conn.commit()
        process_tags(conn, task_id, request.form.get("tags"))


def handle_task_deletion(c):
    delete_id = request.form.get("delete_id")
    if delete_id:
        delete_task(c, delete_id)


def handle_task_status_update(c):
    complete_id = request.form.get("complete_id")
    incomplete_id = request.form.get("incomplete_id")

    if complete_id:
        update_task_status(c, complete_id, "完了済み")
    if incomplete_id:
        update_task_status(c, incomplete_id, "未着手")


# --- タスクの追加・更新・削除 ---
def add_task(c, conn, task_name, new_category):
    task_details = request.form.get("task_details")
    due_date = format_date(request.form.get("due_date"))
    priority = request.form.get("priority")
    category = request.form.get("category") or new_category
    tags = request.form.get("tags")
    status = "未着手"
    
    c.execute('''INSERT INTO tasks (name, details, due_date, priority, category, tags, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)''',
                (task_name, task_details, due_date, priority, category, tags, status))
    process_tags(conn, c.lastrowid, tags)


def update_task(c, conn, task_id):
    task_name = request.form.get("task_name")
    task_details = request.form.get("task_details")
    due_date = format_date(request.form.get("due_date"))
    priority = request.form.get("priority")
    category = request.form.get("category")
    tags = request.form.get("tags")
    status = request.form.get("status") or request.form.get("custom_status")
    
    c.execute('''UPDATE tasks
                SET name = ?, details = ?, due_date = ?, priority = ?, category = ?, tags = ?, status = ?
                WHERE id = ?''',
                (task_name, task_details, due_date, priority, category, tags, status, task_id))
    c.execute("DELETE FROM task_tags WHERE task_id = ?", (task_id,))
    process_tags(conn, task_id, tags)
    conn.commit()


def delete_task(cursor, task_id):
    cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    cursor.execute("DELETE FROM task_tags WHERE task_id = ?", (task_id,))
    cursor.execute("DELETE FROM tags WHERE id NOT IN (SELECT DISTINCT tag_id FROM task_tags)")


def update_task_status(cursor, task_id, status):
    cursor.execute("UPDATE tasks SET status = ? WHERE id = ?", (status, task_id))


# --- 編集用 ---
def get_task_for_edit(c, task_id):
    if not isinstance(task_id, int):
        return redirect(url_for("task_manager"))
    
    c.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
    task = c.fetchone()
    if not task:
        return redirect(url_for("task_manager"))
    
    c.execute("SELECT name FROM categories")
    categories = [row[0] for row in c.fetchall()]
    return render_template("edit_task.html", task=task, categories=categories)
