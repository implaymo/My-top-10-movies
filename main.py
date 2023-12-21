import os

import wtforms.validators
from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import requests

db = SQLAlchemy()
app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///top-10-movies.db"
db.init_app(app)
Bootstrap5(app)


class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    year = db.Column(db.Integer)
    description = db.Column(db.String(500))
    rating = db.Column(db.Integer)
    ranking = db.Column(db.Integer)
    review = db.Column(db.String(250))
    img_url = db.Column(db.String(250))


class UpdateRating(FlaskForm):
    new_rating = StringField('Your Rating out of 10 e.g 7.5', validators=[wtforms.validators.DataRequired()])
    your_review = StringField('Your Review', validators=[wtforms.validators.DataRequired()])
    done_button = SubmitField('Done')


class NewMovie(FlaskForm):
    movie_title = StringField('Movie Title', validators=[wtforms.validators.DataRequired()])
    add_movie_button = SubmitField('Add Movie')


@app.route("/")
def home():
    result = db.session.execute(db.select(Movie).order_by(Movie.rating))
    all_movies = result.scalars().all()

    for i in range(len(all_movies)):
        all_movies[i].ranking = len(all_movies) - i
    db.session.commit()
    return render_template("index.html", movies=all_movies)


@app.route("/edit/<int:movie_id>", methods=['GET', 'POST'])
def edit(movie_id):
    """"Form to change some info of the Movie Card"""
    form = UpdateRating()
    movie = db.session.get(Movie, movie_id)
    if form.validate_on_submit():
        movie.rating = form.new_rating.data
        movie.review = form.your_review.data
        db.session.commit()
        return redirect(url_for('home'))
    return render_template("edit.html", form=form, movie_id=movie_id, movie=movie)


@app.route("/delete/<int:movie_id>")
def delete(movie_id):
    movie = db.session.get(Movie, movie_id)
    db.session.delete(movie)
    db.session.commit()
    return redirect(url_for('home'))


@app.route("/add", methods=['GET', 'POST'])
def add():
    """Gets a list of the movies searched. After user clicking the selected movie. Returns to the function to add to DB"""
    form = NewMovie()

    url = "https://api.themoviedb.org/3/search/movie?include_adult=false&language=en-US&page=1"
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {os.environ["API-TOKEN-AUTH"]}"
    }
    if request.method == 'POST':
        all_movies = []
        movie_title = form.movie_title.data

        params = {
            "api_key": f"{os.environ["API KEY"]}",
            "query": movie_title,
            "include_adult": "false",
            "language": "en-US",
            "page": 1
        }
        response = requests.get(url, headers=headers, params=params)
        movies_data = response.json()

        for movie in movies_data["results"]:
            all_movies.append({
                'original_title': movie['original_title'],
                'release_date': movie['release_date'],
                'id': movie['id']
            })
        return render_template("select.html", all_movies=all_movies)

    selected_movie_id = request.args.get('selected_movie')
    if selected_movie_id is not None:
        movie_selected = movie_details(selected_movie_id)
        new_movie = Movie(
            title=movie_selected["title"],
            year=movie_selected['release_date'].split('-')[0],
            description=movie_selected['overview'],
            img_url=f'https://image.tmdb.org/t/p/original/{movie_selected["poster_path"]}',

        )
        db.session.add(new_movie)
        db.session.commit()
        return redirect(url_for('edit', movie_id=new_movie.id))

    return render_template("add.html", form=form)


def movie_details(movie_id):
    """Gives info of the selected movie in select.html"""
    url = f"https://api.themoviedb.org/3/movie/{movie_id}"

    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {os.environ["API-TOKEN-AUTH"]}"
    }
    params = {
        "movie_id": movie_id,
    }
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    return response.json()



if __name__ == '__main__':
    app.run(debug=True)
