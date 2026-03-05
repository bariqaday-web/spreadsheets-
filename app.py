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

class Message(db.Model):
    __tablename__ = 'messages'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class About(db.Model):
    __tablename__ = 'about'
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text)

with app.app_context():
    db.create_all()

@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file"}), 400
    file = request.files['file']
    api_key_imgbb = "6876793f18a24c535787964a06560946" 
    try:
        response = requests.post("https://api.imgbb.com/1/upload", params={"key": api_key_imgbb}, files={"image": file.read()}, timeout=30)
        if response.status_code == 200:
            return jsonify({"url": response.json()['data']['url']})
        return jsonify({"error": "failed"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/projects', methods=['GET', 'POST'])
def handle_projects():
    if request.method == 'POST':
        data = request.json
        new_p = Project(title=data.get('title'), description=data.get('description'), image_url=data.get('image_url'))
        db.session.add(new_p)
        db.session.commit()
        return jsonify({"message": "saved"}), 201
    all_p = Project.query.order_by(Project.created_at.desc()).all()
    return jsonify([{"id":p.id,"title":p.title,"description":p.description,"image_url":p.image_url} for p in all_p])

@app.route('/api/projects/<int:id>', methods=['PUT', 'DELETE'])
def update_delete_project(id):
    project = Project.query.get_or_404(id)
    if request.method == 'PUT':
        data = request.json
        project.title = data.get('title', project.title)
        project.description = data.get('description', project.description)
        project.image_url = data.get('image_url', project.image_url)
        db.session.commit()
        return jsonify({"message": "updated"})
    db.session.delete(project)
    db.session.commit()
    return jsonify({"message": "deleted"})

@app.route('/api/messages', methods=['GET', 'POST'])
def handle_messages():
    if request.method == 'POST':
        data = request.json
        new_m = Message(name=data.get('name'), message=data.get('message'))
        db.session.add(new_m)
        db.session.commit()
        return jsonify({"message": "sent"}), 201
    all_m = Message.query.order_by(Message.created_at.desc()).all()
    return jsonify([{"id":m.id,"name":m.name,"message":m.message} for m in all_m])

@app.route('/api/messages/<int:id>', methods=['DELETE'])
def delete_message(id):
    msg = Message.query.get_or_404(id)
    db.session.delete(msg)
    db.session.commit()
    return jsonify({"message": "deleted"})

@app.route('/api/about', methods=['GET', 'POST'])
def handle_about():
    about_record = About.query.first()
    if request.method == 'POST':
        content = request.json.get('content')
        if about_record: about_record.content = content
        else: db.session.add(About(content=content))
        db.session.commit()
        return jsonify({"message": "updated"})
    return jsonify({"content": about_record.content if about_record else ""})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
    
