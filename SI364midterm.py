###############################
####### SETUP (OVERALL) #######
###############################

## Import statements
# Import statements
import os
from flask import Flask, render_template, session, redirect, url_for, flash, request
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField # Note that you may need to import more here! Check out examples that do what you want to figure out what.
from wtforms.validators import Required # Here, too
from flask_sqlalchemy import SQLAlchemy
from imdb import IMDb # pip install imdbpy

## App setup code
app = Flask(__name__)
app.debug = True
app.use_reloader = True

## All app.config values
app.config['SECRET_KEY'] = 'secretstring364midterm'
app.config['SQLALCHEMY_DATABASE_URI'] = "postgres://AbbySnyder@localhost/abisny364midterm"
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

## Statements for db setup (and manager setup if using Manager)
db = SQLAlchemy(app)


######################################
######## HELPER FXNS (If any) ########
######################################
def get_or_create_movie(title, release_year):
    if not Year.query.filter_by(name=release_year).first():
        db.session.add(Year(name=release_year))
    if Movie.query.filter_by(title=title, release_year=release_year).first():
        return Movie.query.filter_by(title=title, release_year=release_year).first()
    movie = Movie(title=title, release_year=release_year)
    db.session.add(movie)
    db.session.commit()
    return movie


##################
##### MODELS #####
##################

class Name(db.Model):
    __tablename__ = "names"
    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String(64))
    def __repr__(self):
        return "{} (ID: {})".format(self.name, self.id)

class Movie(db.Model):
    __tablename__ = "movies"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(64))
    release_year = db.Column(db.Integer, db.ForeignKey('years.name'))
    def __repr__(self):
        return "{}, {} (ID: {})".format(self.title, self.release_year, self.id)

class Year(db.Model):
    __tablename__ = "years"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Integer, unique=True)
    movies = db.relationship('Movie', backref='Genre')
    def __repr__(self):
        return "{} (ID: {})".format(self.name, self.id)

###################
###### FORMS ######
###################

class NameForm(FlaskForm):
    name = StringField("Please enter your name.",validators=[Required()])
    submit = SubmitField()

class MovieForm(FlaskForm):
    title = StringField("Please enter the title of a movie.", validators=[Required()])
    submit = SubmitField()


#######################
###### VIEW FXNS ######
#######################

## Error handling routes
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500
########################

@app.route('/', methods=['GET', 'POST'])
def home():
    form = NameForm() # User should be able to enter name after name and each one will be saved, even if it's a duplicate! Sends data with GET
    if form.validate_on_submit():
        name = form.name.data
        newname = Name(name=name)
        db.session.add(newname)
        db.session.commit()
        return redirect(url_for('all_names'))
    return render_template('base.html', form=form)

@app.route('/all_names')
def all_names():
    names = Name.query.all()
    return render_template('name_example.html',names=names)

@app.route('/movies', methods=['GET', 'POST'])
def movies():
    form = MovieForm()
    if form.validate_on_submit():
        ia = IMDb()
        first_result = ia.search_movie(form.title.data)[0]
        movie = get_or_create_movie(title=first_result['title'], release_year=first_result['year'])
        return redirect(url_for('all_movies'))
    return render_template('movie_form.html', form=form)

@app.route('/all_movies')
def all_movies():
    movies = Movie.query.all()
    return render_template('all_movies.html', movies=movies)

## Code to run the application...
if __name__ == '__main__':
    db.create_all() # Will create any defined models when you run the application
    app.run(use_reloader=True,debug=True) # The usual

# Put the code to do so here!
# NOTE: Make sure you include the code you need to initialize the database structure when you run the application!
