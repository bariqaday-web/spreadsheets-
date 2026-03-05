import os
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 

CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://neondb_owner:npg_m8LEJPzVH7jw@ep-sweet-mode-ai35kmho-pooler.c-4.us-east-1.aws.neon.tech/neondb?sslmode=require'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Project(db.Model):
    __tablename__ = 'projects'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    image_url = db.Column(db.Text) 
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

with app.app_context():
    db.create_all()

@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file"}), 400
    file = request.files['file']
    api_key_imgbb = "6876793f18a24c535787964a06560946" 
    try:
        response = requests.post(
            "https://api.imgbb.com/1/upload",
            params={"key": api_key_imgbb},
            files={"image": file.read()},
            timeout=30
        )
        if response.status_code == 200:
            return jsonify({"url": response.json()['data']['url']})
        return jsonify({"error": "Upload failed"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/projects', methods=['POST', 'GET'])
def handle_projects():
    if request.method == 'POST':
        data = request.json
        new_p = Project(title=data.get('title'), description=data.get('description'), image_url=data.get('image_url'))
        db.session.add(new_p)
        db.session.commit()
        return jsonify({"message": "Saved"}), 201
    all_p = Project.query.order_by(Project.created_at.desc()).all()
    return jsonify([{"id":p.id,"title":p.title,"description":p.description,"image_url":p.image_url} for p in all_p])

@app.route('/api/projects/<int:id>', methods=['DELETE'])
def delete_project(id):
    p = Project.query.get_or_404(id)
    db.session.delete(p)
    db.session.commit()
    return jsonify({"message": "Deleted"})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
                                              
