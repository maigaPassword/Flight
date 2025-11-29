"""
Create a new Budget Buy request for testing
"""
from app import app, db
from models import BudgetBuyRequest, User
from datetime import datetime, timedelta

with app.app_context():
    # Get admin user
    admin = User.query.filter_by(email='admin@skyela.com').first()
    
    if not admin:
        print("❌ Admin user not found!")
        exit(1)
    
    print(f"✅ Found user: {admin.name} ({admin.email})")
    
    # Create new request
    departure = datetime.now() + timedelta(days=7)  # One week from now
    
    request = BudgetBuyRequest(
        user_id=admin.user_id,
        origin='JFK',
        destination='LAX',
        departure_date=departure.date(),
        return_date=None,
        trip_duration_weeks=None,
        min_budget=0,
        max_budget=500,  # Wide budget range to ensure match
        preferred_airline=None,
        non_stop_only=False,
        max_stops=None,
        preferred_time=None,
        mode='auto_book',
        status='pending',
        created_at=datetime.utcnow()
    )
    
    db.session.add(request)
    db.session.commit()
    
    print(f"\n✅ Created Budget Buy Request #{request.request_id}")
    print(f"   Route: {request.origin} → {request.destination}")
    print(f"   Date: {request.departure_date}")
    print(f"   Budget: ${request.min_budget} - ${request.max_budget}")
    print(f"   Mode: {request.mode}")
    print(f"   Status: {request.status}")
    print(f"\n💡 Now go to Budget Buy page and click 'Check Now' button!")
