from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, render_template, redirect, url_for
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from db import mongo
from models import AuthUser
import plotly
import plotly.graph_objs as go
import plotly.io as pio
import json

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
# @routes.route('/generate_report', methods=['GET'])
# @login_required
# def generate_report():
#     blood_sugar = mongo.db.blood_sugar_readings
#     one_week_ago = datetime.now() - timedelta(days=7)
#     recent_readings = list(blood_sugar.find({'timestamp': {'$gte': one_week_ago}, 'user_id': current_user.id}))
#
#     if not recent_readings:
#         message = "No readings in the past week."
#         if request.is_json:
#             return jsonify({"message": message}), 404
#         else:
#             return render_template("report.html", message=message)
#
#     total_value = sum([float(reading['value']) for reading in recent_readings])
#     average_value = total_value / len(recent_readings)
#
#     if request.is_json:
#         return jsonify({
#             "message": "Weekly Report Generated",
#             "average_blood_sugar": average_value,
#             "total_readings": len(recent_readings)
#         }), 200
#     else:
#         return render_template("report.html",
#                                message="Weekly Report Generated",
#                                average_blood_sugar=average_value,
#                                total_readings=len(recent_readings))


@routes.route('/generate_report', methods=['GET'])
@login_required
def generate_report():
    blood_sugar = mongo.db.blood_sugar_readings
    one_week_ago = datetime.now() - timedelta(days=7)
    recent_readings = list(blood_sugar.find({'timestamp': {'$gte': one_week_ago}, 'user_id': current_user.id}))
    print(f"Recent Readings Retrieved: {recent_readings}")

    if not recent_readings:
        message = "No readings in the past week."
        if request.is_json:
            return jsonify({"message": message}), 404
        else:
            return render_template("report.html", message=message)

    # Calculate total and average
    total_value = sum([float(reading['value']) for reading in recent_readings])
    average_value = total_value / len(recent_readings)

    # Prepare data for Plotly graph
    timestamps = [reading['timestamp'].strftime("%Y-%m-%d %H:%M:%S") for reading in recent_readings]
    values = [float(reading['value']) for reading in recent_readings]

    # # Create Plotly graph
    # graph = go.Figure()
    # graph.add_trace(go.Scatter(x=timestamps, y=values, mode='lines+markers', name='Blood Sugar'))
    # graph.update_layout(
    #     title="Blood Sugar Trends (Past Week)",
    #     xaxis_title="Timestamp",
    #     yaxis_title="Blood Sugar Level (mg/dL)",
    #     template="plotly_white"
    # )
    # graph_html = pio.to_html(graph, full_html=False)
    hardcoded_timestamps = ["2025-01-21 12:00:00", "2025-01-22 12:00:00", "2025-01-23 12:00:00"]
    hardcoded_values = [120, 130, 125]

    graph = go.Figure()
    graph.add_trace(go.Scatter(x=hardcoded_timestamps, y=hardcoded_values, mode='lines+markers', name='Blood Sugar'))
    graph.update_layout(
        title="Blood Sugar Trends",
        xaxis_title="Timestamp",
        yaxis_title="Blood Sugar Level (mg/dL)",
        template="plotly_white"
    )
    graph_html = pio.to_html(graph, full_html=False)

    # Log values for debugging
    print(f"Recent Readings: {recent_readings}")
    print(f"Total Value: {total_value}, Average Value: {average_value}")

    # Return JSON response or render the template
    if request.is_json:
        return jsonify({
            "message": "Weekly Report Generated",
            "average_blood_sugar": average_value,
            "total_readings": len(recent_readings),
            "graph_html": graph_html
        }), 200
    else:
        return render_template("report.html",
                               message="Weekly Report Generated",
                               average_blood_sugar=average_value,
                               total_readings=len(recent_readings),
                               graph_html=graph_html)



