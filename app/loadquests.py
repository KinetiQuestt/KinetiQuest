from flask import Flask, flash, request, redirect, url_for, render_template, session
from hashlib import sha256
from models import db, User, Quest, Pet
from sqlalchemy import update
import re
from datetime import datetime, timedelta
import pytz

def load_presets():
    fake_username = "fake_user"
    fake_email = "fake_user@example.com"
    fake_pass = "password123"
    fake_password = sha256(fake_pass.encode()).hexdigest()  
    fake_role = "user"

    
    fake_user = User(username=fake_username, email=fake_email, password_hash=fake_password, role=fake_role)
    fake_user.save()

    
    quest1_description = "Drink 4 glasses of water"
    quest1 = Quest(
        description=quest1_description,
        user_id=fake_user.id,
        quest_type="daily",
        duration_hours=24,  
        weight=5,  
        due_date=datetime.now(tz=pytz.utc) + timedelta(days=1),  
        repeat_days=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
        end_of_day=True  
    )
    quest1.save()

    
    quest2_description = "Do 10 pushups"
    quest2 = Quest(
        description=quest2_description,
        user_id=fake_user.id,
        quest_type="daily",
        duration_hours=24,  
        weight=5,  
        due_date=datetime.now(tz=pytz.utc) + timedelta(days=1),  
        repeat_days=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
        end_of_day=True  
    )
    quest2.save()

    
    quest3_description = "Clean desk"
    quest3 = Quest(
        description=quest3_description,
        user_id=fake_user.id,
        quest_type="daily",
        duration_hours=24,  
        weight=5,  
        due_date=datetime.now(tz=pytz.utc) + timedelta(days=1),  
        repeat_days=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
        end_of_day=True  
    )
    quest3.save()

    
    quest4_description = "Take 5 minutes without devices"
    quest4 = Quest(
        description=quest4_description,
        user_id=fake_user.id,
        quest_type="daily",
        duration_hours=24,  
        weight=5,  
        due_date=datetime.now(tz=pytz.utc) + timedelta(days=1),  
        repeat_days=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
        end_of_day=True  
    )
    quest4.save()

    
    quest5_description = "Empty sink of dishes"
    quest5 = Quest(
        description=quest5_description,
        user_id=fake_user.id,
        quest_type="daily",
        duration_hours=24,  
        weight=5,  
        due_date=datetime.now(tz=pytz.utc) + timedelta(days=1),  
        repeat_days=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
        end_of_day=True  
    )
    quest5.save()

    

    return fake_user

if __name__ == "__main__":
    load_presets()