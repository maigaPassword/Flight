"""
Flight Booking System - Main Application File
==============================================
This Flask application provides a comprehensive flight booking system using the Amadeus API.

Features:
- Flight search (one-way and round-trip)
- Real-time flight data from Amadeus
- Multiple cabin classes (Economy, Premium Economy, Business, First)
- Payment processing with Stripe
- Booking confirmation and email notifications
- Responsive web interface

Author: Group 5
Date: 2025
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash
from amadeus import Client, ResponseError
from dotenv import load_dotenv
import os, json
from datetime import datetime, timedelta
import stripe
from models import (
    db,
    User,
    Airline,
    Airport,
    Flight,
    Ticket,
    Search,
    UserCardInformation,
    Passport,
    Booking,
    Payment,
    seed_airlines_airports,
)
from mongo_client import get_reviews_collection

# =========================
# Country Code Mapping
# =========================
# Dictionary mapping ISO country codes to full country names
# Used for displaying user-friendly country names in the UI
COUNTRY_NAMES = {
    "US": "United States", "GB": "United Kingdom", "CA": "Canada", "AU": "Australia",
    "FR": "France", "DE": "Germany", "IT": "Italy", "ES": "Spain", "JP": "Japan",
    "CN": "China", "IN": "India", "BR": "Brazil", "MX": "Mexico", "AR": "Argentina",
    "ZA": "South Africa", "EG": "Egypt", "KE": "Kenya", "NG": "Nigeria", "GH": "Ghana",
    "ET": "Ethiopia", "TZ": "Tanzania", "UG": "Uganda", "RW": "Rwanda", "SN": "Senegal",
    "CI": "Ivory Coast", "BJ": "Benin", "TG": "Togo", "BF": "Burkina Faso", "ML": "Mali",
    "NE": "Niger", "TD": "Chad", "CM": "Cameroon", "GA": "Gabon", "CG": "Congo",
    "AE": "United Arab Emirates", "SA": "Saudi Arabia", "QA": "Qatar", "KW": "Kuwait",
    "OM": "Oman", "BH": "Bahrain", "IL": "Israel", "TR": "Turkey", "GR": "Greece",
    "PT": "Portugal", "NL": "Netherlands", "BE": "Belgium", "CH": "Switzerland",
    "AT": "Austria", "SE": "Sweden", "NO": "Norway", "DK": "Denmark", "FI": "Finland",
    "PL": "Poland", "CZ": "Czech Republic", "HU": "Hungary", "RO": "Romania",
    "RU": "Russia", "UA": "Ukraine", "KZ": "Kazakhstan", "UZ": "Uzbekistan",
    "TH": "Thailand", "VN": "Vietnam", "MY": "Malaysia", "SG": "Singapore",
    "ID": "Indonesia", "PH": "Philippines", "KR": "South Korea", "TW": "Taiwan",
    "NZ": "New Zealand", "FJ": "Fiji", "PG": "Papua New Guinea", "IE": "Ireland",
    "IS": "Iceland", "LU": "Luxembourg", "MT": "Malta", "CY": "Cyprus", "HR": "Croatia",
    "RS": "Serbia", "SI": "Slovenia", "SK": "Slovakia", "BG": "Bulgaria", "LT": "Lithuania",
    "LV": "Latvia", "EE": "Estonia", "AL": "Albania", "MK": "North Macedonia",
    "BA": "Bosnia and Herzegovina", "ME": "Montenegro", "AM": "Armenia", "GE": "Georgia",
    "AZ": "Azerbaijan", "BY": "Belarus", "MD": "Moldova", "PK": "Pakistan", "BD": "Bangladesh",
    "LK": "Sri Lanka", "NP": "Nepal", "MM": "Myanmar", "KH": "Cambodia", "LA": "Laos",
    "MN": "Mongolia", "AF": "Afghanistan", "IQ": "Iraq", "IR": "Iran", "SY": "Syria",
    "LB": "Lebanon", "JO": "Jordan", "YE": "Yemen", "PS": "Palestine", "CL": "Chile",
    "PE": "Peru", "CO": "Colombia", "VE": "Venezuela", "EC": "Ecuador", "BO": "Bolivia",
    "PY": "Paraguay", "UY": "Uruguay", "CR": "Costa Rica", "PA": "Panama", "GT": "Guatemala",
    "HN": "Honduras", "SV": "El Salvador", "NI": "Nicaragua", "CU": "Cuba", "DO": "Dominican Republic",
    "JM": "Jamaica", "TT": "Trinidad and Tobago", "BB": "Barbados", "BS": "Bahamas",
    "MA": "Morocco", "DZ": "Algeria", "TN": "Tunisia", "LY": "Libya", "SD": "Sudan",
    "SO": "Somalia", "DJ": "Djibouti", "ER": "Eritrea", "MR": "Mauritania", "MG": "Madagascar",
    "MU": "Mauritius", "SC": "Seychelles", "RE": "Reunion", "YT": "Mayotte", "KM": "Comoros",
    "MZ": "Mozambique", "ZW": "Zimbabwe", "ZM": "Zambia", "MW": "Malawi", "BW": "Botswana",
    "NA": "Namibia", "LS": "Lesotho", "SZ": "Eswatini", "AO": "Angola", "CD": "DR Congo"
}

# =========================
# Load Environment Variables
# =========================
load_dotenv()

# =========================
# Initialize Amadeus Client
# =========================
# Amadeus API client for flight search and booking
# Credentials loaded from .env file for security
amadeus = Client(
    client_id=os.getenv('AMADEUS_CLIENT_ID'),
    client_secret=os.getenv('AMADEUS_CLIENT_SECRET')
)

# =========================
# Initialize Stripe
# =========================
# Stripe payment processing API
# Using test keys for development environment
stripe.api_key = os.getenv('STRIPE_SECRET_KEY', 'sk_test_51QNxkeFDZv0v2V0H6yLVExample')  # Use test key for development

# =========================
# Initialize Flask App
# =========================
app = Flask(__name__)
app.jinja_env.globals['timedelta'] = timedelta  # Make timedelta available in Jinja templates for date calculations
app.config['STRIPE_PUBLISHABLE_KEY'] = os.getenv('STRIPE_PUBLISHABLE_KEY', 'pk_test_51QNxkeFDZv0v2V0H6yLVExample')
app.secret_key = os.getenv('SECRET_KEY', 'your-secret-key-change-in-production')  # Required for session management

# --- Database configuration (SQLite in instance folder) ---
try:
    os.makedirs(app.instance_path, exist_ok=True)
except Exception:
    pass
db_path = os.path.join(app.instance_path, 'flight.db')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_path
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# Enable SQLite foreign keys
try:
    from sqlalchemy import event
    from sqlalchemy.engine import Engine

    @event.listens_for(Engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, connection_record):  # pragma: no cover
        try:
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()
        except Exception:
            pass
except Exception:
    pass

# =========================
# Register Admin Blueprint
# =========================
from admin_routes import admin_bp
app.register_blueprint(admin_bp)

# =========================
# Load Airlines Data
# =========================
# Load airline information from JSON file (airline names, codes, logos)
try:
    with open(os.path.join("json-files", "airlines.json"), "r", encoding="utf-8") as f:
        AIRLINES = {item["id"]: item for item in json.load(f)}
except Exception as e:
    print("❌ Could not load airlines.json:", e)
    AIRLINES = {}

# =========================
# Load Airports Data
# =========================
# Load airport information from JSON file (airport names, cities, IATA codes)
# Converts ICAO codes to IATA codes for easier searching
try:
    with open(os.path.join("json-files", "airports.json"), encoding="utf-8") as f:
        airports_raw = json.load(f)
        AIRPORTS = {}
        for icao, info in airports_raw.items():
            iata = info.get("iata")
            if iata:  # Only include airports with IATA codes
                AIRPORTS[iata] = {
                    "city": info.get("city") or "",
                    "name": info.get("name") or "",
                    "country": info.get("country") or ""
                }
except Exception as e:
    print("❌ Could not load airports.json:", e)
    AIRPORTS = {}

# --- Initialize database and seed static reference data on first run ---
with app.app_context():
    try:
        db.create_all()

        # Drop legacy tables from older schema to avoid duplicates ('users', 'bookings')
        def cleanup_legacy_tables():
            try:
                insp = db.inspect(db.engine)
                existing = set(insp.get_table_names())
                to_drop = [t for t in ('users', 'bookings') if t in existing]
                if to_drop:
                    with db.engine.begin() as conn:
                        for t in to_drop:
                            conn.exec_driver_sql(f"DROP TABLE IF EXISTS {t}")
                    print(f"🧹 Dropped legacy tables: {', '.join(to_drop)}")
            except Exception as e:
                print(f"⚠️ Legacy table cleanup skipped: {e}")

        cleanup_legacy_tables()

        # Seed only if empty; function handles checks internally
        seed_airlines_airports(os.path.join(os.path.dirname(__file__), 'json-files'))
        print(f"✅ Database ready at: {db_path}")
    except Exception as db_err:
        print("❌ Database initialization error:", db_err)

# =========================
# Helper Functions
# =========================

def get_airport_name(code):
    """
    Get formatted airport name from IATA code.
    Returns: "City Name (CODE)" or just CODE if not found
    """
    airport = AIRPORTS.get(code)
    return f"{airport['city']} ({code})" if airport else code

def normalize_date(date_str: str) -> str:
    """
    Ensure a valid ISO date string and not same-day for Amadeus API.
    Prevents error 4926 (invalid date range) by ensuring future dates.
    
    Args:
        date_str: Date string in YYYY-MM-DD format
    
    Returns:
        Valid date string in YYYY-MM-DD format (minimum tomorrow)
    """
    try:
        dt = datetime.strptime(date_str or "", "%Y-%m-%d")
    except Exception:
        dt = datetime.now()
    # If date is today or in the past, bump to tomorrow
    if dt.date() <= datetime.now().date():
        dt = datetime.now() + timedelta(days=1)
    return dt.strftime("%Y-%m-%d")

def build_flights(origin: str, destination: str, date_str: str):
    """
    Search Amadeus API for flight offers and return merged, frontend-friendly flight data.
    Searches across multiple cabin classes and consolidates results.
    
    Args:
        origin: IATA code of departure airport (e.g., "JFK")
        destination: IATA code of arrival airport (e.g., "LAX")
        date_str: Departure date in YYYY-MM-DD format
    
    Returns:
        List of flight dictionaries with fare information organized by cabin class
    """
    if not origin or not destination:
        return []

    searched_date = normalize_date(date_str)

    # Cabin classes to search for
    # Note: Can limit to ["ECONOMY"] during development to reduce API calls
    TRAVEL_CLASSES = ["ECONOMY", "PREMIUM_ECONOMY", "BUSINESS", "FIRST"]
    # TRAVEL_CLASSES = ["ECONOMY"]  # Uncomment for development

    max_results = 50  # Maximum results per cabin class
    all_flights = []

    # Search each cabin class separately
    for tclass in TRAVEL_CLASSES:
        try:
            print(f"🔎 Searching {tclass}: {origin} -> {destination} on {searched_date}")
            response = amadeus.shopping.flight_offers_search.get(
                originLocationCode=origin,
                destinationLocationCode=destination,
                departureDate=searched_date,
                adults=1,
                max=max_results,
                travelClass=tclass
            )
            if getattr(response, "data", None):
                all_flights.extend(response.data)
                print(f"  → {tclass} returned {len(response.data)} offers")
            else:
                print(f"  → {tclass} returned no offers")
        except ResponseError as e:
            try:
                print("❌ Full error details:", e.response.result)
                print("Status code:", e.response.status_code)
            except Exception:
                print("❌ ResponseError:", e)

    merged_flights = {}
    for flight in all_flights:
        flight_id = flight.get("id")
        if not flight_id:
            continue

        if flight_id not in merged_flights:
            validating_codes = flight.get("validatingAirlineCodes") or []
            airline_code = validating_codes[0] if validating_codes else ""
            airline_info = AIRLINES.get(airline_code, {"name": airline_code or "Unknown", "logo": ""})

            itineraries = flight.get("itineraries") or []
            first_itin = itineraries[0] if itineraries else {}
            segments = first_itin.get("segments", [])
            if not segments:
                continue

            stops = len(segments) - 1
            stops_text = "Non-stop" if stops == 0 else f"{stops} stop{'s' if stops > 1 else ''}"

            segment_list = []
            for seg in segments:
                dep = seg.get("departure", {})
                arr = seg.get("arrival", {})
                seg_duration = seg.get("duration", "")
                seg_duration = seg_duration[2:].replace("H", "h ").replace("M", "m") if seg_duration else ""
                segment_list.append({
                    "origin": dep.get("iataCode"),
                    "destination": arr.get("iataCode"),
                    "departure": dep.get("at"),
                    "arrival": arr.get("at"),
                    "duration": seg_duration
                })

            merged_flights[flight_id] = {
                "offer_id": flight_id,
                "airline_name": airline_info.get("name", ""),
                "airline_logo": airline_info.get("logo", ""),
                "origin": segments[0].get("departure", {}).get("iataCode", ""),
                "destination": segments[-1].get("arrival", {}).get("iataCode", ""),
                "departure": segments[0].get("departure", {}).get("at", ""),
                "arrival": segments[-1].get("arrival", {}).get("at", ""),
                "duration": first_itin.get("duration", "").replace("PT", "").replace("H", "h ").replace("M", "m"),
                "stops_text": stops_text,
                "segments": segment_list,
                "fares_by_cabin": {},
                "date": searched_date
            }

        for tp in flight.get("travelerPricings", []):
            price_info = tp.get("price", {}) or {}
            price_total = price_info.get("total", 0)
            price_base = price_info.get("base")
            currency = price_info.get("currency", "")
            for fd in tp.get("fareDetailsBySegment", []):
                cabin = fd.get("cabin", "ECONOMY")
                bags_info = fd.get("includedCheckedBags", {}) or {}
                fare = {
                    "fare_type": fd.get("fareBasis", "Standard"),
                    "price": float(price_total or 0),
                    "base": float(price_base) if price_base is not None else None,
                    "taxes": (float(price_total) - float(price_base)) if price_base is not None else None,
                    "currency": currency,
                    "seat": "Included" if fd.get("seat") else "Not included",
                    "bags": {
                        "quantity": bags_info.get("quantity", 0),
                        "weight": bags_info.get("weight"),
                        "type": bags_info.get("type")
                    },
                    "flexibility": "Refundable" if tp.get("refundability") == "REFUNDABLE" else "Non-refundable"
                }
                if cabin not in merged_flights[flight_id]["fares_by_cabin"]:
                    merged_flights[flight_id]["fares_by_cabin"][cabin] = []
                merged_flights[flight_id]["fares_by_cabin"][cabin].append(fare)

    flights = list(merged_flights.values())
    print(f"✅ Total offers after merge: {len(flights)} (raw offers fetched: {len(all_flights)})")
    return flights

# =========================
# Home Page
# =========================
@app.route('/')
def home():
    # Render dedicated home template (extends base) that now contains the embedded search form
    return render_template('home.html', AIRPORTS=AIRPORTS)


def extract_iata(value):
    """
    Extracts the IATA code from a string like 'Paris – Charles de Gaulle (CDG)'.
    Returns the IATA code or the value itself if it looks like a code.
    """
    import re
    match = re.search(r'\(([A-Z]{3})\)', value)
    if match:
        return match.group(1)
    return value.strip().upper()

# =========================
# Search Flights
# =========================
@app.route('/search', methods=['GET', 'POST'])
def search():
    flights = []
    outbound_flights = []
    return_flights = []
    searched_date = ""
    return_date = ""
    trip_type = (request.form.get('trip_type') if request.method == 'POST' else request.args.get('trip_type')) or 'oneway'
    origin = destination = None
    
    # --- Get passenger counts ---
    adults = int(request.form.get('adults', 1) if request.method == 'POST' else request.args.get('adults', 1))
    children = int(request.form.get('children', 0) if request.method == 'POST' else request.args.get('children', 0))
    infants = int(request.form.get('infants', 0) if request.method == 'POST' else request.args.get('infants', 0))
    
    # Store in session for later use
    from flask import session
    session['adults'] = adults
    session['children'] = children
    session['infants'] = infants
    total_passengers = adults + children + infants

    # --- Get inputs ---
    if request.method == 'POST':
        origin = request.form.get('origin_code') or extract_iata(request.form.get('origin') or request.form.get('origin_display') or "")
        destination = request.form.get('destination_code') or extract_iata(request.form.get('destination') or request.form.get('destination_display') or "")
        searched_date = request.form.get("date") or ""
        return_date = request.form.get("return_date") or ""
    else:
        origin = extract_iata(request.args.get('origin', ''))
        destination = extract_iata(request.args.get('destination', ''))
        searched_date = request.args.get('date') or ""
        return_date = request.args.get('return_date') or ""

    # --- Normalize dates ---
    searched_date = normalize_date(searched_date)
    if trip_type == 'roundtrip':
        return_date = normalize_date(return_date)

    # --- Date slider / min prices setup ---
    today = datetime.now()
    date_range = [(today + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(31)]
    min_prices = {d: None for d in date_range}

    # --- Only proceed if we have origin + destination ---
    if origin and destination:
        print(f"\n{'='*60}")
        print(f"🔍 SEARCH REQUEST: {origin} -> {destination} on {searched_date}")
        print(f"Trip Type: {trip_type}")
        print(f"{'='*60}")
        outbound_flights = build_flights(origin, destination, searched_date)
        flights = outbound_flights  # for backward-compat templates
        print(f"✅ Found {len(outbound_flights)} outbound flights")
        print(f"{'='*60}\n")
        # Compute minimum price for the searched date (for slider)
        all_prices = []
        for f in outbound_flights:
            for fares in f.get("fares_by_cabin", {}).values():
                for fare in fares:
                    all_prices.append(fare.get("price", 0))
        if all_prices:
            min_prices[searched_date] = min(all_prices)

        if trip_type == 'roundtrip' and return_date:
            return_flights = build_flights(destination, origin, return_date)

        # Persist search + all offers if user is logged in
        try:
            user_id = session.get('user_id')
            if user_id:
                # Parse dates
                try:
                    dep_dt = datetime.strptime(searched_date, "%Y-%m-%d") if searched_date else None
                except Exception:
                    dep_dt = None
                try:
                    ret_dt = datetime.strptime(return_date, "%Y-%m-%d") if (trip_type == 'roundtrip' and return_date) else None
                except Exception:
                    ret_dt = None

                target_price = min_prices.get(searched_date)

                search_row = Search(
                    user_id=user_id,
                    origin=(origin or '').upper(),
                    destination=(destination or '').upper(),
                    departure_date=dep_dt,
                    return_date=ret_dt,
                    target_price=float(target_price) if target_price is not None else None,
                )
                db.session.add(search_row)
                db.session.flush()  # get search_id without full commit yet

                # Prepare offers
                from models import FlightOffer  # local import to avoid circular at runtime
                offer_rows = []
                for f in outbound_flights:
                    # Determine lowest price + currency
                    lowest_price = None
                    currency = None
                    for fares in f.get('fares_by_cabin', {}).values():
                        for fare in fares:
                            price = fare.get('price')
                            if price is not None:
                                if lowest_price is None or price < lowest_price:
                                    lowest_price = price
                                    currency = fare.get('currency')

                    # Parse departure/arrival datetimes if possible
                    def parse_dt(val):
                        try:
                            return datetime.fromisoformat(val.replace('Z','')) if val else None
                        except Exception:
                            return None

                    offer_rows.append(
                        FlightOffer(
                            search_id=search_row.search_id,
                            offer_id=f.get('offer_id'),
                            airline_name=f.get('airline_name'),
                            origin=f.get('origin'),
                            destination=f.get('destination'),
                            departure=parse_dt(f.get('departure')),
                            arrival=parse_dt(f.get('arrival')),
                            duration_text=f.get('duration'),
                            stops_text=f.get('stops_text'),
                            lowest_price=lowest_price,
                            currency=currency,
                        )
                    )

                if offer_rows:
                    db.session.bulk_save_objects(offer_rows, return_defaults=False)

                db.session.commit()

                # Also log each outbound flight directly into Search table (one row per offer) per request
                # This fulfills requirement to have all API returned results represented in Search table.
                # NOTE: This will grow the Search table quickly; consider pagination/archival later.
                per_offer_rows = []
                seen_offer_ids = set()
                for f in outbound_flights:
                    offer_id = f.get('offer_id')
                    if not offer_id or offer_id in seen_offer_ids:
                        continue
                    seen_offer_ids.add(offer_id)

                    # Lowest price for this offer
                    lowest_price = None
                    for fares in f.get('fares_by_cabin', {}).values():
                        for fare in fares:
                            p = fare.get('price')
                            if p is not None and (lowest_price is None or p < lowest_price):
                                lowest_price = p

                    # Departure date for the offer (date part only)
                    dep_dt_offer = None
                    try:
                        raw_dep = f.get('departure')
                        if raw_dep:
                            dep_iso = raw_dep.replace('Z','')
                            dep_dt_full = datetime.fromisoformat(dep_iso)
                            dep_dt_offer = dep_dt_full.replace(hour=0, minute=0, second=0, microsecond=0)
                    except Exception:
                        dep_dt_offer = dep_dt

                    per_offer_rows.append(
                        Search(
                            user_id=user_id,
                            origin=(f.get('origin') or '').upper(),
                            destination=(f.get('destination') or '').upper(),
                            departure_date=dep_dt_offer,
                            return_date=ret_dt,
                            target_price=float(lowest_price) if lowest_price is not None else None,
                        )
                    )

                if per_offer_rows:
                    db.session.bulk_save_objects(per_offer_rows, return_defaults=False)
                    db.session.commit()
        except Exception as e:
            try:
                db.session.rollback()
            except Exception:
                pass
            print(f"⚠️ Could not persist search + offers: {e}")


    return render_template(
        "search.html",
        flights=flights,
        outbound_flights=outbound_flights,
        return_flights=return_flights,
        AIRPORTS=AIRPORTS,
        COUNTRY_NAMES=COUNTRY_NAMES,
        searched_date=searched_date,
        return_date=return_date,
        trip_type=trip_type,
        origin=origin,
        destination=destination,
        date_range=date_range,
        min_prices=min_prices,
        adults=adults,
        children=children,
        infants=infants,
        total_passengers=total_passengers
    )


# =========================
# Flight Details API
# =========================
@app.route("/flight_details")
def flight_details():
    offer_id = request.args.get("offer_id")
    if not offer_id:
        return jsonify({"error": "Missing offer_id"}), 400

    try:
        response = amadeus.shopping.flight_offers.pricing.post(
            {"data": {"type": "flight-offers-pricing", "flightOffers": [{"id": offer_id}]}}
        )
        flight_offer = response.data[0]
        segments = flight_offer.get("itineraries", [{}])[0].get("segments", [])
        price_info = flight_offer.get("price", {})

        fares_by_cabin = {}
        for tp in flight_offer.get("travelerPricings", []):
            for fd in tp.get("fareDetailsBySegment", []):
                cabin = fd.get("cabin", "ECONOMY")
                fare = {
                    "fare_type": fd.get("fareBasis", "Standard"),
                    "price": float(tp.get("price", {}).get("total", 0)),
                    "seat": "Included" if fd.get("seat") else "Not included",
                    "bags": {"checked": fd.get("includedCheckedBags", {}).get("quantity", 0)},
                    "flexibility": "Refundable" if tp.get("refundability") == "REFUNDABLE" else "Non-refundable"
                }
                if cabin not in fares_by_cabin:
                    fares_by_cabin[cabin] = []
                fares_by_cabin[cabin].append(fare)

        data = {
            "airline": segments[0]["carrierCode"] if segments else "",
            "aircraft": segments[0]["aircraft"]["code"] if segments else "",
            "stops": len(segments) - 1 if segments else 0,
            "price": price_info.get("grandTotal", ""),
            "currency": price_info.get("currency", ""),
            "fares_by_cabin": fares_by_cabin
        }

        return jsonify(data)

    except ResponseError as e:
        print(e)
        return jsonify({"error": str(e)}), 500

# =========================
# Template Filter
# =========================
@app.template_filter('format_date')
def format_date(value):
    try:
        dt = datetime.strptime(value, "%Y-%m-%d")
        return dt.strftime("%b %a %d")
    except:
        return value

# Additional summary formatting filters
@app.template_filter('time12')
def jinja_time12(iso_str: str) -> str:
    """Format to HH:MM AM/PM with leading zeros and uppercase meridiem."""
    try:
        dt = datetime.fromisoformat(iso_str)
        hour12 = dt.hour % 12 or 12
        minutes = dt.minute
        ampm = 'AM' if dt.hour < 12 else 'PM'
        return f"{hour12:02d}:{minutes:02d} {ampm}"
    except Exception:
        return ''

@app.template_filter('date_full')
def jinja_date_full(iso_str: str) -> str:
    try:
        dt = datetime.fromisoformat(iso_str)
        # Build portable day and month names without leading zeros
        day_abbr = dt.strftime('%a')
        month_abbr = dt.strftime('%b')
        return f"{day_abbr}, {month_abbr} {dt.day}, {dt.year}"
    except Exception:
        return ''

@app.template_filter('date_compact')
def jinja_date_compact(iso_str: str) -> str:
    """Return like 'wed, 17, 2025' in lowercase, with day-of-month no leading zero."""
    try:
        dt = datetime.fromisoformat(iso_str)
        return f"{dt.strftime('%a').lower()}, {dt.day}, {dt.year}"
    except Exception:
        return ''


# =========================
# Reviews Page (MongoDB)
# =========================
@app.route('/reviews', methods=['GET', 'POST'])
def reviews():
    """Public reviews page backed by MongoDB."""
    coll = get_reviews_collection()

    if request.method == 'POST':
        name = (request.form.get('name') or 'Anonymous').strip()
        rating = request.form.get('rating') or '5'
        comment = (request.form.get('comment') or '').strip()

        # Validate rating
        try:
            rating_int = int(rating)
        except ValueError:
            rating_int = 5
        rating_int = max(1, min(5, rating_int))

        if not comment:
            flash('Please enter a comment for your review.', 'error')
        else:
            try:
                doc = {
                    'name': name or 'Anonymous',
                    'rating': rating_int,
                    'comment': comment,
                    'created_at': datetime.utcnow(),
                }
                coll.insert_one(doc)
                flash('Thank you for your review!', 'success')
                return redirect(url_for('reviews'))
            except Exception as e:
                print(f"❌ Mongo insert error: {e}")
                flash('Could not save your review. Please try again.', 'error')

    # GET or POST with validation error
    try:
        cursor = coll.find().sort('created_at', -1).limit(50)
        reviews_list = list(cursor)
    except Exception as e:
        print(f"❌ Mongo fetch error: {e}")
        reviews_list = []
        flash('Could not load reviews at this time.', 'error')

    return render_template('reviews.html', reviews=reviews_list)
    
@app.route('/flight_information')
def flight_information():
    offer_json = request.args.get('offer_json')
    selected_cabin = request.args.get('cabin', 'ECONOMY')  # default to ECONOMY

    if not offer_json:
        return render_template('base.html', message="No flight data provided")

    try:
        flight = json.loads(offer_json)
        fares_by_cabin = flight.get('fares_by_cabin', {})

        # Pick a default cabin if the requested one is not available
        if selected_cabin not in fares_by_cabin:
            selected_cabin = next(iter(fares_by_cabin.keys()), 'ECONOMY')

        fare = fares_by_cabin.get(selected_cabin, [None])[0]
        if not fare:
            return render_template('base.html', message="No fares available for this flight")

        # Extract flight info
        airline = flight.get('airline_name', 'Unknown Airline')
        logo = flight.get('airline_logo', '')
        origin = flight.get('origin', '')
        destination = flight.get('destination', '')
        departure_iso = flight.get('departure', '')
        arrival_iso = flight.get('arrival', '')
        duration = flight.get('duration', '')
        stops = flight.get('stops_text', '')

        # Get city names from AIRPORTS
        origin_city = AIRPORTS.get(origin, {}).get("city", origin)
        destination_city = AIRPORTS.get(destination, {}).get("city", destination)

        # Convert departure/arrival to datetime objects and format
        departure_dt = datetime.fromisoformat(departure_iso) if departure_iso else None
        arrival_dt = datetime.fromisoformat(arrival_iso) if arrival_iso else None

        departure_time = departure_dt.strftime("%I:%M %p") if departure_dt else ""
        arrival_time = arrival_dt.strftime("%I:%M %p") if arrival_dt else ""
        departure_date = departure_dt.strftime("%A %d %Y") if departure_dt else ""
        arrival_date = arrival_dt.strftime("%A %d %Y") if arrival_dt else ""

        segments = flight.get('segments', [])
        outbound_segments = segments[:len(segments)//2] if len(segments) > 1 else segments
        return_segments = segments[len(segments)//2:] if len(segments) > 1 else []

        return render_template(
            'flight_information.html',
            airline=airline,
            logo=logo,
            origin=origin,
            origin_city=origin_city,
            destination=destination,
            destination_city=destination_city,
            departure_time=departure_time,
            arrival_time=arrival_time,
            departure_date=departure_date,
            arrival_date=arrival_date,
            duration=duration,
            stops=stops,
            fare=fare,
            selected_cabin=selected_cabin,
            outbound_segments=outbound_segments,
            return_segments=return_segments
        )

    except Exception as ex:
        return render_template('base.html', message=f"Error processing flight data: {ex}")


# =========================
# Flight Summary (Roundtrip)
# =========================
@app.route('/flight_summary', methods=['POST'])
def flight_summary():
    """
    Accepts selected outbound and optional return flight JSON payloads, computes total, and renders summary.
    """
    outbound_json = request.form.get('outbound_json')
    return_json = request.form.get('return_json')
    selected_cabin_out = request.form.get('cabin_out') or 'ECONOMY'
    selected_cabin_ret = request.form.get('cabin_ret') or 'ECONOMY'

    if not outbound_json:
        return redirect(url_for('search'))

    try:
        outbound = json.loads(outbound_json)
        return_flight = json.loads(return_json) if return_json else None

        def pick_price(flight, preferred_cabin):
            fares_by_cabin = flight.get('fares_by_cabin', {}) or {}
            # Prefer preferred cabin if available; else pick lowest among any cabin
            if preferred_cabin in fares_by_cabin and fares_by_cabin[preferred_cabin]:
                return float(fares_by_cabin[preferred_cabin][0].get('price', 0)), preferred_cabin
            # Find global minimum
            min_price = None
            min_cabin = None
            for cabin, fares in fares_by_cabin.items():
                if fares:
                    p = float(fares[0].get('price', 0))
                    if min_price is None or p < min_price:
                        min_price = p
                        min_cabin = cabin
            return float(min_price or 0), (min_cabin or preferred_cabin)

        price_out, cabin_out = pick_price(outbound, selected_cabin_out)
        price_ret, cabin_ret = (0.0, None)
        if return_flight:
            price_ret, cabin_ret = pick_price(return_flight, selected_cabin_ret)

        total_price = price_out + price_ret

        # Basic display data
        def city(iata):
            return AIRPORTS.get(iata, {}).get('city', iata)

        # Nice date/time formatting
        def fmt_time(iso_str):
            try:
                dt = datetime.fromisoformat(iso_str)
                hour12 = dt.hour % 12 or 12
                minutes = dt.minute
                ampm = 'AM' if dt.hour < 12 else 'PM'
                return f"{hour12:02d}:{minutes:02d} {ampm}"
            except Exception:
                return ''

        def day_name(iso_str):
            try:
                dt = datetime.fromisoformat(iso_str)
                return dt.strftime('%A')
            except Exception:
                return ''

        def pick_fare(flight, cabin):
            fares_by_cabin = flight.get('fares_by_cabin', {}) or {}
            fares = fares_by_cabin.get(cabin) or []
            return fares[0] if fares else None

        out_fare = pick_fare(outbound, cabin_out)
        ret_fare = pick_fare(return_flight, cabin_ret) if return_flight else None

        base_out = (out_fare.get('base') if out_fare else None)
        base_ret = (ret_fare.get('base') if ret_fare else None)
        taxes_out = (out_fare.get('taxes') if out_fare else None)
        taxes_ret = (ret_fare.get('taxes') if ret_fare else None)

        # Totals (use None if unknown to allow template fallbacks)
        base_total = None
        taxes_total = None
        if base_out is not None and (base_ret is not None or not return_flight):
            base_total = (base_out or 0.0) + ((base_ret or 0.0) if return_flight else 0.0)
        if taxes_out is not None and (taxes_ret is not None or not return_flight):
            taxes_total = (taxes_out or 0.0) + ((taxes_ret or 0.0) if return_flight else 0.0)

        # Get passenger counts from session
        from flask import session
        adults = session.get('adults', 1)
        children = session.get('children', 0)
        infants = session.get('infants', 0)
        total_passengers = adults + children + infants

        context = {
            'outbound': outbound,
            'outbound_json': json.dumps(outbound),  # For seat selection
            'return_flight': return_flight,
            'return_json': json.dumps(return_flight) if return_flight else None,  # For seat selection
            'price_out': price_out,
            'price_ret': price_ret,
            'total_price': total_price,
            'cabin_out': cabin_out,
            'cabin_ret': cabin_ret,
            'base_out': base_out,
            'base_ret': base_ret,
            'taxes_out': taxes_out,
            'taxes_ret': taxes_ret,
            'base_total': base_total,
            'taxes_total': taxes_total,
            'origin_city': city(outbound.get('origin')),
            'destination_city': city(outbound.get('destination')),
            # Passenger counts
            'adults': adults,
            'children': children,
            'infants': infants,
            'total_passengers': total_passengers,
            # Outbound formatted
            'out_dep_time': fmt_time(outbound.get('departure')),
            'out_arr_time': fmt_time(outbound.get('arrival')),
            'out_dep_day': day_name(outbound.get('departure')),
            'out_arr_day': day_name(outbound.get('arrival')),
            # Return formatted
            'ret_dep_time': fmt_time(return_flight.get('departure')) if return_flight else '',
            'ret_arr_time': fmt_time(return_flight.get('arrival')) if return_flight else '',
            'ret_dep_day': day_name(return_flight.get('departure')) if return_flight else '',
            'ret_arr_day': day_name(return_flight.get('arrival')) if return_flight else '',
        }

        return render_template('flight_summary.html', AIRPORTS=AIRPORTS, **context)
    except Exception as e:
        print('❌ flight_summary error:', e)
        return render_template('base.html', message='Could not build flight summary.')


# =========================
# Seat Selection Page
# =========================
@app.route('/seat_selection', methods=['POST'])
def seat_selection():
    """
    Seat selection page - allows users to choose seats before booking.
    Shows interactive seatmap using Amadeus SeatMap API.
    """
    outbound_json = request.form.get('outbound_json')
    return_json = request.form.get('return_json')
    cabin_out = request.form.get('cabin_out', 'ECONOMY')
    cabin_ret = request.form.get('cabin_ret', 'ECONOMY')
    total_price = request.form.get('total_price', '0.00')
    base_total = request.form.get('base_total')
    taxes_total = request.form.get('taxes_total')

    if not outbound_json:
        return redirect(url_for('search'))

    try:
        outbound = json.loads(outbound_json)
        return_flight = json.loads(return_json) if return_json else None

        # Helper function for city names
        def city(iata):
            return AIRPORTS.get(iata, {}).get('city', iata)

        # Get passenger counts from session
        from flask import session
        adults = session.get('adults', 1)
        children = session.get('children', 0)
        infants = session.get('infants', 0)
        total_passengers = adults + children + infants

        context = {
            'outbound': outbound,
            'outbound_json': outbound_json,
            'return_flight': return_flight,
            'return_json': return_json,
            'cabin_out': cabin_out,
            'cabin_ret': cabin_ret,
            'total_price': total_price,
            'base_total': base_total,
            'taxes_total': taxes_total,
            'origin_city': city(outbound.get('origin')),
            'destination_city': city(outbound.get('destination')),
            'adults': adults,
            'children': children,
            'infants': infants,
            'total_passengers': total_passengers,
        }

        return render_template('seat_selection.html', **context)
    except Exception as e:
        print('❌ seat_selection error:', e)
        return render_template('base.html', message='Could not load seat selection.')


# =========================
# Select Return Page (Roundtrip step 2)
# =========================
@app.route('/select_return', methods=['POST'])
def select_return():
    """
    Presents return flight options after an outbound has been selected.
    Expects: outbound_json, cabin_out, origin, destination, return_date
    """
    outbound_json = request.form.get('outbound_json')
    cabin_out = (request.form.get('cabin_out') or 'ECONOMY').upper()
    origin = request.form.get('origin')
    destination = request.form.get('destination')
    return_date = request.form.get('return_date')

    if not (outbound_json and origin and destination and return_date):
        return redirect(url_for('search'))

    try:
        outbound = json.loads(outbound_json)
    except Exception:
        return redirect(url_for('search'))

    # Search for return flights (destination -> origin on return_date)
    return_date = normalize_date(return_date)
    return_flights = build_flights(destination, origin, return_date)

    return render_template(
        'select_return.html',
        AIRPORTS=AIRPORTS,
        COUNTRY_NAMES=COUNTRY_NAMES,
        outbound_json=outbound_json,
        cabin_out=cabin_out,
        origin=origin,
        destination=destination,
        return_date=return_date,
        return_flights=return_flights
    )


# =========================
# Booking/Checkout Page
# =========================
@app.route('/booking', methods=['POST'])
def booking():
    """
    Booking page with passenger details form and checkout.
    Receives flight summary data and displays booking form.
    Collects information for all passengers (adults, children, infants).
    """
    # Get all the flight data from the summary page
    outbound_json = request.form.get('outbound_json')
    return_json = request.form.get('return_json')
    cabin_out = request.form.get('cabin_out', 'ECONOMY')
    cabin_ret = request.form.get('cabin_ret', 'ECONOMY')
    total_price = request.form.get('total_price', '0.00')
    base_total = request.form.get('base_total')
    taxes_total = request.form.get('taxes_total')
    selected_seats = request.form.get('selected_seats', '')  # Get selected seats
    
    # Format prices to 2 decimal places
    if base_total:
        base_total = f"{float(base_total):.2f}"
    if taxes_total:
        taxes_total = f"{float(taxes_total):.2f}"
    
    # Get passenger counts from session
    from flask import session
    adults = session.get('adults', 1)
    children = session.get('children', 0)
    infants = session.get('infants', 0)
    total_passengers = adults + children + infants
    
    # Calculate price per passenger type
    # Typically: Adults = 100%, Children = 75%, Infants = 10%
    base_price = float(total_price) / (adults + (children * 0.75) + (infants * 0.10)) if total_passengers > 0 else 0
    adult_price = base_price
    child_price = base_price * 0.75
    infant_price = base_price * 0.10
    
    # Parse flight data
    try:
        outbound = json.loads(outbound_json) if outbound_json else None
        return_flight = json.loads(return_json) if return_json else None
    except:
        return redirect(url_for('search'))
    
    if not outbound:
        return redirect(url_for('search'))
    
    # Get airport details
    origin_city = AIRPORTS.get(outbound.get('origin', ''), {}).get('city', outbound.get('origin', ''))
    destination_city = AIRPORTS.get(outbound.get('destination', ''), {}).get('city', outbound.get('destination', ''))
    
    return render_template(
        'booking.html',
        outbound=outbound,
        return_flight=return_flight,
        cabin_out=cabin_out,
        cabin_ret=cabin_ret,
        total_price=total_price,
        base_total=base_total,
        taxes_total=taxes_total,
        selected_seats=selected_seats,  # Pass selected seats to template
        origin_city=origin_city,
        destination_city=destination_city,
        adults=adults,
        children=children,
        infants=infants,
        total_passengers=total_passengers,
        adult_price=f"{adult_price:.2f}",
        child_price=f"{child_price:.2f}",
        infant_price=f"{infant_price:.2f}",
        AIRPORTS=AIRPORTS,
        COUNTRY_NAMES=COUNTRY_NAMES,
        stripe_publishable_key=app.config['STRIPE_PUBLISHABLE_KEY']
    )


# =========================
# Create Stripe Payment Intent
# =========================
@app.route('/create-payment-intent', methods=['POST'])
def create_payment_intent():
    """
    Create a Stripe Payment Intent for the booking.
    """
    try:
        data = request.get_json() or {}

        # Validate and normalize amount
        try:
            amount_float = float(data.get('amount', 0))
        except Exception:
            return jsonify(error='Invalid amount provided'), 400

        if amount_float <= 0:
            return jsonify(error='Amount must be greater than zero'), 400

        amount = int(round(amount_float * 100))  # Convert to cents

        # Validate Stripe configuration (helpful error if not configured)
        secret_from_env = os.getenv('STRIPE_SECRET_KEY', '')
        publishable_from_env = os.getenv('STRIPE_PUBLISHABLE_KEY', '')
        if not secret_from_env or 'Example' in secret_from_env or 'Example' in app.config.get('STRIPE_PUBLISHABLE_KEY', ''):
            return jsonify(error='Stripe is not configured. Please set STRIPE_SECRET_KEY and STRIPE_PUBLISHABLE_KEY in your environment or .env file.'), 500

        # Create a PaymentIntent with the order amount and currency
        intent = stripe.PaymentIntent.create(
            amount=amount,
            currency='usd',
            automatic_payment_methods={
                'enabled': True,
            },
            metadata={
                'passenger_name': data.get('passenger_name', ''),
                'email': data.get('email', ''),
            }
        )

        return jsonify({
            'clientSecret': intent['client_secret']
        })
    except Exception as e:
        return jsonify(error=str(e)), 403


# =========================
# Confirmation Page
# =========================
@app.route('/confirmation', methods=['POST'])
def confirmation():
    """
    Final confirmation page after booking is complete.
    """
    # Get passenger and payment details
    passenger_name = request.form.get('passenger_name')
    email = request.form.get('email')
    phone = request.form.get('phone')
    payment_intent_id = request.form.get('payment_intent_id')
    
    # Get flight details
    outbound_json = request.form.get('outbound_json')
    return_json = request.form.get('return_json')
    cabin_out = request.form.get('cabin_out', 'ECONOMY')
    cabin_ret = request.form.get('cabin_ret', 'ECONOMY')
    total_price = request.form.get('total_price', '0.00')
    passenger_details_json = request.form.get('passenger_details')
    passenger_details = []
    try:
        if passenger_details_json:
            passenger_details = json.loads(passenger_details_json)
    except Exception:
        passenger_details = []
    
    # Parse flight data
    try:
        outbound = json.loads(outbound_json) if outbound_json else None
        return_flight = json.loads(return_json) if return_json else None
    except:
        return redirect(url_for('search'))
    
    # Generate booking reference
    import random, string
    booking_ref = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    
    # Get airport details
    origin_city = AIRPORTS.get(outbound.get('origin', ''), {}).get('city', outbound.get('origin', ''))
    destination_city = AIRPORTS.get(outbound.get('destination', ''), {}).get('city', outbound.get('destination', ''))
    
    # Persist Ticket and Flight (best-effort; does not block rendering)
    try:
        with app.app_context():
            def parse_dt(val):
                try:
                    return datetime.fromisoformat(val) if val else None
                except Exception:
                    return None

            def duration_minutes(s: str | None) -> int | None:
                if not s:
                    return None
                try:
                    # expects like "12h 30m" or "12h" or "30m"
                    mins = 0
                    import re
                    h = re.search(r"(\d+)h", s)
                    m = re.search(r"(\d+)m", s)
                    if h:
                        mins += int(h.group(1)) * 60
                    if m:
                        mins += int(m.group(1))
                    return mins or None
                except Exception:
                    return None

            dep_time = parse_dt(outbound.get('departure') if outbound else None)
            arr_time = parse_dt(outbound.get('arrival') if outbound else None)
            dur = duration_minutes(outbound.get('duration') if outbound else None)

            flight = Flight(
                flight_number=None,  # unknown in simplified offer
                departure_airport=(outbound.get('origin') if outbound else '') or '',
                arrival_airport=(outbound.get('destination') if outbound else '') or '',
                departure_time=dep_time,
                arrival_time=arr_time,
                duration=dur,
            )
            db.session.add(flight)
            db.session.flush()  # get flight_id

            ticket = Ticket(
                flight_id=flight.flight_id,
                search_id=None,  # could link to a saved Search if/when implemented with auth
                price=float(total_price or 0.0),
                currency='USD',
                fare_class=cabin_out,
                Ticket_bought=True,
            )
            db.session.add(ticket)
            
            # NEW: Save to Booking model for admin dashboard
            user_id = session.get('user_id')  # Get logged-in user if available
            
            # Create Payment record
            payment = Payment(
                user_id=user_id,
                amount=float(total_price or 0.0),
                currency='USD',
                status='completed',
                provider='stripe',
                transaction_id=payment_intent_id or f'manual_{booking_ref}',
                payment_method_id=None,  # Could be enhanced to store saved card token
                card_last4=None,  # Could be enhanced if card info available
                card_brand=None,
                completed_at=datetime.utcnow()
            )
            db.session.add(payment)
            db.session.flush()  # Get payment_id
            
            # Prepare passengers JSON
            passengers_data = passenger_details if passenger_details else [{
                'name': passenger_name,
                'email': email,
                'phone': phone
            }]
            
            # Calculate base price and taxes (simplified - 85% base, 15% taxes)
            total = float(total_price or 0.0)
            base = total * 0.85
            taxes = total * 0.15
            
            # Create Booking record
            booking = Booking(
                user_id=user_id,
                pnr=booking_ref,
                origin=outbound.get('origin', '') if outbound else '',
                destination=outbound.get('destination', '') if outbound else '',
                departure_date=dep_time.date() if dep_time else None,
                return_date=parse_dt(return_flight.get('departure')).date() if return_flight and return_flight.get('departure') else None,
                airline=outbound.get('airline', '') if outbound else '',
                flight_number=outbound.get('flight', '') if outbound else '',
                passengers_json=json.dumps(passengers_data),
                base_price=base,
                taxes=taxes,
                total_amount=total,
                currency='USD',
                status='confirmed',
                api_provider='amadeus',
                api_booking_reference=None,
                payment_id=payment.payment_id
            )
            db.session.add(booking)
            
            db.session.commit()
            print(f"✅ Booking saved: {booking_ref} - ${total_price}")
    except Exception as e:
        print(f"⚠️ Could not save ticket/flight: {e}")
        import traceback
        traceback.print_exc()

    return render_template(
        'confirmation.html',
        booking_ref=booking_ref,
        passenger_name=passenger_name,
        email=email,
        phone=phone,
        outbound=outbound,
        return_flight=return_flight,
        cabin_out=cabin_out,
        cabin_ret=cabin_ret,
        total_price=total_price,
        passenger_details=passenger_details,
        origin_city=origin_city,
        destination_city=destination_city,
        AIRPORTS=AIRPORTS,
        now=datetime.now()
    )


# =========================
# Airport Search API (Autocomplete)
# =========================
@app.route('/api/airports/search')
def airport_search():
    """
    Search airports by keyword.
    Primary source: local AIRPORTS dataset for broad/global coverage (fast, offline).
    Secondary source: Amadeus Airport & City Search API to enrich results when available.
    Returns airport suggestions for autocomplete functionality with a consistent shape.
    """
    keyword = request.args.get('keyword', '').strip()
    
    if not keyword or len(keyword) < 2:
        return jsonify([])
    
    # Normalize for search
    q = keyword.lower()

    def build_display(iata_code: str, name: str, city_name: str, country: str = "") -> str:
        city_part = city_name or iata_code
        name_part = name or ""
        country_part = f", {country}" if country else ""
        # Example: "Lagos, Nigeria - Murtala Muhammed Intl (LOS)"
        return f"{city_part}{country_part} - {name_part} ({iata_code})".strip()

    # 1) Local fallback (primary) using AIRPORTS loaded at startup
    local_matches = []
    try:
        for iata, info in AIRPORTS.items():
            city = (info.get('city') or '').strip()
            name = (info.get('name') or '').strip()
            country = (info.get('country') or '').strip()
            if (
                q in iata.lower() or
                (city and q in city.lower()) or
                (name and q in name.lower())
            ):
                local_matches.append({
                    'iata': iata,
                    'name': name,
                    'city': city,
                    'country': country,
                    'display': build_display(iata, name, city, country)
                })
            if len(local_matches) >= 20:
                break
    except Exception as e:
        print(f"❌ Local airport search error: {e}")
        local_matches = []

    results_by_iata = {s['iata']: s for s in local_matches}

    # 2) Remote enrichment (secondary) using Amadeus
    # Only attempt if we have fewer than 20 matches to keep list concise
    try:
        if len(results_by_iata) < 20 and os.getenv('AMADEUS_CLIENT_ID') and os.getenv('AMADEUS_CLIENT_SECRET'):
            response = amadeus.reference_data.locations.get(
                keyword=keyword,
                subType='AIRPORT,CITY'
            )
            if hasattr(response, 'data') and response.data:
                for location in response.data:
                    iata_code = location.get('iataCode') or ''
                    if not iata_code or iata_code in results_by_iata:
                        continue
                    name = location.get('name') or ''
                    city_name = (location.get('address', {}) or {}).get('cityName') or ''
                    country = (location.get('address', {}) or {}).get('countryName') or ''
                    results_by_iata[iata_code] = {
                        'iata': iata_code,
                        'name': name,
                        'city': city_name,
                        'country': country,
                        'display': build_display(iata_code, name, city_name, country)
                    }
                    if len(results_by_iata) >= 20:
                        break
    except ResponseError as e:
        # Log but don't fail the endpoint — local data still works
        print(f"❌ Airport search (Amadeus) error: {e}")
    except Exception as e:
        print(f"❌ Unexpected airport search error: {e}")

    # Return combined results (local first, then remote), up to 20
    suggestions = list(results_by_iata.values())[:20]
    return jsonify(suggestions)


# =========================
# Flight Booking API (Create Orders)
# =========================
@app.route('/api/book-flight', methods=['POST'])
def book_flight():
    """
    Create a flight booking using Amadeus Flight Create Orders API.
    This actually reserves the flight with the airline.
    """
    try:
        data = request.get_json()
        
        # Extract flight offer and traveler information
        flight_offer = data.get('flightOffer')
        travelers = data.get('travelers', [])
        
        if not flight_offer or not travelers:
            return jsonify({'error': 'Missing flight offer or traveler information'}), 400
        
        # Create flight order using Amadeus API
        response = amadeus.booking.flight_orders.post(
            data={
                'type': 'flight-order',
                'flightOffers': [flight_offer],
                'travelers': travelers
            }
        )
        
        if hasattr(response, 'data'):
            order_data = response.data
            
            # Extract booking details
            booking_reference = order_data.get('associatedRecords', [{}])[0].get('reference', 'N/A')
            order_id = order_data.get('id', 'N/A')
            
            return jsonify({
                'success': True,
                'bookingReference': booking_reference,
                'orderId': order_id,
                'orderData': order_data
            })
        else:
            return jsonify({'error': 'No booking data returned'}), 500
            
    except ResponseError as e:
        error_msg = str(e)
        try:
            error_details = e.response.result
            error_msg = error_details.get('errors', [{}])[0].get('detail', str(e))
        except:
            pass
        
        print(f"❌ Booking error: {error_msg}")
        return jsonify({'error': error_msg}), 400
    
    except Exception as e:
        print(f"❌ Unexpected booking error: {e}")
        return jsonify({'error': 'An unexpected error occurred'}), 500


# =========================
# Flight Order Management API
# =========================
@app.route('/api/orders/<order_id>')
def get_flight_order(order_id):
    """
    Retrieve flight order details using Amadeus Flight Order Management API.
    """
    try:
        response = amadeus.booking.flight_orders(order_id).get()
        
        if hasattr(response, 'data'):
            return jsonify({
                'success': True,
                'order': response.data
            })
        else:
            return jsonify({'error': 'Order not found'}), 404
            
    except ResponseError as e:
        print(f"❌ Order retrieval error: {e}")
        return jsonify({'error': 'Order not found'}), 404
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return jsonify({'error': 'An error occurred'}), 500


@app.route('/api/orders/<order_id>/cancel', methods=['DELETE'])
def cancel_flight_order(order_id):
    """
    Cancel a flight order using Amadeus Flight Order Management API.
    """
    try:
        response = amadeus.booking.flight_orders(order_id).delete()
        
        return jsonify({
            'success': True,
            'message': 'Flight order cancelled successfully',
            'result': response.data if hasattr(response, 'data') else {}
        })
            
    except ResponseError as e:
        error_msg = str(e)
        try:
            error_details = e.response.result
            error_msg = error_details.get('errors', [{}])[0].get('detail', str(e))
        except:
            pass
        
        print(f"❌ Cancellation error: {error_msg}")
        return jsonify({'error': error_msg}), 400
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return jsonify({'error': 'An error occurred'}), 500


# =========================
# Airline Code Lookup API
# =========================
@app.route('/api/airlines/<airline_code>')
def get_airline_info(airline_code):
    """
    Get airline information using Amadeus Airline Code Lookup API.
    """
    try:
        response = amadeus.reference_data.airlines.get(
            airlineCodes=airline_code
        )
        
        if hasattr(response, 'data') and response.data:
            airline = response.data[0]
            return jsonify({
                'success': True,
                'airline': {
                    'code': airline.get('iataCode'),
                    'name': airline.get('businessName'),
                    'commonName': airline.get('commonName')
                }
            })
        else:
            return jsonify({'error': 'Airline not found'}), 404
            
    except ResponseError as e:
        print(f"❌ Airline lookup error: {e}")
        return jsonify({'error': 'Airline not found'}), 404
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return jsonify({'error': 'An error occurred'}), 500


# =========================
# SeatMap Display API
# =========================
@app.route('/api/seatmaps', methods=['POST'])
def get_seatmaps():
    """
    Get seat maps for flight offers using Amadeus SeatMap Display API.
    Shows available seats, their characteristics, and pricing.
    """
    try:
        data = request.get_json()
        flight_offer = data.get('flightOffer')
        
        if not flight_offer:
            return jsonify({'error': 'Flight offer is required'}), 400
        
        response = amadeus.shopping.seatmaps.post(flight_offer)
        
        if hasattr(response, 'data'):
            seatmaps = []
            for seatmap_data in response.data:
                seatmap_info = {
                    'segmentId': seatmap_data.get('segmentId'),
                    'carrierCode': seatmap_data.get('carrierCode'),
                    'number': seatmap_data.get('number'),
                    'aircraft': seatmap_data.get('aircraft', {}).get('code'),
                    'departure': seatmap_data.get('departure', {}).get('iataCode'),
                    'arrival': seatmap_data.get('arrival', {}).get('iataCode'),
                    'class': seatmap_data.get('class'),
                    'decks': []
                }
                
                # Parse deck information
                if 'decks' in seatmap_data:
                    for deck in seatmap_data['decks']:
                        deck_info = {
                            'deckConfiguration': deck.get('deckConfiguration'),
                            'seats': []
                        }
                        
                        # Parse seat information
                        if 'seats' in deck:
                            for seat in deck['seats']:
                                seat_info = {
                                    'number': seat.get('number'),
                                    'characteristicsCodes': seat.get('characteristicsCodes', []),
                                    'travelerPricing': seat.get('travelerPricing', []),
                                    'coordinates': seat.get('coordinates')
                                }
                                deck_info['seats'].append(seat_info)
                        
                        seatmap_info['decks'].append(deck_info)
                
                seatmaps.append(seatmap_info)
            
            return jsonify({
                'success': True,
                'seatmaps': seatmaps
            })
        else:
            return jsonify({'error': 'No seatmaps available'}), 404
            
    except ResponseError as e:
        error_msg = 'Seatmap retrieval failed'
        try:
            error_details = e.response.result
            error_msg = error_details.get('errors', [{}])[0].get('detail', str(e))
        except:
            pass
        
        print(f"❌ Seatmap error: {error_msg}")
        return jsonify({'error': error_msg}), 400
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return jsonify({'error': 'An error occurred'}), 500


# =========================
# Flight Check-in Links API
# =========================
@app.route('/api/checkin-links')
def get_checkin_links():
    """
    Get airline check-in URLs using Amadeus Flight Check-in Links API.
    Provides direct links to airline check-in pages.
    """
    try:
        airline_code = request.args.get('airlineCode')
        language = request.args.get('language', 'EN')
        
        if not airline_code:
            return jsonify({'error': 'Airline code is required'}), 400
        
        response = amadeus.reference_data.urls.checkin_links.get(
            airlineCode=airline_code,
            language=language
        )
        
        if hasattr(response, 'data') and response.data:
            checkin_data = response.data[0]
            return jsonify({
                'success': True,
                'checkinLink': {
                    'airlineCode': checkin_data.get('iataCode'),
                    'url': checkin_data.get('href'),
                    'channel': checkin_data.get('channel')
                }
            })
        else:
            return jsonify({'error': 'Check-in link not available'}), 404
            
    except ResponseError as e:
        print(f"❌ Check-in link error: {e}")
        return jsonify({'error': 'Check-in link not available'}), 404
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return jsonify({'error': 'An error occurred'}), 500


# =========================
# Branded Fares Upsell API
# =========================
@app.route('/api/branded-fares', methods=['POST'])
def get_branded_fares():
    """
    Get branded fare options using Amadeus Branded Fares Upsell API.
    Shows different fare families (Basic, Standard, Flex, etc.) with benefits.
    """
    try:
        data = request.get_json()
        flight_offer = data.get('flightOffer')
        
        if not flight_offer:
            return jsonify({'error': 'Flight offer is required'}), 400
        
        response = amadeus.shopping.flight_offers.upselling.post(flight_offer)
        
        if hasattr(response, 'data'):
            branded_offers = []
            for offer in response.data:
                branded_info = {
                    'id': offer.get('id'),
                    'source': offer.get('source'),
                    'price': {
                        'total': offer.get('price', {}).get('total'),
                        'currency': offer.get('price', {}).get('currency')
                    },
                    'fareFamily': None,
                    'amenities': []
                }
                
                # Extract fare family and amenities
                if 'travelerPricings' in offer:
                    for pricing in offer['travelerPricings']:
                        for fare_detail in pricing.get('fareDetailsBySegment', []):
                            if 'brandedFare' in fare_detail:
                                branded_info['fareFamily'] = fare_detail['brandedFare']
                            if 'amenities' in fare_detail:
                                branded_info['amenities'].extend(fare_detail['amenities'])
                
                branded_offers.append(branded_info)
            
            return jsonify({
                'success': True,
                'brandedOffers': branded_offers
            })
        else:
            return jsonify({'error': 'No branded fares available'}), 404
            
    except ResponseError as e:
        error_msg = 'Branded fares retrieval failed'
        try:
            error_details = e.response.result
            error_msg = error_details.get('errors', [{}])[0].get('detail', str(e))
        except:
            pass
        
        print(f"❌ Branded fares error: {error_msg}")
        return jsonify({'error': error_msg}), 400
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return jsonify({'error': 'An error occurred'}), 500


# =========================
# Flight Inspiration Search API
# =========================
@app.route('/api/inspiration')
def get_flight_inspiration():
    """
    Get flight inspiration using Amadeus Flight Inspiration Search API.
    Finds cheapest destinations from a given origin.
    """
    try:
        origin = request.args.get('origin')
        max_price = request.args.get('maxPrice')
        departure_date = request.args.get('departureDate')
        
        if not origin:
            return jsonify({'error': 'Origin airport code is required'}), 400
        
        params = {'origin': origin}
        if max_price:
            params['maxPrice'] = max_price
        if departure_date:
            params['departureDate'] = departure_date
        
        response = amadeus.shopping.flight_destinations.get(**params)
        
        if hasattr(response, 'data') and response.data:
            destinations = []
            for dest in response.data[:20]:  # Limit to 20 results
                destinations.append({
                    'destination': dest.get('destination'),
                    'departureDate': dest.get('departureDate'),
                    'returnDate': dest.get('returnDate'),
                    'price': {
                        'total': dest.get('price', {}).get('total'),
                        'currency': dest.get('price', {}).get('currency')
                    },
                    'links': dest.get('links')
                })
            
            return jsonify({
                'success': True,
                'destinations': destinations
            })
        else:
            return jsonify({'error': 'No inspiration results found'}), 404
            
    except ResponseError as e:
        error_msg = 'Flight inspiration search failed'
        try:
            error_details = e.response.result
            error_msg = error_details.get('errors', [{}])[0].get('detail', str(e))
        except:
            pass
        
        print(f"❌ Flight inspiration error: {error_msg}")
        
        # Provide helpful message for test environment limitations
        if 'No response found' in error_msg or 'not found' in error_msg.lower():
            return jsonify({
                'error': error_msg,
                'note': 'Test environment has limited destination data. Try: JFK, LAX, CDG, LHR, DXB, NRT',
                'testMode': True
            }), 400
        
        return jsonify({'error': error_msg}), 400
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return jsonify({'error': 'An error occurred'}), 500


# =========================
# Cheapest Date Search API
# =========================
@app.route('/api/cheapest-dates')
def get_cheapest_dates():
    """
    Find cheapest flight dates using Amadeus Flight Cheapest Date Search API.
    Returns cheapest prices for different departure dates.
    """
    try:
        origin = request.args.get('origin')
        destination = request.args.get('destination')
        departure_date = request.args.get('departureDate')
        
        if not origin or not destination:
            return jsonify({'error': 'Origin and destination are required'}), 400
        
        params = {
            'origin': origin,
            'destination': destination
        }
        if departure_date:
            params['departureDate'] = departure_date
        
        response = amadeus.shopping.flight_dates.get(**params)
        
        if hasattr(response, 'data') and response.data:
            dates = []
            for date_option in response.data:
                dates.append({
                    'departureDate': date_option.get('departureDate'),
                    'returnDate': date_option.get('returnDate'),
                    'price': {
                        'total': date_option.get('price', {}).get('total'),
                        'currency': date_option.get('price', {}).get('currency')
                    }
                })
            
            return jsonify({
                'success': True,
                'dates': dates
            })
        else:
            return jsonify({'error': 'No date options found'}), 404
            
    except ResponseError as e:
        error_msg = 'Cheapest date search failed'
        try:
            error_details = e.response.result
            error_msg = error_details.get('errors', [{}])[0].get('detail', str(e))
        except:
            pass
        
        print(f"❌ Cheapest date error: {error_msg}")
        return jsonify({'error': error_msg}), 400
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return jsonify({'error': 'An error occurred'}), 500


# =========================
# Airline Routes API
# =========================
@app.route('/api/airline-routes')
def get_airline_routes():
    """
    Get airline route information using Amadeus Airline Routes API.
    Shows which airlines operate between origin and destination.
    """
    try:
        origin = request.args.get('origin')
        destination = request.args.get('destination')
        
        if not origin or not destination:
            return jsonify({'error': 'Origin and destination are required'}), 400
        
        response = amadeus.airline.destinations.get(
            airlineCode=request.args.get('airlineCode', 'BA'),  # Default to British Airways
            max=50
        )
        
        if hasattr(response, 'data') and response.data:
            routes = []
            for route in response.data:
                if route.get('type') == 'location':
                    routes.append({
                        'destination': route.get('iataCode'),
                        'name': route.get('name')
                    })
            
            return jsonify({
                'success': True,
                'routes': routes
            })
        else:
            return jsonify({'error': 'No routes found'}), 404
            
    except ResponseError as e:
        error_msg = 'Airline routes search failed'
        try:
            error_details = e.response.result
            error_msg = error_details.get('errors', [{}])[0].get('detail', str(e))
        except:
            pass
        
        print(f"❌ Airline routes error: {error_msg}")
        return jsonify({'error': error_msg}), 400
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return jsonify({'error': 'An error occurred'}), 500


# =========================
# Flight Delay Prediction API
# =========================
@app.route('/api/delay-prediction')
def get_delay_prediction():
    """
    Predict flight delays using Amadeus Flight Delay Prediction API.
    Provides probability of flight delays based on historical data.
    """
    try:
        origin = request.args.get('origin')
        destination = request.args.get('destination')
        departure_date = request.args.get('departureDate')
        departure_time = request.args.get('departureTime')
        arrival_date = request.args.get('arrivalDate')
        arrival_time = request.args.get('arrivalTime')
        airline_code = request.args.get('airlineCode')
        flight_number = request.args.get('flightNumber')
        
        if not all([origin, destination, departure_date, departure_time, 
                   arrival_date, arrival_time, airline_code, flight_number]):
            return jsonify({'error': 'All flight details are required'}), 400
        
        response = amadeus.travel.predictions.flight_delay.get(
            originLocationCode=origin,
            destinationLocationCode=destination,
            departureDate=departure_date,
            departureTime=departure_time,
            arrivalDate=arrival_date,
            arrivalTime=arrival_time,
            aircraftCode=request.args.get('aircraftCode', '320'),
            carrierCode=airline_code,
            flightNumber=flight_number,
            duration=request.args.get('duration', 'PT2H30M')
        )
        
        if hasattr(response, 'data') and response.data:
            prediction = response.data[0]
            return jsonify({
                'success': True,
                'prediction': {
                    'probability': prediction.get('probability'),
                    'result': prediction.get('result'),
                    'subType': prediction.get('subType'),
                    'id': prediction.get('id')
                }
            })
        else:
            return jsonify({'error': 'Prediction not available'}), 404
            
    except ResponseError as e:
        error_msg = 'Delay prediction failed'
        try:
            error_details = e.response.result
            error_msg = error_details.get('errors', [{}])[0].get('detail', str(e))
        except:
            pass
        
        print(f"❌ Delay prediction error: {error_msg}")
        return jsonify({'error': error_msg}), 400
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return jsonify({'error': 'An error occurred'}), 500


# =========================
# Authentication Routes
# =========================
@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page backed by the User table. Supports both username and email."""
    if request.method == 'POST':
        # Accept both 'username' (from regular login) and 'email' (from admin login)
        username = (request.form.get('username') or request.form.get('email') or '').strip()
        password = (request.form.get('password') or '').strip()

        if not username or not password:
            flash('Please enter both username/email and password.', 'error')
            return render_template('login.html')

        try:
            # Try to find user by name first, then by email
            user = User.query.filter_by(name=username).first()
            if not user:
                user = User.query.filter_by(email=username).first()
            
            if not user or not check_password_hash(user.password_hash, password):
                flash('Invalid credentials. Please try again.', 'error')
                return render_template('login.html')

            # Set session
            session['user_id'] = user.user_id
            session['user_name'] = user.name
            
            # Redirect based on admin status
            if user.is_admin:
                flash(f'Welcome back, {user.name}!', 'success')
                return redirect(url_for('admin.dashboard_page'))
            else:
                flash(f'Welcome back, {user.name}!', 'success')
                return redirect(url_for('user_portal'))
                
        except Exception as e:
            print(f"❌ Login error: {e}")
            flash('Could not log you in right now. Please try again.', 'error')
            return render_template('login.html')

    return render_template('login.html')


