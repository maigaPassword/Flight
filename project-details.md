## Flight Booking System — Project Details

This document is a comprehensive context summary for the Flight project (Flask-based). It is intended to be given to an AI or new developer to quickly understand the codebase, API surface, frontend structure, runtime requirements, and typical developer workflows.

## Project at-a-glance

- Name: Flight (repository folder: `Flight`)
- Language/Framework: Python 3.x, Flask
- Purpose: A web application that searches flights (via Amadeus APIs), supports one-way and round-trip flows, allows seat selection, payments (Stripe integration), and creates bookings (Amadeus Flight Orders).
- Author / Team: Group 5 (header comment in `app.py`)

## Key files and directories

- `app.py` — Main Flask application (routes, API wrappers, Amadeus + Stripe integrations, helper functions). Contains the application logic and all server routes.
- `requirements.txt` — Python dependencies.
- `json-files/airlines.json` — Local airlines metadata (id, name, logo, etc.).
- `json-files/airports.json` — Local airports mapping (ICAO/IATA, city, name, country) used for autocomplete and display.
- `templates/` — Jinja2 templates for the frontend UI. Key templates found:
  - `home.html` — landing page with search form.
  - `search.html` — flight search results and filters.
  - `flight_information.html` — detailed flight info.
  - `flight_summary.html` — price summary and totals.
  - `seat_selection.html` — seat map UI.
  - `select_return.html` — step to pick a return flight for roundtrip.
  - `booking.html` — passenger details and checkout.
  - `confirmation.html` — booking confirmation page.
  - `base.html` — base layout.
- `static/` — static assets (CSS, JS, images): `css/style.css`, `js/script.js`, `img/`.

## High-level architecture

- Presentation: Jinja2 templates served by Flask endpoints. Frontend uses `static/js/script.js` for interactivity (autocomplete, seat selection, Stripe integration hooks, etc.).
- Backend: Flask app (`app.py`) that:
  - Loads local data (`airlines.json`, `airports.json`).
  - Uses Amadeus SDK for flight searches, pricing, seatmaps, branded fares, inspiration, cheapest dates, order creation and management.
  - Uses Stripe SDK to create PaymentIntents for checkout.
- Data: Primary data sources are local JSON files and Amadeus API responses. The UI expects flight offers to be normalized into a frontend-friendly shape by helper functions in `app.py` (notably `build_flights`).

## Environment variables (important)

The app reads credentials and keys from environment variables (or `.env` via `python-dotenv`):

- `AMADEUS_CLIENT_ID` — Amadeus API client id
- `AMADEUS_CLIENT_SECRET` — Amadeus API client secret
- `STRIPE_SECRET_KEY` — Stripe secret key (used on server)
- `STRIPE_PUBLISHABLE_KEY` — Stripe publishable key (passed to templates)
- `SECRET_KEY` — Flask secret key (session security)

If any of the Amadeus or Stripe keys are missing, some endpoints will gracefully fall back to local data or return helpful error messages (see `create_payment_intent` which checks Stripe config and returns a 500 if not configured).

## Dependencies

See `requirements.txt`. Primary packages:

- `Flask` — web framework
- `amadeus` — Amadeus Python SDK
- `stripe` — Stripe Python client
- `python-dotenv` — load `.env` files

Exact pinned versions are in `requirements.txt`.

## How to run (development) — PowerShell (Windows)

1. Create and activate a virtual environment (optional but recommended):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install dependencies:

```powershell
pip install -r requirements.txt
```

3. Create a `.env` file in the `Flight` folder (or set environment variables) with values for:

- `AMADEUS_CLIENT_ID`
- `AMADEUS_CLIENT_SECRET`
- `STRIPE_SECRET_KEY`
- `STRIPE_PUBLISHABLE_KEY`
- `SECRET_KEY`

Example `.env` (DO NOT commit to repo):

```text
AMADEUS_CLIENT_ID=your_id_here
AMADEUS_CLIENT_SECRET=your_secret_here
STRIPE_SECRET_KEY=sk_test_xxx
STRIPE_PUBLISHABLE_KEY=pk_test_xxx
SECRET_KEY=change-this-secret
```

4. Run the app (development mode):

```powershell
# from inside c:\Users\shail\skyvela\Flight
python app.py
```

The app runs with `debug=True` by default when executed directly (`app.run(debug=True)` in `app.py`).

## API surface (routes & short descriptions)

This app exposes both page routes (render templates) and JSON APIs used by the frontend or third-party clients. Below is a non-exhaustive list extracted from `app.py`.

- GET `/` → Home page (template: `home.html`) — search form
- GET/POST `/search` → Search flights (renders `search.html`) — handles one-way and roundtrip; uses `build_flights` which calls Amadeus.
- GET `/flight_details` → Returns detailed flight pricing JSON for an `offer_id` (calls Amadeus pricing endpoint).
- GET `/flight_information` → Renders `flight_information.html` for a selected flight (accepts `offer_json` and `cabin` query params).
- POST `/flight_summary` → Renders `flight_summary.html` combining outbound and optional return flight JSONs.
- POST `/seat_selection` → Renders `seat_selection.html` for seat map display.
- POST `/select_return` → Renders `select_return.html` with return flight options (used in roundtrip flow).
- POST `/booking` → Renders `booking.html` (passenger details form) and calculates passenger-type pricing.
- POST `/create-payment-intent` → JSON API to create Stripe PaymentIntent. Expects JSON body with `amount` and optional metadata like `passenger_name`/`email`.
- POST `/confirmation` → Renders `confirmation.html` after payment/booking; accepts passenger and booking form data.

