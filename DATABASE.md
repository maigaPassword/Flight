# Database (SQLite)

This project uses SQLite via Flask-SQLAlchemy.

- Location: `instance/flight.db` (auto-created on first run)
- Models: `models.py` (User, Airline, Airport, Booking)
- Seeding: Airlines and Airports are seeded from `json-files/` on first run when tables are empty.

## Initialize or re-seed manually

Use these from the `Flight` folder in PowerShell on Windows:

```powershell
# Optional: create/activate venv
python -m venv .venv; .\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Initialize DB and seed reference data
flask --app app.py init-db
```

To reset during development, delete `instance/flight.db` and run the `init-db` command again.

## Run the app

```powershell
python app.py
```

On startup you should see a message like:

```
✅ Database ready at: C:\path\to\Flight\instance\flight.db
```
