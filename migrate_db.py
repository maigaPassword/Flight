"""
Database Migration Script
=========================
Adds is_admin column to existing User table
"""

from app import app, db
from sqlalchemy import text

def migrate_database():
    """Add is_admin column to User table if it doesn't exist"""
    
    with app.app_context():
        print("=" * 60)
        print("DATABASE MIGRATION - Adding is_admin column")
        print("=" * 60)
        
        try:
            # Check if column exists
            with db.engine.connect() as conn:
                result = conn.execute(text("PRAGMA table_info(User)"))
                columns = [row[1] for row in result]
                
                print(f"\nCurrent User table columns: {columns}")
                
                if 'is_admin' in columns:
                    print("\n✅ is_admin column already exists!")
                else:
                    print("\n⚠️  is_admin column missing. Adding it now...")
                    
                    # Add the column with default value False
                    conn.execute(text("ALTER TABLE User ADD COLUMN is_admin BOOLEAN DEFAULT 0"))
                    conn.commit()
                    
                    print("✅ is_admin column added successfully!")
                
                # Verify the change
                result = conn.execute(text("PRAGMA table_info(User)"))
                columns = [row[1] for row in result]
                print(f"\nUpdated User table columns: {columns}")
                
                # Show all users
                result = conn.execute(text("SELECT user_id, name, email, is_admin FROM User"))
                users = result.fetchall()
                
                print(f"\n📊 Current users in database: {len(users)}")
                for user in users:
                    print(f"  - {user[1]} ({user[2]}) - Admin: {bool(user[3])}")
                
                print("\n" + "=" * 60)
                print("✅ Migration completed successfully!")
                print("=" * 60)
                
        except Exception as e:
            print(f"\n❌ Migration error: {e}")
            print("\nIf you see 'duplicate column name', the migration already ran.")
            print("You can safely ignore this error.")

if __name__ == '__main__':
    migrate_database()
