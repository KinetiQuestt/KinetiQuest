"""from sqlalchemy.orm import Mapped, mapped_column, scoped_session, sessionmaker
from flask import Flask, request, jsonify, url_for, redirect, g, session, render_template_string
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from flask_github import GitHub
from datetime import datetime """

from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os



app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///central-user-storage.db'

db = SQLAlchemy(app)



class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    db_path = db.Column(db.String(120), nullable=False)

with app.app_context():
    db.create_all()

def create_user_db(username):
    """ On account creation, creates a new database to store personalized user information.

        Args:
            String -> Username
        
        Returns:
            String -> User's Database location
    """

    # Checks if server has folder for user databases
    if not os.path.exists('user_dbs'):
        os.makedirs('user_dbs')
    
    # Creates formatted string for new users database
    user_db_path = f'user_dbs/{username}.db'

    engine = create_engine(f'sqlite:///{user_db_path}')

    Base = db.Model.metadata
    
    class UserData(Base):
        __tablename__ = 'user_data'
        id = db.Column(db.Integer, primary_key=True)
        data = db.Column(db.String(80)) # Additional columns to be added as we further define a 'User'
    
    # Create the table within the user's own database
    Base.create_all(bind=engine)

    return user_db_path

@app.route('/register', methods=['POST'])
def register():
    """ Registers a user with a unique username and hashed password

        Returns:
            Bool -> Creation Successful
            String -> Corresponding message    
    """

    # Reads from the POSTed json form the username and password
    username = request.form.get('username')
    if not username:
        return {"error": "Not valid username!"}, 400
    
    password = request.form.get('hash')
    if not password:
        return {"error": "Not valid hash!"}, 400

     # Check if user already exists, returns False and message 
    if User.query.filter_by(username=username).first():
        return {"error": "User already exists!"}, 400
    
    user_db_path = create_user_db(username)

    new_user = User(username=username, password_hash=password, db_path=user_db_path)
    db.session.add(new_user)
    db.session.commit()

    return {"success": f"User {username} registered with database at {user_db_path}"}, 200

def main():
    return 0

if __name__ == "__main__":
    app.app_context().push()

    app.run(debug=True)