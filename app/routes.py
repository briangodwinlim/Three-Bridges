from flask import render_template, url_for, flash, redirect, request, abort
from app import app, db, bcrypt, turbo
from app.forms import RegistrationForm, LoginForm, AdminForm, PlayForm, MessageForm, OpponentForm
from app.models import Player, Score, Record, Message, Opponent
from flask_login import login_user, current_user, login_required
from flask_login.utils import logout_user
import pandas as pd
import numpy as np
import datetime as dt
import threading
import time

max_players = 10

@app.route("/")
@app.route("/home")
def home():
    return render_template('home.html')

@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit() and len(Player.query.all()) <= max_players+1:
        password = form.password.data if form.password.data else "NA"
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        user = Player(username = form.username.data.upper(), password = hashed_password)
        db.session.add(user)
        db.session.commit()

        if len(Player.query.all()) == 1:
            opponent = Opponent(opponent_id=user.id, player=user)
        elif len(Player.query.all()) % 2 == 0:
            opponent = Opponent(opponent_id=user.id, player=user)
        elif len(Player.query.all()) % 2 == 1:
            opponent_ = Opponent.query.all()[-1]
            opponent = Opponent(opponent_id=opponent_.player_id, player=user)
            opponent_.opponent_id = user.id
        db.session.add(opponent)
        db.session.commit()

        login_user(user, remember=False)
        flash(f'Account created. Welcome {user.username}!', 'success')
        return redirect(url_for('home'))

    elif len(Player.query.all()) > max_players+1:
        flash('Maximum players reached. Please try again later.', 'danger')
        return redirect(url_for('home'))
    return render_template('register.html', title="Register", form=form)

@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = Player.query.filter_by(username=form.username.data.upper()).first()
        password = form.password.data if form.password.data else "NA"
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            flash(f'Welcome {user.username}', 'success')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Log in failed', 'danger')
    return render_template('login.html', title="Login", form=form)

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route("/admin", methods=['GET', 'POST'])
@login_required
def admin():
    if current_user != Player.query.first():
        abort(403)

    score = Score.query.get(1)
    form = AdminForm()
    if form.validate_on_submit():
        score.AA = form.AA.data; score.AB = form.AB.data; score.AC = form.AC.data
        score.BA = form.BA.data; score.BB = form.BB.data; score.BC = form.BC.data
        score.CA = form.CA.data; score.CB = form.CB.data; score.CC = form.CC.data
        
        if form.reset.data in ['player', 'game', 'message']:
            for message in Message.query.all():
                db.session.delete(message)

        if form.reset.data in ['player', 'game']:
            for record in Record.query.all():
                db.session.delete(record)

        if form.reset.data == 'player':
            for opponent in Opponent.query.all():
                if opponent.player == current_user: continue
                db.session.delete(opponent)

            for user in Player.query.all():
                if user == current_user: continue
                db.session.delete(user)
        
        if form.reset.data == 'score':
            score = Score.query.first()
            init = 1
            score.AA = init; score.AB = init; score.AC = init
            score.BA = init; score.BB = init; score.BC = init
            score.CA = init; score.CB = init; score.CC = init
        
        db.session.commit()

        flash('Update successful', 'success')
        return redirect(url_for('admin'))

    if request.method == 'GET':
        form.AA.data = score.AA; form.AB.data = score.AB; form.AC.data = score.AC 
        form.BA.data = score.BA; form.BB.data = score.BB; form.BC.data = score.BC 
        form.CA.data = score.CA; form.CB.data = score.CB; form.CC.data = score.CC 
    
    return render_template('admin.html', title='Admin', form=form)

@app.route("/match", methods=['GET', 'POST'])
@login_required
def match():
    if current_user != Player.query.first():
        abort(403)

    form = OpponentForm()
    for player_form in form.player:
        player_form.choices = [(str(player.id), player.username) for player in Player.query.all()]

    if form.validate_on_submit(): 
        for idx, player_form in enumerate(form.player):
            player = Player.query.all()[idx]
            opponent = Opponent.query.filter_by(player_id=player.id).first()
            opponent.opponent_id = int(player_form.data)
            db.session.commit()
        
        for player in Player.query.all():
            if player == current_user: continue
            my_opponent_id = Opponent.query.filter_by(player_id=player.id).first().opponent_id 
            im_opponent = Opponent.query.filter_by(opponent_id=player.id).filter(Opponent.player!=current_user).all()
            if len(im_opponent) != 1 or my_opponent_id != im_opponent[0].player_id or my_opponent_id == 1:
                    flash('Please check match up', 'danger')
                    break
        return redirect(url_for('match'))
    
    if request.method == 'GET':
        form.player.entries = []
        for player in Player.query.all():
            form.player.append_entry()
            form.player[-1].label = player.username
            form.player[-1].choices = [(str(player_.id), player_.username) for player_ in Player.query.all()]
            form.player[-1].data = str(player.opponent[0].opponent_id)

    return render_template('match.html', title='Match', form=form)

def my_opponent(user):
    return Player.query.get(Opponent.query.filter_by(player=user).first().opponent_id)

