import os
import psycopg2
from psycopg2.extras import RealDictCursor
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app) # للسماح بالاتصال من واجهة موقعك في Netlify

# كلمة السر الخاصة بلوحة تحكم EBQAD
API_PASSWORD = "EBQAD_SECURE_2026"

# جلب رابط قاعدة البيانات من المتغيرات التي وضعناها في Railway
DATABASE_URL = os.getenv('DATABASE_URL')

def get_db_connection():
    # الاتصال بقاعدة PostgreSQL الدائمية
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    return conn

def init_db():
    """تأسيس الجداول تلقائياً في PostgreSQL إذا لم تكن موجودة"""
    conn = get_db_connection()
    cur = conn.cursor()
    # إنشاء جدول المشاريع
    cur.execute('''
        CREATE TABLE IF NOT EXISTS projects (
            id SERIAL PRIMARY KEY,
            title TEXT,
            description TEXT,
            image_url TEXT,
            tech_stack TEXT DEFAULT 'FullStack'
        );
    ''')
    # إنشاء جدول الرسائل
    cur.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id SERIAL PRIMARY KEY,
            name TEXT,
            email TEXT,
            message TEXT,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    ''')
    # إنشاء جدول النبذة (About)
    cur.execute('''
        CREATE TABLE IF NOT EXISTS about (
            id SERIAL PRIMARY KEY,
            content TEXT
        );
    ''')
    
    # التأكد من وجود محتوى افتراضي في About
    cur.execute('SELECT COUNT(*) FROM about')
    if cur.fetchone()[0] == 0:
        cur.execute('INSERT INTO about (content) VALUES (%s)', ("Default Content",))
        
    conn.commit()
    cur.close()
    conn.close()
    print("✅ Database Permanently Initialized")

@app.route('/api/projects', methods=['GET', 'POST'])
def handle_projects():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    if request.method == 'POST':
        # التحقق من كلمة السر المرسلة في الـ Header
        if request.headers.get('X-API-KEY') != API_PASSWORD:
            return jsonify({"error": "Unauthorized"}), 401
            
        data = request.json
        cur.execute(
            'INSERT INTO projects (title, description, image_url, tech_stack) VALUES (%s, %s, %s, %s)',
            (data.get('title'), data.get('description'), data.get('image_url'), data.get('tech_stack'))
        )
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"status": "success"}), 201

    # جلب المشاريع لعرضها
    cur.execute('SELECT * FROM projects ORDER BY id DESC')
    res = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(res)

@app.route('/api/projects/<int:id>', methods=['DELETE'])
def delete_project(id):
    if request.headers.get('X-API-KEY') != API_PASSWORD:
        return jsonify({"error": "Unauthorized"}), 401
        
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('DELETE FROM projects WHERE id=%s', (id,))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"status": "deleted"})

# تأسيس القاعدة عند تشغيل السيرفر
init_db()

if __name__ == '__main__':
    # التشغيل على المنفذ المطلوب من قبل Railway
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
    
