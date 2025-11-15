# ✈️ Seat Selection Feature - Implementation Guide

## 🎯 Overview
Interactive seat map selection allowing passengers to choose their preferred seats before booking, with real-time pricing and visual seat availability.

---

## 🚀 How to Use Seat Selection

### Step-by-Step User Flow:

1. **Search for Flights**
   - Go to http://127.0.0.1:5000
   - Enter origin (e.g., "CDG" or type "paris" for autocomplete)
   - Enter destination (e.g., "JFK" or type "new york")
   - Select departure date
   - Click "Search Flights"

2. **Select Your Flight**
   - Browse available flights on the results page
   - Click "Select" on your preferred flight

3. **Review Flight Summary**
   - On the summary page, you'll see **TWO buttons**:
     - **"Select Seats"** (NEW!) - Opens the interactive seat map
     - **"Continue to Booking"** - Skips seat selection

4. **Choose Your Seats** (NEW FEATURE!)
   - Click "Select Seats" button
   - View the interactive aircraft cabin layout
   - Available seats show in blue
   - Occupied seats show greyed out
   - Extra legroom seats have a ⭐ icon
   - Click on seats to select/deselect
   - See your selections and pricing in real-time
   - Can select up to the number of passengers
   - Click "Continue to Booking" with seats
   - OR click "Skip Seat Selection" to proceed without seats

5. **Complete Booking**
   - Fill in passenger details
   - Complete payment with Stripe
   - Receive confirmation with seat assignments (if selected)

---

## 🎨 Features Implemented

### Visual Features:
- ✅ **Interactive Seatmap** - Visual aircraft layout with clickable seats
- ✅ **Color-Coded Seats** - Available (blue), Occupied (grey), Selected (cyan glow)
- ✅ **Special Seats** - Extra legroom seats marked with ⭐
- ✅ **Aircraft Styling** - Realistic cabin appearance with nose/tail
- ✅ **Real-Time Feedback** - Instant visual feedback on selection
- ✅ **Responsive Layout** - Works on all screen sizes

### Functional Features:
- ✅ **Seat Pricing** - Individual seat pricing (extra legroom = $25, standard = $15)
- ✅ **Passenger Limits** - Can't select more seats than passengers
- ✅ **Price Calculator** - Real-time total price with seat costs
- ✅ **Selected Seats Summary** - Shows all selected seats with remove option
- ✅ **Amadeus API Integration** - Calls `/api/seatmaps` for real seatmap data
- ✅ **Mock Fallback** - Shows realistic seatmap if API data unavailable

### Technical Features:
- ✅ **Amadeus SeatMap API** - `/api/seatmaps` endpoint implemented
- ✅ **Seat Characteristics** - Parses legroom, window, aisle info
- ✅ **Session Persistence** - Seats passed through booking flow
- ✅ **Form Integration** - Seats included in booking submission

---

## 📋 Seatmap Layout

### Mock Seatmap Configuration:
```
Row 1-20
Columns: A B C | AISLE | D E F

A & F = Window seats
C & D = Aisle seats
B & E = Middle seats

Row 1 & 12 = Extra legroom (exit rows) - $25
Other rows = Standard seats - $15
```

### Legend:
- 🟦 **Blue** - Available seat
- ⚪ **Grey** - Occupied seat
- 🔵 **Cyan Glow** - Your selected seat
- ⭐ **Star Icon** - Extra legroom seat

---

## 🔧 Technical Implementation

### New Files Created:
1. **`templates/seat_selection.html`** (600+ lines)
   - Full interactive UI with aircraft visualization
   - Real-time seat selection JavaScript
   - Amadeus API integration
   - Mock seatmap fallback

### Modified Files:
1. **`app.py`**
   - Added `/seat_selection` route (POST)
   - Modified `flight_summary` to pass JSON data
   - Modified `booking` route to accept selected seats
   - Already had `/api/seatmaps` API endpoint

2. **`templates/flight_summary.html`**
   - Added "Select Seats" button
   - Kept "Continue to Booking" for skip option
   - Both buttons pass same form data

---

## 🎯 API Endpoints Used

### 1. `/api/seatmaps` (POST)
**Purpose:** Fetch real seatmap data from Amadeus

**Request:**
```javascript
fetch('/api/seatmaps', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    flightOffer: {...} // Flight offer object
  })
})
```

**Response:**
```json
{
  "success": true,
  "seatmaps": [{
    "segmentId": "1",
    "carrierCode": "AF",
    "aircraft": "320",
    "decks": [{
      "seats": [
        {
          "number": "1A",
          "characteristicsCodes": ["WINDOW", "LEG_SPACE"],
          "travelerPricing": [{"price": "25.00"}],
          "coordinates": {"x": 0, "y": 0}
        }
      ]
    }]
  }]
}
```

### 2. `/seat_selection` (POST)
**Purpose:** Display seat selection page

**Form Data:**
- `outbound_json` - Flight data
- `return_json` - Return flight data (optional)
- `cabin_out` - Cabin class
- `total_price` - Current price
- Other booking data

**Returns:** Seat selection HTML page

---

## 💰 Pricing Structure

### Base Flight Price:
Passed from flight summary

### Seat Costs:
- **Standard Seat:** $15.00 per seat
- **Extra Legroom:** $25.00 per seat (rows 1, 12)
- **Total:** Base Price + (Seat Price × Selected Seats)

