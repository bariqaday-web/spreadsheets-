import os
import psycopg2
from psycopg2.extras import RealDictCursor
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

API_PASSWORD = "EBQAD_SECURE_2026"
DATABASE_URL = os.getenv('DATABASE_URL')

def get_db_connection():
    return psycopg2.connect(DATABASE_URL, sslmode='require')

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    # جدول المشاريع
    cur.execute('''
        CREATE TABLE IF NOT EXISTS projects (
            id SERIAL PRIMARY KEY,
            title TEXT,
            description TEXT,
            image_url TEXT,
            tech_stack TEXT DEFAULT 'FullStack'
        );
    ''')
    # جدول الرسائل (أضفنا خانة الهاتف phone)
    cur.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id SERIAL PRIMARY KEY,
            name TEXT,
            email TEXT,
            phone TEXT, 
            message TEXT,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    ''')
    # جدول النبذة
    cur.execute('''
        CREATE TABLE IF NOT EXISTS about (
            id SERIAL PRIMARY KEY,
            content TEXT
        );
    ''')
    conn.commit()
    cur.close()
    conn.close()
    print("✅ Database Synchronized")

@app.route('/api/projects', methods=['GET', 'POST'])
def handle_projects():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    if request.method == 'POST':
        if request.headers.get('X-API-KEY') != API_PASSWORD:
            return jsonify({"error": "Unauthorized"}), 401
        data = request.json
        cur.execute(
            'INSERT INTO projects (title, description, image_url, tech_stack) VALUES (%s, %s, %s, %s)',
            (data.get('title'), data.get('description'), data.get('image_url'), data.get('tech_stack'))
        )
        conn.commit()
        return jsonify({"status": "created"}), 201

    cur.execute('SELECT * FROM projects ORDER BY id DESC')
    res = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(res)

# --- الدالة المفقودة التي تسبب مشكلة التحديث ---
@app.route('/api/projects/<int:id>', methods=['PUT', 'DELETE'])
def project_detail(id):
    if request.headers.get('X-API-KEY') != API_PASSWORD:
        return jsonify({"error": "Unauthorized"}), 401
        
    conn = get_db_connection()
    cur = conn.cursor()

    if request.method == 'PUT':
        data = request.json
        cur.execute(
            'UPDATE projects SET title=%s, description=%s, image_url=%s, tech_stack=%s WHERE id=%s',
            (data.get('title'), data.get('description'), data.get('image_url'), data.get('tech_stack'), id)
        )
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"status": "updated"})

    elif request.method == 'DELETE':
        cur.execute('DELETE FROM projects WHERE id=%s', (id,))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"status": "deleted"})

@app.route('/api/messages', methods=['GET', 'POST', 'DELETE'])
def handle_messages():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    if request.method == 'POST':
        data = request.json
        cur.execute(
            'INSERT INTO messages (name, email, phone, message) VALUES (%s, %s, %s, %s)',
            (data.get('name'), data.get('email'), data.get('phone'), data.get('message'))
        )
        conn.commit()
        return jsonify({"status": "sent"}), 201

    if request.headers.get('X-API-KEY') != API_PASSWORD:
        return jsonify({"error": "Unauthorized"}), 401

    cur.execute('SELECT * FROM messages ORDER BY id DESC')
    res = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(res)

# إضافة مسار حذف الرسالة لتعمل اللوحة بشكل كامل
@app.route('/api/messages/<int:id>', methods=['DELETE'])
def delete_message(id):
    if request.headers.get('X-API-KEY') != API_PASSWORD:
        return jsonify({"error": "Unauthorized"}), 401
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('DELETE FROM messages WHERE id=%s', (id,))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"status": "deleted"})

@app.route('/api/about', methods=['GET', 'POST'])
def handle_about():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    if request.method == 'POST':
        if request.headers.get('X-API-KEY') != API_PASSWORD:
            return jsonify({"error": "Unauthorized"}), 401
        content = request.json.get('content')
        cur.execute('DELETE FROM about') # نمسح القديم
        cur.execute('INSERT INTO about (content) VALUES (%s)', (content,))
        conn.commit()
        return jsonify({"status": "updated"})
    
    cur.execute('SELECT * FROM about LIMIT 1')
    res = cur.fetchone() or {"content": ""}
    cur.close()
    conn.close()
    return jsonify(res)

init_db()

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
        