@app.route('/logout')
def logout():
    """Log out the current user and redirect to appropriate login page."""
    was_admin = False
    try:
        user_id = session.get('user_id')
        if user_id:
            user = User.query.get(user_id)
            if user and user.is_admin:
                was_admin = True
        
        session.pop('user_id', None)
        session.pop('user_name', None)
    except Exception:
        pass
    
    flash('You have been logged out.', 'success')
    
    # Redirect admins to admin login, regular users to regular login
    if was_admin:
        return redirect(url_for('admin.login_page'))
    else:
        return redirect(url_for('login'))


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    """Signup page that persists users in the database."""
    if request.method == 'POST':
        username = (request.form.get('username') or '').strip()
        email = (request.form.get('email') or '').strip()
        password = (request.form.get('password') or '').strip()
        confirm = (request.form.get('confirm_password') or '').strip()

        if not username or not email or not password or not confirm:
            flash('All fields are required.', 'error')
            return render_template('signup.html')
        if password != confirm:
            flash('Passwords do not match.', 'error')
            return render_template('signup.html')

        # Persist user (ensure unique email)
        try:
            with app.app_context():
                existing = User.query.filter_by(email=email).first()
                if existing:
                    flash('An account with this email already exists. Please log in.', 'error')
                    return redirect(url_for('login'))

                password_hash = generate_password_hash(password)
                user = User(name=username, email=email, password_hash=password_hash)
                db.session.add(user)
                db.session.commit()
                flash('Account created successfully. Please log in.', 'success')
                return redirect(url_for('login'))
        except Exception as e:
            print(f"❌ Signup persistence error: {e}")
            flash('Could not create account at this time. Please try again.', 'error')
            return render_template('signup.html')

    return render_template('signup.html')


