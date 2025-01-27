from bson import ObjectId
from flask import Flask
from db import mongo
from flask_login import LoginManager
from models import AuthUser,UserData


app = Flask(__name__)
app.secret_key="7b070c3d7d344000ee366baa50cdd6ce"

app.config["MONGO_URI"]="mongodb://localhost:27017/sugarPal"

mongo.init_app(app)
login_manager=LoginManager()
login_manager.init_app(app)
login_manager.login_view = "routes.login"

@login_manager.user_loader
def load_user(user_id):
    print("Loading user with ID:", user_id)  # Add this line for debugging
    user_data = mongo.db.users.find_one({"_id": ObjectId(user_id)})
    if user_data:
        return AuthUser(
            str(user_data["_id"]),
            user_data["username"],
            user_data["email"],
            user_data["password"],
        )
    return None


from routes import routes

app.register_blueprint(routes)

if __name__ == '__main__':
    app.run(debug=True)