### Example:
```
Flight: $500.00
2 Passengers select 2 extra legroom seats ($25 each)
Total: $500.00 + $50.00 = $550.00
```

---

## 🧪 Testing the Feature

### Test Scenario 1: Basic Seat Selection
1. Search: CDG → JFK on any future date
2. Select any flight
3. Click "Select Seats"
4. Choose 1 seat (e.g., "5A")
5. Verify seat highlights in cyan
6. Check summary shows "Seat 5A"
7. Check total price updated
8. Click "Continue to Booking"
9. Verify seats passed to booking page

### Test Scenario 2: Multiple Passengers
1. On home page, select 3 passengers (click passenger icon)
2. Search and select flight
3. Click "Select Seats"
4. Try selecting 4 seats → Should block (limit = 3)
5. Select 3 different seats
6. Verify all 3 shown in summary
7. Remove one seat by clicking × 
8. Verify price updates
9. Continue to booking

### Test Scenario 3: Skip Seat Selection
1. Search and select flight
2. On summary page, click "Continue to Booking" (not "Select Seats")
3. Verify goes directly to booking page
4. No seats shown, original price maintained

### Test Scenario 4: Extra Legroom
1. Select seats on Row 1 or Row 12
2. Verify ⭐ icon appears
3. Verify price is $25 (not $15)
4. Check total price calculation

---

## 🎨 UI/UX Highlights

### Aircraft Visualization:
- Rounded aircraft nose at top
- Gradient background simulating fuselage
- Proper aisle spacing (3-3 configuration)
- Row numbers on left
- Seat letters (A-F) in seats

### Interactive Elements:
- **Hover Effect:** Seats scale up and glow blue
- **Click Effect:** Selected seats glow cyan with shadow
- **Disable Effect:** Occupied seats can't be clicked (cursor: not-allowed)
- **Legend:** Clear visual guide at bottom

### Responsive Design:
- Centers on all screen sizes
- Seat grid adapts to viewport
- Touch-friendly for mobile (45px × 45px seats)

---

## 📊 Data Flow

```
1. Flight Summary Page
   ↓
   [User clicks "Select Seats"]
   ↓
2. POST to /seat_selection
   - Carries: flight JSON, cabin, price, passenger count
   ↓
3. Seat Selection Page Loads
   - Displays flight info header
   - Calls /api/seatmaps with flight data
   ↓
4. JavaScript Renders Seatmap
   - Real data from API OR mock fallback
   - User selects seats
   - Calculates pricing
   ↓
5. POST to /booking
   - Carries: all flight data + selected_seats
   - Updates total_price with seat costs
   ↓
6. Booking Page
   - Shows flight + seat details
   - Proceeds to payment
```

---

## 🔮 Future Enhancements

### Potential Additions:
- 🎨 3D seat visualization
- 💺 Seat characteristics badges (legroom, recline, power outlet)
- 🎫 Paid seat upgrades at checkout
- 📱 Mobile-optimized touch gestures
- 🔄 Live seat availability updates
- 💳 Seat-only purchases for existing bookings
- 📊 Popular seat heat maps
- 🎯 Seat recommendations based on preferences

---

## ⚠️ Known Limitations

### Test Environment:
- Amadeus SeatMap API may have limited data for test flights
- Falls back to realistic mock seatmap automatically
- Mock uses randomized occupancy (70% available, 30% taken)

### Current Scope:
- Single cabin class only (selected cabin)
- No multi-segment seatmap (shows first segment)
- No seat hold/lock functionality
- Pricing is simplified (doesn't vary by actual airline pricing)

---

## 📝 Code Structure

### Template Organization:
```html
<div class="seat-selection-container">
  <!-- Flight Info Header -->
  <div class="flight-info-header">
    Route, Airline, Cabin, Passengers
  </div>
  
  <!-- Selected Seats Summary -->
  <div class="selected-seats-summary">
    List of selected seats with remove buttons
    Total price display
  </div>
  
  <!-- Interactive Seatmap -->
  <div class="seatmap-section">
    <div class="aircraft-container">
      Rows of seats with click handlers
    </div>
    <div class="seat-legend">
      Visual guide
    </div>
  </div>
  
  <!-- Action Buttons -->
  <div class="action-buttons">
    Skip button | Continue button
  </div>
</div>
```

### JavaScript Functions:
- `loadSeatmap()` - Fetches from API
- `renderSeatmap(data)` - Renders real API data
- `showMockSeatmap()` - Fallback to mock
- `toggleSeat(number, price)` - Select/deselect
- `updateSummary()` - Update price and display

---

## 🎉 Summary

**Seat selection is now fully integrated** into your flight booking flow! Users can:
- ✈️ View realistic aircraft seat layouts
- 🪑 Select their preferred seats visually
- 💵 See real-time pricing with seat costs
- ⏭️ Skip if they don't want to choose seats
- 🎯 Complete booking with seat assignments

The feature uses the Amadeus SeatMap Display API with intelligent fallback to a mock seatmap for demo purposes.

---

**Server Status:** Running at http://127.0.0.1:5000
**Ready to Test:** Yes! Search for flights and try the seat selection now!

---

Generated: November 14, 2025
