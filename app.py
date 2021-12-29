import os
from flask import (
    Flask, flash, render_template,
    redirect, request, session, url_for)
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
if os.path.exists("env.py"):
    import env


app = Flask(__name__)

app.config["MONGO_DBNAME"] = os.environ.get("MONGO_DBNAME")
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
app.secret_key = os.environ.get("SECRET_KEY")

mongo = PyMongo(app)


@app.route("/")
@app.route("/index")
def index():
    recently_added_films = list(
        mongo.db.films.find().sort("date_added", -1).limit(6))
    return render_template(
        "index.html", recently_added_films=recently_added_films)


@app.route("/get_films")
def get_films():
    films = mongo.db.films.find()
    return render_template("index.html", films=films)


@app.route("/search", methods=["GET"])
def search():
    query = request.args.get("query")
    films = list(mongo.db.films.find({"$text": {"$search": query}}))
    return render_template("index.html", films=films, search_str=query)


@app.route("/get_reviews")
def get_reviews():
    """
    get the list of reviews to show on reviews.html
    """
    reviews = list(mongo.db.films.find())
    return render_template("reviews.html", reviews=reviews)


@app.route("/see_review/<reviews>", methods=["GET", "POST"])
def see_review(reviews):
    """
    view the full review of individual book
    """
    reviews = list(mongo.db.reviews.find({"_id": ObjectId(reviews)}))
    return render_template("book_review.html", reviews=reviews)


@app.route("/create", methods=["GET", "POST"])
def create():
    if request.method == "POST":
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

        session["user"] = request.form.get("username").lower()
        flash("Account Created!")
        return redirect(url_for("profile", username=session["user"]))

    return render_template("create.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:

            if check_password_hash(
                    existing_user["password"], request.form.get("password")):
                        session["user"] = request.form.get("username").lower()
                        flash("Welcome, {}".format(
                            request.form.get("username")))
                        return redirect(url_for(
                            "profile", username=session["user"]))
            else:
                flash("Incorrect Username and/or Password")
                return redirect(url_for("login"))

        else:
            flash("Incorrect Username and/or Password")
            return redirect(url_for("login"))

    return render_template("login.html")


@app.route("/profile/<username>", methods=["GET", "POST"])
def profile(username):
    username = mongo.db.users.find_one(
        {"username": session["user"]})["username"]
    user_films = list(mongo.db.films.find({'reviewed_by': session["user"]}))

    if session["user"]:
        return render_template(
            "profile.html", username=username, user_films=user_films)

    return redirect(url_for("login"))


@app.route("/logout")
def logout():
    flash("You have been logged out")
    session.pop("user")
    return redirect(url_for("login"))


@app.route("/upload_review", methods=["GET", "POST"])
def upload_review():
    if request.method == "POST":
        now = datetime.now()
        film = {
            "genre_name": request.form.get("genre_name"),
            "film_title": request.form.get("film_title"),
            "review": request.form.get("review"),
            "date_added": now.strftime("%d/%m/%Y"),
            "reviewed_by": session["user"],
            "image_url": request.form.get("image_url")
        }
        mongo.db.films.insert_one(film)
        flash("Review Successfully Added")
        return redirect(url_for("index"))

    genres = mongo.db.genres.find().sort("genre", 1)
    return render_template("upload_review.html", genres=genres)


@app.route("/edit_film/<film_id>", methods=["GET", "POST"])
def edit_film(film_id):

    if request.method == "POST":
        submit = {
            "genre_name": request.form.get("genre_name"),
            "film_title": request.form.get("film_title"),
            "review": request.form.get("review"),
            "reviewed_by": session["user"],
            "image_url": request.form.get("image_url")
        }
        mongo.db.films.update({"_id": ObjectId(film_id)}, submit)
        flash("Review Successfully Updated")
    film = mongo.db.films.find_one({"_id": ObjectId(film_id)})
    genres = mongo.db.genres.find().sort("genre_name", 1)
    return render_template("edit_film.html", film=film, genres=genres)


@app.route("/delete_film/<film_id>")
def delete_film(film_id):
    mongo.db.films.remove({"_id": ObjectId(film_id)})
    flash("Review Successfully Deleted")
    return redirect(url_for("get_films"))


if __name__ == "__main__":
    app.run(host=os.environ.get("IP"),
            port=int(os.environ.get("PORT")),
            debug=True)