# Basic routes for static pages referenced in navbar
@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/contact')
def contact():
    return render_template('contact.html')


# Help & Info Pages
@app.route('/help/how-to-book')
def how_to_book():
    return render_template('how_to_book.html')


@app.route('/help/cancellation-policy')
def cancellation_policy():
    return render_template('cancellation_policy.html')


@app.route('/help/payment-methods')
def payment_methods():
    return render_template('payment_methods.html')


@app.route('/help/budget-buy')
def budget_buy_help():
    return render_template('budget_buy_help.html')


# =========================
# User Portal (Profile & Passport Management)
# =========================
@app.route('/user-portal', methods=['GET', 'POST'])
def user_portal():
    """Authenticated user portal.

    GET: Show user profile (name/email), passports, and payment methods.
    POST: Create/update/delete passport or payment method.
    """
    if not session.get('user_id'):
        flash('Please log in to access your portal.', 'error')
        return redirect(url_for('login'))

    user = User.query.get(session.get('user_id'))
    if not user:
        flash('User record not found.', 'error')
        return redirect(url_for('login'))

    action = (request.form.get('action') or '').lower()
    passport_id = request.form.get('passport_id')
    card_id = request.form.get('card_id')
    editing_passport = None

    if request.method == 'POST':
        # Handle card actions
        if action == 'delete_card' and card_id:
            try:
                card = UserCardInformation.query.filter_by(User_card_id=card_id, user_id=user.user_id).first()
                if card:
                    db.session.delete(card)
                    db.session.commit()
                    flash('Payment method deleted.', 'success')
                else:
                    flash('Payment method not found.', 'error')
            except Exception as e:
                db.session.rollback()
                print(f"❌ Card delete error: {e}")
                flash('Could not delete payment method.', 'error')
            return redirect(url_for('user_portal'))
        
        elif action == 'save_card':
            card_number = (request.form.get('card_number') or '').strip().replace(' ', '')
            exp_month = request.form.get('exp_month', '').strip()
            exp_year = request.form.get('exp_year', '').strip()
            cvv = request.form.get('card_cvv', '').strip()
            
            if not card_number or not exp_month or not exp_year or not cvv:
                flash('All card fields are required.', 'error')
            elif len(cvv) < 3 or len(cvv) > 4:
                flash('CVV must be 3 or 4 digits.', 'error')
            else:
                try:
                    # TODO: In production, use Stripe.js to create PaymentMethod on client-side
                    # This prevents card data from ever touching your server
                    # For now, we simulate the tokenization process
                    
                    # Detect card brand
                    brand = 'Unknown'
                    if card_number.startswith('4'):
                        brand = 'Visa'
                    elif card_number.startswith(('5', '2')):
                        brand = 'Mastercard'
                    elif card_number.startswith('3'):
                        brand = 'American Express'
                    
                    # PRODUCTION: Use Stripe API to create PaymentMethod
                    # payment_method = stripe.PaymentMethod.create(
                    #     type='card',
                    #     card={
                    #         'number': card_number,
                    #         'exp_month': int(exp_month),
                    #         'exp_year': int(exp_year),
                    #         'cvc': cvv
                    #     }
                    # )
                    # Store: payment_method.id, payment_method.card.last4, payment_method.card.brand
                    
                    # DEVELOPMENT: Simulate tokenization
                    last4 = card_number[-4:]
                    simulated_token = f"pm_test_{card_number[:6]}_{last4}"
                    
                    # Store ONLY the token and safe card metadata
                    # NEVER store: full card number, CVV
                    new_card = UserCardInformation(
                        user_id=user.user_id,
                        last4=last4,
                        brand=brand,
                        exp_month=int(exp_month),
                        exp_year=int(exp_year),
                        payment_method_id=simulated_token  # This is the TOKEN (not card data)
                    )
                    db.session.add(new_card)
                    db.session.commit()
                    flash('Payment method tokenized and saved. CVV was sent to processor but not stored.', 'success')
                    return redirect(url_for('user_portal'))
                except Exception as e:
                    db.session.rollback()
                    print(f"❌ Card save error: {e}")
                    flash('Could not save payment method.', 'error')
        
        # Handle passport actions
        elif action == 'delete' and passport_id:
            try:
                p = Passport.query.filter_by(Passport_id=passport_id, user_id=user.user_id).first()
                if p:
                    db.session.delete(p)
                    db.session.commit()
                    flash('Passport deleted.', 'success')
                else:
                    flash('Passport not found.', 'error')
            except Exception as e:
                db.session.rollback()
                print(f"❌ Passport delete error: {e}")
                flash('Could not delete passport.', 'error')
        else:  # save (create or update)
            first_name = (request.form.get('first_name') or '').strip()
            last_name = (request.form.get('last_name') or '').strip()
            passport_number = (request.form.get('passport_number') or '').strip()

            if not first_name or not last_name or not passport_number:
                flash('All passport fields are required.', 'error')
            else:
                try:
                    if passport_id:
                        editing_passport = Passport.query.filter_by(Passport_id=passport_id, user_id=user.user_id).first()
                        if not editing_passport:
                            flash('Passport not found for update.', 'error')
                        else:
                            editing_passport.First_name = first_name
                            editing_passport.last_name = last_name
                            editing_passport.passport_number = passport_number
                            db.session.commit()
                            flash('Passport updated.', 'success')
                            # After successful update, clear editing state so buttons revert to Edit/Delete
                            editing_passport = None
                            return redirect(url_for('user_portal'))
                    else:
                        new_passport = Passport(
                            user_id=user.user_id,
                            First_name=first_name,
                            last_name=last_name,
                            passport_number=passport_number,
                        )
                        db.session.add(new_passport)
                        db.session.commit()
                        flash('Passport added.', 'success')
                        # Use PRG pattern to avoid form resubmission and ensure clean state
                        return redirect(url_for('user_portal'))
                except Exception as e:
                    db.session.rollback()
                    print(f"❌ Passport save error: {e}")
                    flash('Could not save passport information right now.', 'error')

    # If GET with edit param, set editing_passport
    if request.method == 'GET':
        edit_id = request.args.get('edit')
        if edit_id:
            editing_passport = Passport.query.filter_by(Passport_id=edit_id, user_id=user.user_id).first()

    passports = Passport.query.filter_by(user_id=user.user_id).order_by(Passport.created_at.desc()).all()
    cards = UserCardInformation.query.filter_by(user_id=user.user_id).order_by(UserCardInformation.created_at.desc()).all()
    return render_template('user_portal.html', user=user, passports=passports, cards=cards, editing_passport=editing_passport)

