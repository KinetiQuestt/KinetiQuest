from flask import Flask, flash, request, redirect, url_for, render_template, session
from hashlib import sha256
from models import db, User, Quest, Pet
from sqlalchemy import update
import re
from datetime import datetime, timedelta
import pytz
from loadquests import load_presets

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.db'
email_pattern = re.compile(r'^[^\s@]+@[^\s@]+\.[^\s@]+$')

db.init_app(app)



######################################
########## Main User Pages ###########
######################################

# global bool to check for first login
firstLogin = False

@app.route('/')
def welcome():
    # This route renders the main homepage, which is index.html
    return render_template('index.html')

@app.route('/create', methods=['GET', 'POST'])
def create():
    global firstLogin

    if request.method == 'GET':
        return render_template('create.html')
    
    # Read the form data
    petName = request.form.get('petName')
    petType = request.form.get('petSelection')

    # Fetch user_id from session
    user_id = session.get('user_id')

    if not user_id:
        flash("User session not found, please login again.", 'error')
        return redirect(url_for('login'))

    # Save pet information to the database
    new_pet = Pet(user_id=user_id, pet_type=petType, name=petName)
    db.session.add(new_pet)
    db.session.commit()

    # Save pet info in session for immediate use
    session['pet_name'] = petName
    session['pet_type'] = petType

    # Redirect to home
    firstLogin = False
    return redirect(url_for('newquests'))


