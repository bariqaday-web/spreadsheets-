import os
import sqlite3
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
# تفعيل CORS ضروري للسماح لمتصفحك بالاتصال بسيرفر ريلوي
CORS(app)

# تحديد مسار قاعدة البيانات SQL بشكل احترافي ليعمل داخل ريلوي
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'database.db')

# مفتاح الأمان (يجب أن يطابق الموجود في كود الـ HTML)
API_KEY = "EBQAD_SECURE_2026"

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # هذا يسمح لنا بالتعامل مع النتائج كقاموس (Dictionary)
    return conn

# إنشاء الجدول فور تشغيل السيرفر إذا لم يكن موجوداً
def init_db():
    with get_db_connection() as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS projects 
            (id INTEGER PRIMARY KEY AUTOINCREMENT, 
             title TEXT, 
             description TEXT, 
             image_url TEXT, 
             tech_stack TEXT)''')

init_db()

# دالة التحقق من الصلاحية (Security Check)
def is_authorized():
    return request.headers.get("X-API-KEY") == API_KEY

# --- المسارات (Endpoints) ---

# 1. جلب المشاريع (عرض للجميع)
@app.route('/api/projects', methods=['GET'])
def get_projects():
    with get_db_connection() as conn:
        items = conn.execute('SELECT * FROM projects ORDER BY id DESC').fetchall()
    return jsonify({"items": [dict(ix) for ix in items]})

# 2. إضافة مشروع جديد (يحتاج حماية)
@app.route('/api/projects', methods=['POST'])
def add_project():
    if not is_authorized():
        return jsonify({"error": "Unauthorized"}), 403
    
    data = request.json
    with get_db_connection() as conn:
        conn.execute('INSERT INTO projects (title, description, image_url, tech_stack) VALUES (?, ?, ?, ?)',
                     (data['title'], data['description'], data['image_url'], data['tech_stack']))
    return jsonify({"status": "success"}), 201

# 3. تعديل مشروع موجود (يحتاج حماية)
@app.route('/api/projects/<int:id>', methods=['PUT'])
def update_project(id):
    if not is_authorized():
        return jsonify({"error": "Unauthorized"}), 403
    
    data = request.json
    with get_db_connection() as conn:
        conn.execute('UPDATE projects SET title=?, description=?, image_url=?, tech_stack=? WHERE id=?',
                     (data['title'], data['description'], data['image_url'], data['tech_stack'], id))
    return jsonify({"status": "updated"})

# 4. حذف مشروع (يحتاج حماية)
@app.route('/api/projects/<int:id>', methods=['DELETE'])
def delete_project(id):
    if not is_authorized():
        return jsonify({"error": "Unauthorized"}), 403
    
    with get_db_connection() as conn:
        conn.execute('DELETE FROM projects WHERE id=?', (id,))
    return jsonify({"status": "deleted"})

if __name__ == '__main__':
    # ريلوي يعطي التطبيق منفذ عشوائي، هذا السطر يسحب المنفذ آلياً
    port = int(os.environ.get("PORT", 5000))
    # تشغيل السيرفر على 0.0.0.0 متاح للإنترنت
    app.run(host='0.0.0.0', port=port)
    
