from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app) # للسماح للفرونت-أند بالاتصال بالباك-أند

# مفتاح الأمان (يجب أن يتطابق مع API_KEY في كود الـ HTML الخاص بك)
API_KEY = "EBQAD_SECURE_2026"

# محاكاة لقاعدة بيانات (في الواقع ستستخدم SQL كما في خطتك)
projects = [
    {"id": 1, "title": "مشروع SQL", "description": "تحليل بيانات", "image_url": "", "tech_stack": "SQL, Python"}
]

# دالة للتحقق من الصلاحية (Middleware بسيطة)
def check_auth():
    return request.headers.get("X-API-KEY") == API_KEY

# 1. مسار حذف المشروع (Delete)
@app.route('/api/projects/<int:project_id>', methods=['DELETE'])
def delete_project(project_id):
    if not check_auth():
        return jsonify({"message": "غير مصرح لك"}), 403
    
    global projects
    projects = [p for p in projects if p['id'] != project_id]
    return jsonify({"message": "تم الحذف بنجاح"}), 200

# 2. مسار تعديل المشروع (Update - PUT)
# هذا المسار يعدل (العنوان، الوصف، الصورة، والتقنيات) دفعة واحدة أو جزء منها
@app.route('/api/projects/<int:project_id>', methods=['PUT'])
def update_project(project_id):
    if not check_auth():
        return jsonify({"message": "غير مصرح لك"}), 403

    data = request.json
    project = next((p for p in projects if p['id'] == project_id), None)
    
    if project:
        # تحديث الحقول بناءً على ما وصل من الـ Form
        project['title'] = data.get('title', project['title'])
        project['description'] = data.get('description', project['description'])
        project['image_url'] = data.get('image_url', project['image_url'])
        project['tech_stack'] = data.get('tech_stack', project['tech_stack'])
        
        return jsonify(project), 200
    
    return jsonify({"message": "المشروع غير موجود"}), 404

# 3. مسار جلب المشاريع (للعرض في اللوحة)
@app.route('/api/projects', methods=['GET'])
def get_projects():
    return jsonify({"items": projects, "total_pages": 1}), 200

if __name__ == '__main__':
    app.run(debug=True)
    
