from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_file
from pymongo import MongoClient
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from bson import ObjectId
import os
import uuid
import io
import cv2
import numpy as np
from datetime import datetime

import tensorflow as tf
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image

from gpt4all import GPT4All
from fpdf import FPDF
import matplotlib.cm as cm

from bson.objectid import ObjectId
from bson.errors import InvalidId

# ====== App Configuration ======
app = Flask(__name__)
app.secret_key = "your_secret_key"

# ====== MongoDB Configuration ======
client = MongoClient("mongodb://localhost:27017/")
db = client["xray_disease_db"]
users_collection = db["users"]
reports_collection = db["reports"]

# ====== Upload Folders ======
UPLOAD_FOLDER = "static/uploads"
REPORTS_FOLDER = "static/reports"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["REPORTS_FOLDER"] = REPORTS_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(REPORTS_FOLDER, exist_ok=True)

# ====== Load Models ======
model = None
gpt_model = None
disease_labels = ["Normal", "Pneumonia", "Fracture"]

try:
    model = load_model(r"D:\\CU\\AIML_project\\xray_disease_detector_gui\\models\\xray_final_model.h5")
    print("✅ X-ray Model Loaded Successfully")
except Exception as e:
    print("❌ Error loading X-ray Model:", e)

try:
    gpt_model = GPT4All(
        model_name="ggml-gpt4all-j-v1.3-groovy.bin",
        model_path=r"D:\\CU\\AIML_project\\xray_disease_detector_gui\\models"
    )
    print("✅ GPT4All Model Loaded Successfully")
except Exception as e:
    print("❌ Error loading GPT Model:", e)

# ====== Routes ======

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        password = request.form["password"]
        user = users_collection.find_one({"email": email})
        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["user_id"]
            return redirect("/dashboard")
        return render_template("login.html", error="❌ Invalid Email or Password")
    return render_template("login.html")

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form["name"].strip()
        email = request.form["email"].strip().lower()
        phone = request.form["phone"].strip()
        password = request.form["password"]

        if users_collection.find_one({"email": email}):
            return render_template("signup.html", error="⚠️ Email already registered!")

        user_id = str(uuid.uuid4())[:8]
        hashed_password = generate_password_hash(password)

        users_collection.insert_one({
            "user_id": user_id,
            "name": name,
            "email": email,
            "phone": phone,
            "password": hashed_password
        })

        return render_template("login.html", success="✅ Signup successful!")
    return render_template("signup.html")

#-----------------------------------------------------------------------------------

@app.route("/predict", methods=["POST"])
def predict():
    if "xray" not in request.files:
        return jsonify({"error": "❌ No file uploaded!"}), 400

    file = request.files["xray"]
    if file.filename == "":
        return jsonify({"error": "❌ No file selected!"}), 400

    filename = secure_filename(file.filename)
    file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(file_path)

    try:
        # 🖼️ Preprocess image
        img = image.load_img(file_path, target_size=(224, 224), color_mode="grayscale")
        img_array = image.img_to_array(img)
        img_array = np.expand_dims(img_array, axis=(0, -1)) / 255.0

        # 🤖 Predict
        prediction = model.predict(img_array)[0][0]
        diagnosis = "Pneumonia" if prediction > 0.5 else "Normal"
        confidence_percentage = round((prediction if prediction > 0.5 else (1 - prediction)) * 100, 2)

        # 🧾 Collect patient info
        patient_name = request.form.get("name", "")
        patient_age = request.form.get("age", "")
        blood_group = request.form.get("blood_group", "")

        report_id = None

        # 📝 Store in DB if user is logged in
        if "user_id" in session:
            report_data = {
                "user_id": session["user_id"],
                "patient_name": patient_name,
                "age": patient_age,
                "blood_group": blood_group,
                "filename": filename,
                "file_path": file_path,
                "diagnosis": diagnosis,
                "confidence": confidence_percentage,
                "timestamp": datetime.now()
            }
            inserted_report = reports_collection.insert_one(report_data)
            report_id = str(inserted_report.inserted_id)

        # 📄 Render result with all data including report_id
        return render_template("result.html",
                               diagnosis_text=diagnosis,
                               confidence_text=confidence_percentage,
                               image_url=file_path,
                               user_name=patient_name,
                               user_age=patient_age,
                               user_blood=blood_group,
                               user_id=session.get("user_id"),
                               report_id=report_id,  # ✅ Pass to HTML
                               request=request)

    except Exception as e:
        return jsonify({"error": f"❌ Error processing image: {str(e)}"}), 500

