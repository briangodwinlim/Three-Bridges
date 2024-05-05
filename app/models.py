from app import db, login_manager
from flask_login import UserMixin


class Score(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    AA = db.Column(db.Float, nullable=False); AB = db.Column(db.Float, nullable=False); AC = db.Column(db.Float, nullable=False)
    BA = db.Column(db.Float, nullable=False); BB = db.Column(db.Float, nullable=False); BC = db.Column(db.Float, nullable=False)
    CA = db.Column(db.Float, nullable=False); CB = db.Column(db.Float, nullable=False); CC = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return f"""
            {self.AA} {self.AB} {self.AC}
            {self.BA} {self.BB} {self.BC}
            {self.CA} {self.CB} {self.CC}
        """


class Player(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    reset_game = db.Column(db.Boolean(), nullable=False, default=False)
    
    record = db.relationship('Record', backref='player', lazy=True)
    opponent = db.relationship('Opponent', backref='player', lazy=True)
    messages_sent = db.relationship('Message', foreign_keys='Message.sender_id', backref='sender', lazy=True)
    messages_received = db.relationship('Message', foreign_keys='Message.recipient_id', backref='recipient', lazy=True)

    def __repr__(self):
        return f"Player({self.username})"


@login_manager.user_loader
def load_user(user_id):
    return Player.query.get(int(user_id))


class Record(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    bridge = db.Column(db.String(20), nullable=False)
    player_id = db.Column(db.Integer, db.ForeignKey('player.id'), nullable=False)

    def __repr__(self):
        return f"Record({Player.query.get(self.player_id).username}, {self.bridge})"


class Opponent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    opponent_id = db.Column(db.Integer, nullable=False)
    player_id = db.Column(db.Integer, db.ForeignKey('player.id'), nullable=False)

    def __repr__(self):
        return f"{Player.query.get(self.player_id).username} - {Player.query.get(self.opponent_id).username}"


class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.String(150), nullable=False)
    timestamp = db.Column(db.DateTime, index=True, nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('player.id'), nullable=False)
    recipient_id = db.Column(db.Integer, db.ForeignKey('player.id'), nullable=False)

    def __repr__(self):
        return f"""
        From {Player.query.get(self.sender_id).username} to {Player.query.get(self.recipient_id).username}:
            {self.body}
        """
