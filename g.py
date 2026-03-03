from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

API_KEY = "EBQAD_SECURE_2026"
projects = [] # ملاحظة: عند إعادة تشغيل السيرفر ستختفي البيانات، سأعلمك لاحقاً كيف نربطها بـ SQL لتبقى دائمة.

def check_auth():
    return request.headers.get("X-API-KEY") == API_KEY

# جلب المشاريع (موجود)
@app.route('/api/projects', methods=['GET'])
def get_projects():
    return jsonify({"items": projects, "total_pages": 1}), 200

# إضافة مشروع جديد (كان ناقصاً في الرد السابق)
@app.route('/api/projects', methods=['POST'])
def add_project():
    if not check_auth(): return jsonify({"message": "Forbidden"}), 403
    data = request.json
    new_project = {
        "id": len(projects) + 1,
        "title": data.get('title'),
        "description": data.get('description'),
        "image_url": data.get('image_url'),
        "tech_stack": data.get('tech_stack')
    }
    projects.append(new_project)
    return jsonify(new_project), 201

# تعديل مشروع (موجود)
@app.route('/api/projects/<int:project_id>', methods=['PUT'])
def update_project(project_id):
    if not check_auth(): return jsonify({"message": "Forbidden"}), 403
    data = request.json
    project = next((p for p in projects if p['id'] == project_id), None)
    if project:
        project.update(data)
        return jsonify(project), 200
    return jsonify({"message": "Not Found"}), 404

# حذف مشروع (موجود)
@app.route('/api/projects/<int:project_id>', methods=['DELETE'])
def delete_project(project_id):
    if not check_auth(): return jsonify({"message": "Forbidden"}), 403
    global projects
    projects = [p for p in projects if p['id'] != project_id]
    return jsonify({"success": True}), 200

if __name__ == '__main__':
    app.run(debug=True, port=5000)
    