JSON API endpoints (programmatic):

- GET `/api/airports/search?keyword=...` → Autocomplete airport suggestions (local `AIRPORTS` first, falls back to Amadeus).
- POST `/api/book-flight` → Create flight order (Amadeus Flight Orders API). Payload: JSON with `flightOffer` and `travelers`.
- GET `/api/orders/<order_id>` → Retrieve flight order details.
- DELETE `/api/orders/<order_id>/cancel` → Cancel an order.
- GET `/api/airlines/<airline_code>` → Airline meta lookup.
- POST `/api/seatmaps` → Get seatmaps for a flight offer (Amadeus seatmaps).
- GET `/api/checkin-links?airlineCode=...` → Airline check-in URL lookup.
- POST `/api/branded-fares` → Branded fares upsell retrieval.
- GET `/api/inspiration` → Flight inspiration (cheapest destinations from origin).
- GET `/api/cheapest-dates` → Cheapest dates API.
- GET `/api/airline-routes` → Airline route info.
- GET `/api/delay-prediction` → Delay prediction API (uses Amadeus predictions).

Notes: many APIs require Amadeus credentials (or will return helpful errors). Responses are normalized and/or transformed into frontend-friendly structures in `app.py`.

## Data shapes and examples (common payloads)

- Flight offer (frontend-friendly shape produced by `build_flights` — simplified):

```json
{
  "offer_id": "12345",
  "airline_name": "Example Air",
  "airline_logo": "",
  "origin": "JFK",
  "destination": "LAX",
  "departure": "2025-12-01T08:00:00",
  "arrival": "2025-12-01T11:00:00",
  "duration": "5h 0m",
  "stops_text": "Non-stop",
  "segments": [{"origin":"JFK","destination":"LAX","departure":"...","arrival":"...","duration":"..."}],
  "fares_by_cabin": {"ECONOMY": [{"fare_type":"Standard","price":250.0,"base":200.0,"taxes":50.0,...}], "BUSINESS": [...]}
}
```

- Booking payload (for `/api/book-flight`):

```json
{
  "flightOffer": { ... },
  "travelers": [
    {
      "id": "1",
      "dateOfBirth": "1990-01-01",
      "name": {"firstName": "John", "lastName": "Doe"},
      "gender": "MALE",
      "contact": {"emailAddress": "john@example.com", "phones": [...]}
    }
  ]
}
```

- Stripe create-payment-intent expects JSON like:

```json
{ "amount": 199.99, "passenger_name": "John Doe", "email": "john@example.com" }
```

Responses for the Amadeus-backed APIs are proxied or transformed; check `app.py` for exact fields and error handling.

## Frontend flow / user workflow

Typical user flow implemented by the app:

1. Home (`/`) — user enters origin/destination, dates, passengers, and trip type.
2. Search (`/search`) — backend calls Amadeus via `build_flights` and returns offers grouped by cabin class.
3. User clicks a flight → `flight_information` page to view selected option and fare details.
4. For roundtrip: after selecting an outbound, user goes to `select_return` to choose the return flight.
5. Flight summary (`/flight_summary`) — shows combined pricing and allows seat selection.
6. Seat selection (`/seat_selection`) optionally uses `/api/seatmaps` to fetch seat maps.
7. Booking (`/booking`) — user fills passenger details and proceeds to checkout; frontend creates a Stripe PaymentIntent via `/create-payment-intent`.
8. After successful payment and (optionally) a call to `/api/book-flight`, the user sees `confirmation` with booking reference and details.

## Testing and verification notes

- No unit tests are included in the repository snapshot. If you add tests, prefer `pytest` and create small fixtures for typical Amadeus responses. Mock calls to Amadeus and Stripe when running CI.
- Quick manual verification steps:
  - Ensure environment variables are set (or use test keys).
  - Run `python app.py` and navigate to `http://127.0.0.1:5000/`.
  - Try searching for common airport codes (e.g., `JFK`, `LAX`, `CDG`). The local `airports.json` is the primary source for autocompletion.

## Quality and limitations

- The app uses live Amadeus APIs extensively. In test/dev environments without proper Amadeus credentials, many endpoints will either fall back to local data or return helpful errors. That behavior is intentional.
- Security: secret keys (Stripe, Amadeus, Flask SECRET_KEY) must not be committed to source. Use `.env` for local development.
- Performance: `build_flights` currently loops over multiple cabin classes and can fetch many offers (max=50 per class). For development, it suggests limiting to `ECONOMY` to reduce calls and latency.

## Developer handoff / suggestions

- Add a `.env.example` with placeholder variable names (no secrets) to make onboarding easier.
- Add lightweight unit tests for helper functions (`normalize_date`, `extract_iata`, `build_flights` with mocked client) and endpoint smoke tests for key routes.
- Consider extracting Amadeus and Stripe wrappers to a separate module for cleaner separation and easier mocking.
- Add basic logging configuration (instead of print statements) to ease debugging and log collection.

## Where to look for behavior/details in code

- Search `app.py` for `@app.route` decorators to see routes and parameters.
- Inspect `build_flights` for how flight offers are normalized and how `fares_by_cabin` is structured.
- Review `templates/` for expected context keys the templates expect (e.g., `outbound_json`, `adults`, `fares_by_cabin`).

## Contact / notes

If you need more details about a specific route, data shape, or want me to generate a JSON schema for an endpoint (e.g., `/api/book-flight` payload), say which endpoint and I'll produce one.

---

Generated for: repository `Flight` (folder)
