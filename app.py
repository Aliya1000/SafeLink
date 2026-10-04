from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from config import Config
from pymongo import MongoClient
from bson import ObjectId # Add this to your imports at the top
from datetime import datetime
import secrets
import qrcode
import os


# =========================================================
# 1. CREATE FLASK APPLICATION
# =========================================================

app = Flask(__name__)
app.config.from_object(Config)
# Create folder for QR codes if it doesn't exist
QR_FOLDER = os.path.join('static', 'qrcodes')
if not os.path.exists(QR_FOLDER):
    os.makedirs(QR_FOLDER)


# =========================================================
# 2. CONNECT TO MONGODB
# =========================================================

client = MongoClient(
    app.config["MONGO_URI"],
    serverSelectionTimeoutMS=2000
)

try:
    client.admin.command("ping")
    print("✅ Successfully connected to MongoDB!")
except Exception as e:
    print("❌ MongoDB connection failed:", e)

db = client["safelink_db"]


# =========================================================
# 3. DATABASE HELPER
# =========================================================

def get_db():
    return db
# =========================================================
# SECURITY DECORATOR
# =========================================================
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Please login to access this page.", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

# Security Configuration for Cookies
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,   # Prevents JS from reading the cookie (Stops XSS)
    SESSION_COOKIE_SAMESITE='Lax',  # Prevents Cross-Site Request Forgery (CSRF)
)


# =========================================================
# 4. HOME PAGE
# =========================================================

@app.route("/")
def index():
    return render_template("index.html")


# =========================================================
# 5. REGISTER
# =========================================================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        phone = request.form.get("phone", "").strip()
        password = request.form.get("password", "")

        # Check empty fields
        if not name or not email or not phone or not password:
            flash("Please fill in all fields.", "danger")
            return redirect(url_for("register"))
        # --- ADD THIS CODE HERE ---
        if len(password) < 6:
            flash("Password must be at least 6 characters long.", "danger")
            return redirect(url_for("register"))
        # --------------------------
        db = get_db()

        # Check if email already exists
        if db.users.find_one({"email": email}):
            flash("Email already registered!", "danger")
            return redirect(url_for("register"))

        # Hash password
        hashed_password = generate_password_hash(password)

        # Save user
        db.users.insert_one({
            "name": name,
            "email": email,
            "phone": phone,
            "password": hashed_password
        })

        flash("Registration successful! Please login.", "success")

        return redirect(url_for("login"))

    return render_template("register.html")


# =========================================================
# 6. LOGIN
# =========================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        db = get_db()

        user = db.users.find_one({"email": email})

        if user and check_password_hash(user["password"], password):

            session["user_id"] = str(user["_id"])
            session["user_name"] = user["name"]

            return redirect(url_for("dashboard"))

        flash("Invalid email or password", "danger")

    return render_template("login.html")

# =========================================================
# 10. QR CODE GENERATION
# =========================================================
@app.route("/qr/generate")
@login_required
def generate_qr():
    db = get_db()
    user_id = session['user_id']

    profile = db.profiles.find_one({"user_id": user_id})
    if not profile:
        flash("Please complete your profile first!", "warning")
        return redirect(url_for("profile"))

    # --- NEW CLEANUP LOGIC ---
    # Check if the user already has a QR record and delete the physical file
    old_qr = db.qr_codes.find_one({"user_id": user_id, "active": True})
    if old_qr:
        old_file_path = os.path.join(QR_FOLDER, old_qr['qr_image'])
        if os.path.exists(old_file_path):
            os.remove(old_file_path) # Deletes the old file to save space
    # -------------------------

    secure_token = secrets.token_urlsafe(32)
    emergency_url = f"{request.host_url}emergency/{secure_token}"
    
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(emergency_url)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    file_name = f"qr_{user_id}_{secrets.token_hex(4)}.png" # Added a small random hex to prevent browser caching
    file_path = os.path.join(QR_FOLDER, file_name)
    img.save(file_path)

    db.qr_codes.update_many({"user_id": user_id}, {"$set": {"active": False}})
    
    db.qr_codes.insert_one({
        "user_id": user_id,
        "secure_token": secure_token,
        "qr_image": file_name,
        "active": True,
        "created_at": datetime.utcnow()
    })

    flash("Your Emergency QR Code has been updated!", "success")
    return redirect(url_for("dashboard"))
