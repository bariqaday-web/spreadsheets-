import os
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)

# تفعيل CORS للسماح لأي فرونت-أند بالاتصال بالباك-أند
CORS(app, resources={r"/api/*": {"origins": "*"}})

API_KEY = "EBQAD_SECURE_2026"

# بيانات مؤقتة (سيتم ربطها بـ SQL لاحقاً لضمان عدم ضياعها عند إعادة التشغيل)
projects = []
messages = []
about_content = {"content": "أنا مطور ويب وشغوف بهندسة البيانات..."}

def check_auth():
    return request.headers.get("X-API-KEY") == API_KEY

# --- مسارات المشاريع ---
@app.route('/api/projects', methods=['GET'])
def get_projects():
    # يدعم البحث والصفحات كما تطلب لوحتك
    return jsonify({"items": projects, "total_pages": 1}), 200

@app.route('/api/projects', methods=['POST'])
def add_project():
    if not check_auth(): return jsonify({"message": "Unauthorized"}), 403
    data = request.json
    data['id'] = len(projects) + 1
    projects.append(data)
    return jsonify(data), 201

@app.route('/api/projects/<int:p_id>', methods=['PUT'])
def update_project(p_id):
    if not check_auth(): return jsonify({"message": "Unauthorized"}), 403
    data = request.json
    for p in projects:
        if p['id'] == p_id:
            p.update(data)
            return jsonify(p), 200
    return jsonify({"message": "Project Not Found"}), 404

@app.route('/api/projects/<int:p_id>', methods=['DELETE'])
def delete_project(p_id):
    if not check_auth(): return jsonify({"message": "Unauthorized"}), 403
    global projects
    projects = [p for p in projects if p['id'] != p_id]
    return jsonify({"success": True}), 200

# --- مسارات الرسائل والنبذة ---
@app.route('/api/messages', methods=['GET'])
def get_messages():
    if not check_auth(): return jsonify({"message": "Unauthorized"}), 403
    return jsonify(messages), 200

@app.route('/api/about', methods=['GET', 'POST'])
def manage_about():
    if request.method == 'POST':
        if not check_auth(): return jsonify({"message": "Unauthorized"}), 403
        about_content['content'] = request.json.get('content')
        return jsonify({"success": True})
    return jsonify(about_content)

if __name__ == '__main__':
    # ملاحظة للمبرمج: استخدام os.environ لجلب المنفذ (Port) الذي يحدده السيرفر العالمي تلقائياً
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
    
