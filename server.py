"""Movie Ratings."""

from jinja2 import StrictUndefined

from flask import (Flask, render_template, redirect, request, flash, session)
from flask_debugtoolbar import DebugToolbarExtension

from model import User, Rating, Movie, connect_to_db, db


app = Flask(__name__)

# Required to use Flask sessions and the debug toolbar
app.secret_key = "ABC"

# Raise error if undefined variable is used in Jinja2
app.jinja_env.undefined = StrictUndefined


@app.route('/')
def index():
    """Homepage."""

    invalid = request.args.get('invalid')
    return render_template('homepage.html', invalid=invalid)


@app.route('/users')
def user_list():
    """Show list of users."""

    users = User.query.all()
    return render_template("user_list.html", users=users)


@app.route('/movies')
def movie_list():
    """Show list of movies."""

    movies = Movie.query.order_by('title').all()
    return render_template("movie_list.html", movies=movies)


@app.route('/register')
def show_reg_form():
    """Display user registration form."""

    return render_template('reg_form.html')


@app.route('/register', methods=['POST'])
def submit_reg_form():
    """Check for unique user email and create new user."""

    email = request.form.get('email')
    password = request.form.get('password')

    existing_emails = db.session.query(User.email)

    if email in existing_emails:
        pass
    else:
        user = User(email=email, password=password)
        db.session.add(user)
        db.session.commit()
        session['user_id'] = user.user_id

    return redirect('/')


@app.route('/login', methods=['POST'])
def submit_login_form():
    """Check for unique email and password. If correct, log in."""

    email = request.form.get('email')
    password = request.form.get('password')

    result = User.query.filter((User.email == email) &
                               (User.password == password))

    if result.count() == 0:
        # flash('Username and/or password incorrect.')
        return redirect('/?invalid=True')
    else:
        user = result.first()
        session['user_id'] = user.user_id
        flash('Logged in')
        return redirect('/user/' + str(user.user_id))


@app.route('/logout')
def submit_logout():
    """Logs out user by emptying session and redirects to homepage"""

    del session['user_id']
    return redirect('/')


@app.route('/user/<user_id>')
def show_user_page(user_id):
    """Show information relating to specific user."""

    user = User.query.get(user_id)
    user_ratings = user.ratings

    return render_template('user_info.html', user=user,
                           user_ratings=user_ratings)


@app.route('/movie/<movie_id>')
def show_movie_page(movie_id):
    """Show information relating to specific movie."""

    movie = Movie.query.get(movie_id)
    movie_ratings = movie.ratings

    user_id = session.get("user_id")

    if user_id:
        user_rating = Rating.query.filter_by(movie_id=movie_id,
                                             user_id=user_id).first()
    else:
        user_rating = None

    # Get ave rating of movie

    rating_scores = [r.score for r in movie.ratings]
    avg_rating = float(sum(rating_scores)) / len(rating_scores)

    prediction = None

    # Prediction code: only predict if the user hasn't rated it

    if (not user_rating) and user_id:
        user = User.query.get(user_id)
        if user:
            prediction = user.predict_rating(movie)

    if prediction:
        # User hasn't scored; use our prediction if we made one
        effective_rating = prediction

    elif user_rating:
        # User has already scored for real; use that
        effective_rating = user_rating.score

    else:
        # User hasn't scored and we couldn't get a prediction
        effective_rating = None

    # Get the eye's rating, either by prediction or using real rating

    the_eye = (User.query.filter_by(email="the-eye@of-judgment.com").one())
    eye_rating = Rating.query.filter_by(user_id=the_eye.user_id,
                                        movie_id=movie.movie_id).first()
    if eye_rating is None:
        eye_rating = the_eye.predict_rating(movie)

    else:
        eye_rating = eye_rating.score

    if eye_rating and effective_rating:
        difference = abs(eye_rating - effective_rating)

    else:
        difference = None

    # Depending on how different we are from the Eye, choose a
    # message

    BERATEMENT_MESSAGES = [
        "I suppose you don't have such bad taste after all.",
        "I regret every decision that I've ever made that has " +
            "brought me to listen to your opinion.",
        "Words fail me, as your taste in movies has clearly " +
            "failed you.",
        "That movie is great. For a clown to watch. Idiot.",
        "Words cannot express the awfulness of your taste."
    ]

    if difference:
        beratement = BERATEMENT_MESSAGES[int(difference)]

    else:
        beratement = None


    return render_template('movie_info.html', movie=movie,
                           movie_ratings=movie_ratings,
                           average=avg_rating,
                           prediction=prediction,
                           beratement=beratement,
                           eye_rating=eye_rating)


@app.route('/add_rating', methods=['POST'])
def add_rating():
    """Processes new or updated rating."""

    user_id = int(request.form.get('user_id'))
    movie_id = int(request.form.get('movie_id'))
    score = int(request.form.get('score'))
    # import pdb; pdb.set_trace()

    result = Rating.query.filter((Rating.user_id == user_id) &
                               (Rating.movie_id == movie_id))

    if result.count() == 0:
        new_rating = Rating(movie_id=movie_id, score=score, user_id=user_id)
        db.session.add(new_rating)
    else:
        row = result.first()
        row.score = score

    db.session.commit()

    flash("Thanks for adding a rating!")

    return redirect('/movie/' + str(movie_id))

if __name__ == "__main__":
    # We have to set debug=True here, since it has to be True at the
    # point that we invoke the DebugToolbarExtension
    # app.debug = True
    # make sure templates, etc. are not cached in debug mode
    app.jinja_env.auto_reload = app.debug

    connect_to_db(app)

    # Use the DebugToolbar
    # DebugToolbarExtension(app)

    app.run(port=5000, host='0.0.0.0')
