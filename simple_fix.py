import sqlite3
import os

def fix_database():
    """
    Simple fix that directly modifies the SQLite database
    without importing Flask - this avoids import issues
    """
    
    db_file = 'comment.db'
    
    # Check if database exists
    if not os.path.exists(db_file):
        print(f"Database {db_file} doesn't exist yet. Run your Flask app first to create it.")
        return
    
    # Connect to database
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    try:
        # Check current user table structure
        cursor.execute("PRAGMA table_info(user)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        print("Current user table columns:", column_names)
        
        # Add missing columns if they don't exist
        changes_made = False
        
        if 'email' not in column_names:
            print("Adding email column...")
            cursor.execute("ALTER TABLE user ADD COLUMN email VARCHAR(120)")
            
            # Set default emails for existing users
            cursor.execute("SELECT id, username FROM user")
            users = cursor.fetchall()
            
            for user_id, username in users:
                email = f"{username.lower().replace(' ', '_').replace('ī', 'i').replace('ā', 'a').replace('ṭ', 't').replace('ḥ', 'h')}@example.com"
                cursor.execute("UPDATE user SET email = ? WHERE id = ?", (email, user_id))
            
            changes_made = True
            print("✓ Email column added")
        
        if 'image' not in column_names:
            print("Adding image column...")
            cursor.execute("ALTER TABLE user ADD COLUMN image VARCHAR(20) DEFAULT 'default.jpg'")
            changes_made = True
            print("✓ Image column added")
        
        if changes_made:
            conn.commit()
            print("\n✅ Database updated successfully!")
        else:
            print("\n✅ Database already has all required columns!")
        
        # Show final structure
        cursor.execute("PRAGMA table_info(user)")
        columns = cursor.fetchall()
        print("\nFinal user table structure:")
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")
        
        # Show users
        cursor.execute("SELECT id, username, email FROM user")
        users = cursor.fetchall()
        print(f"\nUsers in database ({len(users)}):")
        for user in users:
            print(f"  - ID: {user[0]}, Username: {user[1]}, Email: {user[2]}")
    
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    
    finally:
        conn.close()

def delete_and_recreate():
    """
    Nuclear option: delete the database entirely
    Your Flask app will recreate it when you restart
    """
    db_file = 'site.db'
    
    if os.path.exists(db_file):
        confirm = input(f"Are you sure you want to DELETE {db_file}? This will remove ALL data! (yes/no): ")
        if confirm.lower() == 'yes':
            os.remove(db_file)
            print(f"✅ Deleted {db_file}")
            print("Now restart your Flask app - it will create a new database with the correct schema.")
        else:
            print("Operation cancelled.")
    else:
        print(f"Database {db_file} doesn't exist.")

if __name__ == '__main__':
    print("Database Fix Options:")
    print("1. Fix existing database (add missing columns)")
    print("2. Delete database and start fresh")
    
    choice = input("\nEnter choice (1 or 2): ").strip()
    
    if choice == '1':
        fix_database()
    elif choice == '2':
        delete_and_recreate()
    else:
        print("Invalid choice. Please run again and choose 1 or 2.")