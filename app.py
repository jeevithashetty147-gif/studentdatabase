import os
import sqlite3
from pathlib import Path

from flask import Flask, flash, g, redirect, render_template, request, url_for

try:
    import psycopg
    from psycopg.rows import dict_row
except ImportError:  # pragma: no cover - only needed when DATABASE_URL is set
    psycopg = None
    dict_row = None


BASE_DIR = Path(__file__).resolve().parent
LOCAL_DATABASE = BASE_DIR / "students.db"
VERCEL_DATABASE = Path("/tmp") / "students.db"

app = Flask(__name__, static_folder="public", static_url_path="")
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "student-portal-secret-key")
app.config["DATABASE_URL"] = os.getenv("DATABASE_URL", "").strip()
app.config["DATABASE_MODE"] = "postgres" if app.config["DATABASE_URL"] else "sqlite"
app.config["DATABASE"] = (
    LOCAL_DATABASE if app.config["DATABASE_MODE"] == "postgres" or not os.getenv("VERCEL") else VERCEL_DATABASE
)
app.config["USING_EPHEMERAL_STORAGE"] = bool(
    os.getenv("VERCEL") and app.config["DATABASE_MODE"] == "sqlite"
)


def _connect():
    if app.config["DATABASE_MODE"] == "postgres":
        if psycopg is None:
            raise RuntimeError(
                "psycopg is required when DATABASE_URL is set. Install dependencies from requirements.txt."
            )

        return psycopg.connect(app.config["DATABASE_URL"], row_factory=dict_row)

    connection = sqlite3.connect(app.config["DATABASE"])
    connection.row_factory = sqlite3.Row
    return connection


def _param_placeholder():
    return "%s" if app.config["DATABASE_MODE"] == "postgres" else "?"


def _like_operator():
    return "ILIKE" if app.config["DATABASE_MODE"] == "postgres" else "LIKE"


def get_db():
    if "db" not in g:
        g.db = _connect()
    return g.db


def init_db():
    db = _connect()

    if app.config["DATABASE_MODE"] == "postgres":
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS students (
                id BIGSERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                course TEXT NOT NULL,
                phone TEXT NOT NULL
            )
            """
        )
    else:
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                course TEXT NOT NULL,
                phone TEXT NOT NULL
            )
            """
        )

    db.commit()
    db.close()


@app.teardown_appcontext
def close_db(_error):
    db = g.pop("db", None)
    if db is not None:
        db.close()


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        course = request.form.get("course", "").strip()
        phone = request.form.get("phone", "").strip()

        if not all([name, email, course, phone]):
            flash("Please fill in all fields.", "error")
            return redirect(url_for("index"))

        db = get_db()
        placeholder = _param_placeholder()
        db.execute(
            f"INSERT INTO students (name, email, course, phone) VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder})",
            (name, email, course, phone),
        )
        db.commit()
        flash("Student added successfully.", "success")
        return redirect(url_for("index"))

    return render_template("index.html")


@app.route("/students")
def student_list():
    query = request.args.get("q", "").strip()
    db = get_db()
    placeholder = _param_placeholder()
    like_operator = _like_operator()

    if query:
        students = db.execute(
            f"""
            SELECT * FROM students
            WHERE name {like_operator} {placeholder}
               OR email {like_operator} {placeholder}
               OR course {like_operator} {placeholder}
               OR phone {like_operator} {placeholder}
            ORDER BY id DESC
            """,
            tuple(f"%{query}%" for _ in range(4)),
        ).fetchall()
    else:
        students = db.execute(
            "SELECT * FROM students ORDER BY id DESC"
        ).fetchall()

    return render_template("students.html", students=students, query=query)


@app.context_processor
def inject_runtime_state():
    return {"using_ephemeral_storage": app.config["USING_EPHEMERAL_STORAGE"]}


init_db()


if __name__ == "__main__":
    app.run(debug=True)
