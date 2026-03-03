import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import requests # سنحتاجها لإرسال الصور لسيرفر خارجي

app = Flask(__name__)
CORS(app)

# =========================================================
# 🔗 إعدادات الاتصال وقاعدة البيانات
# =========================================================
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://neondb_owner:npg_m8LEJPzVH7jw@ep-sweet-mode-ai35kmho-pooler.c-4.us-east-1.aws.neon.tech/neondb?sslmode=require'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
API_KEY = "EBQAD_SECURE_2026"

# =========================================================
# 📊 الجداول (Models)
# =========================================================

class Project(db.Model):
    __tablename__ = 'projects'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    image_url = db.Column(db.Text)
    tech_stack = db.Column(db.String(100), default="Data Engineering Stack")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Message(db.Model):
    __tablename__ = 'messages'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150))
    phone = db.Column(db.String(50))
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class AboutMe(db.Model):
    __tablename__ = 'about_me'
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# إنشاء الجداول تلقائياً
with app.app_context():
    db.create_all()

# =========================================================
# 🛠️ العمليات البرمجية (APIs)
# =========================================================

def verify_token():
    return request.headers.get('X-API-KEY') == API_KEY

# --- خدمة رفع الصور (Image Upload) ---
# سنستخدم سيرفر ImgBB المجاني لرفع صورك لكي لا تملأ مساحة قاعدة البيانات
@app.route('/api/upload', methods=['POST'])
def upload_file():
    if not verify_token(): return jsonify({"error": "Unauthorized"}), 401
    if 'file' not in request.files: return jsonify({"error": "No file"}), 400
    
    file = request.files['file']
    # استخدم API KEY مجاني من موقع ImgBB (هذا واحد تجريبي)
    api_key_imgbb = "6876793f18a24c535787964a06560946" 
    
    response = requests.post(
        "https://api.imgbb.com/1/upload",
        params={"key": api_key_imgbb},
        files={"image": file.read()}
    )
    
    if response.status_code == 200:
        return jsonify({"url": response.json()['data']['url']})
    return jsonify({"error": "Upload failed"}), 500

# --- مسارات المشاريع ---
@app.route('/api/projects', methods=['GET'])
def get_projects():
    all_p = Project.query.order_by(Project.created_at.desc()).all()
    return jsonify([{"id":p.id,"title":p.title,"description":p.description,"image_url":p.image_url} for p in all_p])

@app.route('/api/projects', methods=['POST'])
def create_project():
    if not verify_token(): return jsonify({"error": "Unauthorized"}), 401
    data = request.json
    new_p = Project(title=data['title'], description=data['description'], image_url=data['image_url'])
    db.session.add(new_p)
    db.session.commit()
    return jsonify({"message": "Success"}), 201

@app.route('/api/projects/<int:id>', methods=['PUT'])
def update_project(id):
    if not verify_token(): return jsonify({"error": "Unauthorized"}), 401
    p = Project.query.get_or_404(id)
    data = request.json
    p.title = data.get('title', p.title)
    p.description = data.get('description', p.description)
    p.image_url = data.get('image_url', p.image_url)
    db.session.commit()
    return jsonify({"message": "Updated"})

@app.route('/api/projects/<int:id>', methods=['DELETE'])
def delete_project(id):
    if not verify_token(): return jsonify({"error": "Unauthorized"}), 401
    p = Project.query.get_or_404(id)
    db.session.delete(p)
    db.session.commit()
    return jsonify({"message": "Deleted"})

# --- مسارات الرسائل ---
@app.route('/api/messages', methods=['GET'])
def fetch_messages():
    if not verify_token(): return jsonify({"error": "Unauthorized"}), 401
    msgs = Message.query.order_by(Message.created_at.desc()).all()
    return jsonify([{"id":m.id,"name":m.name,"message":m.message,"date":m.created_at} for m in msgs])

@app.route('/api/messages/<int:id>', methods=['DELETE'])
def drop_message(id):
    if not verify_token(): return jsonify({"error": "Unauthorized"}), 401
    m = Message.query.get_or_404(id)
    db.session.delete(m)
    db.session.commit()
    return jsonify({"message": "Deleted"})

# --- مسار النبذة ---
@app.route('/api/about', methods=['GET', 'POST'])
def manage_about():
    about = AboutMe.query.first()
    if request.method == 'POST':
        if not verify_token(): return jsonify({"error": "Unauthorized"}), 401
        content = request.json.get('content')
        if about: about.content = content
        else: db.session.add(AboutMe(content=content))
        db.session.commit()
        return jsonify({"message": "Updated"})
    return jsonify({"content": about.content if about else ""})

# =========================================================
# 🚀 تشغيل السيرفر المتوافق مع Railway
# =========================================================
if __name__ == '__main__':
    # الكود مدمج الآن ليعمل محلياً وفي السيرفر السحابي
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
