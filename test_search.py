"""
Quick test to check if JFK -> CDG search returns results
"""
from amadeus import Client, ResponseError
from dotenv import load_dotenv
import os

load_dotenv()

amadeus = Client(
    client_id=os.getenv('AMADEUS_CLIENT_ID'),
    client_secret=os.getenv('AMADEUS_CLIENT_SECRET')
)

print("Testing JFK → CDG on 2025-12-06")
print("=" * 60)

try:
    response = amadeus.shopping.flight_offers_search.get(
        originLocationCode="JFK",
        destinationLocationCode="CDG",
        departureDate="2025-12-06",
        adults=1,
        max=5
    )
    
    if hasattr(response, 'data') and response.data:
        print(f"✅ SUCCESS! Found {len(response.data)} flight offers")
        print("\nFirst flight details:")
        first = response.data[0]
        print(f"  Offer ID: {first.get('id')}")
        print(f"  Price: {first.get('price', {}).get('grandTotal')} {first.get('price', {}).get('currency')}")
        
        itin = first.get('itineraries', [{}])[0]
        segments = itin.get('segments', [])
        if segments:
            print(f"  Airline: {segments[0].get('carrierCode')}")
            print(f"  Departure: {segments[0].get('departure', {}).get('at')}")
            print(f"  Arrival: {segments[-1].get('arrival', {}).get('at')}")
    else:
        print("❌ No flight data returned")
        
except ResponseError as e:
    print(f"❌ API Error: {e}")
    try:
        print(f"Error details: {e.response.result}")
    except:
        pass
except Exception as e:
    print(f"❌ Unexpected error: {e}")

print("=" * 60)
