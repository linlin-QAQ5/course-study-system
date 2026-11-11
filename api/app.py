import os

import pymysql
from flask import Flask, jsonify, request
from pymysql.cursors import DictCursor

app = Flask(__name__)
app.json.ensure_ascii = False
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024


def connect_db():
    return pymysql.connect(
        host=os.environ["DB_HOST"],
        port=3306,
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        database=os.environ["DB_NAME"],
        charset="utf8mb4",
        cursorclass=DictCursor,
        autocommit=True,
        connect_timeout=5,
        read_timeout=5,
        write_timeout=5,
    )


@app.errorhandler(pymysql.MySQLError)
def database_error(error):
    app.logger.error("Database operation failed: %s", error)
    return jsonify(error="数据库暂时不可用，请稍后重试"), 503


@app.get("/health")
def health():
    connection = connect_db()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT id FROM study_records LIMIT 0")
        return jsonify(status="ok")
    finally:
        connection.close()


@app.get("/api/records")
def list_records():
    connection = connect_db()
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT id, course, content, completed,
                       DATE_FORMAT(created_at, '%%Y-%%m-%%d %%H:%%i:%%s')
                           AS created_at
                FROM study_records
                ORDER BY id DESC
            """, ())
            rows = cursor.fetchall()
        for row in rows:
            row["completed"] = bool(row["completed"])
        return jsonify(rows)
    finally:
        connection.close()


@app.post("/api/records")
def create_record():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify(error="请求必须包含JSON对象"), 400

    course = data.get("course")
    content = data.get("content")

    if not isinstance(course, str) or not isinstance(content, str):
        return jsonify(error="课程名称和学习内容必须是文字"), 400

    course = course.strip()
    content = content.strip()

    if not 1 <= len(course) <= 100:
        return jsonify(error="课程名称应为1—100个字符"), 400
    if not 1 <= len(content) <= 500:
        return jsonify(error="学习内容应为1—500个字符"), 400

    connection = connect_db()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO study_records (course, content) VALUES (%s, %s)",
                (course, content),
            )
            record_id = cursor.lastrowid
        return jsonify(id=record_id, message="记录已保存"), 201
    finally:
        connection.close()


@app.patch("/api/records/<int:record_id>")
def update_record(record_id):
    data = request.get_json(silent=True)
    if not isinstance(data, dict) or type(data.get("completed")) is not bool:
        return jsonify(error="completed必须为true或false"), 400

    connection = connect_db()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT id FROM study_records WHERE id=%s", (record_id,)
            )
            if cursor.fetchone() is None:
                return jsonify(error="记录不存在"), 404
            cursor.execute(
                "UPDATE study_records SET completed=%s WHERE id=%s",
                (data["completed"], record_id),
            )
        return jsonify(message="状态已更新")
    finally:
        connection.close()


@app.delete("/api/records/<int:record_id>")
def delete_record(record_id):
    connection = connect_db()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "DELETE FROM study_records WHERE id=%s", (record_id,)
            )
            if cursor.rowcount == 0:
                return jsonify(error="记录不存在"), 404
        return jsonify(message="记录已删除")
    finally:
        connection.close()