@app.route('/create_quests', methods=['GET', 'POST'])
def newquests():
    if request.method == 'GET':
        return render_template('newquests.html')
    
    user_id = session.get('user_id')

    if not user_id:
        flash("User session not found, please login again.", 'error')
        return redirect(url_for('login'))
    

    fake_user = User.query.filter_by(username="fake_user").first()
    fake_quests = Quest.query.filter_by(assigned_to=fake_user.id).all()

    selections = request.form.get("clickedButtons")
    for quest in fake_quests:
        if quest.description in selections:
            copied_quest = Quest(
            description=quest.description,
            user_id=user_id,
            quest_type=quest.quest_type,
            weight=quest.reward,
            due_date=datetime.now(tz=pytz.utc) + timedelta(days=1),
            repeat_days=quest.repeat_days,
            end_of_day=quest.end_of_day,)
            copied_quest.save()
    db.session.commit()   
    
    return redirect(url_for('home'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    global firstLogin

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

    firstLogin = True

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

    # reset due dates for each quest
    for quest in user.quests:
        quest.reset_due_date()
    db.session.commit()

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

    # Redirect to home page after successful login, or pet creation page if first time
    if (firstLogin):
        return redirect(url_for('create'))
    
    return redirect(url_for('home'))

@app.route('/home', methods=['GET'])
def home():
    username = session.get('username', 'Guest')
    user_id = session.get('user_id')

    # Initialize the pet variable to None
    pet = None

    # Fetch the user's pet either from session or from the database
    pet_name = session.get('pet_name')
    pet_type = session.get('pet_type')

    pet = Pet.query.filter_by(user_id=user_id).first()
    if pet:
        pet_name = pet.name
        pet_type = pet.pet_type
        # Update the session with the pet information
        session['pet_name'] = pet_name
        session['pet_type'] = pet_type

    user_quests = Quest.query.filter_by(assigned_to=user_id).all()

    # Render the template with the correct pet values
    return render_template('home.html',
                           username=username,
                           pet_type=pet_type,
                           pet_name=pet_name,
                           pet_happiness=pet.happiness if pet else None,
                           pet_hunger=pet.hunger if pet else None,
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

@app.route('/api/feed_pet', methods=['POST'])
def feed_pet():
    food_type = request.form.get('type', 'food')  # 'food' or 'special'

    # Fetch the userss pet
    user_id = session.get('user_id')
    if not user_id:
        return {"error": "User session not found!"}, 400

    pet = Pet.query.filter_by(user_id=user_id).first()
    if not pet:
        return {"error": "Pet not found!"}, 404

    # Update the food quantity
    # use function because it was hard to track down this hardcoding here
    pet.feed(food_type)

    pet.update()  # Save changes to the database
    return {
        "success": True,
        "food_quantity": pet.food_quantity,
        "special_food_quantity": pet.special_food_quantity,
        "hunger": pet.hunger
    }, 200

@app.route('/api/get_food_quantities', methods=['GET'])
def get_food_quantities():
    user_id = session.get('user_id')
    if not user_id:
        return {"error": "Unauthorized"}, 401

    pet = Pet.query.filter_by(user_id=user_id).first()
    if not pet:
        return {"error": "Pet not found!"}, 404

    return {
        "food_quantity": pet.food_quantity,
        "special_food_quantity": pet.special_food_quantity
    }, 200

@app.route('/api/update_food_quantities', methods=['POST'])
def update_food_quantities():
    user_id = session.get('user_id')
    if not user_id:
        return {"error": "Unauthorized"}, 401

    pet = Pet.query.filter_by(user_id=user_id).first()
    if not pet:
        return {"error": "Pet not found!"}, 404

    food_quantity = request.form.get('food_quantity')
    special_food_quantity = request.form.get('special_food_quantity')

    if food_quantity is not None:
        pet.food_quantity = int(food_quantity)

    if special_food_quantity is not None:
        pet.special_food_quantity = int(special_food_quantity)

    db.session.commit()

    return {"success": "Food quantities updated successfully!"}, 200


######################################
###### API and Quest Management ######
######################################


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
    due_date = request.form.get('due_date')  # 'YYYY-MM-DD'
    due_time = request.form.get('due_time')  # 'HH:MM'
    repeat_days = request.form.getlist('repeat_days')  # ['Monday', 'Wednesday']
    end_of_day = bool(request.form.get('end_of_day'))  # bool

    if not task_description or not task_type or not user_id:
        return {"error": "Missing field in POST!"}, 400

    # convert format of data and time
    if due_date:
        due_date = datetime.strptime(due_date, '%Y-%m-%d').replace(tzinfo=pytz.utc)
    if due_time:
        due_time = datetime.strptime(due_time, '%H:%M').time()

    # Create a new quest
    new_quest = Quest(description=task_description, user_id=user_id, quest_type=task_type, 
                      due_date=due_date, repeat_days=repeat_days, due_time=due_time, end_of_day=end_of_day)
    new_quest.save()

    return {"success": "Task added successfully!", "task_id": new_quest.id}, 200

@app.route('/api/update_task', methods=['POST'])
def update_task():
    """ API request to update an existing task.
        Post:
            Int -> task_id = ID of the task to be updated
            String -> new_description = updated description of the task

        Return:
            String -> Success/Error
            Int -> Return Code
    """
    task_id = request.form.get('task_id')
    new_description = request.form.get('new_description')

    # Validate input
    if not task_id or not new_description:
        return {"error": "Missing field in POST!"}, 400

    # Find the task
    task = Quest.query.get(task_id)
    if not task:
        return {"error": "Task not found!"}, 404

    # Update the task description
    task.description = new_description
    db.session.commit()

    return {"success": "Task updated successfully!"}, 200

@app.route('/api/delete_task', methods=['POST'])
def delete_task():
    """ API request to mark a task as deleted.
        Post:
            Int -> task_id = ID of the task to be deleted

        Return:
            String -> Success/Error
            Int -> Return Code
    """
    task_id = request.form.get('task_id')

    # Validate input
    if not task_id:
        return {"error": "Missing task ID in POST!"}, 400

    # Find the task
    task = Quest.query.get(task_id)
    if not task:
        return {"error": "Task not found!"}, 404

    # Mark the task as deleted instead of actually deleting it
    try:
        db.session.delete(task)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return {"error": f"Failed to delete task. Error: {str(e)}"}, 500

    return {"success": "Task marked as deleted."}, 200

@app.route('/api/complete_task', methods=['POST'])
def complete_task():
    """ API request to mark a task as completed.
        Post:
            Int -> task_id = ID of the task to be marked as complete

        Return:
            String -> Success/Error
            Int -> Return Code
    """
    task_id = request.form.get('task_id')

    # Validate input
    if not task_id:
        app.logger.error("Task ID is missing in the request.")
        return {"error": "Missing task ID in POST!"}, 400

    try:
        task_id = int(task_id)  # Ensure an integer
    except ValueError:
        app.logger.error("Task ID must be an integer.")
        return {"error": "Invalid task ID format!"}, 400

    # Find the task
    task = Quest.query.get(task_id)
    if not task:
        app.logger.error(f"Task with ID {task_id} not found.")
        return {"error": "Task not found!"}, 404

    # Fetch user pet
    user_id = session.get('user_id')
    pet = Pet.query.filter_by(user_id=user_id).first()

    if not pet:
        app.logger.error(f"Pet for user ID {user_id} not found.")
        return {"error": "Pet not found!"}, 404

    # Mark the task as completed and update food quantity
    try:
        if task.status != 'completed':
            task.status = 'completed'
            task.end_time = datetime.now(tz=pytz.utc)

            # Update pet food quantities based on task type
            if task.quest_type == 'daily':
                pet.food_quantity += 1
            elif task.quest_type == 'weekly':
                pet.special_food_quantity += 1

            app.logger.info(f"Task with ID {task_id} status set to completed. Attempting to commit...")
            db.session.commit()
            app.logger.info(f"Task with ID {task_id} successfully committed as completed.")
    except Exception as e:
        app.logger.error(f"Error occurred while marking task as completed: {e}", exc_info=True)
        db.session.rollback()  # Rollback in case of an error
        return {"error": f"Failed to complete task. Error: {str(e)}"}, 500

    return {"success": "Task marked as completed!", "task_type": task.quest_type}, 200

@app.route('/api/completed_tasks', methods=['GET'])
def completed_tasks():
    user_id = session.get('user_id')
    if not user_id:
        return {"error": "Unauthorized"}, 401

    # Fetch all completed tasks for the user
    completed_tasks = Quest.query.filter_by(assigned_to=user_id, status='completed').all()

    tasks_data = [
        {
            "description": task.description,
            "completed_at": task.end_time.isoformat(),
            "quest_type": task.quest_type,
            "is_deleted": False
        }
        for task in completed_tasks
    ]
    return {"tasks": tasks_data}


@app.route('/logout')
def logout():
    if 'user_id' in session:
        session.clear()
        flash('You have been logged out successfully.', 'info')
    else:
        flash('You are not logged in.', 'warning')
    return redirect(url_for('login'))


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        user = User.query.filter_by(username="fake_user").first()
        if not user:
            load_presets()
    # app.app_context().push()
    

    app.run(debug=True)