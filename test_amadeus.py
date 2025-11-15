"""
Test Amadeus API Connection
"""
from amadeus import Client, ResponseError
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Initialize Amadeus client
amadeus = Client(
    client_id=os.getenv('AMADEUS_CLIENT_ID'),
    client_secret=os.getenv('AMADEUS_CLIENT_SECRET')
)

print("="*60)
print("Testing Amadeus API Connection")
print("="*60)
print(f"Client ID: {os.getenv('AMADEUS_CLIENT_ID')}")
print(f"Client Secret: {os.getenv('AMADEUS_CLIENT_SECRET')[:10]}...")
print("="*60)

# Test a simple flight search
try:
    print("\n🔍 Testing flight search: JFK -> LAX on 2025-12-15")
    response = amadeus.shopping.flight_offers_search.get(
        originLocationCode='JFK',
        destinationLocationCode='LAX',
        departureDate='2025-12-15',
        adults=1,
        max=5
    )
    
    print(f"\n✅ SUCCESS! Found {len(response.data)} flight offers")
    
    if response.data:
        flight = response.data[0]
        print(f"\nFirst flight example:")
        print(f"  - Airline: {flight.get('validatingAirlineCodes', ['Unknown'])[0]}")
        print(f"  - Price: {flight.get('price', {}).get('total')} {flight.get('price', {}).get('currency')}")
        itinerary = flight.get('itineraries', [{}])[0]
        print(f"  - Duration: {itinerary.get('duration', 'Unknown')}")
    
except ResponseError as e:
    print(f"\n❌ ERROR: ResponseError occurred")
    try:
        error_data = e.response.result
        print(f"Status Code: {e.response.status_code}")
        print(f"Error Details: {error_data}")
    except:
        print(f"Error: {e}")
except Exception as e:
    print(f"\n❌ ERROR: {type(e).__name__}: {e}")

print("\n" + "="*60)
