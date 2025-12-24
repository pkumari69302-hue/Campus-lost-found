import os
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from werkzeug.utils import secure_filename
import firebase_admin
from firebase_admin import credentials, firestore, storage
from datetime import datetime

# ---------- Firebase setup ----------
# Ensure serviceAccount.json is in your project root
cred = credentials.Certificate("serviceAccount.json")
firebase_admin.initialize_app(cred, {
    'storageBucket': 'lost-found-55192.firebasestorage.app'
})

db = firestore.client()
bucket = storage.bucket()

# ---------- Flask app ----------
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "supersecretkey_change_this_later")

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB max file size

# ---------- Helper Functions ----------
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def get_items_by_type(item_type=None, search_query="", category=None, limit=None):
    """Centralized function to fetch items from Firestore with filters"""
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
            searchable_text = (
                item.get("title", "") + " " + 
                item.get("description", "") + " " + 
                item.get("category", "")
            ).lower()
            if search_query.lower() not in searchable_text:
                continue
        
        items.append(item)
    
    items.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    
    if limit:
        items = items[:limit]
    
    return items

# ---------- Routes ----------

@app.route("/")
def home():
    search = request.args.get("q", "").strip()
    category = request.args.get("category", "").strip()
    
    items = get_items_by_type(search_query=search, category=category if category else None)
    categories = sorted(list(set(item.get("category", "Other") for item in items if item.get("category"))))
    
    return render_template(
        "home.html", 
        items=items, 
        page_title="All Items", 
        q=search,
        categories=categories,
        selected_category=category
    )

@app.route("/report/<item_type>", methods=["GET", "POST"])
def report_item(item_type):
    if item_type not in ["lost", "found"]:
        flash("Invalid item type.", "danger")
        return redirect(url_for("home"))

    # Fix for TemplateAssertionError: Get today's date to pass to template
    today_date = datetime.now().strftime('%Y-%m-%d')

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        if not title:
            flash("Title is required!", "danger")
            return render_template("report_item.html", item_type=item_type, today=today_date)

        # Handle Cloud Image Upload
        image_url = ""
        file = request.files.get("image_file")
        
        if file and file.filename and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            blob_path = f"items/{timestamp}_{filename}"
            
            blob = bucket.blob(blob_path)
            file.seek(0)
            blob.upload_from_string(
                file.read(),
                content_type=file.content_type
            )
            
            blob.make_public()
            image_url = blob.public_url

        data = {
            "title": title,
            "description": request.form.get("description", "").strip(),
            "category": request.form.get("category", "Other").strip(),
            "location": request.form.get("location", "").strip(),
            "date": request.form.get("date", ""),
            "type": item_type,
            "image_url": image_url,
            "status": "open",
            "phone": request.form.get("phone", "").strip(),
            "hostel": request.form.get("hostel", "").strip(),
            "color": request.form.get("color", "").strip(),
            "created_at": datetime.now().isoformat()
        }
        
        db.collection("items").add(data)
        flash(f"Successfully reported {item_type} item: {title}", "success")
        return redirect(url_for("home"))

    return render_template("report_item.html", item_type=item_type, today=today_date)

@app.route("/item/<item_id>", methods=["GET", "POST"])
def item_detail(item_id):
    item_ref = db.collection("items").document(item_id)
    snap = item_ref.get()
    
    if not snap.exists:
        flash("Item not found.", "warning")
        return redirect(url_for("home"))

    item = snap.to_dict()
    item["id"] = item_id

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        message = request.form.get("message", "").strip()
        
        if not name:
            flash("Name is required to submit a claim.", "danger")
            return redirect(url_for("item_detail", item_id=item_id))
        
        claim_data = {
            "item_id": item_id,
            "name": name,
            "message": message,
            "created_at": datetime.now().isoformat()
        }
        db.collection("claims").add(claim_data)
        flash("Claim submitted successfully!", "success")
        return redirect(url_for("item_detail", item_id=item_id))

    claim_docs = db.collection("claims").where("item_id", "==", item_id).stream()
    claims = [c.to_dict() for c in claim_docs]
    
    return render_template("item_detail.html", item=item, claims=claims)

@app.route("/lost")
def lost_items():
    search = request.args.get("q", "").strip()
    category = request.args.get("category", "").strip()
    items = get_items_by_type("lost", search, category if category else None)
    categories = sorted(list(set(item.get("category", "Other") for item in items if item.get("category"))))
    return render_template("home.html", items=items, page_title="Lost Items", q=search, categories=categories, selected_category=category, filter_type="lost")

@app.route("/found")
def found_items():
    search = request.args.get("q", "").strip()
    category = request.args.get("category", "").strip()
    items = get_items_by_type("found", search, category if category else None)
    categories = sorted(list(set(item.get("category", "Other") for item in items if item.get("category"))))
    return render_template("home.html", items=items, page_title="Found Items", q=search, categories=categories, selected_category=category, filter_type="found")

@app.route("/fun")
def fun_page():
    return render_template("fun.html")

@app.route("/api/stats")
def api_stats():
    all_items = get_items_by_type()
    return jsonify({"total": len(all_items), "lost": len([i for i in all_items if i.get("type") == "lost"]), "found": len([i for i in all_items if i.get("type") == "found"])})

@app.errorhandler(404)
def not_found(e):
    return render_template("error.html", error_code=404, error_message="Page not found"), 404

@app.errorhandler(500)
def server_error(e):
    return render_template("error.html", error_code=500, error_message="Internal server error"), 500

if __name__ == "__main__":
    app.run(debug=True)