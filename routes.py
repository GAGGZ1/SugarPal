

from flask import Blueprint,request,jsonify
from datetime import datetime, timedelta
from db import mongo

routes=Blueprint('routes',__name__)

@routes.route('/add_reading',methods=['POST'])
def add_reading():
    data=request.json
    value=data.get('value')
    timestamp=datetime.now()

    blood_sugar=mongo.db.blood_sugar_readings
    reading={'value':value,'timestamp':timestamp}
    blood_sugar.insert_one(reading)

    return jsonify({"message":"Readings added Successfully!"}),201

@routes.route('/get_trends',methods=['GET'])
def get_trends():
    blood_sugar=mongo.db.blood_sugar_readings
    readings=list(blood_sugar.find())

    trends=[{'value':reading['value'],'timestamp':reading['timestamp'].strftime("%y-%m-%d %H:%M:%S")} for reading in readings]
    return jsonify({'trends':trends}),200

@routes.route('/add_meal',methods=['POST'])
def add_meal():
    data=request.json
    food_items=data.get('food_items')
    calories=data.get('calories')
    insulin_required=calories/10

    meal=mongo.db.meals
    meal_entry={'food_items':food_items,'calories':calories,'insulin_required':insulin_required,'timestamp':datetime.now()}
    meal.insert_one(meal_entry)

    return jsonify({"message":"Meal Logged Successfully!"}),201

@routes.route('/send_notification',methods=['POST'])
def send_notification():
    data=request.json
    user_id=data.get('user_id')
    blood_sugar_value=data.get('blood_sugar_value')

    message="Blood sugar alert!"
    send_push_notification(user_id,message)

    return jsonify({"message": "Notification sent!"}),200

def send_push_notification(user_id,message):
    print(f"Sent notification to {user_id}:{message}")

@routes.route('/generate_report',methods=['GET'])
def generate_report():
    blood_sugar=mongo.db.blood_sugar_readings
    one_week_ago=datetime.now() - timedelta(days=7)
    recent_readings=list(blood_sugar.find({'timestamp':{'$gte':one_week_ago}}))

    if not recent_readings:
        return jsonify({"message":"No readings in the past week."}),404

    total_value=sum([reading['value'] for reading in recent_readings])
    average_value=total_value / len(recent_readings)

    return jsonify({
        "message":"Weekly Report Generated",
        "average_blood_sugar":average_value,
        "total_readings":len(recent_readings)
    }),200


