from flask import Flask, render_template, request, jsonify
from amadeus import Client, ResponseError
from dotenv import load_dotenv
import os, json
from datetime import datetime, timedelta

# =========================
# Load Environment Variables
# =========================
load_dotenv()

# =========================
# Initialize Amadeus Client
# =========================
amadeus = Client(
    client_id=os.getenv('AMADEUS_API_KEY'),
    client_secret=os.getenv('AMADEUS_API_SECRET')
)

# =========================
# Initialize Flask App
# =========================
app = Flask(__name__)
app.jinja_env.globals['timedelta'] = timedelta  # Needed for Jinja templates

# =========================
# Load Airlines Data
# =========================
try:
    with open(os.path.join("json-files", "airlines.json"), "r", encoding="utf-8") as f:
        AIRLINES = {item["id"]: item for item in json.load(f)}
except Exception as e:
    print("❌ Could not load airlines.json:", e)
    AIRLINES = {}

# =========================
# Load Airports Data
# =========================
try:
    with open(os.path.join("json-files", "airports.json"), encoding="utf-8") as f:
        airports_raw = json.load(f)
        AIRPORTS = {}
        for icao, info in airports_raw.items():
            iata = info.get("iata")
            if iata:
                AIRPORTS[iata] = {
                    "city": info.get("city") or "",
                    "name": info.get("name") or ""
                }
except Exception as e:
    print("❌ Could not load airports.json:", e)
    AIRPORTS = {}

# =========================
# Helper Functions
# =========================
def get_airport_name(code):
    airport = AIRPORTS.get(code)
    return f"{airport['city']} ({code})" if airport else code

# =========================
# Home Page
# =========================
@app.route('/')
def home():
    return render_template('base.html')


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
    searched_date = ""
    origin = destination = None

    # --- Get inputs ---
    if request.method == 'POST':
        origin = request.form.get('origin_code') or extract_iata(request.form.get('origin') or request.form.get('origin_display') or "")
        destination = request.form.get('destination_code') or extract_iata(request.form.get('destination') or request.form.get('destination_display') or "")
        searched_date = request.form.get("date") or ""
    else:
        origin = extract_iata(request.args.get('origin', ''))
        destination = extract_iata(request.args.get('destination', ''))
        searched_date = request.args.get('date') or ""

    # --- Ensure a valid date (ISO) and avoid same-day (Amadeus 4926) ---
    try:
        dt = datetime.strptime(searched_date, "%Y-%m-%d")
    except Exception:
        dt = datetime.now()

    # If user requested today or earlier, use tomorrow
    if dt.date() <= datetime.now().date():
        dt = datetime.now() + timedelta(days=1)
    searched_date = dt.strftime("%Y-%m-%d")

    # --- Date slider / min prices setup ---
    today = datetime.now()
    date_range = [(today + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(31)]
    min_prices = {d: None for d in date_range}

    # --- Only proceed if we have origin + destination ---
    if origin and destination:
        # Option: during development you can use just ECONOMY to reduce calls
        TRAVEL_CLASSES = ["ECONOMY", "BUSINESS", "FIRST"]
        # TRAVEL_CLASSES = ["ECONOMY"]

        max_results = 50
        all_flights = []

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
                # <-- IMPORTANT: add the returned offers into all_flights
                if getattr(response, "data", None):
                    all_flights.extend(response.data)
                    print(f"  → {tclass} returned {len(response.data)} offers")
                else:
                    print(f"  → {tclass} returned no offers")
            except ResponseError as e:
                # print full response payload so we can debug
                try:
                    print("❌ Full error details:", e.response.result)
                    print("Status code:", e.response.status_code)
                except Exception:
                    print("❌ ResponseError:", e)

        # --- Merge flights by ID and build frontend-friendly objects ---
        merged_flights = {}
        for flight in all_flights:
            flight_id = flight.get("id")
            if not flight_id:
                continue

            if flight_id not in merged_flights:
                # safe access to airline info
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

            # Add fares to the cabin (from travelerPricings)
            for tp in flight.get("travelerPricings", []):
                price_total = tp.get("price", {}).get("total", 0)
                for fd in tp.get("fareDetailsBySegment", []):
                    cabin = fd.get("cabin", "ECONOMY")
                    bags_info = fd.get("includedCheckedBags", {}) or {}
                    fare = {
                        "fare_type": fd.get("fareBasis", "Standard"),
                        "price": float(price_total or 0),
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

        # --- Compute minimum price for the searched date (for slider) ---
        all_prices = []
        for f in flights:
            for fares in f.get("fares_by_cabin", {}).values():
                for fare in fares:
                    all_prices.append(fare.get("price", 0))
        if all_prices:
            min_prices[searched_date] = min(all_prices)

        print(f"✅ Total offers after merge: {len(flights)} (raw offers fetched: {len(all_flights)})")
        if len(all_flights) > 0:
            # show a sample for debugging
            try:
                print("Sample offer (first):")
                print(json.dumps(all_flights[0], indent=2)[:4000])  # trim very long prints
            except Exception:
                pass


    return render_template(
        "search.html",
        flights=flights,
        AIRPORTS=AIRPORTS,
        searched_date=searched_date,
        origin=origin,
        destination=destination,
        date_range=date_range,
        min_prices=min_prices
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
    



# =========================
# Run App
# =========================
if __name__ == '__main__':
    app.run(debug=True)
