import numpy as np
import pandas as pd
import datetime as dt
from flask_login.utils import logout_user
from flask_login import login_user, current_user, login_required
from flask import render_template, url_for, flash, redirect, request, abort, jsonify

from app import app, db, bcrypt, VERSION, MAX_PLAYERS
from app.models import Score, Player, Record, Opponent, Message
from app.forms import ScoreForm, OpponentForm, RegistrationForm, LoginForm, PlayForm, MessageForm


@app.route('/log')
def log():
    return render_template('log.html', title='Log')


@app.route('/')
@app.route('/home')
def home():
    return render_template('home.html', version_number=VERSION)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    form = RegistrationForm()
    if form.validate_on_submit() and len(Player.query.all()) < MAX_PLAYERS:
        # Add player
        password = form.password.data if form.password.data else 'password'
        password = bcrypt.generate_password_hash(password).decode('utf-8')
        user = Player(username=form.username.data.lower(), password=password)
        db.session.add(user)
        db.session.commit()

        # Assign opponent
        if len(Player.query.all()) == 1: # Admin
            opponent = Opponent(opponent_id=user.id, player=user)
        elif len(Player.query.all()) % 2 == 0: # Odd player
            opponent = Opponent(opponent_id=user.id, player=user)
        elif len(Player.query.all()) % 2 == 1: # Even player
            opponent_ = Opponent.query.all()[-1]
            opponent_.opponent_id = user.id
            opponent = Opponent(opponent_id=opponent_.player_id, player=user)
        db.session.add(opponent)
        db.session.commit()

        # Login player
        login_user(user, remember=False)
        flash(f'Account created. Welcome {user.username}!', 'success')
        return redirect(url_for('home'))

    elif len(Player.query.all()) >= MAX_PLAYERS:
        flash('Maximum players reached. Please try again later.', 'danger')
        return redirect(url_for('home'))
    
    return render_template('register.html', title='Register', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = Player.query.filter_by(username=form.username.data.lower()).first()
        password = form.password.data if form.password.data else 'password'
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            flash(f'Welcome {user.username}!', 'success')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Log in failed', 'danger')

    return render_template('login.html', title='Login', form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))


def my_opponent(user):
    opponent = Opponent.query.filter_by(player=user).first().opponent_id
    return Player.query.filter_by(id=opponent).first()

def scoreboard(user):
    opponent = my_opponent(user)
    opponent_username = opponent.username + (' (Opponent)' if user.username == opponent.username else '')
    df = pd.DataFrame()
    bridge_dict = dict(PlayForm.bridge.kwargs['choices'] + [('', '')])
    my_record = Record.query.filter_by(player=user).all()
    op_record = Record.query.filter_by(player=opponent).all()
    score = Score.query.first()

    for i in range(10):
        my_move = my_record[i].bridge if i < len(my_record) else ''
        op_move = ''
        my_score = np.nan
        op_score = np.nan
        if i < len(op_record) and i < len(my_record):
            op_move = op_record[i].bridge
            my_score = getattr(score, my_move + op_move)
            op_score = getattr(score, op_move + my_move)

        my_move = bridge_dict[my_move]
        op_move = bridge_dict[op_move]

        df = pd.concat([df, pd.DataFrame([[i + 1, my_move, op_move, my_score, op_score]], 
                                         columns=['Round', user.username, opponent_username, 'Your Score', f'{opponent_username} Score'])
                        ]).reset_index(drop=True)
            
    df = pd.concat([df, pd.DataFrame([['Total', '', '', df['Your Score'].dropna().sum(), df[f'{opponent_username} Score'].dropna().sum()]], 
                                     columns=['Round', user.username, opponent_username, 'Your Score', f'{opponent_username} Score'])
                    ]).reset_index(drop=True).fillna('')
    return df


@app.route('/fetch_summary')
@login_required
def fetch_summary():
    if current_user.id != 1:
        abort(403)
        
    score_df = pd.DataFrame([i for i in range(1, 11)] + ['Total'], columns=['Round'])
    for user in Player.query.all():
        score_df = pd.concat([score_df, scoreboard(user)[['Your Score']].rename({'Your Score': user.username}, axis=1)], axis=1)
    score_df = score_df.to_json(orient='records')
    return jsonify({'score_df': score_df})


@app.route('/summary')
@login_required
def summary():
    if current_user.id != 1:
        abort(403)
    return render_template('summary.html', title='Summary')


@app.route('/match', methods=['GET', 'POST'])
@login_required
def match():
    if current_user.id != 1:
        abort(403)

    form = OpponentForm()
    for player_form in form.player:
        player_form.choices = [(str(player.id), player.username) for player in Player.query.all()]

    if form.validate_on_submit(): 
        for idx, player_form in enumerate(form.player):
            player = Player.query.all()[idx]
            opponent = Opponent.query.filter_by(player=player).first()
            opponent.opponent_id = int(player_form.data)
            db.session.commit()
        
        for player in Player.query.all():
            if player == current_user: 
                continue
            
            my_opponent_id = Opponent.query.filter_by(player=player).first().opponent_id
            im_opponent = Opponent.query.filter_by(opponent_id=player.id).filter(Opponent.player != current_user).all()
            if len(im_opponent) != 1 or my_opponent_id != im_opponent[0].player_id or my_opponent_id == 1:
                flash('Please check match up', 'danger')
                break

        flash('Update successful', 'success')
        return redirect(url_for('match'))
    
    if request.method == 'GET':
        form.player.entries = []
        for player in Player.query.all():
            form.player.append_entry()
            form.player[-1].label = player.username
            form.player[-1].choices = [(str(player_.id), player_.username) for player_ in Player.query.all()]
            form.player[-1].data = str(player.opponent[0].opponent_id)

    return render_template('match.html', title='Match', form=form)


