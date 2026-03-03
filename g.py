import os
import sqlite3
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# تحديد مسار قاعدة البيانات ليعمل على سيرفر ريلوي بشكل دائم
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'database.db')

API_KEY = "EBQAD_SECURE_2026"

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            image_url TEXT,
            tech_stack TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

@app.route('/api/projects', methods=['GET'])
def get_projects():
    conn = get_db_connection()
    projects = conn.execute('SELECT * FROM projects ORDER BY id DESC').fetchall()
    conn.close()
    return jsonify({"items": [dict(p) for p in projects]})

@app.route('/api/projects', methods=['POST'])
def add_project():
    if request.headers.get("X-API-KEY") != API_KEY: return jsonify({"error": "Unauthorized"}), 403
    data = request.json
    conn = get_db_connection()
    conn.execute('INSERT INTO projects (title, description, image_url, tech_stack) VALUES (?, ?, ?, ?)',
                 (data['title'], data['description'], data['image_url'], data['tech_stack']))
    conn.commit()
    conn.close()
    return jsonify({"status": "success"}), 201

@app.route('/api/projects/<int:id>', methods=['DELETE'])
def delete_project(id):
    if request.headers.get("X-API-KEY") != API_KEY: return jsonify({"error": "Unauthorized"}), 403
    conn = get_db_connection()
    conn.execute('DELETE FROM projects WHERE id=?', (id,))
    conn.commit()
    conn.close()
    return jsonify({"status": "deleted"})

if __name__ == '__main__':
    # ريلوي يعطي التطبيق منفذ (Port) عشوائي، هذا السطر يجعله يعمل هناك
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
    
