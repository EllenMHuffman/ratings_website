"""Movie Ratings."""

from jinja2 import StrictUndefined

from flask import (Flask, render_template, redirect, request, flash, session)
from flask_debugtoolbar import DebugToolbarExtension

from model import User, Rating, Movie, connect_to_db, db


app = Flask(__name__)

# Required to use Flask sessions and the debug toolbar
app.secret_key = "ABC"

# Normally, if you use an undefined variable in Jinja2, it fails
# silently. This is horrible. Fix this so that, instead, it raises an
# error.
app.jinja_env.undefined = StrictUndefined


@app.route('/')
def index():
    """Homepage."""
    return render_template('homepage.html')


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

    return redirect('/')


@app.route('/login', methods=['GET'])
def show_login_form():
    """Display user log-in page."""

    return render_template('login.html')


@app.route('/login', methods=['POST'])
def submit_login_form():
    """Check for unique email and password. If correct, log in."""

    email = request.form.get('email')
    password = request.form.get('password')

    result = User.query.filter((User.email == email) &
                               (User.password == password))

    if result.count() == 0:
        flash('Username and/or password incorrect.')
        return redirect('/login')
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

    return render_template('movie_info.html', movie=movie,
                           movie_ratings=movie_ratings)


@app.route('/add_rating', methods=['POST'])
def add_rating():
    """Processes new or updated rating."""

    user_id = request.form.get('user_id')
    movie_id = request.form.get('movie_id')
    score = request.form.get('score')

    result = Rating.query.filter((Rating.user_id == user_id) &
                               (Rating.movie_id == movie_id))

    if result.count() == 0:
        new_rating = Rating(movie_id=movie_id, score=score, user_id=user_id)
        db.session.add(new_rating)
    else:
        #need to update existing rating and fix add error
        pass

    db.session.commit()

    flash("Thanks for adding a rating!")

    return redirect('/movie/<movie_id>')

if __name__ == "__main__":
    # We have to set debug=True here, since it has to be True at the
    # point that we invoke the DebugToolbarExtension
    app.debug = True
    # make sure templates, etc. are not cached in debug mode
    app.jinja_env.auto_reload = app.debug

    connect_to_db(app)

    # Use the DebugToolbar
    DebugToolbarExtension(app)

    app.run(port=5000, host='0.0.0.0')
