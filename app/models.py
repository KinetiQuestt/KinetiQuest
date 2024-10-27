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

    #Pet, just one for now
    pet = db.relationship('Pet', backref='owner', uselist=False)

    
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

    def start_quest(self, user): 
        # Creating new quest for individual user
        new_quest = QuestCopy(self.id)
        new_quest.assign_quest(user)

        new_quest.save()
        
        return new_quest.id

    def finish_quest(self, quest_copy_id):
        completed_quest = next((copy for copy in self.copies if copy.id == quest_copy_id), None)

        if completed_quest is None:
            return f"QuestCopy with id {quest_copy_id} does not exist for this Quest."
        
        if completed_quest.status != 'complete':
            return f"Quest not yet marked as completed."

        completed_quest.delete()

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

    status = db.Column(db.String(20), default='unstarted', nullable=False)
    reward = db.Column(db.Integer, nullable=False)
    quest_type = db.Column(db.String(10), nullable=False)

    start_time = db.Column(db.DateTime, default=lambda: datetime.now(tz=pytz.utc))
    end_time = db.Column(db.DateTime)


    def __init__(self, quest_id, reward=0, duration_hours=2, quest_type="daily"):
        self.quest_id = quest_id
        self.reward = reward
        self.quest_type = quest_type
        # some sort of calculation on the end time of the quest
        # needed to add here too to avoid type error
        self.start_time = datetime.now()
        self.end_time = self.start_time + timedelta(hours=duration_hours)

    def assign_quest(self, user):
        self.assigned_to = user.id
        self.status = 'started'

    def save(self):
        db.session.add(self)
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

class Pet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pet_type = db.Column(db.String(50), nullable=False)
    name = db.Column(db.String(50), nullable=False, default="Spot")
    happiness = db.Column(db.Integer, nullable=False, default=100)
    hunger = db.Column(db.Integer, nullable=False, default=100)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(tz=pytz.utc))
    updated_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(tz=pytz.utc), onupdate=lambda: datetime.now(tz=pytz.utc))

    # user = db.relationship('User', backref='pet', uselist=False)

    def __repr__(self):
        return f"<Pet(id={self.id}, name={self.name}, pet_type={self.pet_type}, health={self.happiness}, hunger={self.hunger})>"

    def __init__(self, user_id, pet_type, name="Spot", hunger=100, happiness=100):
        self.user_id = user_id
        self.pet_type = pet_type
        self.name = name
        self.hunger = hunger
        self.happiness = happiness

    def feed(self, amount):
        self.hunger = max(0, self.hunger - amount)
        self.update()

    def play(self, amount):
        self.happiness = min(100, self.happiness + amount)
        self.update()

    def save(self):
        db.session.add(self)
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    def update(self):
        self.updated_at = datetime.now(tz=pytz.utc)
        db.session.commit()


# class QuestAssignment(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
#     quest_id = db.Column(db.Integer, db.ForeignKey('quest.id'), nullable=False)

#     user = db.relationship('User', backref='assignments')
#     quest = db.relationship('Quest', backref='assignments')