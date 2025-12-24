import os
import json
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from werkzeug.utils import secure_filename
import firebase_admin
from firebase_admin import credentials, firestore, storage
from datetime import datetime

# ---------- Firebase setup ----------
# This logic checks for the Render Secret File first, then falls back to local
service_account_path = "serviceAccount.json"

if not firebase_admin._apps:
    if os.path.exists(service_account_path):
        cred = credentials.Certificate(service_account_path)
    else:
        # Fallback for Render Environment Variable if you used the 'Value' field instead of 'Secret File'
        service_account_info = os.environ.get('FIREBASE_SERVICE_ACCOUNT_JSON')
        if service_account_info:
            cred = credentials.Certificate(json.loads(service_account_info))
        else:
            raise ValueError("No Firebase Service Account found!")

    firebase_admin.initialize_app(cred, {
        'storageBucket': 'lost-found-55192.firebasestorage.app'
    })

db = firestore.client()
bucket = storage.bucket()

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev_key_123")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def get_items_by_type(item_type=None, search_query="", category=None, limit=None):
    query = db.collection("items")
    if item_type:
        query = query.where("type", "==", item_type)
    if category:
        query = query.where("category", "==", category)
    
    docs = query.stream()
    items = []
    for d in docs:
        item = d.to_dict()
        item["id"] = d.id
        if search_query:
            text = (item.get("title", "") + " " + item.get("description", "")).lower()
            if search_query.lower() not in text: continue
        items.append(item)
    items.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return items[:limit] if limit else items

# ---------- Routes ----------

@app.route("/")
def home():
    search = request.args.get("q", "").strip()
    category = request.args.get("category", "").strip()
    items = get_items_by_type(search_query=search, category=category if category else None)
    categories = sorted(list(set(item.get("category", "Other") for item in items if item.get("category"))))
    return render_template("home.html", items=items, page_title="All Items", q=search, categories=categories)

@app.route("/report/<item_type>", methods=["GET", "POST"])
def report_item(item_type):
    # FIX: Pass today's date to template to avoid Jinja2 'date' filter error
    today_date = datetime.now().strftime('%Y-%m-%d')

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        image_url = ""
        file = request.files.get("image_file")
        
        if file and file.filename and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            blob = bucket.blob(f"items/{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}")
            blob.upload_from_string(file.read(), content_type=file.content_type)
            blob.make_public()
            image_url = blob.public_url

        data = {
            "title": title,
            "description": request.form.get("description", ""),
            "category": request.form.get("category", "Other"),
            "location": request.form.get("location", ""),
            "date": request.form.get("date", ""),
            "type": item_type,
            "image_url": image_url,
            "created_at": datetime.now().isoformat()
        }
        db.collection("items").add(data)
        flash(f"Reported {item_type} item!", "success")
        return redirect(url_for("home"))

    return render_template("report_item.html", item_type=item_type, today=today_date)

@app.route("/item/<item_id>", methods=["GET", "POST"])
def item_detail(item_id):
    item_ref = db.collection("items").document(item_id)
    snap = item_ref.get()
    if not snap.exists: return redirect(url_for("home"))
    item = snap.to_dict()
    item["id"] = item_id

    if request.method == "POST":
        db.collection("claims").add({
            "item_id": item_id,
            "name": request.form.get("name"),
            "message": request.form.get("message"),
            "created_at": datetime.now().isoformat()
        })
        flash("Claim submitted!", "success")
        return redirect(url_for("item_detail", item_id=item_id))

    claims = [c.to_dict() for c in db.collection("claims").where("item_id", "==", item_id).stream()]
    return render_template("item_detail.html", item=item, claims=claims)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
