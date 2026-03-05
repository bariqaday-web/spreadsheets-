import os
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
CORS(app)

# قاعدة البيانات: PostgreSQL على Railway أو SQLite محلي
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL", "sqlite:///local.db")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# جدول المشاريع
class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    image_url = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# جدول الرسائل
class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=True)
    email = db.Column(db.String(150), nullable=True)
    message = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# جدول النص التعريفي
class About(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=True)

with app.app_context():
    db.create_all()

# --- رفع الصور ---
@app.route("/api/upload", methods=["POST"])
def upload():
    if "file" not in request.files:
        return jsonify({"error": "no file"}), 400
    file = request.files["file"]
    imgbb_key = "6876793f18a24c535787964a06560946"  # مفتاحك
    try:
        r = requests.post(
            "https://api.imgbb.com/1/upload",
            params={"key": imgbb_key},
            files={"image": file}
        )
        if r.status_code == 200:
            return jsonify({"url": r.json()["data"]["url"]})
        return jsonify({"error": "upload failed"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- مشاريع ---
@app.route("/api/projects", methods=["GET", "POST"])
def projects():
    if request.method == "POST":
        data = request.json
        title = data.get("title")
        if not title:
            return jsonify({"error": "title required"}), 400
        p = Project(
            title=title,
            description=data.get("description") or "",
            image_url=data.get("image_url") or ""
        )
        db.session.add(p)
        db.session.commit()
        return jsonify({"message": "created"}), 201
    items = Project.query.order_by(Project.id.desc()).all()
    return jsonify([{"id": p.id, "title": p.title, "description": p.description, "image_url": p.image_url} for p in items])

@app.route("/api/projects/<int:id>", methods=["PUT", "DELETE"])
def project_edit(id):
    p = Project.query.get_or_404(id)
    if request.method == "PUT":
        data = request.json
        p.title = data.get("title") or p.title
        p.description = data.get("description") or p.description
        p.image_url = data.get("image_url") or p.image_url
        db.session.commit()
        return jsonify({"message": "updated"})
    db.session.delete(p)
    db.session.commit()
    return jsonify({"message": "deleted"})

# --- الرسائل ---
@app.route("/api/messages", methods=["GET", "POST"])
def messages():
    if request.method == "POST":
        data = request.json
        m = Message(
            name=data.get("name") or "",
            email=data.get("email") or "",
            message=data.get("message") or ""
        )
        db.session.add(m)
        db.session.commit()
        return jsonify({"message": "sent"})
    msgs = Message.query.order_by(Message.id.desc()).all()
    return jsonify([{"id": m.id, "name": m.name, "email": m.email, "message": m.message} for m in msgs])

@app.route("/api/messages/<int:id>", methods=["DELETE"])
def delete_message(id):
    m = Message.query.get_or_404(id)
    db.session.delete(m)
    db.session.commit()
    return jsonify({"message": "deleted"})

# --- النص التعريفي ---
@app.route("/api/about", methods=["GET", "POST"])
def about():
    a = About.query.first()
    if request.method == "POST":
        content = request.json.get("content")
        if a:
            a.content = content
        else:
            db.session.add(About(content=content))
        db.session.commit()
        return jsonify({"message": "saved"})
    return jsonify({"content": a.content if a else ""})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print("Server running at https://web-production-387d.up.railway.app/")
    app.run(host="0.0.0.0", port=port)
