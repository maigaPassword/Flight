"""
Test auto-booking directly
"""
from app import app, db, amadeus
from models import BudgetBuyRequest, User, Passport, Flight, Ticket, Payment, Booking
from datetime import datetime, timedelta
from amadeus import ResponseError
import json
import random
import string

with app.app_context():
    # Get the latest request
    request = BudgetBuyRequest.query.filter_by(status='pending').first()
    
    if not request:
        print("❌ No pending requests found!")
        exit(1)
    
    print(f"✅ Found request #{request.request_id}")
    print(f"   Route: {request.origin} → {request.destination}")
    print(f"   Budget: ${request.min_budget} - ${request.max_budget}")
    
    # Get user and passport
    user = User.query.get(request.user_id)
    passport = Passport.query.filter_by(user_id=request.user_id).first()
    
    print(f"   User: {user.name}")
    print(f"   Passport: {'Yes' if passport else 'No'}")
    
    # Search for flights
    print(f"\n🔎 Searching for flights...")
    try:
        date_str = request.departure_date.strftime('%Y-%m-%d')
        
        response = amadeus.shopping.flight_offers_search.get(
            originLocationCode=request.origin,
            destinationLocationCode=request.destination,
            departureDate=date_str,
            adults=1,
            max=10
        )
        
        if not hasattr(response, 'data') or not response.data:
            print("❌ No flights found")
            exit(1)
        
        print(f"✅ Found {len(response.data)} offers")
        
        # Find lowest price
        lowest_price = None
        best_offer = None
        for offer in response.data:
            try:
                price = float(offer.get('price', {}).get('total', 0))
                if price > 0 and (lowest_price is None or price < lowest_price):
                    lowest_price = price
                    best_offer = offer
            except Exception:
                continue
        
        if lowest_price is None:
            print("❌ Could not extract price")
            exit(1)
        
        print(f"💰 Lowest price: ${lowest_price}")
        print(f"🎯 Budget range: ${request.min_budget} - ${request.max_budget}")
        
        # Check if in budget
        in_budget = request.min_budget <= lowest_price <= request.max_budget
        print(f"{'✅' if in_budget else '❌'} In budget: {in_budget}")
        
        if not in_budget:
            print("\n⏳ Price not in budget range")
            exit(0)
        
        # AUTO-BOOK!
        print(f"\n🚀 AUTO-BOOKING...")
        
        # Extract flight details
        itinerary = best_offer.get('itineraries', [{}])[0]
        segments = itinerary.get('segments', [{}])
        first_segment = segments[0] if segments else {}
        
        print(f"   Airline: {first_segment.get('carrierCode', 'Unknown')}")
        print(f"   Flight: {first_segment.get('number', 'Unknown')}")
        
        # Parse times
        dep_time_str = first_segment.get('departure', {}).get('at', '')
        arr_time_str = first_segment.get('arrival', {}).get('at', '')
        
        try:
            dep_time = datetime.fromisoformat(dep_time_str.replace('Z', '+00:00')) if dep_time_str else None
            arr_time = datetime.fromisoformat(arr_time_str.replace('Z', '+00:00')) if arr_time_str else None
        except:
            dep_time = None
            arr_time = None
        
        # Create Flight record
        flight = Flight(
            flight_number=first_segment.get('carrierCode', '') + first_segment.get('number', ''),
            departure_airport=request.origin,
            arrival_airport=request.destination,
            departure_time=dep_time,
            arrival_time=arr_time,
            duration=None
        )
        db.session.add(flight)
        db.session.flush()
        print(f"   ✅ Created Flight record (ID: {flight.flight_id})")
        
        # Create Ticket
        ticket = Ticket(
            flight_id=flight.flight_id,
            search_id=None,
            price=lowest_price,
            currency='USD',
            fare_class='ECONOMY',
            Ticket_bought=True
        )
        db.session.add(ticket)
        db.session.flush()
        print(f"   ✅ Created Ticket record (ID: {ticket.ticket_id})")
        
        # Create Payment
        payment = Payment(
            user_id=request.user_id,
            amount=lowest_price,
            currency='USD',
            status='completed',
            provider='budget_buy',
            transaction_id=f'BB{request.request_id:06d}',
            payment_method_id=None,
            card_last4=None,
            card_brand=None,
            completed_at=datetime.utcnow()
        )
        db.session.add(payment)
        db.session.flush()
        print(f"   ✅ Created Payment record (ID: {payment.payment_id})")
        
        # Passenger data
        passengers_data = [{
            'name': f"{passport.First_name} {passport.last_name}" if passport else user.name,
            'passport': passport.passport_number if passport else None,
            'type': 'adult'
        }]
        
        # Calculate base + taxes
        base = lowest_price * 0.85
        taxes = lowest_price * 0.15
        
        # Generate PNR
        pnr = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        print(f"   📋 PNR: {pnr}")
        
        # Create Booking
        booking = Booking(
            user_id=request.user_id,
            pnr=pnr,
            origin=request.origin,
            destination=request.destination,
            departure_date=dep_time.date() if dep_time else request.departure_date,
            return_date=request.return_date,
            airline=first_segment.get('carrierCode', 'Unknown'),
            flight_number=first_segment.get('carrierCode', '') + first_segment.get('number', ''),
            passengers_json=json.dumps(passengers_data),
            base_price=base,
            taxes=taxes,
            total_amount=lowest_price,
            currency='USD',
            status='confirmed',
            api_provider='amadeus_budget_buy',
            api_booking_reference=f'BB{request.request_id:06d}',
            payment_id=payment.payment_id
        )
        db.session.add(booking)
        db.session.flush()
        print(f"   ✅ Created Booking record (ID: {booking.booking_id})")
        
        # Update budget request
        request.status = 'booked'
        request.booked_ticket_id = ticket.ticket_id
        request.booked_price = lowest_price
        request.booking_confirmation = pnr
        request.completed_at = datetime.utcnow()
        
        db.session.commit()
        
        print(f"\n{'='*60}")
        print(f"🎉 BOOKING SUCCESSFUL!")
        print(f"{'='*60}")
        print(f"PNR: {pnr}")
        print(f"Price: ${lowest_price:.2f}")
        print(f"Saved: ${request.max_budget - lowest_price:.2f}")
        print(f"Status: {request.status}")
        print(f"{'='*60}\n")
        
    except ResponseError as e:
        print(f"❌ Amadeus API error: {e}")
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