#
# @routes.route('/blood-sugar-chart')
# def blood_sugar_chart():
#     # Sample data: Blood sugar readings for a week
#     days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
#     readings = [110, 120.98, 130, 115, 75, 135, 125]
#     data = list(zip(days, readings))
#
#     # Create a Plotly graph
#     fig = go.Figure()
#     fig.add_trace(go.Scatter(x=days, y=readings, mode='lines+markers', name='Blood Sugar'))
#     fig.update_layout(
#         title='Blood Sugar Readings Over a Week',
#         xaxis_title='Day of the Week',
#         yaxis_title='Blood Sugar (mg/dL)',
#         template='plotly_dark'  # Optional: Use a dark theme
#     )
#
#     # Convert the graph to JSON
#     graph_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
#
#     # Pass both the days and readings to the template
#     # return render_template('chart.html', graph_json=graph_json, days=days, readings=readings)
#     return render_template('chart.html', graph_json=graph_json, data=data)


@routes.route('/blood-sugar-chart')
@login_required
def blood_sugar_chart():
    # Get the current user (Replace this with your actual user logic)
    user_id = current_user.id

    # Get the readings from the last 7 days for the current user
    one_week_ago = datetime.now() - timedelta(days=7)
    blood_sugar = mongo.db.blood_sugar_readings
    recent_readings = list(blood_sugar.find({'timestamp': {'$gte': one_week_ago}, 'user_id': user_id}))

    print(f"Recent Readings Retrieved: {recent_readings}")

    # Extract the days (timestamps) and blood sugar values
    days = [reading['timestamp'].strftime('%Y-%m-%d %H:%M:%S') for reading in recent_readings]
    readings = [float(reading['value']) for reading in recent_readings]

    # Combine the days and readings into a list of tuples
    data = list(zip(days, readings))

    # Create a Plotly graph
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=days, y=readings, mode='lines+markers', name='Blood Sugar'))
    fig.update_layout(
        title='Blood Sugar Readings Over Time',
        xaxis_title='Timestamp',
        yaxis_title='Blood Sugar (mg/dL)',
        template='plotly_dark'  # Optional: Use a dark theme
    )

    # Convert the graph to JSON
    graph_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    # Pass the combined data to the template
    return render_template('chart.html', graph_json=graph_json, data=data)

#
# @routes.route('/meal_chart')
# def meal_chart():
#     # Get meal data from the database
#     meal_collection = mongo.db.meals
#     one_week_ago = datetime.now() - timedelta(days=7)  # Adjust this based on your needs
#     user_id = current_user.id  # Replace with your logged-in user's ID
#
#     recent_meals = list(meal_collection.find({'timestamp': {'$gte': one_week_ago}, 'user_id': user_id}))
#     print(recent_meals)
#     # Prepare data for plotting
#     timestamps = [meal['timestamp'] for meal in recent_meals]
#     calories = [float(meal['calories']) for meal in recent_meals]
#     print(timestamps)
#     print(calories)
#     # Create a Plotly graph
#     fig = go.Figure()
#     fig.add_trace(go.Scatter(x=timestamps, y=calories, mode='lines+markers', name='Calories Consumed'))
#     fig.update_layout(
#         title='Calories Consumed Over Time',
#         xaxis_title='Timestamp',
#         yaxis_title='Calories',
#         template='plotly_dark'  # Optional: Use a dark theme
#     )
#
#     # Convert the graph to JSON
#     graph_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
#
#     return render_template('meal_chart.html', graph_json=graph_json)
#






@routes.route('/meal_chart_pie')
def meal_chart():
    # Get the current date and calculate one week ago
    one_week_ago = datetime.now() - timedelta(days=7)

    # Retrieve meals data from the 'meals' collection for the last 7 days (replace with actual MongoDB collection)
    meals_collection = mongo.db.meals
    user_id = current_user.id  # Ensure you have user_id in the session
    recent_meals = list(meals_collection.find({'timestamp': {'$gte': one_week_ago}, 'user_id': user_id}))

    # Data processing: count the occurrences of each food item
    food_items_count = {}
    for meal in recent_meals:
        food_item = meal['food_items']
        if food_item in food_items_count:
            food_items_count[food_item] += 1
        else:
            food_items_count[food_item] = 1

    # Prepare data for the pie chart
    food_items = list(food_items_count.keys())
    counts = list(food_items_count.values())

    # Create a Plotly Pie chart
    fig = go.Figure(data=[go.Pie(labels=food_items, values=counts, hole=0.3)])  # Pie chart with a hole (donut chart)
    fig.update_layout(title='Food Item Distribution in the Last Week')

    # Convert the graph to JSON
    graph_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    return render_template('meal_chart_pie.html', graph_json=graph_json)
