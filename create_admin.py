"""
Create Admin User Script
========================
Run this script to create an admin user for the Skyela admin dashboard.

Usage:
    python create_admin.py
"""

from app import app, db
from models import User
from werkzeug.security import generate_password_hash

def create_admin_user():
    """Create an admin user for the dashboard"""
    
    with app.app_context():
        print("=" * 50)
        print("Skyela Admin User Creation")
        print("=" * 50)
        
        # Check if admin already exists
        existing_admin = User.query.filter_by(email='admin@skyela.com').first()
        if existing_admin:
            print("\n⚠️  Admin user already exists!")
            print(f"Email: {existing_admin.email}")
            print(f"Name: {existing_admin.name}")
            
            response = input("\nDo you want to update the password? (y/n): ")
            if response.lower() == 'y':
                new_password = input("Enter new password: ")
                existing_admin.password_hash = generate_password_hash(new_password)
                db.session.commit()
                print("\n✅ Admin password updated successfully!")
            else:
                print("\n❌ Operation cancelled.")
            return
        
        # Get admin details
        print("\nEnter admin details:")
        name = input("Name (default: Admin User): ").strip() or "Admin User"
        email = input("Email (default: admin@skyela.com): ").strip() or "admin@skyela.com"
        password = input("Password (default: admin123): ").strip() or "admin123"
        
        # Create admin user
        admin = User(
            name=name,
            email=email,
            password_hash=generate_password_hash(password),
            is_admin=True
        )
        
        db.session.add(admin)
        db.session.commit()
        
        print("\n" + "=" * 50)
        print("✅ Admin user created successfully!")
        print("=" * 50)
        print(f"\nName: {name}")
        print(f"Email: {email}")
        print(f"Password: {password}")
        print(f"\nAdmin Dashboard: http://localhost:5000/admin/dashboard")
        print("=" * 50)

if __name__ == '__main__':
    try:
        create_admin_user()
    except Exception as e:
        print(f"\n❌ Error creating admin user: {e}")
        print("\nMake sure:")
        print("1. The database is initialized (run: flask init-db)")
        print("2. All dependencies are installed")
        print("3. The Flask app is properly configured")
