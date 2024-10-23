from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from datetime import datetime
from datetime import timedelta
import pytz

db = SQLAlchemy()



class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)

    role = db.Column(db.String(50), nullable=False, default='user') # user, admin (maybe something like worker later)

    # Timing Columns
    account_creation = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(tz=pytz.utc))
    account_updated = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(tz=pytz.utc), onupdate=lambda: datetime.now(tz=pytz.utc))

    #Quests
    quests = db.relationship('QuestCopy', backref='assigned_user', lazy='joined', foreign_keys='QuestCopy.assigned_to')


    
    # Representation of User (can be more flushed out)
    def __repr__(self) -> str:
        return f"<User(id={self.id}, username={self.username}, account_creation={self.account_creation}, account_updated={self.account_updated})>"

    def __init__(self, username, email, password_hash, role='user'):
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.role = role

    def save(self):
        db.session.add(self)
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    def update(self, username, email):
        self.username = username
        self.email = email
        db.session.commit()


class Quest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(200), nullable=False)

    copies = db.relationship('QuestCopy', backref='quest', lazy=True)

    added = db.Column(db.DateTime, default=lambda: datetime.now(tz=pytz.utc))
    

    def __repr__(self) -> str:
        return f"<Quest(id={self.id}, description={self.description})>"
    
    def __init__(self, description):
        self.description = description

    def create_copy(self):
        new_quest = QuestCopy(self.id)
        new_quest.save()
        return new_quest.id



    def save(self):
        db.session.add(self)
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

class QuestCopy(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quest_id = db.Column(db.Integer, db.ForeignKey('quest.id'), nullable=False)
    assigned_to = db.Column(db.Integer, db.ForeignKey('user.id'))

    status = db.Column(db.String(20), default='unstarted')

    start_time = db.Column(db.DateTime, default=lambda: datetime.now(tz=pytz.utc))
    end_time = db.Column(db.DateTime)


    def __init__(self, quest_id, duration_hours=2):
        self.quest_id = quest_id
        # some sort of calculation on the end time of the quest
        self.end_time = self.start_time + timedelta(hours=duration_hours)


    def save(self):
        db.session.add(self)
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

        
# class QuestAssignment(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
#     quest_id = db.Column(db.Integer, db.ForeignKey('quest.id'), nullable=False)

#     user = db.relationship('User', backref='assignments')
#     quest = db.relationship('Quest', backref='assignments')