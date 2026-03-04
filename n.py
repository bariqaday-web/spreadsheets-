Import os
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # يسمح برفع حتى 16 ميجابايت

CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)


# إعدادات قاعدة بيانات Neon (تخزين الروابط)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://neondb_owner:npg_m8LEJPzVH7jw@ep-sweet-mode-ai35kmho-pooler.c-4.us-east-1.aws.neon.tech/neondb?sslmode=require'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- الجداول ---
class Project(db.Model):
    __tablename__ = 'projects'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    image_url = db.Column(db.Text) # هنا سيخزن رابط "نوني" الأبدي
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

with app.app_context():
    db.create_all()

# --- خدمة الرفع الدائم (Permanent Storage) ---
@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file"}), 400
    
    file = request.files['file']
    
    # إعدادات الرفع (باستخدام ImgBB كخادم تخزين أبدي بـ API Key دائم)
    # ملاحظة: ImgBB يوفر تخزين أبدي للصور المرفوعة عبر الـ API الخاص به
    api_key_imgbb = "6876793f18a24c535787964a06560946" 
    
    try:
        # إرسال الصورة للتخزين السحابي
        response = requests.post(
            "https://api.imgbb.com/1/upload",
            params={"key": api_key_imgbb},
            files={"image": file.read()}
        )
        
        if response.status_code == 200:
            # استخراج الرابط المباشر (Direct Link) الذي لا يموت
            permanent_url = response.json()['data']['url']
            return jsonify({"url": permanent_url})
        else:
            return jsonify({"error": "فشل التخزين في نوني"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- حفظ المشروع في قاعدة البيانات ---
@app.route('/api/projects', methods=['POST'])
def create_project():
    data = request.json
    new_p = Project(
        title=data.get('title'),
        description=data.get('description'),
        image_url=data.get('image_url')
    )
    db.session.add(new_p)
    db.session.commit()
    return jsonify({"message": "تم الحفظ بنجاح في Neon"}), 201

# --- جلب المشاريع لعرضها في البروتفوليو ---
@app.route('/api/projects', methods=['GET'])
def get_projects():
    all_p = Project.query.order_by(Project.created_at.desc()).all()
    return jsonify([{"id":p.id,"title":p.title,"description":p.description,"image_url":p.image_url} for p in all_p])

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
    


