from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func

db = SQLAlchemy()



class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)

    # Timing Columns
    account_creation = db.Column(db.DateTime(timezone=True), server_default=func.now())
    account_updated = db.Column(db.DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Pet Tracking Columns - not quite sure how long its gonna
    # stay like this, kinda want
    pet_name = db.Column(db.String(80))

    # Representation of User (can be more flushed out)
    def __repr__(self) -> str:
        return f"User(id={self.id!r}), Name(username={self.username!r}), Created(account_creation={self.account_creation!r}), Last Login(account_updated={self.account_updated!r})"

class Quest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(200), nullable=False)
    weight = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), default='pending')

    def __repr__(self) -> str:
        return f"Quest(id={self.id!r}, Description(description={self.description!r}), Weight(weight={self.weight!r}), Status(status={self.status!r})"

class QuestAssignment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    quest_id = db.Column(db.Integer, db.ForeignKey('quest.id'), nullable=False)

    user = db.relationship('User', backref='assignments')
    quest = db.relationship('Quest', backref='assignments')