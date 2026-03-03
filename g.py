import os
import psycopg2
from psycopg2.extras import RealDictCursor
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
# تفعيل CORS للسماح للوحة التحكم بالاتصال بالسيرفر
CORS(app)

API_PASSWORD = "EBQAD_SECURE_2026"
DATABASE_URL = os.getenv("DATABASE_URL")

# -------------------------
# اتصال قاعدة البيانات
# -------------------------
def get_db_connection():
    if not DATABASE_URL:
        raise Exception("خطأ: DATABASE_URL غير موجود في متغيرات البيئة")
    return psycopg2.connect(DATABASE_URL, sslmode="require")

# -------------------------
# إنشاء الجداول (تجهيز البيئة)
# -------------------------
def init_db():
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # جدول المشاريع
        cur.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                id SERIAL PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT,
                image_url TEXT,
                tech_stack TEXT DEFAULT 'FullStack'
            );
        """)

        # جدول الرسائل
        cur.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id SERIAL PRIMARY KEY,
                name TEXT,
                email TEXT,
                message TEXT,
                date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # جدول النبذة الشخصية
        cur.execute("""
            CREATE TABLE IF NOT EXISTS about (
                id SERIAL PRIMARY KEY,
                content TEXT
            );
        """)

        conn.commit()
        cur.close()
        conn.close()
        print("✅ تم فحص وإنشاء الجداول بنجاح")
    except Exception as e:
        print("❌ فشل في تهيئة قاعدة البيانات:", e)

# -------------------------
# المسارات (Routes)
# -------------------------

@app.route("/")
def home():
    return "EBQAD Server is Running Successfully 🚀"

# 1. إدارة المشاريع (عرض وإضافة)
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
                "INSERT INTO projects (title, description, image_url, tech_stack) VALUES (%s, %s, %s, %s) RETURNING id",
                (data.get("title"), data.get("description"), data.get("image_url"), data.get("tech_stack", "FullStack"))
            )
            new_id = cur.fetchone()['id']
            conn.commit()
            return jsonify({"status": "created", "id": new_id}), 201

        # في حالة GET: عرض كل المشاريع
        cur.execute("SELECT * FROM projects ORDER BY id DESC")
        res = cur.fetchall()
        return jsonify(res)

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if 'cur' in locals(): cur.close()
        if 'conn' in locals(): conn.close()

# 2. إدارة مشروع محدد (تعديل وحذف) - تم دمج الكود الذي أرسلته هنا
@app.route('/api/projects/<int:id>', methods=['PUT', 'DELETE'])
def project_detail(id):
    if request.headers.get('X-API-KEY') != API_PASSWORD:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        # التعديل (PUT)
        if request.method == 'PUT':
            data = request.json
            query = '''
                UPDATE projects 
                SET title=%s, description=%s, image_url=%s, tech_stack=%s 
                WHERE id=%s
                RETURNING *
            '''
            cur.execute(query, (
                data.get('title'),
                data.get('description'),
                data.get('image_url'),
                data.get('tech_stack', 'FullStack'),
                id
            ))
            updated_row = cur.fetchone()
            conn.commit()
            
            if not updated_row:
                return jsonify({"error": f"المشروع رقم {id} غير موجود"}), 404
            return jsonify(updated_row), 200

        # الحذف (DELETE)
        if request.method == 'DELETE':
            cur.execute("DELETE FROM projects WHERE id=%s RETURNING id", (id,))
            deleted_id = cur.fetchone()
            conn.commit()
            
            if not deleted_id:
                return jsonify({"error": "المشروع غير موجود أصلاً"}), 404
            return jsonify({"status": "deleted", "id": id}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if 'cur' in locals(): cur.close()
        if 'conn' in locals(): conn.close()

# 3. إدارة النبذة الشخصية (About)
@app.route("/api/about", methods=["GET", "POST"])
def handle_about():
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        if request.method == "POST":
            if request.headers.get("X-API-KEY") != API_PASSWORD:
                return jsonify({"error": "Unauthorized"}), 401
            
            data = request.json
            cur.execute("DELETE FROM about") # مسح القديم
            cur.execute("INSERT INTO about (content) VALUES (%s)", (data.get("content"),))
            conn.commit()
            return jsonify({"status": "updated"}), 200

        cur.execute("SELECT content FROM about LIMIT 1")
        res = cur.fetchone() or {"content": ""}
        return jsonify(res)
    finally:
        if 'cur' in locals(): cur.close()
        if 'conn' in locals(): conn.close()

# 4. الرسائل (عرض وحذف)
@app.route("/api/messages", methods=["GET", "DELETE"])
def handle_messages():
    if request.headers.get("X-API-KEY") != API_PASSWORD:
        return jsonify({"error": "Unauthorized"}), 401
    
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # عرض الرسائل
        if request.method == "GET":
            cur.execute("SELECT * FROM messages ORDER BY date DESC")
            return jsonify(cur.fetchall())

    finally:
        if 'cur' in locals(): cur.close()
        if 'conn' in locals(): conn.close()

# -------------------------
# تشغيل التطبيق
# -------------------------
init_db()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
    
