"""
Test Admin Dashboard Setup
===========================
Quick test to verify admin dashboard is ready.
"""

import sys
import os

def check_files():
    """Check if all required files exist"""
    print("🔍 Checking files...")
    
    required_files = [
        'admin_routes.py',
        'create_admin.py',
        'static/css/admin_dashboard.css',
        'templates/admin_base.html',
        'templates/admin_login.html',
        'templates/admin_dashboard.html',
        'templates/admin_bookings.html',
        'templates/admin_users.html',
        'templates/admin_payments.html',
        'templates/admin_refunds.html',
        'templates/admin_flight_api.html',
        'templates/admin_settings.html',
        'templates/admin_logs.html',
    ]
    
    missing = []
    for file in required_files:
        if not os.path.exists(file):
            missing.append(file)
            print(f"  ❌ Missing: {file}")
        else:
            print(f"  ✅ Found: {file}")
    
    if missing:
        print(f"\n❌ {len(missing)} files missing!")
        return False
    else:
        print(f"\n✅ All {len(required_files)} files present!")
        return True

def check_models():
    """Check if models are updated"""
    print("\n🔍 Checking models...")
    
    try:
        from models import (
            User, Booking, Payment, RefundRequest,
            FlightAPIProvider, SystemSettings, APILog
        )
        print("  ✅ User model")
        print("  ✅ Booking model")
        print("  ✅ Payment model")
        print("  ✅ RefundRequest model")
        print("  ✅ FlightAPIProvider model")
        print("  ✅ SystemSettings model")
        print("  ✅ APILog model")
        print("\n✅ All models imported successfully!")
        return True
    except ImportError as e:
        print(f"  ❌ Model import error: {e}")
        return False

def check_blueprint():
    """Check if admin blueprint is registered"""
    print("\n🔍 Checking blueprint registration...")
    
    try:
        from app import app
        
        # Check if admin blueprint is registered
        admin_blueprint_found = False
        for blueprint_name in app.blueprints:
            if blueprint_name == 'admin':
                admin_blueprint_found = True
                print(f"  ✅ Admin blueprint registered: {blueprint_name}")
        
        if admin_blueprint_found:
            print("\n✅ Admin blueprint is registered!")
            return True
        else:
            print("\n❌ Admin blueprint not registered!")
            return False
    except Exception as e:
        print(f"  ❌ Error checking blueprint: {e}")
        return False

def main():
    """Run all checks"""
    print("=" * 60)
    print("SKYELA ADMIN DASHBOARD - INSTALLATION CHECK")
    print("=" * 60)
    
    checks = [
        check_files(),
        check_models(),
        check_blueprint()
    ]
    
    print("\n" + "=" * 60)
    if all(checks):
        print("✅ ALL CHECKS PASSED!")
        print("=" * 60)
        print("\n📝 Next steps:")
        print("1. Initialize database: flask init-db")
        print("2. Create admin user: python create_admin.py")
        print("3. Start server: python app.py")
        print("4. Visit: http://localhost:5000/admin/dashboard")
        print("\n✨ Admin dashboard is ready to use!")
    else:
        print("❌ SOME CHECKS FAILED")
        print("=" * 60)
        print("\nPlease review the errors above and fix them.")
    print()

if __name__ == '__main__':
    main()