def scoreboard(user):
    opponent = my_opponent(user)
    df = pd.DataFrame()
    bridge_dict = dict(PlayForm.bridge.kwargs['choices'] + [('', '')])
    my_record = Record.query.filter_by(player=user).all()
    op_record = Record.query.filter_by(player=opponent).all()
    score = Score.query.first()

    for i in range(10):
        my_move = my_record[i].bridge if i < len(my_record) else ''
        op_move = ''
        my_score = np.nan
        if i < len(op_record) and i < len(my_record):
            op_move = op_record[i].bridge
            my_score = getattr(score, my_move+op_move)

        my_move = bridge_dict[my_move]
        op_move = bridge_dict[op_move]

        df = pd.concat([df,
            pd.DataFrame([[i+1, my_move, op_move, my_score]], 
                    columns=['Round', user.username, opponent.username, 'Score'])
        ]).reset_index(drop=True)
            
    df = pd.concat([df,
        pd.DataFrame([['Total', '', '', df['Score'].dropna().sum()]], 
                columns=['Round', user.username, opponent.username, 'Score'])
    ]).reset_index(drop=True)
    df['Score'] = df['Score'].fillna('')

    return df

@app.route("/play", methods=['GET', 'POST'])
@login_required
def play():
    play_form = PlayForm()
    if play_form.validate_on_submit():
        record = Record(bridge = play_form.bridge.data, player = current_user)
        db.session.add(record)
        db.session.commit()
        return redirect(url_for('play'))
    
    message_form = MessageForm()
    if message_form.validate_on_submit():
        recipients = [my_opponent(current_user)] if current_user != Player.query.first() else [player for player in Player.query.all()]
        for recipient in recipients:
            message = Message(author = current_user, recipient = recipient, 
                        body = message_form.message.data, timestamp = dt.datetime.now())
            db.session.add(message)
        db.session.commit()
        return redirect(url_for('play'))
    
    messages = Message.query.filter((Message.sender_id==current_user.id)|(Message.recipient_id==current_user.id)).all()
    if current_user.id == 1:
        messages = Message.query.filter((Message.sender_id==current_user.id)&(Message.recipient_id==current_user.id)).all()
    checked = (dt.datetime.now() - messages[-1].timestamp).total_seconds() < 3 if len(messages) else False

    df = scoreboard(current_user)
    if df.iloc[-2,1] != '' and df.iloc[-2,2] != '' and not checked:
        flash('Game Over', 'info')
    elif df.iloc[-2,1] != '' and df.iloc[-2,2] == '' and not checked:
        flash('Please wait for the game to finish', 'info')

    return render_template('play.html', title='Play', play_form=play_form, message_form=message_form, 
                df=df, messages=messages, user=current_user, checked=checked)

def score_summary():
    score_df = pd.DataFrame([i for i in range(1,11)] + ['Total'], columns=['Round'])
    for user in Player.query.all():
        score_df = pd.concat([score_df, scoreboard(user)[['Score']].rename({'Score': user.username}, axis=1)], axis=1)
    return score_df

@app.route("/overview")
@login_required
def overview():
    if current_user != Player.query.first():
        abort(403)
    return render_template('overview.html', title='Overview')

@app.route("/log")
def log():
    return render_template('log.html', title='Log')

@app.context_processor
def inject_load():
    return {'score': Score.query.first(),
            'score_summary': score_summary(),
            'version_number': '1.2',
            'bridge_dict': dict(PlayForm.bridge.kwargs['choices'] + [('', '')])}

@app.before_first_request
def before_first_request():
    if 'Turbo' not in [thread.name for thread in threading.enumerate()]:
        print('Turbo Executed')
        threading.Thread(target=update_table, daemon=True, name='Turbo').start()

@turbo.user_id
def get_user_id():
    return current_user.id if current_user.is_authenticated else 0

def update_table():
    with app.app_context():
        while True:
            time.sleep(1)
            turbo.push(turbo.replace(render_template('overview_scoreboard.html'),'overview_scoreboard'))
            turbo.push(turbo.replace(render_template('play_score.html'),'play_score'))
            for user in Player.query.all():
                try: 
                    turbo.push(turbo.replace(render_template('play_scoreboard.html', df=scoreboard(user)),'play_scoreboard'), to=user.id)
                    
                    messages = Message.query.filter((Message.sender_id==user.id)|(Message.recipient_id==user.id)).all()
                    if user.id == 1: 
                        messages = Message.query.filter((Message.sender_id==user.id)&(Message.recipient_id==user.id)).all()
                    if (dt.datetime.now() - messages[-1].timestamp).total_seconds() < 3:
                        turbo.push(turbo.replace(render_template('play_chatbox.html', messages=messages, user=user),'chatbox'), to=user.id)
                    
                    incoming_messages = Message.query.filter_by(recipient_id=user.id).all()
                    if (dt.datetime.now() - incoming_messages[-1].timestamp).total_seconds() < 5 and user.id != 1:
                        turbo.push(turbo.replace('<span class="chat-badge" id="notification">!<span>', 'notification'), to=user.id)
                    elif user.id != 1:
                        turbo.push(turbo.replace('<span id="notification"><span>', 'notification'), to=user.id)

                except Exception:
                    pass