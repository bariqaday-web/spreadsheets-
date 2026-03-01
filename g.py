from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import sqlite3
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app) # للسماح بالاتصال من Netlify

API_PASSWORD = "EBQAD_SECURE_2026"

# إعدادات المسارات
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'ebqad_system.db')
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        conn.execute('CREATE TABLE IF NOT EXISTS projects (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, description TEXT, image_url TEXT, tech_stack TEXT)')
        conn.execute('CREATE TABLE IF NOT EXISTS messages (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, email TEXT, message TEXT, date TIMESTAMP DEFAULT CURRENT_TIMESTAMP)')
        conn.execute('CREATE TABLE IF NOT EXISTS about (id INTEGER PRIMARY KEY AUTOINCREMENT, content TEXT)')
        if not conn.execute('SELECT * FROM about WHERE id=1').fetchone():
            conn.execute('INSERT INTO about (id, content) VALUES (1, "Default Content")')
        conn.commit()

# مسار عرض الصور المرفوعة
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# مسار الرفع الجديد من الاستوديو
@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files: return jsonify({"error": "No file"}), 400
    file = request.files['file']
    if file:
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        return jsonify({"url": f"{request.host_url}uploads/{filename}"}), 200

@app.route('/api/projects', methods=['GET', 'POST'])
def projects():
    conn = get_db()
    if request.method == 'POST':
        if request.headers.get('X-API-KEY') != API_PASSWORD: return jsonify({"error": "401"}), 401
        d = request.json
        conn.execute('INSERT INTO projects (title, description, image_url, tech_stack) VALUES (?,?,?,?)', 
                     (d.get('title'), d.get('description'), d.get('image_url'), d.get('tech_stack')))
        conn.commit()
        return jsonify({"status": "success"}), 201
    res = conn.execute('SELECT * FROM projects ORDER BY id DESC').fetchall()
    return jsonify([dict(r) for r in res])

@app.route('/api/projects/<int:id>', methods=['DELETE'])
def delete_project(id):
    if request.headers.get('X-API-KEY') != API_PASSWORD: return jsonify({"error": "401"}), 401
    conn = get_db()
    conn.execute('DELETE FROM projects WHERE id=?', (id,))
    conn.commit()
    return jsonify({"status": "deleted"})

init_db()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
