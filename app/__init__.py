import os
import click
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask.cli import with_appcontext
from flask_sqlalchemy import SQLAlchemy
from flask import Flask, render_template


VERSION = '2.0'
MAX_PLAYERS = 10


# Set-up app environments
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'ThreeBridges')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', '')
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'app.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'


from app import routes
from app.models import Score, Player


# Error pages
@app.errorhandler(404)
def error_404(error):
    return render_template('error.html', message="Page not found"), 404

@app.errorhandler(403)
def error_403(error):
    return render_template('error.html', message="You don't have permission"), 403

@app.errorhandler(500)
def error_500(error):
    return render_template('error.html', message="Something went wrong"), 500

app.register_error_handler(404, error_404)
app.register_error_handler(403, error_403)
app.register_error_handler(500, error_500)


# Admin utilities
@click.command(name='create_tables')
@with_appcontext
def create_tables():
    db.drop_all()
    db.create_all()
    db.session.add(Score(AA=1, AB=0, AC=0, BA=0, BB=1, BC=0, CA=0, CB=0, CC=1))
    db.session.commit()
    print('Tables created')

@click.command(name='print_players')
@with_appcontext
def print_players():
    print(f'Current Players ({len(Player.query.all())})')
    for user in Player.query.all():
        print(user)

app.cli.add_command(create_tables)
app.cli.add_command(print_players)