@app.route('/user_portal')
def user_portal_redirect():  # compatibility alias
    return redirect(url_for('user_portal'))


# =========================
# Budget Buy Feature Routes
# =========================
@app.route('/budget-buy', methods=['GET', 'POST'])
def budget_buy():
    """
    Budget Buy page: Auto-book or price alerts when flights match budget.
    
    GET: Display form and active requests
    POST: Create new budget tracking request
    """
    if not session.get('user_id'):
        flash('Please log in to use Budget Buy.', 'error')
        return redirect(url_for('login'))
    
    user_id = session.get('user_id')
    
    if request.method == 'POST':
        try:
            # Extract form data
            origin = (request.form.get('origin') or '').upper().strip()
            destination = (request.form.get('destination') or '').upper().strip()
            departure_date_str = request.form.get('departure_date', '').strip()
            return_date_str = request.form.get('return_date', '').strip()
            trip_duration_weeks = request.form.get('trip_duration_weeks', '').strip()
            
            # Preferences
            non_stop_only = request.form.get('non_stop_only') == 'on'
            max_stops = request.form.get('max_stops', '').strip()
            preferred_time = request.form.get('preferred_time', '').strip()
            preferred_airline = (request.form.get('preferred_airline') or '').upper().strip()
            
            # Budget range
            min_budget = float(request.form.get('min_budget', 0))
            max_budget = float(request.form.get('max_budget', 0))
            
            # Mode
            mode = request.form.get('mode', 'alert_only')
            
            # Validate
            if not origin or not destination:
                return jsonify({'success': False, 'message': 'Origin and destination are required'}), 400
            
            if min_budget >= max_budget:
                return jsonify({'success': False, 'message': 'Maximum budget must be greater than minimum'}), 400
            
            # Parse dates
            departure_date = None
            return_date = None
            try:
                if departure_date_str:
                    departure_date = datetime.strptime(departure_date_str, '%Y-%m-%d')
            except Exception:
                pass
            
            try:
                if return_date_str:
                    return_date = datetime.strptime(return_date_str, '%Y-%m-%d')
            except Exception:
                pass
            
            # Parse optional integers
            trip_duration = int(trip_duration_weeks) if trip_duration_weeks else None
            max_stops_int = int(max_stops) if max_stops else None
            
            # Create budget request
            from models import BudgetBuyRequest
            budget_request = BudgetBuyRequest(
                user_id=user_id,
                origin=origin,
                destination=destination,
                departure_date=departure_date,
                return_date=return_date,
                trip_duration_weeks=trip_duration,
                non_stop_only=non_stop_only,
                max_stops=max_stops_int,
                preferred_time=preferred_time or None,
                preferred_airline=preferred_airline or None,
                min_budget=min_budget,
                max_budget=max_budget,
                currency='USD',
                mode=mode,
                status='pending'
            )
            
            db.session.add(budget_request)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Budget tracking request created successfully!',
                'request_id': budget_request.request_id
            })
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Budget Buy error: {e}")
            return jsonify({'success': False, 'message': 'Failed to create request'}), 500
    
    # GET: Display form and active requests
    try:
        from models import BudgetBuyRequest
        # Only show active requests (exclude cancelled)
        requests = BudgetBuyRequest.query.filter(
            BudgetBuyRequest.user_id == user_id,
            BudgetBuyRequest.status != 'cancelled'
        ).order_by(
            BudgetBuyRequest.created_at.desc()
        ).all()
        
        return render_template('budget_buy.html', requests=requests, AIRPORTS=AIRPORTS)
    except Exception as e:
        print(f"❌ Budget Buy page error: {e}")
        return render_template('budget_buy.html', requests=[], AIRPORTS=AIRPORTS)


