"""
Quick script to add passport information for admin user
"""
from app import app, db
from models import Passport, User

with app.app_context():
    # Get admin user
    admin = User.query.filter_by(email='admin@skyela.com').first()
    
    if not admin:
        print("❌ Admin user not found!")
        exit(1)
    
    print(f"✅ Found user: {admin.name} ({admin.email})")
    print(f"   User ID: {admin.user_id}")
    
    # Check if passport exists
    passport = Passport.query.filter_by(user_id=admin.user_id).first()
    
    if passport:
        print(f"✅ Passport already exists:")
        print(f"   Name: {passport.First_name} {passport.last_name}")
        print(f"   Number: {passport.passport_number}")
    else:
        print("\n📝 Creating passport information...")
        passport = Passport(
            user_id=admin.user_id,
            First_name="Admin",
            last_name="User",
            passport_number="P123456789"
        )
        db.session.add(passport)
        db.session.commit()
        print("✅ Passport information added!")
        print(f"   Name: {passport.First_name} {passport.last_name}")
        print(f"   Number: {passport.passport_number}")
