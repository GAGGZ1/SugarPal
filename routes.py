from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, render_template, redirect, url_for
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from db import mongo
from models import AuthUser

routes = Blueprint('routes', __name__)

# Home page
@routes.route("/")
def home():
    if request.is_json:  # Handle API request
        return jsonify({"message": "Welcome to the Home page"})
    return render_template("home.html")  # Handle HTML request

# Register page
@routes.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        if request.is_json:  # Handle API request
            data = request.json
            username = data.get('username')
            email = data.get('email')
            password = generate_password_hash(data.get('password'))
        else:  # Handle HTML form
            username = request.form["username"]
            email = request.form["email"]
            password = generate_password_hash(request.form["password"])

        if mongo.db.users.find_one({"email": email}):
            return jsonify({"message": "Email already registered."}), 400 if request.is_json else "Email already registered."

        mongo.db.users.insert_one({
            "username": username,
            "email": email,
            "password": password
        })
        if request.is_json:
            return jsonify({"message": "Registration successful!"}), 201
        return redirect(url_for("routes.login"))

    if request.is_json:  # Handle API request
        return jsonify({"message": "Please send a POST request to register with username, email, and password."}), 400
    return render_template("register.html")  # Handle HTML request

# Login page
@routes.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.is_json:  # Handle API request
            data = request.json
            email = data.get('email')
            password = data.get('password')
        else:  # Handle HTML form
            email = request.form["email"]
            password = request.form["password"]

        user_data = mongo.db.users.find_one({"email": email})
        if user_data and check_password_hash(user_data["password"], password):
            user = AuthUser(
                str(user_data["_id"]),
                user_data["username"],
                user_data["email"],
                user_data["password"]
            )
            login_user(user)
            next_page = request.args.get('next')
            if request.is_json:
                return jsonify({"message": "Login successful!"}), 200
            return redirect(next_page or url_for("routes.dashboard"))

        return jsonify({"message": "Invalid email or password."}), 400 if request.is_json else "Invalid email or password."
    if request.is_json:
        return jsonify({"message": "Please send a POST request to login with email and password."}), 400
    return render_template("login.html")

# Dashboard page
@routes.route("/dashboard")
@login_required
def dashboard():
    if request.is_json:  # Handle API request
        return jsonify({"username": current_user.username, "user_id": current_user.id})
    return render_template("dashboard.html", username=current_user.username, user_id=current_user.id)

# Logout
@routes.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("routes.home"))

# Add reading (handles both form submission and API)
@routes.route('/add_reading', methods=['POST'])
@login_required
def add_reading():
    if request.is_json:  # Handle API request
        data = request.json
        value = data.get('value')
    else:  # Handle HTML form
        value = request.form.get('reading')

    timestamp = datetime.now()
    blood_sugar = mongo.db.blood_sugar_readings
    reading = {'value': value, 'timestamp': timestamp, 'user_id': current_user.id}
    blood_sugar.insert_one(reading)

    if request.is_json:
        return jsonify({"message": "Reading added successfully!"}), 201
    else:
        return redirect(url_for('routes.dashboard'))

# Get trends (handles both form and API)
@routes.route('/get_trends', methods=['GET'])
@login_required
def get_trends():
    blood_sugar = mongo.db.blood_sugar_readings
    readings = list(blood_sugar.find({'user_id': current_user.id}))

    trends = [{'value': reading['value'], 'timestamp': reading['timestamp'].strftime("%y-%m-%d %H:%M:%S")} for reading
              in readings]

    if request.is_json:
        return jsonify({'trends': trends}), 200
    else:
        return render_template("dashboard.html", trends=trends, username=current_user.username)

# Add meal (handles both form and API)
@routes.route('/add_meal', methods=['POST'])
@login_required
def add_meal():
    if request.is_json:  # Handle API request
        data = request.json
        food_items = data.get('food_items')
        calories = data.get('calories')
    else:  # Handle HTML form
        food_items = request.form.get('meal')
        calories = request.form.get('calories')

    insulin_required = int(calories) / 10
    meal = mongo.db.meals
    meal_entry = {
        'food_items': food_items,
        'calories': calories,
        'insulin_required': insulin_required,
        'timestamp': datetime.now(),
        'user_id': current_user.id
    }
    meal.insert_one(meal_entry)

    if request.is_json:
        return jsonify({"message": "Meal logged successfully!"}), 201
    else:
        return redirect(url_for('routes.dashboard'))
@routes.route('/send_notification', methods=['POST'])
@login_required
def send_notification():
    if request.is_json:  # Handle API request
        data = request.json
        user_id = data.get('user_id')
        blood_sugar_value = data.get('blood_sugar_value')
    else:  # Handle HTML form
        user_id = current_user.user_id
        blood_sugar_value = request.form.get('blood_sugar_value')

    # Ensure blood_sugar_value is a number
    try:
        blood_sugar_value = float(blood_sugar_value)
    except ValueError:
        return jsonify({"message": "Invalid blood sugar value."}), 400

    if blood_sugar_value > 180:
        message = f"Alert: High blood sugar detected! Current level: {blood_sugar_value}."
    elif blood_sugar_value < 70:
        message = f"Alert: Low blood sugar detected! Current level: {blood_sugar_value}."
    else:
        message = f"Your blood sugar is in normal range: {blood_sugar_value}."

    send_push_notification(user_id, message)

    if request.is_json:
        return jsonify({"message": "Notification sent!"}), 200
    else:
        return redirect(url_for('routes.dashboard'))


def send_push_notification(user_id, message):
    print(f"Sent notification to {user_id}: {message}")

# Generate report (handles both form and API)
@routes.route('/generate_report', methods=['GET'])
@login_required
def generate_report():
    blood_sugar = mongo.db.blood_sugar_readings
    one_week_ago = datetime.now() - timedelta(days=7)
    recent_readings = list(blood_sugar.find({'timestamp': {'$gte': one_week_ago}, 'user_id': current_user.id}))

    if not recent_readings:
        message = "No readings in the past week."
        if request.is_json:
            return jsonify({"message": message}), 404
        else:
            return render_template("report.html", message=message)

    total_value = sum([float(reading['value']) for reading in recent_readings])
    average_value = total_value / len(recent_readings)

    if request.is_json:
        return jsonify({
            "message": "Weekly Report Generated",
            "average_blood_sugar": average_value,
            "total_readings": len(recent_readings)
        }), 200
    else:
        return render_template("report.html",
                               message="Weekly Report Generated",
                               average_blood_sugar=average_value,
                               total_readings=len(recent_readings))