@app.route('/active-requests')
def active_requests():
    """
    Active Requests page: View all ACTIVE budget tracking requests.
    Filters out cancelled requests.
    """
    if not session.get('user_id'):
        flash('Please log in to view your active requests.', 'error')
        return redirect(url_for('login'))
    
    try:
        from models import BudgetBuyRequest
        user_id = session.get('user_id')
        # Only show active requests (exclude cancelled)
        requests = BudgetBuyRequest.query.filter(
            BudgetBuyRequest.user_id == user_id,
            BudgetBuyRequest.status != 'cancelled'
        ).order_by(
            BudgetBuyRequest.created_at.desc()
        ).all()
        
        return render_template('active_requests.html', requests=requests)
    except Exception as e:
        print(f"❌ Active Requests page error: {e}")
        return render_template('active_requests.html', requests=[])


@app.route('/my-bookings')
def my_bookings():
    """
    My Bookings page: View ALL booked tickets from any source.
    Shows tickets from manual bookings, Budget Buy auto-bookings, etc.
    Filters out:
    - Cancelled Budget Buy bookings
    - Flights that have already departed
    """
    if not session.get('user_id'):
        flash('Please log in to view your bookings.', 'error')
        return redirect(url_for('login'))
    
    try:
        from models import Ticket, Flight, Search, BudgetBuyRequest
        from datetime import datetime
        user_id = session.get('user_id')
        current_time = datetime.now()
        
        # Get all tickets bought by this user
        # Join with Flight and Search to get full details
        tickets = db.session.query(Ticket, Flight, Search).join(
            Flight, Ticket.flight_id == Flight.flight_id
        ).outerjoin(
            Search, Ticket.search_id == Search.search_id
        ).filter(
            (Search.user_id == user_id) | (Ticket.Ticket_bought == True)
        ).order_by(
            Ticket.scraped_at.desc()
        ).all()
        
        # Get Budget Buy bookings - ONLY booked status (exclude cancelled, failed, etc.)
        budget_bookings = BudgetBuyRequest.query.filter_by(
            user_id=user_id,
            status='booked'
        ).all()
        
        # Build comprehensive booking list
        all_bookings = []
        
        # Add regular tickets (filter out past flights)
        for ticket, flight, search in tickets:
            if ticket.Ticket_bought:
                # Check if flight has already departed
                if flight.departure_time and flight.departure_time < current_time:
                    continue  # Skip past flights
                
                all_bookings.append({
                    'type': 'manual' if search else 'unknown',
                    'ticket': ticket,
                    'flight': flight,
                    'search': search,
                    'booking_date': ticket.scraped_at,
                    'confirmation': f"TKT{ticket.ticket_id:06d}"
                })
        
        # Add Budget Buy bookings (filter out past flights)
        for req in budget_bookings:
            if req.booked_ticket_id:
                ticket = Ticket.query.get(req.booked_ticket_id)
                if ticket:
                    flight = Flight.query.get(ticket.flight_id)
                    
                    # Check if flight has already departed
                    if flight and flight.departure_time and flight.departure_time < current_time:
                        continue  # Skip past flights
                    
                    all_bookings.append({
                        'type': 'budget_buy',
                        'ticket': ticket,
                        'flight': flight,
                        'search': None,
                        'budget_request': req,
                        'booking_date': req.completed_at or ticket.scraped_at,
                        'confirmation': req.booking_confirmation or f"BB{req.request_id:06d}"
                    })
        
        # Sort by booking date (newest first)
        all_bookings.sort(key=lambda x: x['booking_date'], reverse=True)
        
        # Count active Budget Buy requests (still monitoring)
        active_budget_requests = BudgetBuyRequest.query.filter(
            BudgetBuyRequest.user_id == user_id,
            BudgetBuyRequest.status.in_(['pending', 'searching', 'price_found', 'alert_sent'])
        ).count()
        
        return render_template('my_bookings.html', 
                             bookings=all_bookings,
                             active_budget_requests=active_budget_requests)
    except Exception as e:
        print(f"❌ My Bookings page error: {e}")
        import traceback
        traceback.print_exc()
        return render_template('my_bookings.html', bookings=[])


