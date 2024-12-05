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

    def determine_streak(self) -> int:
        streak = 0
        for quest in self.quests:
            streak = streak + (quest.reward * quest.streak)
        return streak

    # call this once during each login
    def update_pet_status_on_login(self):
        # not pet confirmation but shouldn't be needed
        if not self.pet:
            return  

        # Get the current time and the last login time
        now = datetime.now(tz=pytz.utc)
        last_login = self.account_updated

        # timezones again
        if last_login and last_login.tzinfo is None:
            last_login = last_login.replace(tzinfo=pytz.utc)

        # time difference in hours
        time_diff = (now - last_login).total_seconds() / 3600 # seconds to hours
        # print(time_diff)

        # changes happiness and hunger decrease rate based on streaks of quests
        # currently super high for demonstration purposes
        happiness_decrease = map_to_range(self.determine_streak(), 25, 500, 1500, 150) * time_diff
        hunger_decrease = map_to_range(self.determine_streak(), 25, 500, 3000, 300) * time_diff

        # print(self.pet.happiness)
        self.pet.happiness = max(0, self.pet.happiness - int(happiness_decrease))
        # print(self.pet.happiness)
        # print(self.pet.hunger)
        self.pet.hunger = max(0, self.pet.hunger - int(hunger_decrease))
        # print(self.pet.hunger)

        # now set acoount updated to now
        self.account_updated = now
        

        db.session.commit()

    

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

    status = db.Column(db.String(20), default='uncompleted', nullable=False)
    reward = db.Column(db.Integer, nullable=False, default=0)
    quest_type = db.Column(db.String(10), nullable=False)
    is_deleted = db.Column(db.Boolean, default=False)
    repeat = db.Column(db.Boolean, default=False)
    streak = db.Column(db.Integer, default=0)

    start_time = db.Column(db.DateTime, default=lambda: datetime.now(tz=pytz.utc))
    end_time = db.Column(db.DateTime)

    due_date = db.Column(db.DateTime(timezone=True)) # date due
    repeat_days = db.Column(JSON, default=[]) # format is like ['Monday', 'Tuesday'] I think but in a JSON column
    due_time = db.Column(db.Time)  # time due
    end_of_day = db.Column(db.Boolean, default=False) # for if we just want to default to end of day

    def __repr__(self) -> str:
        return f"<Quest(id={self.id}, description={self.description}, assigned_to={self.assigned_to}, status={self.status})>"


    # helper to go from day to int for easy of use
    def day_to_int(self, day):
        days_map = {
            'Monday': 0,
            'Tuesday': 1,
            'Wednesday': 2,
            'Thursday': 3,
            'Friday': 4,
            'Saturday': 5,
            'Sunday': 6
        }
        return days_map.get(day, -1)
    

    def __init__(self, description, user_id, quest_type='daily', duration_hours=24, weight=5, due_date=None, repeat_days=None, due_time=None, end_of_day=True, repeat=False):
        self.description = description
        self.assigned_to = user_id
        self.quest_type = quest_type
        self.start_time = datetime.now(tz=pytz.utc)
        self.end_time = self.start_time + timedelta(hours=duration_hours)
        self.due_date = due_date or self.start_time
        self.due_time = due_time
        self.end_of_day = end_of_day
        self.repeat = repeat


        # print("Added task type")
        # print(self.quest_type)
        self.repeat_days = []
        for day in repeat_days:
            self.repeat_days.append(self.day_to_int(day))

        if (len(repeat_days) == 7) and (self.quest_type == 'specific'):
            self.quest_type = 'daily'
        elif (self.quest_type == 'specific') and (len(repeat_days) == 0):
            self.quest_type = 'none'
        elif (self.quest_type == 'specific') and (len(repeat_days) == 1):
            self.quest_type = 'weekly'
        elif (self.quest_type == 'weekly') and (len(repeat_days) == 0):
            self.repeat_days = [datetime.now().weekday()]

        if self.quest_type == 'none':
            self.reward = 1
        elif self.quest_type == 'daily':
            self.reward = 6
        elif self.quest_type == 'specific':
            self.reward = 9
        elif self.quest_type == 'weekly':
            self.reward = 12
        else:
            self.reward = weight


        if due_date and due_time:
            pre_timezone_date = datetime.combine(due_date.date(), due_time)
            self.due_date = pre_timezone_date.astimezone(pytz.utc)
        elif due_date:
            # Default to end of day if no time is provided
            self.due_date = due_date.replace(hour=23, minute=59, second=59)
            # print(self.due_date)
        else:
            # If no due_date is provided, default to 24 hours from now
            self.due_date = datetime.now(tz=pytz.utc) + timedelta(days=1)



    def finish_quest(self):
        if self.status != 'completed':
            self.status = 'completed'
            self.end_time = datetime.now(tz=pytz.utc)
            db.session.commit()
        
    
    

    # untested
    def reset_due_date(self):
        

        now = datetime.now(tz=pytz.utc)
        due_date = self.due_date.replace(tzinfo=pytz.utc)
        
        # make sure due_date is timezone-aware
        if due_date and due_date.tzinfo is None:
            self.due_date = self.due_date.replace(tzinfo=pytz.utc)
            

        # when past due, we just reset due data to +1 day for daily
        if self.quest_type == 'daily' and now > due_date:

            end_of_due_day = due_date + timedelta(days=1)
            if now < end_of_due_day:
                self.streak = self.streak + 1
            else:
                self.streak = 0
            
            self.due_date = now + timedelta(days=1)
            # remember to actually update status
            self.status = 'uncompleted'
            


        elif self.quest_type == 'weekly' and now > due_date:
            self.status = 'uncompleted'
            
            end_of_due_week = due_date + timedelta(days=7)
            if now < end_of_due_week:
                self.streak = self.streak + 1
            else:
                self.streak = 0

            next_due_day = self.repeat_days[0]

            days_until_next_due = (next_due_day - now.weekday()) % 7
            if days_until_next_due == 0:
                days_until_next_due = 7
            self.due_date = now + timedelta(days=days_until_next_due)
            

        elif self.quest_type == 'specific' and now > due_date:
            # remember to actually update status
            self.status = 'uncompleted'

            # convert days to ints
            numeric_repeat_days = sorted(self.repeat_days)

            if not numeric_repeat_days:
                # should never get here
                return

            # Set next due date based on current weekday
            # we default to next day being first day
            next_due_day = self.repeat_days[0]

            # but if can iterate through the repeaded day and get a later time, we do that
            for day in self.repeat_days:
                # now.weekday() should be int in same format as the helper function dict
                if day > now.weekday():
                    next_due_day=day
                    # break bc we sorted
                    break

            days_until_next_due = (next_due_day - now.weekday()) % 7
            if days_until_next_due == 0:
                days_until_next_due = 7

            end_of_due_time = due_date + timedelta(days=days_until_next_due)
            if due_date < end_of_due_time:
                self.streak = self.streak + 1
            else:
                self.streak = 0
            self.due_date = now + timedelta(days=days_until_next_due)

        if not self.repeat and now > due_date:
            self.status = 'inactive'

        # else:
            # self.due_date = now + timedelta(days=1)


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

    # default to 80
    def __init__(self, user_id, pet_type, name="Spot", hunger=80, happiness=80, food_quantity=1, special_food_quantity=1):
        self.user_id = user_id
        self.pet_type = pet_type
        self.name = name
        self.hunger = hunger
        self.happiness = happiness
        self.food_quantity = food_quantity
        self.special_food_quantity = special_food_quantity

    def feed(self, food_type):
        # increase hunger (max 0)
        # counter intuitive but looks better if not hungry is full bar
        if food_type == 'food' and self.food_quantity > 0:
            self.food_quantity -= 1
            self.hunger = min(100, self.hunger + 10)
        elif food_type == 'special' and self.special_food_quantity > 0:
            self.special_food_quantity -= 1
            self.hunger = min(100, self.hunger + 20)

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


def map_to_range(value, from_min, from_max, to_min, to_max):
    if from_min == from_max:
        raise ValueError("Source range cannot have zero length.")
    
    if value > from_max:
        value = from_max
    if value < from_min:
        value = from_min
    
    # Linear mapping formula
    return int(to_min + (value - from_min) * (to_max - to_min) / (from_max - from_min))