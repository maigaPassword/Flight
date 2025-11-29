"""
Budget Buy Price Monitoring Service
====================================
Background service that monitors flight prices for active Budget Buy requests
and triggers auto-booking or alerts when prices match user budgets.

This script should be run as a separate process or scheduled task:
- Can be run with: python budget_monitor.py
- Or scheduled with cron/Task Scheduler to run every hour
- Or integrated with Celery/RQ for proper background task management

Author: Group 5
Date: 2025
"""

import os
import sys
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db, amadeus
from models import BudgetBuyRequest, Passport, User, Flight, Ticket
from amadeus import ResponseError

# Load environment variables
load_dotenv()

# Email configuration
SMTP_HOST = os.getenv('SMTP_HOST', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
SMTP_USER = os.getenv('SMTP_USER', '')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', '')
FROM_EMAIL = os.getenv('FROM_EMAIL', 'noreply@skyvela.com')


def send_email(to_email, subject, html_content):
    """Send email notification to user."""
    try:
        if not SMTP_USER or not SMTP_PASSWORD:
            print(f"⚠️ Email not configured - would send to {to_email}: {subject}")
            return False
        
        msg = MIMEMultipart('alternative')
        msg['From'] = FROM_EMAIL
        msg['To'] = to_email
        msg['Subject'] = subject
        
        html_part = MIMEText(html_content, 'html')
        msg.attach(html_part)
        
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
        
        print(f"✅ Email sent to {to_email}")
        return True
    except Exception as e:
        print(f"❌ Email error: {e}")
        return False


def search_flights(origin, destination, departure_date):
    """Search for flights using Amadeus API."""
    try:
        date_str = departure_date.strftime('%Y-%m-%d') if isinstance(departure_date, datetime) else departure_date
        
        print(f"🔎 Searching: {origin} → {destination} on {date_str}")
        
        response = amadeus.shopping.flight_offers_search.get(
            originLocationCode=origin,
            destinationLocationCode=destination,
            departureDate=date_str,
            adults=1,
            max=10
        )
        
        if hasattr(response, 'data') and response.data:
            print(f"  → Found {len(response.data)} offers")
            return response.data
        else:
            print(f"  → No offers found")
            return []
    except ResponseError as e:
        print(f"❌ Search error: {e}")
        return []
    except Exception as e:
        print(f"❌ Unexpected search error: {e}")
        return []


def get_lowest_price(flight_offers):
    """Extract lowest price from flight offers."""
    if not flight_offers:
        return None
    
    lowest = None
    for offer in flight_offers:
        try:
            price = float(offer.get('price', {}).get('total', 0))
            if price > 0 and (lowest is None or price < lowest):
                lowest = price
        except Exception:
            continue
    
    return lowest


def process_auto_book(request, user, lowest_price, flight_offer):
    """Process auto-booking when price is found."""
    try:
        # Check if user has passport info
        passport = Passport.query.filter_by(user_id=user.user_id).first()
        if not passport:
            print(f"⚠️ Request {request.request_id}: No passport info for auto-booking")
            request.status = 'price_found'
            db.session.commit()
            
            # Send alert instead
            send_price_alert(request, user, lowest_price)
            return
        
        print(f"🚀 Auto-booking for request {request.request_id}")
        
        # In production, you would call Amadeus booking API here
        # For now, we'll simulate the booking
        
        # Create flight record
        flight = Flight(
            flight_number=None,
            departure_airport=request.origin,
            arrival_airport=request.destination,
            departure_time=request.departure_date,
            arrival_time=None,
            duration=None
        )
        db.session.add(flight)
        db.session.flush()
        
        # Create ticket record
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
        
        # Update request
        request.status = 'booked'
        request.booked_ticket_id = ticket.ticket_id
        request.booked_price = lowest_price
        request.booking_confirmation = f"BB{request.request_id:06d}"
        request.completed_at = datetime.utcnow()
        
        db.session.commit()
        
        # Send confirmation email
        send_booking_confirmation(request, user, lowest_price)
        
        print(f"✅ Auto-booked request {request.request_id} at ${lowest_price}")
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Auto-booking error: {e}")
        # Fallback to alert mode
        request.status = 'price_found'
        db.session.commit()
        send_price_alert(request, user, lowest_price)


def send_price_alert(request, user, price):
    """Send price alert email to user."""
    subject = f"✈️ Price Alert: {request.origin} → {request.destination}"
    
    html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 2rem; color: white;">
            <h1 style="margin: 0;">✈️ Price Alert!</h1>
        </div>
        
        <div style="padding: 2rem; background: #f9fafb;">
            <h2 style="color: #1f2937;">Flight Price Within Your Budget</h2>
            
            <p>Good news! We found a flight matching your budget requirements:</p>
            
            <div style="background: white; padding: 1.5rem; border-radius: 8px; margin: 1rem 0;">
                <h3 style="margin-top: 0; color: #4f46e5;">{request.origin} → {request.destination}</h3>
                <p><strong>Departure:</strong> {request.departure_date.strftime('%B %d, %Y') if request.departure_date else 'Flexible'}</p>
                <p><strong>Price Found:</strong> <span style="font-size: 1.5rem; color: #10b981; font-weight: bold;">${price:.2f}</span></p>
                <p><strong>Your Budget:</strong> ${request.min_budget:.2f} - ${request.max_budget:.2f}</p>
            </div>
            
            <p>
                <a href="http://localhost:5000/search?origin={request.origin}&destination={request.destination}&date={request.departure_date.strftime('%Y-%m-%d') if request.departure_date else ''}" 
                   style="display: inline-block; background: #4f46e5; color: white; padding: 1rem 2rem; 
                          text-decoration: none; border-radius: 8px; font-weight: bold; margin: 1rem 0;">
                    View & Book Now
                </a>
            </p>
            
            <p style="color: #6b7280; font-size: 0.875rem;">
                This is an automated alert from your Budget Buy request. 
                Prices may change quickly, so book soon!
            </p>
        </div>
        
        <div style="background: #e5e7eb; padding: 1rem; text-align: center; color: #6b7280; font-size: 0.813rem;">
            <p>© 2025 Skyvela | Powered by Amadeus API</p>
        </div>
    </body>
    </html>
    """
    
    send_email(user.email, subject, html)
    
    # Update request status
    request.status = 'alert_sent'
    request.completed_at = datetime.utcnow()
    db.session.commit()


def send_booking_confirmation(request, user, price):
    """Send booking confirmation email."""
    subject = f"✅ Booking Confirmed: {request.origin} → {request.destination}"
    
    html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <div style="background: linear-gradient(135deg, #10b981 0%, #059669 100%); padding: 2rem; color: white;">
            <h1 style="margin: 0;">✅ Booking Confirmed!</h1>
        </div>
        
        <div style="padding: 2rem; background: #f9fafb;">
            <h2 style="color: #1f2937;">Your Flight Has Been Booked</h2>
            
            <p>Great news! We automatically booked your flight within your budget:</p>
            
            <div style="background: white; padding: 1.5rem; border-radius: 8px; margin: 1rem 0; border-left: 4px solid #10b981;">
                <h3 style="margin-top: 0; color: #10b981;">Booking Reference: {request.booking_confirmation}</h3>
                <p><strong>Route:</strong> {request.origin} → {request.destination}</p>
                <p><strong>Departure:</strong> {request.departure_date.strftime('%B %d, %Y') if request.departure_date else 'TBD'}</p>
                <p><strong>Price:</strong> <span style="font-size: 1.5rem; color: #10b981; font-weight: bold;">${price:.2f}</span></p>
                <p style="color: #6b7280; font-size: 0.875rem;">Saved from budget: ${request.max_budget - price:.2f}</p>
            </div>
            
            <p>
                <a href="http://localhost:5000/user-portal" 
                   style="display: inline-block; background: #10b981; color: white; padding: 1rem 2rem; 
                          text-decoration: none; border-radius: 8px; font-weight: bold; margin: 1rem 0;">
                    View Booking Details
                </a>
            </p>
            
            <p style="background: #fef3c7; padding: 1rem; border-radius: 8px; border-left: 4px solid #f59e0b;">
                <strong>Next Steps:</strong><br>
                • Check your email for e-ticket<br>
                • Check-in online 24 hours before departure<br>
                • Arrive at airport 2-3 hours early
            </p>
        </div>
        
        <div style="background: #e5e7eb; padding: 1rem; text-align: center; color: #6b7280; font-size: 0.813rem;">
            <p>© 2025 Skyvela | Powered by Amadeus API</p>
        </div>
    </body>
    </html>
    """
    
    send_email(user.email, subject, html)


def process_request(request):
    """Process a single budget buy request."""
    try:
        print(f"\n{'='*60}")
        print(f"Processing Request #{request.request_id}")
        print(f"Route: {request.origin} → {request.destination}")
        print(f"Budget: ${request.min_budget} - ${request.max_budget}")
        print(f"Mode: {request.mode}")
        print(f"{'='*60}")
        
        # Update last checked time
        request.last_checked_at = datetime.utcnow()
        request.status = 'searching'
        db.session.commit()
        
        # Get user
        user = User.query.get(request.user_id)
        if not user:
            print(f"⚠️ User not found for request {request.request_id}")
            return
        
        # Search flights
        flight_offers = search_flights(
            request.origin,
            request.destination,
            request.departure_date or (datetime.now() + timedelta(days=7))
        )
        
        if not flight_offers:
            print(f"  → No flights found, keeping status as pending")
            request.status = 'pending'
            db.session.commit()
            return
        
        # Get lowest price
        lowest_price = get_lowest_price(flight_offers)
        
        if lowest_price is None:
            print(f"  → Could not extract price")
            request.status = 'pending'
            db.session.commit()
            return
        
        print(f"  → Lowest price found: ${lowest_price}")
        print(f"  → Budget range: ${request.min_budget} - ${request.max_budget}")
        
        # Check if price is within budget
        if request.min_budget <= lowest_price <= request.max_budget:
            print(f"✅ Price matches budget!")
            request.status = 'price_found'
            db.session.commit()
            
            # Process based on mode
            if request.mode == 'auto_book':
                process_auto_book(request, user, lowest_price, flight_offers[0])
            else:  # alert_only
                send_price_alert(request, user, lowest_price)
        else:
            print(f"  → Price ${lowest_price} not in budget range")
            request.status = 'pending'
            db.session.commit()
        
    except Exception as e:
        print(f"❌ Error processing request {request.request_id}: {e}")
        try:
            db.session.rollback()
            request.status = 'pending'
            db.session.commit()
        except Exception:
            pass


def monitor_prices():
    """Main monitoring loop."""
    with app.app_context():
        print(f"\n{'='*80}")
        print(f"Budget Buy Price Monitor - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*80}\n")
        
        # Get all active requests
        active_requests = BudgetBuyRequest.query.filter(
            BudgetBuyRequest.status.in_(['pending', 'searching'])
        ).all()
        
        if not active_requests:
            print("📭 No active budget requests to process")
            return
        
        print(f"📊 Found {len(active_requests)} active request(s)\n")
        
        for request in active_requests:
            process_request(request)
            time.sleep(2)  # Rate limiting between requests
        
        print(f"\n{'='*80}")
        print(f"✅ Monitoring cycle complete")
        print(f"{'='*80}\n")


if __name__ == '__main__':
    print("🚀 Starting Budget Buy Price Monitor...")
    print("Press Ctrl+C to stop\n")
    
    # Check if running in continuous mode or one-time
    continuous = '--continuous' in sys.argv
    
    if continuous:
        print("Running in continuous mode (every 60 minutes)")
        while True:
            try:
                monitor_prices()
                print(f"😴 Sleeping for 60 minutes...\n")
                time.sleep(3600)  # Sleep for 1 hour
            except KeyboardInterrupt:
                print("\n\n👋 Shutting down monitor...")
                break
            except Exception as e:
                print(f"❌ Monitor error: {e}")
                time.sleep(60)  # Sleep 1 minute on error
    else:
        print("Running one-time check")
        monitor_prices()
        print("\n✅ Done! Use --continuous flag for continuous monitoring")
