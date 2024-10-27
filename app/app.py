from flask import Flask, flash, request, redirect, url_for, render_template, session
from hashlib import sha256
from models import db, User, Quest, QuestCopy, Pet
from sqlalchemy import update
import re

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.db'
email_pattern = re.compile(r'^[^\s@]+@[^\s@]+\.[^\s@]+$')

db.init_app(app)



######################################
########## Main User Pages ###########
######################################

@app.route('/')
def welcome():
    # This route renders the main homepage, which is index.html
    return render_template('index.html')



@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')

    # Read the form data
    username = request.form.get('username')
    password = request.form.get('password')
    email = request.form.get('email')

    # Validate input and check for existing users
    if not username:
        flash('Please enter a valid username.', 'error')
        return render_template('register.html')

    email_pattern = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
    if not email or not re.match(email_pattern, email):
        flash('Please enter a valid email.', 'error')
        return render_template('register.html')

    if password:
        password_hash = sha256(password.encode()).hexdigest()
    else:
        flash('Password hashing failed.', 'error')
        return render_template('register.html')

    if User.query.filter_by(username=username).first():
        flash('Username already exists.', 'error')
        return render_template('register.html')

    if User.query.filter_by(email=email).first():
        flash('Email already registered.', 'error')
        return render_template('register.html')

    new_user = User(username=username, password_hash=password_hash, email=email)
    new_user.save()

    # Create pet, most things just default for now, can apadt as needed
    new_pet = Pet(user_id=new_user.id, pet_type="dog") 
    new_pet.save()

    # Flash a success message and redirect to login page
    flash('Registration successful! Please login.', 'success')
    return redirect(url_for('login'))



@app.route('/login', methods=['GET', 'POST'])
def login():
    """ Authenticates a user with username and password.

        Post:
            String -> username = username to authenticate
            String -> password = raw password to compare with the stored hash

        Returns:
            Redirect -> Success/Error
    """

    if request.method == 'GET':
        return render_template('login.html')

    # Read the username and password from the POST form
    username = request.form.get('username')
    password = request.form.get('password')

    # Validate the input
    if not username or not password:
        flash('Please enter both username and password!', 'error')
        return render_template('login.html')

    # Fetch the user from the database
    user = User.query.filter_by(username=username).first()

    # Check if user exists
    if not user:
        flash('User does not exist!', 'error')  # Show error if the user does not exist
        return render_template('login.html')

    # Hash the input password to compare with the stored password
    hashed_password = sha256(password.encode()).hexdigest()

    # Check if the hashed password matches the stored hashed password
    if user.password_hash != hashed_password:
        flash('Incorrect username or password!', 'error')  # Show error if the password is incorrect
        return render_template('login.html')

    # Clear any previous session data before setting new session data
    session.clear()

    # Set session data for the logged-in user
    session['user_id'] = user.id
    session['username'] = user.username  # Set the username in session

    db.session.execute(
        update(User).where(User.id == user.id)
    )

    if user.pet:
        session['pet_type'] = user.pet.pet_type
        session['pet_happiness'] = user.pet.happiness
        session['pet_hunger'] = user.pet.hunger

    # Redirect to home page after successful login
    return redirect(url_for('home'))



@app.route('/home', methods=['GET'])
def home():
    username = session.get('username', 'Guest')
    user_id = session.get('user_id')
    pet = Pet.query.filter_by(user_id=user_id).first()
    user_quests = QuestCopy.query.filter_by(assigned_to=user_id).all()

    return render_template('home.html',
                           username=username,
                           pet_type=pet.pet_type,
                           pet_happiness=pet.happiness,
                           pet_hunger=pet.hunger,
                           user_quests=user_quests)


@app.route('/user_quests/')
def user_quests():
    username = session.get('username', None)

    if not username:
        return redirect(url_for('login'))

    user = User.query.filter_by(username=username).first()
    if not user:
        return "User not found."
    
    # Query the user's quest assignments
    # assignments = QuestAssignment.query.filter_by(user_id=user.id).all()
    
    # Get the quests through the assignments
    # quests = [assignment.quest.description for assignment in assignments]
    
    return f"quests for {username}: " #+ ', '.join(quests)


######################################
###### API and Quest Management ######
######################################

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
    if not description or not weight:
        return {"Error" : "Missing field in POST!"}, 400
    
    # Create and store the new quest
    new_quest = Quest(description=description, weight=weight)
    db.session.add(new_quest)
    db.session.commit()
    
    return {"success" : "Quest created successfully!", "quest": new_quest.__repr__()}, 200

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

@app.route('/api/add_task', methods=['POST'])
def add_task():
    """ API request to add a quest for the logged-in user.
        Post:
            String -> task_description = description of the task
            String -> task_type = type of task ('daily' or 'weekly')

        Return:
            String -> Success/Error
            Int -> Return Code
    """
    task_description = request.form.get('task_description')
    task_type = request.form.get('task_type')
    user_id = session.get('user_id')

    if not task_description or not task_type or not user_id:
        return {"error": "Missing field in POST!"}, 400

    # Create a new quest
    new_quest = Quest(description=task_description)
    new_quest.save()

    # Create a quest copy for the user
    quest_copy = QuestCopy(quest_id=new_quest.id, quest_type=task_type)
    quest_copy.assign_quest(User.query.get(user_id))
    quest_copy.save()

    return {"success": "Task added successfully!"}, 200


@app.route('/logout')
def logout():
    session.clear()  # Clear session on logout
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))



if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    # app.app_context().push()

    app.run(debug=True)