#------------------------------------------------------------------------------------
@app.route("/chat", methods=["POST"])
def chat_with_ai():
    if not gpt_model:
        return jsonify({"error": "❌ GPT model not loaded!"}), 500

    data = request.get_json()
    user_message = data.get("message", "")
    if not user_message:
        return jsonify({"error": "⚠️ Empty message!"}), 400

    try:
        response = gpt_model.generate(
            user_message,
            max_tokens=100,
            temp=0.7,
            top_k=40,
            top_p=0.9,
            n_batch=4
        )
        return jsonify({"response": response})
    except Exception as e:
        return jsonify({"error": f"🔥 GPT Error: {str(e)}"}), 500

########------------------------------------------------------------------------------

@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect("/")

    # Get user info
    user = users_collection.find_one({"user_id": session["user_id"]}, {"_id": 0})

    # Get all reports for the user, sort by latest first
    reports = list(reports_collection.find({"user_id": session["user_id"]}).sort("timestamp", -1).limit(3))
    # Convert MongoDB ObjectId to string
    for report in reports:
        report["_id"] = str(report["_id"])

    return render_template("dashboard.html", user=user, reports=reports)

#====================================================================================

@app.route("/download_report/<report_id>")
def download_report(report_id):
    if "user_id" not in session:
        return redirect("/")
    try:
        report = reports_collection.find_one({"_id": ObjectId(report_id)})
        if not report:
            return jsonify({"error": "Report not found!"}), 404

        # ✅ Generate PDF dynamically
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)

        pdf.cell(200, 10, txt="X-Ray Disease Detection Report", ln=True, align="C")
        pdf.ln(10)
        pdf.cell(200, 10, txt=f"Name: {report.get('patient_name', 'N/A')}", ln=True)
        pdf.cell(200, 10, txt=f"Age: {report.get('age', 'N/A')}", ln=True)
        pdf.cell(200, 10, txt=f"Blood Group: {report.get('blood_group', 'N/A')}", ln=True)
        pdf.cell(200, 10, txt=f"Disease Detected: {report.get('diagnosis', 'N/A')}", ln=True)
        pdf.cell(200, 10, txt=f"Confidence: {report.get('confidence', 'N/A')}%", ln=True)

        timestamp = report.get("timestamp")
        formatted_time = timestamp.strftime('%Y-%m-%d %H:%M:%S') if timestamp else "N/A"
        pdf.cell(200, 10, txt=f"Date: {formatted_time}", ln=True)

        # ✅ Output as bytes and send
        pdf_bytes = pdf.output(dest='S').encode('latin-1')
        pdf_output = io.BytesIO(pdf_bytes)

        return send_file(pdf_output, as_attachment=True, download_name="xray_disease_report.pdf", mimetype='application/pdf')

    except InvalidId:
        return jsonify({"error": "Invalid Report ID!"}), 400
    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500

#---------------------------------------------------------------------------------------
@app.route("/all_reports")
def all_reports():
    # 🔐 Redirect to login if user not in session
    if "user_id" not in session:
        return redirect(url_for("login"))

    # 📋 Fetch all reports for the logged-in user, sorted by newest first
    all_reports = list(
        reports_collection.find({"user_id": session["user_id"]}).sort("timestamp", -1)
    )

    # 📄 Render the all_reports template with the fetched data
    return render_template("all_reports.html", reports=all_reports)

#----------------------------------------------------------------------------------------
@app.route("/share/<report_id>")
def share_report(report_id):
    # You can add email or WhatsApp share logic here.
    return f"Sharing feature coming soon for report {report_id}"
#-----------------------------------------------------------------------------------------
@app.route("/logout")
def logout():
    session.pop("user_id", None)
    return redirect("/")

# ====== Run Flask App ======
if __name__ == "__main__":
    app.run(debug=True)
