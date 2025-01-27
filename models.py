from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from db import mongo


# from app import mongo

# Authentication User class
class AuthUser(UserMixin):
    def __init__(self, user_id, username, email, password):
        self.id = user_id
        self.username = username
        self.email = email
        self.password = password

    @staticmethod
    def get_user_by_email(email):
        user_data = mongo.db.users.find_one({"email": email})
        if user_data:
            return AuthUser(
                str(user_data["_id"]),
                user_data["username"],
                user_data["email"],
                user_data["password"],
            )
        return None
    def get_id(self):
        return str(self.id)

    def verify_password(self, password):
        return check_password_hash(self.password, password)

    @staticmethod
    def create_user(username, email, password):
        hashed_password = generate_password_hash(password)
        mongo.db.users.insert_one({
            "username": username,
            "email": email,
            "password": hashed_password
        })


# User Data class
class UserData:
    def __init__(self, name, age, contact_info):
        self.name = name
        self.age = age
        self.contact_info = contact_info

    @staticmethod
    def get_user_data(user_id):
        # Assuming that user_data collection stores the user's personal data
        user_data = mongo.db.user_data.find_one({"user_id": user_id})
        if user_data:
            return UserData(
                user_data["name"],
                user_data["age"],
                user_data["contact_info"]
            )
        return None

    def save(self, user_id):
        # Save user data to MongoDB
        mongo.db.user_data.insert_one({
            "user_id": user_id,
            "name": self.name,
            "age": self.age,
            "contact_info": self.contact_info
        })


class BloodSugarReading:
    def __init__(self, value, timestamp=None):
        self.value = value
        self.timestamp = timestamp or datetime.now()

class Meal:
    def __init__(self, food_items, calories, insulin_required, timestamp=None):
        self.food_items = food_items
        self.calories = calories
        self.insulin_required = insulin_required
        self.timestamp = timestamp or datetime.now()

class Exercise:
    def __init__(self, activity, duration, impact, timestamp=None):
        self.activity = activity
        self.duration = duration
        self.impact = impact
        self.timestamp = timestamp or datetime.now()
