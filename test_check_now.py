"""
Test the check-now endpoint manually
"""
from app import app, db
from models import BudgetBuyRequest, User, Passport
from datetime import datetime

with app.app_context():
    # Get all budget requests
    requests = BudgetBuyRequest.query.all()
    
    print(f"\n{'='*60}")
    print(f"Budget Buy Requests Status")
    print(f"{'='*60}\n")
    
    if not requests:
        print("❌ No budget requests found!")
    else:
        for req in requests:
            print(f"Request #{req.request_id}")
            print(f"  Route: {req.origin} → {req.destination}")
            print(f"  Dates: {req.departure_date}")
            print(f"  Budget: ${req.min_budget} - ${req.max_budget}")
            print(f"  Mode: {req.mode}")
            print(f"  Status: {req.status}")
            print(f"  User ID: {req.user_id}")
            
            # Check user
            user = User.query.get(req.user_id)
            if user:
                print(f"  User: {user.name} ({user.email})")
                
                # Check passport
                passport = Passport.query.filter_by(user_id=req.user_id).first()
                if passport:
                    print(f"  ✅ Has passport: {passport.First_name} {passport.last_name}")
                else:
                    print(f"  ❌ No passport info")
            else:
                print(f"  ❌ User not found!")
            
            print()
    
    print(f"{'='*60}\n")