# =========================================================
# 7. LOGOUT
# =========================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("index"))


# =========================================================
# 8. DASHBOARD
# =========================================================

@app.route("/dashboard")
@login_required
def dashboard():
    db = get_db()
    # Fetch user data
    user_data = db.users.find_one({"_id": ObjectId(session['user_id'])})
    
    # Fetch profile data (it might be empty for now)
    profile = db.profiles.find_one({"user_id": session['user_id']})
    
    # Check if QR code exists
    qr_code = db.qr_codes.find_one({"user_id": session['user_id'], "active": True})

    return render_template("dashboard.html", 
                           user=user_data, 
                           profile=profile, 
                           qr_code=qr_code)

#==========================================================
# 9. PROFILE TEMPLATE
# =========================================================


@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    db = get_db()
    user_id = session['user_id']

    if request.method == "POST":
        # 1. Collect Data from Form
        profile_data = {
            "user_id": user_id,
            "full_name": request.form.get("full_name"),
            "blood_group": request.form.get("blood_group"),
            "dob": request.form.get("dob"),
            "emergency_contact_name": request.form.get("contact_name"),
            "emergency_contact_phone": request.form.get("contact_phone"),
            # UPDATE THESE TWO LINES:
            "alt_contact_name": request.form.get("alt_name"),
            "alt_contact_phone": request.form.get("alt_phone"),
            
            "address": request.form.get("address"),
            "allergies": request.form.get("allergies"),
            "medical_conditions": request.form.get("conditions"),
            "medications": request.form.get("medications"),
            "notes": request.form.get("notes"),
            # Privacy Settings (Checkboxes)
            "show_address": True if request.form.get("show_address") else False,
            "show_meds": True if request.form.get("show_meds") else False,
            "updated_at": datetime.utcnow()
        }

        # 2. Update if exists, else Insert (Upsert)
        db.profiles.update_one(
            {"user_id": user_id},
            {"$set": profile_data},
            upsert=True
        )

        flash("Profile updated successfully!", "success")
        return redirect(url_for("dashboard"))

    # GET request: Fetch existing data to pre-fill the form
    existing_profile = db.profiles.find_one({"user_id": user_id})
    return render_template("profile.html", profile=existing_profile)

# =========================================================
# 11. PUBLIC EMERGENCY PROFILE VIEW
# =========================================================

@app.route("/emergency/<token>")
def public_emergency_profile(token):
    db = get_db()
    
    # 1. Find the QR record by the secure token
    qr_record = db.qr_codes.find_one({"secure_token": token, "active": True})
    
    # 2. If token is invalid or revoked, show the error page
    if not qr_record:
        return render_template("emergency_view.html", error="This QR code is invalid or has been revoked.")

    # 3. Find the associated profile
    user_id = qr_record['user_id']
    profile = db.profiles.find_one({"user_id": user_id})
    
    if not profile:
        return render_template("emergency_view.html", error="Profile details not found.")

    # 4. Success: Show the public page
    return render_template("emergency_view.html", profile=profile)

# =========================================================
# 12. ERROR HANDLING
# =========================================================

@app.errorhandler(404)
def page_not_found(e):
    return render_template('error.html', 
                           code=404, 
                           message="Oops! The page you're looking for doesn't exist."), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('error.html', 
                           code=500, 
                           message="Something went wrong on our end. We're working on it!"), 500

# =========================================================
# 14. QR REVOCATION (THE KILL-SWITCH)
# =========================================================

@app.route("/qr/revoke")
@login_required
def revoke_qr():
    if "user_id" not in session:
        return redirect(url_for("login"))

    db = get_db()
    user_id = session['user_id']

    # Set all QR codes for this user to inactive
    result = db.qr_codes.update_many(
        {"user_id": user_id, "active": True},
        {"$set": {
            "active": False,
            "revoked_at": datetime.utcnow()
        }}
    )

    if result.modified_count > 0:
        flash("Your QR code has been revoked and is no longer active.", "warning")
    else:
        flash("No active QR code found to revoke.", "info")

    return redirect(url_for("dashboard"))

# =========================================================
# 13. RUN APPLICATION
# =========================================================

if __name__ == "__main__":

    app.run(
        debug=app.config["DEBUG"],
        host="0.0.0.0",
        port=5000
    )
