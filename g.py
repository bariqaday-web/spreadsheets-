import os
import psycopg2
from psycopg2.extras import RealDictCursor
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests

app = Flask(__name__)
CORS(app)

API_PASSWORD = "EBQAD_SECURE_2026"
DATABASE_URL = os.getenv("DATABASE_URL")

# -------------------------
# اتصال قاعدة البيانات
# -------------------------
def get_db_connection():
    if not DATABASE_URL:
        raise Exception("DATABASE_URL not found in environment variables")
    return psycopg2.connect(DATABASE_URL, sslmode="require")

# -------------------------
# إنشاء الجداول
# -------------------------
def init_db():
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                id SERIAL PRIMARY KEY,
                title TEXT,
                description TEXT,
                image_url TEXT,
                tech_stack TEXT DEFAULT 'FullStack'
            );
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id SERIAL PRIMARY KEY,
                name TEXT,
                email TEXT,
                phone TEXT,
                message TEXT,
                date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS about (
                id SERIAL PRIMARY KEY,
                content TEXT
            );
        """)

        conn.commit()
        cur.close()
        conn.close()
        print("Database initialized successfully")

    except Exception as e:
        print("Database initialization failed:", e)

# -------------------------
# Route رئيسي للفحص
# -------------------------
@app.route("/")
def home():
    return "Server is running successfully"

# -------------------------
# المشاريع
# -------------------------
@app.route("/api/projects", methods=["GET", "POST"])
def handle_projects():
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        if request.method == "POST":
            if request.headers.get("X-API-KEY") != API_PASSWORD:
                return jsonify({"error": "Unauthorized"}), 401

            data = request.json
            cur.execute(
                "INSERT INTO projects (title, description, image_url, tech_stack) VALUES (%s, %s, %s, %s)",
                (
                    data.get("title"),
                    data.get("description"),
                    data.get("image_url"),
                    data.get("tech_stack", "FullStack"),
                ),
            )
            conn.commit()
            cur.close()
            conn.close()
            return jsonify({"status": "created"}), 201

        cur.execute("SELECT * FROM projects ORDER BY id DESC")
        res = cur.fetchall()
        cur.close()
        conn.close()
        return jsonify(res)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# -------------------------
# تشغيل التطبيق
# -------------------------
init_db()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