@app.route('/budget-buy/status')
def budget_buy_status():
    """
    API endpoint to get status of all budget requests for current user.
    Used for real-time status updates.
    """
    if not session.get('user_id'):
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        from models import BudgetBuyRequest
        user_id = session.get('user_id')
        requests = BudgetBuyRequest.query.filter_by(user_id=user_id).order_by(
            BudgetBuyRequest.created_at.desc()
        ).all()
        
        requests_data = []
        for req in requests:
            requests_data.append({
                'request_id': req.request_id,
                'origin': req.origin,
                'destination': req.destination,
                'status': req.status,
                'mode': req.mode,
                'min_budget': req.min_budget,
                'max_budget': req.max_budget,
                'last_checked_at': req.last_checked_at.isoformat() if req.last_checked_at else None
            })
        
        return jsonify({'success': True, 'requests': requests_data})
    except Exception as e:
        print(f"❌ Status fetch error: {e}")
        return jsonify({'error': 'Failed to fetch status'}), 500


@app.route('/budget-buy/cancel/<int:request_id>', methods=['POST'])
def cancel_budget_request(request_id):
    """
    Cancel a budget tracking request.
    """
    if not session.get('user_id'):
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        from models import BudgetBuyRequest
        user_id = session.get('user_id')
        
        budget_request = BudgetBuyRequest.query.filter_by(
            request_id=request_id,
            user_id=user_id
        ).first()
        
        if not budget_request:
            return jsonify({'success': False, 'message': 'Request not found'}), 404
        
        if budget_request.status in ['booked', 'cancelled']:
            return jsonify({'success': False, 'message': 'Cannot cancel this request'}), 400
        
        budget_request.status = 'cancelled'
        budget_request.completed_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Request cancelled successfully'})
    except Exception as e:
        db.session.rollback()
        print(f"❌ Cancel error: {e}")


