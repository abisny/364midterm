###############################
####### SETUP (OVERALL) #######
###############################

## Import statements
# Import statements
import os
from flask import Flask, render_template, session, redirect, url_for, flash, request
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, RadioField # Note that you may need to import more here! Check out examples that do what you want to figure out what.
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

# REQUIRES: title is a string, release_year is an int
# MODIFIES: db tables movies, years
# EFFECTS: adds release_year to Years if not there, adds movie to Movies if
#          not there (with foreign key release_year)
def get_or_create_movie_year(title, release_year):
    if not Year.query.filter_by(name=release_year).first():
        db.session.add(Year(name=release_year))
    if not Movie.query.filter_by(title=title, release_year=release_year).first():
        db.session.add(Movie(title=title, release_year=release_year))
        db.session.commit()

# REQUIRES: valid game_id, guess is a string
# MODIFIES: row for given game_id in table games
# EFFECTS: increments score for game at game_id by one and adds the guess to the
#          "list" of guesses attached to game all if guess hasn't already been made
def increment_score(game_id, guess):
    game = Game.query.filter_by(id=game_id).first()
    if guess not in game.guesses.split(';'):
        game.current_score+=1
        game.guesses += (';' + guess)

# REQUIRES: player and guess are strings, correct either an integer or None
# MODIFIES: db table games
# EFFECTS: adds a new game to the db table games with given player name;
#          increments score if correct guess
def create_game(player, correct, guess):
    game = Game(player=player, current_score=0)
    db.session.add(game)
    if correct: increment_score(game.id, guess)
    return game


##################
##### MODELS #####
##################

class Name(db.Model):
    __tablename__ = "names"
    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String(64))
    def __repr__(self):
        return "{} (ID: {})".format(self.name, self.id)
    def validate_name(self, field):
        if len(str(field.data).split()) < 2:
            raise ValidationError("Name must be at least two words")

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

class Game(db.Model):
    __tablename__ = "games"
    id = db.Column(db.Integer, primary_key=True)
    player = db.Column(db.String(64))
    current_score = db.Column(db.Integer)
    guesses = db.Column(db.String)
    def __repr__(self):
        return "Current score for {} (game #{}) is {}! Great job!".format(self.name, self.id, self.current_score)

###################
###### FORMS ######
###################

class NameForm(FlaskForm):
    name = StringField("Please enter your full name.",validators=[Required()])
    submit = SubmitField()

class MovieForm(FlaskForm):
    title = StringField("Please enter the title of a movie.", validators=[Required()])
    submit = SubmitField()

class GameForm(FlaskForm):
    game_id = StringField("Enter the ID number for the game you want to continue.")
    player = StringField("Enter your name.")
    guess = StringField("Guess a top 250 movie title here.", validators=[Required()])
    submit = SubmitField()

#######################
###### VIEW FXNS ######
#######################

########### Provided routes (NameForm and home) ############
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
    return render_template('name_example.html', names=Name.query.all())
############################################################

## Error handling routes ##
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500
###########################

@app.route('/movies', methods=['GET', 'POST'])
def movies():
    form = MovieForm()
    if form.validate_on_submit():
        ia = IMDb()
        first_result = ia.search_movie(form.title.data)[0]
        get_or_create_movie_year(title=first_result['title'], release_year=first_result['year'])
        return redirect(url_for('all_movies'))
    return render_template('movie_form.html', form=form)

@app.route('/all_movies')
def all_movies():
    return render_template('all_movies.html', movies=Movie.query.all())

@app.route('/play_game', methods=['GET', 'POST'])
def play_game():
    game_choice = 1
    if request.args: game_choice = int(request.args['game'])
    game_form = GameForm()
    if game_form.validate_on_submit():
        ia = IMDb()
        top_250 = [str(item) for item in ia.get_top250_movies()]
        index = None
        for i in range(0, 250):
            if game_form.guess.data == top_250[i]: index = i + 1
        if index and game_choice == 2:
            increment_score(game_id=int(game_form.game_id.data), guess=game_form.guess.data)
        elif game_choice == 1:
            game = create_game(player=game_form.player.data, correct=index, guess=game_form.guess.data)
        db.session.commit()
        return render_template('game_result.html', rank=index)
    return render_template('game.html', form=game_form, game_choice=game_choice)

@app.route('/scores')
def view_scores():
    return render_template('scores.html', games=Game.query.all())

## Code to run the application...
if __name__ == '__main__':
    db.create_all() # Will create any defined models when you run the application
    app.run(use_reloader=True,debug=True) # The usual

# Put the code to do so here!
# NOTE: Make sure you include the code you need to initialize the database structure when you run the application!
