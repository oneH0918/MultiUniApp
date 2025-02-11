import os
from flask import Flask, render_template, request, redirect, url_for
from database.connection import get_db_connection
from database.init_db import init_db
from database.tasks import (
    handle_task_creation, handle_task_deletion, handle_task_status_update,
    fetch_tasks_data, update_task, get_task_for_edit
    )
from datetime import datetime


app = Flask(__name__)


# ホーム画面
@app.route("/")
def index():
    return render_template("index.html")


# タスク管理アプリ
@app.route("/task_manager", methods=["GET", "POST"])
def task_manager():
    with get_db_connection() as conn:
        c = conn.cursor()

        if request.method == "POST":
            handle_task_creation(c, conn)
            handle_task_deletion(c)
            handle_task_status_update(c)
            conn.commit()

        # タスクデータの取得
        data = fetch_tasks_data(c, conn)

    return render_template("task_manager.html", **data)

# 編集用フォームページ
@app.route("/edit_task/<int:task_id>", methods=["GET", "POST"])
def edit_task(task_id):
    with get_db_connection() as conn:
        c = conn.cursor()

        # 編集対象のタスクを取得
        if request.method == "GET":
            return get_task_for_edit(c, task_id)

        # 編集後のデータを保存
        elif request.method == "POST":
            update_task(c, conn, task_id)
            return redirect(url_for("task_manager"))


if __name__ == "__main__":
    init_db()

    port = int(os.environ.get("PORT", 10000))  # Render用のポートを取得（デフォルト10000）
    app.run(host="0.0.0.0", port=port)