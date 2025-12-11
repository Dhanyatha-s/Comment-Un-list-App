import os
from app import app, db
from models import User, Post, Comment

def reset_database():
    """
    This script will:
    1. Delete the existing database file
    2. Create a new database with updated schema
    3. Add a default user
    """
    with app.app_context():
        # Delete existing database file
        db_file = 'site.db'
        if os.path.exists(db_file):
            os.remove(db_file)
            print(f"Deleted existing database: {db_file}")
        
        # Create all tables with new schema
        db.create_all()
        print("Created new database with updated schema")
        
        # Add default user with email
        default_user = User(
            username='Jīvanapāṭhaḥ', 
            email='user@example.com'
        )
        db.session.add(default_user)
        db.session.commit()
        print(f"Added default user: {default_user.username}")
        
        # Verify the database
        users = User.query.all()
        print(f"\nDatabase reset successful!")
        print(f"Users in database: {len(users)}")
        for user in users:
            print(f"- {user.username} ({user.email})")

if __name__ == '__main__':
    reset_database()