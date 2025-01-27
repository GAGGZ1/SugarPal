# db.py
from flask_pymongo import PyMongo

mongo = None

def init_db(app):
    global mongo
    mongo = PyMongo(app)
