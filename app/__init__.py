from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from turbo_flask import Turbo
import os
import secrets
import click
from flask.cli import with_appcontext

app = Flask(__name__)
turbo = Turbo(app)

# secrets.token_hex(16)
app.config['SECRET_KEY'] = '5a84c79054c33f4431941685d92b9e8c'

basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', '').replace('postgres://', 'postgresql://') or \
            'sqlite:///' + os.path.join(basedir, 'app.db')

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

from app import routes
from app.models import Score, Player, Record

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

@click.command(name='create_tables')
@with_appcontext
def create_tables():
    db.drop_all()
    db.create_all()
    init = 1
    db.session.add(Score(AA=init, AB=init, AC=init, BA=init, BB=init, BC=init, CA=init, CB=init, CC=init))
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