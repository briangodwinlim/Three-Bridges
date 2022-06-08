from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, TextAreaField, FloatField, SelectField, FieldList
from wtforms.validators import DataRequired, InputRequired, Length, Email, EqualTo, ValidationError
from app.models import Player

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=20)])
    password = PasswordField('Password (Optional)')
    confirm_password = PasswordField('Confirm Password', validators=[EqualTo('password', 'Password does not match')])
    submit = SubmitField('Register')

    def validate_username(self, username):
        if Player.query.filter_by(username=username.data).first():
            raise ValidationError('Username is taken')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=20)])
    password = PasswordField('Password')
    remember = BooleanField('Remember be')
    submit = SubmitField('Login')

class AdminForm(FlaskForm):
    AA = FloatField('AA', validators=[InputRequired()])
    AB = FloatField('AB', validators=[InputRequired()])
    AC = FloatField('AC', validators=[InputRequired()])
    BA = FloatField('BA', validators=[InputRequired()])
    BB = FloatField('BB', validators=[InputRequired()])
    BC = FloatField('BC', validators=[InputRequired()])
    CA = FloatField('CA', validators=[InputRequired()])
    CB = FloatField('CB', validators=[InputRequired()])
    CC = FloatField('CC', validators=[InputRequired()])
    reset = SelectField('Reset Options', validators=[DataRequired()],
            choices=[('none', 'None'), ('game', 'Reset Game'), ('message', 'Reset Messages'),
                        ('player', 'Reset Players'), ('score', 'Reset Score')])
    submit = SubmitField('Update')

class PlayForm(FlaskForm):
    bridge = SelectField('Select Bridge', validators=[DataRequired()],
            choices=[('A', 'Safe Bridge'), ('B', 'Rocky Bridge'), ('C', 'Vine Bridge')])
    submit = SubmitField('Select')

class MessageForm(FlaskForm):
    message = StringField('Message', validators=[DataRequired(), Length(min=0, max=150)])
    submit = SubmitField('Send')

class OpponentForm(FlaskForm):
    player = FieldList(SelectField('Select Opponent', validators=[DataRequired()]))
    submit = SubmitField('Update')