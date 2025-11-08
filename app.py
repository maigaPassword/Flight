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
    if request.method == 'POST':
        origin = request.form.get('origin_code') or extract_iata(request.form.get('origin') or request.form.get('origin_display'))
        destination = request.form.get('destination_code') or extract_iata(request.form.get('destination') or request.form.get('destination_display'))
        searched_date = request.form.get("date") or ""

    else:
        origin = extract_iata(request.args.get('origin', ''))
        destination = extract_iata(request.args.get('destination', ''))
        searched_date = request.args.get('date') or ""


    if not searched_date:
        searched_date = datetime.now().strftime("%Y-%m-%d")

    # Date range for 31 days and min prices
    today = datetime.now()
    date_range = [(today + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(31)]
    min_prices = {d: None for d in date_range}

    if origin and destination:

        TRAVEL_CLASSES = ["ECONOMY", "BUSINESS", "FIRST"]
        max_results = 50
        all_flights = []

        # Fetch all cabins separately
        for tclass in TRAVEL_CLASSES:
            try:
                response = amadeus.shopping.flight_offers_search.get(
                    originLocationCode=origin,
                    destinationLocationCode=destination,
                    departureDate=searched_date,
                    adults=1,
                    max=max_results,
                    travelClass=tclass
                )
                all_flights.extend(response.data)
                print(f"✅ Fetched {tclass} flights, count: {len(response.data)}")
            except ResponseError as e:
                print(f"❌ Error fetching {tclass} flights:", e)

        # Merge flights by flight ID and combine fares
        merged_flights = {}
        for flight in all_flights:
            flight_id = flight["id"]
            if flight_id not in merged_flights:
                airline_code = flight["validatingAirlineCodes"][0]
                airline_info = AIRLINES.get(airline_code, {"name": airline_code, "logo": ""})
                segments = flight["itineraries"][0]["segments"]
                stops = len(segments) - 1
                stops_text = "Non-stop" if stops == 0 else f"{stops} stop{'s' if stops > 1 else ''}"

                # Segment list for frontend
                segment_list = [
                    {
                        "origin": seg["departure"]["iataCode"],
                        "destination": seg["arrival"]["iataCode"],
                        "departure": seg["departure"]["at"],
                        "arrival": seg["arrival"]["at"],
                        "duration": seg["duration"][2:].replace("H", "h ").replace("M", "m")
                    }
                    for seg in segments
                ]

                merged_flights[flight_id] = {
                    "offer_id": flight_id,
                    "airline_name": airline_info["name"],
                    "airline_logo": airline_info["logo"],
                    "origin": segments[0]["departure"]["iataCode"],
                    "destination": segments[-1]["arrival"]["iataCode"],
                    "departure": segments[0]["departure"]["at"],
                    "arrival": segments[-1]["arrival"]["at"],
                    "duration": flight["itineraries"][0]["duration"][2:].replace("H", "h ").replace("M", "m"),
                    "stops_text": stops_text,
                    "segments": segment_list,
                    "fares_by_cabin": {},
                    "date": searched_date
                }

            # Add fares to the cabin
            for tp in flight.get("travelerPricings", []):
                for fd in tp.get("fareDetailsBySegment", []):
                    cabin = fd.get("cabin", "ECONOMY")
                    # Inside the loop for fares
                    bags_info = fd.get("includedCheckedBags", {})
                    fare = {
                        "fare_type": fd.get("fareBasis", "Standard"),
                        "price": float(tp.get("price", {}).get("total", 0)),
                        "seat": "Included" if fd.get("seat") else "Not included",
                        "bags": {
                            "quantity": bags_info.get("quantity", 0),
                            "weight": bags_info.get("weight", None),  # may be None
                            "type": bags_info.get("type", None)       # KG/LB if present
                        },
                        "flexibility": "Refundable" if tp.get("refundability") == "REFUNDABLE" else "Non-refundable"
                    }

                    if cabin not in merged_flights[flight_id]["fares_by_cabin"]:
                        merged_flights[flight_id]["fares_by_cabin"][cabin] = []
                    merged_flights[flight_id]["fares_by_cabin"][cabin].append(fare)

        flights = list(merged_flights.values())

        # Calculate min price for the day
        all_prices = [fare["price"] for f in flights for fares in f["fares_by_cabin"].values() for fare in fares]
        if all_prices:
            min_prices[searched_date] = min(all_prices)

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
