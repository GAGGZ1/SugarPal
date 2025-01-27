from flask import Flask
from db import init_db


app = Flask(__name__)

app.config["MONGO_URI"]="mongodb://localhost:27017/sugarPal"

init_db(app)

from routes import routes

app.register_blueprint(routes)

if __name__ == '__main__':
    app.run(debug=True)