@app.route('/score', methods=['GET', 'POST'])
@login_required
def score():
    if current_user.id != 1:
        abort(403)

    bridge_dict = dict(PlayForm.bridge.kwargs['choices'] + [('', '')])
    score = Score.query.get(1)
    form = ScoreForm()
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
                if opponent.player == current_user: 
                    opponent.opponent_id = current_user.id
                    continue
                db.session.delete(opponent)

            for user in Player.query.all():
                if user == current_user: 
                    continue
                db.session.delete(user)
        
        if form.reset.data == 'score':
            score = Score.query.first()
            score.AA = 1; score.AB = 0; score.AC = 0
            score.BA = 0; score.BB = 1; score.BC = 0
            score.CA = 0; score.CB = 0; score.CC = 1
        
        db.session.commit()

        flash('Update successful', 'success')
        return redirect(url_for('score'))

    if request.method == 'GET':
        form.AA.data = score.AA; form.AB.data = score.AB; form.AC.data = score.AC 
        form.BA.data = score.BA; form.BB.data = score.BB; form.BC.data = score.BC 
        form.CA.data = score.CA; form.CB.data = score.CB; form.CC.data = score.CC 
    
    return render_template('score.html', title='Score', form=form, bridge_dict=bridge_dict)


@app.route('/fetch_chat')
@login_required
def fetch_chat():
    messages = Message.query.filter((Message.sender_id == current_user.id) | (Message.recipient_id == current_user.id)).all()
    if current_user.id == 1:
        messages = Message.query.filter((Message.sender_id == current_user.id) & (Message.recipient_id == current_user.id)).all()
    messages = [[message.body, message.sender_id == current_user.id, message.sender_id == 1] for message in messages]
    
    notify = False
    incoming_messages = Message.query.filter_by(recipient_id=current_user.id).all()
    if len(incoming_messages) > 0:
        notify = (dt.datetime.now() - incoming_messages[-1].timestamp).total_seconds() < 10 and current_user.id != 1
    
    recipient = 'ALL PLAYERS' if current_user.id == 1 else my_opponent(current_user).username
    return jsonify({'messages': messages, 'notify': notify, 'recipient': recipient})


@app.route('/fetch_scoreboard')
@login_required
def fetch_scoreboard():
    scoreboard_df = scoreboard(current_user)
    
    message = ''
    if scoreboard_df.iloc[-2, 1] != '' and scoreboard_df.iloc[-2, 2] == '':
        message = 'Please wait for the game to finish'
    elif scoreboard_df.iloc[-1, 3] == scoreboard_df.iloc[-1, 4] and scoreboard_df.iloc[-2, 1] != '':
        message = 'Game Over. Tie!'
    elif scoreboard_df.iloc[-2, 1] != '':
        winner = current_user.username if scoreboard_df.iloc[-1, 3] > scoreboard_df.iloc[-1, 4] else my_opponent(current_user).username
        message = f'Game Over. Winner {winner}!'
    
    return jsonify({'scoreboard': scoreboard_df.to_json(orient='records'), 'message': message})


@app.route('/play', methods=['GET', 'POST'])
@login_required
def play():
    play_form = PlayForm()
    disable_play_form = len(Record.query.filter_by(player=current_user).all()) == 10
    if play_form.validate_on_submit():
        record = Record(bridge=play_form.bridge.data, player=current_user)
        db.session.add(record)
        db.session.commit()
        return redirect(url_for('play'))
    
    message_form = MessageForm()
    if message_form.validate_on_submit():
        recipients = [my_opponent(current_user)] if current_user.id != 1 else [player for player in Player.query.all()]
        for recipient in recipients:
            message = Message(sender=current_user, recipient=recipient, body=message_form.message.data, timestamp=dt.datetime.now())
            db.session.add(message)
        db.session.commit()
        return redirect(url_for('play'))
    
    return render_template('play.html', title='Play', play_form=play_form, disable_play_form=disable_play_form,
                           score=Score.query.first(), bridge_dict=dict(PlayForm.bridge.kwargs['choices'] + [('', '')]),
                           message_form=message_form)


@app.route('/reset_game/<int:player_id>', methods=['POST'])
@login_required
def reset_game(player_id):
    if current_user.id != player_id:
        abort(403)
    
    player = Player.query.get(current_user.id)
    player.reset_game = True
    db.session.commit()

    opponent = my_opponent(current_user)
    if opponent.reset_game:
        for record in Record.query.filter_by(player=player).all():
            db.session.delete(record)
        for record in Record.query.filter_by(player=opponent).all():
            db.session.delete(record)
        player.reset_game = False
        opponent.reset_game = False
        db.session.commit()
        flash('New Game', 'success')
    
    else:
        flash('Please wait for your opponent to reset the game', 'info')
        message = Message(sender=current_user, recipient=opponent, body='INFO: Reset Game', timestamp=dt.datetime.now())
        db.session.add(message)
        db.session.commit()
        
    return redirect(url_for('play'))
