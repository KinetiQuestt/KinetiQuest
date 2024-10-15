from flask import Flask, request, redirect, url_for, make_response
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from hashlib import sha256


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.db'

db = SQLAlchemy(app)



class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)

class Quest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(200), nullable=False)
    weight = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), default='pending')

class QuestAssignment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    quest_id = db.Column(db.Integer, db.ForeignKey('quest.id'), nullable=False)
    
    user = db.relationship('User', backref='assignments')
    quest = db.relationship('Quest', backref='assignments')

with app.app_context():
    db.create_all()



@app.route('/register', methods=['POST'])
def register():
    """ Registers a user with a unique username and hashed password
        
        Post:
            String -> username = unique username
            String -> password = raw password to be hashed then stored

        Returns:
            String -> Success/Error   
            Bool -> Respond Code
             
    """

    # Reads from the POSTed json form the username and password
    username = request.form.get('username')
    if not username:
        return {"error": "Not valid username!"}, 400
    
    password = sha256((request.form.get('password')).encode()).hexdigest()
    
    if not password:
        return {"error": "Not valid hash!"}, 400

    # Check if user already exists, returns False and message 
    if User.query.filter_by(username=username).first():
        return {"error": "User already exists!"}, 400
    
    
    new_user = User(username=username, password_hash=password)
    db.session.add(new_user)
    db.session.commit()

    
    response = make_response(redirect(url_for('home')))

    response.set_cookie('logged_in', 1)
    response.set_cookie('username', username)

    return response

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Will display Login Page on a GET request or"""
    if request.method == 'GET':
        return "Please login: "
    
    # Check if login is successful

    
    username = request.form.get('username')
    if not username:
        return {"error": "Not valid username!"}, 400

    response = make_response(redirect(url_for('home')))
    response.set_cookie('logged_in', 1)
    response.set_cookie('username', username)

    return response


@app.route('/home', methods=['GET'])
def home():
    logged_in = request.cookies.get('logged_in')
    

    if logged_in != 1:
        return redirect(url_for('login'))
    username = request.cookies.get('username')
    return f"Welcome {username}!"

@app.route('/api/create_quest', methods=['POST'])
def create_quest():
    """ API request to create a quest.

        Post:
            String -> description = description of quest
            Int -> weight = value of quest

        Return:
            String -> Success/Error
            Int -> Return Code
    """

    # Check for correct permissions for call
    description = request.form.get('description')
    weight = request.form.get('weight')
    
    # Create and store the new quest
    new_quest = Quest(description=description, weight=weight)
    db.session.add(new_quest)
    db.session.commit()
    
    return {"success" : "Quest created successfully!"}, 200

@app.route('/api/assign_quest', methods=['POST'])
def assign_quest():
    """ API request to link a quest to a user.

        Post:
            String -> username = username
            Int -> quest_id = quest_id

        Return:
            String -> Success/Error
            Int -> Return Code
    """
    username = request.form.get('username')
    quest_id = request.form.get('quest_id')
    
    # Find the user and quest
    user = User.query.filter_by(username=username).first()
    quest = Quest.query.get(quest_id)
    
    if not user or not quest:
        return {"error" :f"User or quest not found!"}, 400
    
    # Create a new QuestAssignment to link the user and the quest
    assignment = QuestAssignment(user_id=user.id, quest_id=quest.id)
    db.session.add(assignment)
    db.session.commit()
    
    return {"success" :f"Quest '{quest.description}' assigned to user {user.username}."}, 200

@app.route('/user_quests/<username>')
def user_quests(username):
    user = User.query.filter_by(username=username).first()
    if not user:
        return "User not found."
    
    # Query the user's quest assignments
    assignments = QuestAssignment.query.filter_by(user_id=user.id).all()
    
    # Get the quests through the assignments
    quests = [assignment.quest.description for assignment in assignments]
    
    return f"quests for {username}: " + ', '.join(quests)


def main():
    return 0

if __name__ == "__main__":
    app.app_context().push()

    app.run(debug=True)