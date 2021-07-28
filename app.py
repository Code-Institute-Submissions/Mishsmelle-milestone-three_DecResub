import os
from flask import (
    Flask, flash, render_template,
    redirect, request, session, url_for)
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
if os.path.exists("env.py"):
    import env


app = Flask(__name__)

app.config["MONGO_DBNAME"] = os.environ.get("MONGO_DBNAME")
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
app.secret_key = os.environ.get("SECRET_KEY")

mongo = PyMongo(app)


@app.route("/")
@app.route("/get_films")
def get_films():
    films = mongo.db.films.find()
    return render_template("theupshot.html", films=films)


@app.route("/get_create", methods=["GET", "POST"])
def create():
    return render_template("create.html")
    # check if username already exists in db
    existing_user = mongo.db.users.find_one(
        {"username": request.form.get("username").lower()})

    if existing_user:
        flash("Username already exists")
        return redirect(url_for("create"))

        create = {
            "username": request.form.get("username").lower(),
            "password": generate_password_hash(request.form.get("password"))
        }
        mongo.db.users.insert_one(create)

        # put the new user into 'session' cookie
        session["user"] = request.form.get("username").lower()
        flash("Account Created!")
    return render_template("create.html")

if __name__ == "__main__":
    app.run(host=os.environ.get("IP"),
            port=int(os.environ.get("PORT")),
            debug=True)