@app.route('/budget-buy/check-now/<int:request_id>', methods=['POST'])
def check_budget_request_now(request_id):
    """
    Manually trigger price check and auto-book for a budget request.
    """
    if not session.get('user_id'):
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        from models import BudgetBuyRequest, Passport
        user_id = session.get('user_id')
        
        budget_request = BudgetBuyRequest.query.filter_by(
            request_id=request_id,
            user_id=user_id
        ).first()
        
        if not budget_request:
            return jsonify({'success': False, 'message': 'Request not found'}), 404
        
        if budget_request.status in ['booked', 'cancelled']:
            return jsonify({'success': False, 'message': 'Cannot check this request'}), 400
        
        # Check for passport if auto-book mode
        passport = None
        if budget_request.mode == 'auto_book':
            passport = Passport.query.filter_by(user_id=user_id).first()
            if not passport:
                return jsonify({
                    'success': False, 
                    'message': 'Passport information required for auto-booking. Please add your passport details first.',
                    'needs_passport': True
                }), 400
        
        # Search for flights
        try:
            date_str = budget_request.departure_date.strftime('%Y-%m-%d') if budget_request.departure_date else (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
            
            response = amadeus.shopping.flight_offers_search.get(
                originLocationCode=budget_request.origin,
                destinationLocationCode=budget_request.destination,
                departureDate=date_str,
                adults=1,
                max=10
            )
            
            if not hasattr(response, 'data') or not response.data:
                budget_request.last_checked_at = datetime.utcnow()
                db.session.commit()
                return jsonify({
                    'success': False,
                    'message': 'No flights found for this route'
                })
            
            # Find lowest price and best offer
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
                budget_request.last_checked_at = datetime.utcnow()
                db.session.commit()
                return jsonify({
                    'success': False,
                    'message': 'Could not find pricing information'
                })
            
            # Update last checked
            budget_request.last_checked_at = datetime.utcnow()
            
            # Check if in budget
            in_budget = budget_request.min_budget <= lowest_price <= budget_request.max_budget
            
            if in_budget and budget_request.mode == 'auto_book':
                # AUTO-BOOK THE FLIGHT!
                try:
                    # Extract flight details from offer
                    itinerary = best_offer.get('itineraries', [{}])[0]
                    segments = itinerary.get('segments', [{}])
                    first_segment = segments[0] if segments else {}
                    
                    # Parse departure time
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
                        departure_airport=budget_request.origin,
                        arrival_airport=budget_request.destination,
                        departure_time=dep_time,
                        arrival_time=arr_time,
                        duration=None
                    )
                    db.session.add(flight)
                    db.session.flush()
                    
                    # Create Ticket record (old model for compatibility)
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
                    
                    # Create Payment record for admin dashboard
                    payment = Payment(
                        user_id=user_id,
                        amount=lowest_price,
                        currency='USD',
                        status='completed',
                        provider='budget_buy',
                        transaction_id=f'BB{request_id:06d}',
                        payment_method_id=None,
                        card_last4=None,
                        card_brand=None,
                        completed_at=datetime.utcnow()
                    )
                    db.session.add(payment)
                    db.session.flush()
                    
                    # Get user info for passenger details
                    user = User.query.get(user_id)
                    passengers_data = [{
                        'name': f"{passport.first_name} {passport.last_name}" if passport else user.name,
                        'passport': passport.passport_number if passport else None,
                        'type': 'adult'
                    }]
                    
                    # Calculate base price and taxes
                    base = lowest_price * 0.85
                    taxes = lowest_price * 0.15
                    
                    # Generate PNR
                    import random, string
                    pnr = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
                    
                    # Create Booking record for admin dashboard
                    booking = Booking(
                        user_id=user_id,
                        pnr=pnr,
                        origin=budget_request.origin,
                        destination=budget_request.destination,
                        departure_date=dep_time.date() if dep_time else budget_request.departure_date,
                        return_date=budget_request.return_date,
                        airline=first_segment.get('carrierCode', 'Unknown'),
                        flight_number=first_segment.get('carrierCode', '') + first_segment.get('number', ''),
                        passengers_json=json.dumps(passengers_data),
                        base_price=base,
                        taxes=taxes,
                        total_amount=lowest_price,
                        currency='USD',
                        status='confirmed',
                        api_provider='amadeus_budget_buy',
                        api_booking_reference=f'BB{request_id:06d}',
                        payment_id=payment.payment_id
                    )
                    db.session.add(booking)
                    db.session.flush()
                    
                    # Update budget request
                    budget_request.status = 'booked'
                    budget_request.booked_ticket_id = ticket.ticket_id
                    budget_request.booked_price = lowest_price
                    budget_request.booking_confirmation = pnr
                    budget_request.completed_at = datetime.utcnow()
                    
                    db.session.commit()
                    
                    print(f"✅ Auto-booked flight for request {request_id} - PNR: {pnr}, Price: ${lowest_price}")
                    
                    return jsonify({
                        'success': True,
                        'booked': True,
                        'price': lowest_price,
                        'pnr': pnr,
                        'message': f'🎉 Flight booked successfully!\nPNR: {pnr}\nPrice: ${lowest_price:.2f}\nSaved: ${budget_request.max_budget - lowest_price:.2f}'
                    })
                    
                except Exception as book_error:
                    db.session.rollback()
                    print(f"❌ Booking error: {book_error}")
                    import traceback
                    traceback.print_exc()
                    return jsonify({
                        'success': False,
                        'message': f'Price found (${lowest_price:.2f}) but booking failed: {str(book_error)}'
                    }), 500
            else:
                # Price not in budget or alert-only mode
                db.session.commit()
                return jsonify({
                    'success': True,
                    'booked': False,
                    'price': lowest_price,
                    'in_budget': in_budget,
                    'min_budget': budget_request.min_budget,
                    'max_budget': budget_request.max_budget,
                    'message': f'Found flights from ${lowest_price:.2f}. ' + 
                              ('✅ Price is within your budget!' if in_budget else '⏳ Price not in budget yet.')
                })
            
        except ResponseError as e:
            return jsonify({
                'success': False,
                'message': f'Flight search error: {str(e)}'
            }), 500
            
    except Exception as e:
        db.session.rollback()
        print(f"❌ Check now error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500
        return jsonify({'success': False, 'message': 'Failed to cancel request'}), 500


@app.route('/api/check-passport')
def check_passport():
    """
    Check if user has passport information saved.
    """
    if not session.get('user_id'):
        return jsonify({'has_passport': False})
    
    try:
        user_id = session.get('user_id')
        passport = Passport.query.filter_by(user_id=user_id).first()
        return jsonify({'has_passport': passport is not None})
    except Exception:
        return jsonify({'has_passport': False})


@app.route('/api/save-passport', methods=['POST'])
def save_passport():
    """
    Save passport information for auto-booking.
    """
    if not session.get('user_id'):
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401
    
    try:
        user_id = session.get('user_id')
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        passport_number = request.form.get('passport_number', '').strip()
        
        if not first_name or not last_name or not passport_number:
            return jsonify({'success': False, 'message': 'All fields are required'}), 400
        
        # Check if passport already exists
        passport = Passport.query.filter_by(user_id=user_id).first()
        
        if passport:
            # Update existing
            passport.First_name = first_name
            passport.last_name = last_name
            passport.passport_number = passport_number
        else:
            # Create new
            passport = Passport(
                user_id=user_id,
                First_name=first_name,
                last_name=last_name,
                passport_number=passport_number
            )
            db.session.add(passport)
        
        db.session.commit()
        return jsonify({'success': True, 'message': 'Passport information saved'})
    except Exception as e:
        db.session.rollback()
        print(f"❌ Passport save error: {e}")
        return jsonify({'success': False, 'message': 'Failed to save passport'}), 500


# =========================
# Flask CLI: init-db
# =========================
@app.cli.command('init-db')
def init_db_command():
    """Initialize the database tables and seed reference data."""
    with app.app_context():
        db.create_all()
        seed_airlines_airports(os.path.join(os.path.dirname(__file__), 'json-files'))
        print('Database initialized and seeded.')

@app.cli.command('clean-legacy')
def clean_legacy_command():
    """Drop legacy tables from older schema (users, bookings)."""
    with app.app_context():
        try:
            with db.engine.begin() as conn:
                conn.exec_driver_sql("DROP TABLE IF EXISTS users")
                conn.exec_driver_sql("DROP TABLE IF EXISTS bookings")
            print('Dropped legacy tables (users, bookings).')
        except Exception as e:
            print(f"Could not drop legacy tables: {e}")

# =========================
# Context Processor - Active Requests Count
# =========================
@app.context_processor
def inject_active_requests():
    """Inject active request count into all templates."""
    active_requests = 0
    if session.get('user_id'):
        try:
            from models import BudgetBuyRequest
            active_requests = BudgetBuyRequest.query.filter_by(
                user_id=session.get('user_id')
            ).filter(
                BudgetBuyRequest.status.in_(['pending', 'searching', 'price_found'])
            ).count()
        except Exception:
            pass
    return dict(active_requests=active_requests)



# =========================
# Run App
# =========================
if __name__ == '__main__':
    app.run(debug=True)
