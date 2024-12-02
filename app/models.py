from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from datetime import datetime
from datetime import timedelta
import pytz
from sqlalchemy.dialects.sqlite import JSON

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
    quests = db.relationship('Quest', backref='assigned_user', lazy='joined')

    #Pet, just one for now
    pet = db.relationship('Pet', back_populates='user', uselist=False)


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
    assigned_to = db.Column(db.Integer, db.ForeignKey('user.id'))

    status = db.Column(db.String(20), default='unstarted', nullable=False)
    reward = db.Column(db.Integer, nullable=False, default=0)
    quest_type = db.Column(db.String(10), nullable=False)
    is_deleted = db.Column(db.Boolean, default=False)

    start_time = db.Column(db.DateTime, default=lambda: datetime.now(tz=pytz.utc))
    end_time = db.Column(db.DateTime)

    due_date = db.Column(db.DateTime) # date due
    repeat_days = db.Column(JSON, default=[]) # format is like ['Monday', 'Tuesday'] I think but in a JSON column
    due_time = db.Column(db.Time)  # time due
    end_of_day = db.Column(db.Boolean, default=False) # for if we just want to default to end of day

    def __repr__(self) -> str:
        return f"<Quest(id={self.id}, description={self.description}, assigned_to={self.assigned_to}, status={self.status})>"

    def __init__(self, description, user_id, quest_type='daily', duration_hours=2, weight=5, due_date=None, repeat_days=None, due_time=None, end_of_day=True):
        self.description = description
        self.assigned_to = user_id
        self.quest_type = quest_type
        self.reward=weight
        self.start_time = datetime.now(tz=pytz.utc)
        self.end_time = self.start_time + timedelta(hours=duration_hours)
        self.due_date = due_date or self.start_time
        self.repeat_days = repeat_days or []
        self.due_time = due_time
        self.end_of_day = end_of_day

    def finish_quest(self):
        if self.status != 'completed':
            self.status = 'completed'
            self.end_time = datetime.now(tz=pytz.utc)
            db.session.commit()
        
    # untested
    def reset_due_date(self):
        now = datetime.now(tz=pytz.utc)
        # when past due, we just reset due data to +1 day for daily
        if self.quest_type == 'daily' and now > self.due_date:
            self.due_date = now + timedelta(days=1)
        elif self.quest_type == 'weekly' and self.repeat_days:
            # Set next due date based on current weekday
            # we default to next day being first day
            next_due_day=self.repeat_days[0]
            # but if can iterate through the repeaded day and get a later time, we do that
            for day in self.repeat_days:
                if day > now.weekday():
                        next_due_day=day

            days_until_next_due = (next_due_day - now.weekday()) % 7
            self.due_date = now + timedelta(days=days_until_next_due)

        db.session.commit()


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
    user = db.relationship('User', back_populates='pet', overlaps="owner")
    food_quantity = db.Column(db.Integer, nullable=False, default=1)
    special_food_quantity = db.Column(db.Integer, nullable=False, default=1)

    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(tz=pytz.utc))
    updated_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(tz=pytz.utc), onupdate=lambda: datetime.now(tz=pytz.utc))

    # user = db.relationship('User', backref='pet', uselist=False)

    def __repr__(self):
        return f"<Pet(id={self.id}, name={self.name}, pet_type={self.pet_type}, health={self.happiness}, hunger={self.hunger})>"

    def __init__(self, user_id, pet_type, name="Spot", hunger=100, happiness=100, food_quantity=1, special_food_quantity=1):
        self.user_id = user_id
        self.pet_type = pet_type
        self.name = name
        self.hunger = hunger
        self.happiness = happiness
        self.food_quantity = food_quantity
        self.special_food_quantity = special_food_quantity

    def feed(self, amount):
        # Decrease hunger (max 0)
        self.hunger = max(0, self.hunger - amount)

        # Decrease food quantity (max 0)
        self.food_quantity = max(0, self.food_quantity - 1)

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