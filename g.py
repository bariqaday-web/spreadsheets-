import os
import psycopg2
from psycopg2.extras import RealDictCursor
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
# إعدادات CORS متقدمة لضمان عدم حظر المتصفح لعمليات الرفع (POST/PUT/OPTIONS)
CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)

API_PASSWORD = "EBQAD_SECURE_2026"
DATABASE_URL = os.getenv("DATABASE_URL")

def get_db_connection():
    if not DATABASE_URL:
        raise Exception("DATABASE_URL is missing! Please check Railway environment variables.")
    return psycopg2.connect(DATABASE_URL, sslmode="require")

def init_db():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        # إنشاء الجداول مع دعم حقل الرد (reply)
        cur.execute("CREATE TABLE IF NOT EXISTS projects (id SERIAL PRIMARY KEY, title TEXT NOT NULL, description TEXT, image_url TEXT, tech_stack TEXT DEFAULT 'Data Eng');")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id SERIAL PRIMARY KEY, 
                name TEXT, 
                email TEXT, 
                message TEXT, 
                reply TEXT, 
                date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        cur.execute("CREATE TABLE IF NOT EXISTS about (id SERIAL PRIMARY KEY, content TEXT);")
        conn.commit()
        cur.close()
        conn.close()
        print("Database initialized successfully.")
    except Exception as e:
        print("DB Init Error:", e)

@app.route("/")
def home():
    return "EBQAD Server Active 🚀"

# --- إدارة المشاريع (نشر + عرض بنظام Pagination) ---
@app.route("/api/projects", methods=["GET", "POST", "OPTIONS"])
def handle_projects():
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    if request.method == "POST":
        if request.headers.get("X-API-KEY") != API_PASSWORD:
            return jsonify({"error": "Unauthorized"}), 401
        
        data = request.json
        try:
            cur.execute("INSERT INTO projects (title, description, image_url) VALUES (%s, %s, %s) RETURNING id",
                        (data.get("title"), data.get("description"), data.get("image_url")))
            new_id = cur.fetchone()['id']
            conn.commit()
            return jsonify({"status": "created", "id": new_id}), 201
        except Exception as e:
            conn.rollback()
            return jsonify({"error": str(e)}), 500
        finally:
            cur.close()
            conn.close()

    # نظام الـ Pagination لجلب 10 مشاريع فقط
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 10
        offset = (page - 1) * per_page

        cur.execute("SELECT * FROM projects ORDER BY id DESC LIMIT %s OFFSET %s", (per_page, offset))
        projects = cur.fetchall()
        
        cur.execute("SELECT COUNT(*) FROM projects")
        total_count = cur.fetchone()['count']
        total_pages = (total_count + per_page - 1) // per_page

        return jsonify({
            "items": projects,
            "total_pages": total_pages,
            "current_page": page
        })
    finally:
        cur.close()
        conn.close()

# --- تفاصيل المشروع (تحديث + حذف) ---
@app.route('/api/projects/<int:id>', methods=['PUT', 'DELETE', 'OPTIONS'])
def project_detail(id):
    if request.method == 'OPTIONS':
        return jsonify({"status": "ok"}), 200

    if request.headers.get('X-API-KEY') != API_PASSWORD:
        return jsonify({"error": "Unauthorized"}), 401

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    try:
        if request.method == 'PUT':
            data = request.json
            cur.execute("""
                UPDATE projects 
                SET title=%s, description=%s, image_url=%s 
                WHERE id=%s RETURNING *
            """, (data.get('title'), data.get('description'), data.get('image_url'), id))
            updated = cur.fetchone()
            conn.commit()
            return jsonify(updated) if updated else (jsonify({"error": "Not Found"}), 404)
            
        if request.method == 'DELETE':
            cur.execute("DELETE FROM projects WHERE id=%s RETURNING id", (id,))
            deleted = cur.fetchone()
            conn.commit()
            return jsonify({"status": "deleted"}) if deleted else (jsonify({"error": "Not Found"}), 404)
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cur.close()
        conn.close()

# --- إدارة الرسائل والردود ---
@app.route("/api/messages", methods=["GET"])
def get_messages():
    if request.headers.get("X-API-KEY") != API_PASSWORD:
        return jsonify({"error": "Unauthorized"}), 401
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM messages ORDER BY date DESC")
    res = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(res)

@app.route("/api/messages/<int:id>", methods=["DELETE"])
def delete_message_route(id):
    if request.headers.get("X-API-KEY") != API_PASSWORD:
        return jsonify({"error": "Unauthorized"}), 401
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM messages WHERE id=%s", (id,))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"status": "deleted"})

@app.route("/api/messages/<int:id>/reply", methods=["POST"])
def reply_message(id):
    if request.headers.get("X-API-KEY") != API_PASSWORD:
        return jsonify({"error": "Unauthorized"}), 401
    data = request.json
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE messages SET reply = %s WHERE id = %s", (data.get("reply"), id))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"status": "reply_saved"})

# --- إدارة النبذة (About) ---
@app.route("/api/about", methods=["GET", "POST"])
def handle_about():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    if request.method == "POST":
        if request.headers.get("X-API-KEY") != API_PASSWORD:
            return jsonify({"error": "Unauthorized"}), 401
        cur.execute("DELETE FROM about")
        cur.execute("INSERT INTO about (content) VALUES (%s)", (request.json.get("content"),))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"status": "updated"})
    
    cur.execute("SELECT content FROM about LIMIT 1")
    res = cur.fetchone() or {"content": ""}
    cur.close()
    conn.close()
    return jsonify(res)

init_db()
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
    
