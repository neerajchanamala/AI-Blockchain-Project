from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_pymongo import PyMongo
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import secrets
from flask_cors import CORS
import os
from ml import run_model

from ml import analyze_ingredients_from_image

app = Flask(__name__)
app.config['MONGO_URI'] = 'mongodb://localhost:27017/Safe_Bites'
app.config['SECRET_KEY'] = secrets.token_hex(32)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

mongo = PyMongo(app)

# Enable CORS, allow credentials for frontend origin
CORS(app, supports_credentials=True, origins=["http://127.0.0.1:5500"])

# ---------------------- FRONTEND ROUTES ----------------------
@app.route("/")
def home():
    return render_template("home.html")

@app.route("/login")
def login_page():
    return render_template("login.html")

@app.route("/signup")
def signup_page():
    return render_template("signup.html")

@app.route('/scan', methods=['GET', 'POST'])
def scan():
    if request.method == 'POST':
        if 'image' not in request.files:
            return "No image uploaded", 400

        image = request.files['image']
        if image.filename == '':
            return "No selected file", 400

        filename = secure_filename(image.filename)
        upload_folder = app.config.get('UPLOAD_FOLDER', 'uploads')
        # Make sure upload_folder is inside 'static' so files are accessible in templates
        save_folder = os.path.join('static', upload_folder)
        if not os.path.exists(save_folder):
            os.makedirs(save_folder)

        path = os.path.join(save_folder, filename)
        image.save(path)

        # Analyze image
        results = analyze_ingredients_from_image(path)

        # Render results page, passing analysis_data
        return render_template('analysis.html', analysis_data=results)

    # GET request: render scan form page
    return render_template('scan.html')


@app.route('/scan', methods=['GET', 'POST'])
def scan_page():
    if request.method == 'POST':
        # Get the uploaded file from the form
        file = request.files.get('image')  # assuming the form input name="image"
        if file:
            # Save the file somewhere, e.g. static/uploads/
            filename = secure_filename(file.filename)
            path = os.path.join('static', 'uploads', filename)
            file.save(path)

            # Now analyze the image from the saved path
            results = analyze_ingredients_from_image(path)
            return render_template('analysis.html', analysis_data=results)

        # If no file, handle error or redirect
        return "No file uploaded", 400

    return render_template('scan.html')


from flask import render_template

@app.route("/analysis")
def analysis():
    analysis_data = session.get("analysis_data", [])
    return render_template("analysis.html", analysis_data=analysis_data)




@app.route("/complaint", methods=["GET", "POST"])
def complaint_page():
    if request.method == "GET":
        return render_template("complaint.html")  # Just show the form

    # For POST method - collect form data from frontend
    data = request.get_json()

    complaint_id = mongo.db.complaints.insert_one({
        'name': data['name'],
        'email': data['email'],
        'product': data['product'],
        'ingredient': data['ingredient'],
        'description': data['description'],
        'date': datetime.utcnow()
    }).inserted_id

    return jsonify({'message': 'Complaint filed successfully', 'id': str(complaint_id)}), 201

@app.route("/profile")
def profile_page():
    if 'user_id' not in session:
        return redirect(url_for('login_page'))
    return render_template("profile.html")

@app.route("/history")
def history_page():
    if 'user_id' not in session:
        return redirect(url_for('login_page'))
    return render_template("history.html")

# ---------------------- AUTHENTICATION ----------------------
@app.route("/signup", methods=["POST"])
def signup():
    data = request.get_json()

    if mongo.db.users.find_one({'email': data['email']}):
        return jsonify({'error': 'User already exists'}), 400

    hashed_pw = generate_password_hash(data['password'])
    user_id = mongo.db.users.insert_one({
        'name': data['name'],
        'email': data['email'],
        'password': hashed_pw,
        'created_at': datetime.utcnow()
    }).inserted_id

    return jsonify({'message': 'User registered successfully', 'user_id': str(user_id)}), 201

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    user = mongo.db.users.find_one({"email": data["email"]})

    if user and check_password_hash(user["password"], data["password"]):
        session['user_id'] = str(user['_id'])
        return jsonify({"message": "Login successful"}), 200
    
    return jsonify({"error": "Invalid credentials"}), 401

@app.route("/logout", methods=["POST"])
def logout():
    session.pop('user_id', None)
    return jsonify({'message': 'Logged out successfully'}), 200

# ---------------------- IMAGE ANALYSIS ----------------------
@app.route("/upload_image", methods=["POST"])
def upload_image():
    if 'image' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['image']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)

    try:
        print("Running model on:", filepath)
        analysis_data = run_model(filepath)
        print("Model output:", analysis_data)
        session["analysis_data"] = analysis_data
        return jsonify({"redirect_url": url_for("analysis")})
    except Exception as e:
        print("Model error:", str(e))  # log full stack trace if needed
        return jsonify({"error": f"Error in ML model: {str(e)}"}), 500



# ---------------------- HISTORY API ----------------------
@app.route("/history/data", methods=["GET"])
def get_history():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    scans = list(mongo.db.scans.find({'user_id': session['user_id']}))
    for scan in scans:
        scan['_id'] = str(scan['_id'])
    return jsonify(scans)

# ---------------------- COMPLAINT API ----------------------
@app.route("/complaints", methods=["GET"])
def get_complaints():

    complaints = list(mongo.db.complaints.find({'user_id': session['user_id']}))
    for complaint in complaints:
        complaint['_id'] = str(complaint['_id'])
    return jsonify(complaints)

# ---------------------- MAIN ----------------------
if __name__ == "__main__":
    app.run(debug=True, port=5000)
