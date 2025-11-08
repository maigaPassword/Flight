# app.py
from flask import Flask, render_template, request
from amadeus import Client, ResponseError
from dotenv import load_dotenv
import os, json

# --- Load environment variables ---
load_dotenv()

# --- Initialize Amadeus client ---
amadeus = Client(
    client_id=os.getenv('AMADEUS_API_KEY'),
    client_secret=os.getenv('AMADEUS_API_SECRET')
)

app = Flask(__name__)

# --- Load airline data from json-file/airlines.json ---
try:
    with open(os.path.join("json-files", "airlines.json"), "r", encoding="utf-8") as f:
        AIRLINES = {item["id"]: item for item in json.load(f)}
except Exception as e:
    print("❌ Could not load airlines.json:", e)
    AIRLINES = {}

# --- Home Page ---
@app.route('/')
def home():
    return render_template('base.html')
@app.route('/result')
def result():
    return render_template('result.html')


# --- Search Flights ---
# --- Search Flights ---
@app.route('/search', methods=['GET', 'POST'])
def search():
    flights = []
    if request.method == 'POST':
        origin = request.form.get('origin')
        destination = request.form.get('destination')
        date = request.form.get('date')

        if origin and destination and date:
            try:
                # Fetch flight offers from Amadeus
                response = amadeus.shopping.flight_offers_search.get(
                    originLocationCode=origin,
                    destinationLocationCode=destination,
                    departureDate=date,
                    adults=1,
                    max=250
                )

                # Build a clean flight list
                for flight in response.data:
                    airline_code = flight["validatingAirlineCodes"][0]
                    airline_info = AIRLINES.get(airline_code, {"name": airline_code, "logo": ""})

                    segments = flight["itineraries"][0]["segments"]
                    stops = len(segments) - 1
                    stops_text = "Non-stop" if stops == 0 else f"{stops} stop{'s' if stops > 1 else ''}"

                    # Baggage info (if available)
                    try:
                        baggage = flight["travelerPricings"][0]["fareDetailsBySegment"][0]["includedCheckedBags"]["weight"]
                    except:
                        baggage = "N/A"

                    # Build segment list for popup
                    segment_list = []
                    for seg in segments:
                        segment_list.append({
                            "origin": seg["departure"]["iataCode"],
                            "destination": seg["arrival"]["iataCode"],
                            "departure": seg["departure"]["at"],
                            "arrival": seg["arrival"]["at"],
                            "duration": seg["duration"][2:].replace("H", "h ").replace("M", "m")
                        })

                    flights.append({
                        "airline_name": airline_info["name"],
                        "airline_logo": airline_info["logo"],
                        "price": flight["price"]["total"],
                        "origin": segments[0]["departure"]["iataCode"],
                        "destination": segments[-1]["arrival"]["iataCode"],
                        "departure": segments[0]["departure"]["at"],
                        "arrival": segments[-1]["arrival"]["at"],
                        "duration": flight["itineraries"][0]["duration"][2:].replace("H", "h ").replace("M", "m"),
                        "baggage": baggage,
                        "stops_text": stops_text,
                        "segments": segment_list
                    })

            except ResponseError as e:
                print("❌ Amadeus API Error:", e)

    return render_template('search.html', flights=flights)

# --- About Page ---
@app.route('/about')
def about():
    return render_template('about.html')

# --- Contact Page ---
@app.route('/contact')
def contact():
    return render_template('contact.html')


if __name__ == '__main__':
    app.run(debug=True)
