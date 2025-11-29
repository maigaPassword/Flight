# Skyela Admin Dashboard - Quick Start Guide

## 🚀 Quick Setup (5 minutes)

### Step 1: Install Dependencies (if not already installed)

```bash
pip install flask flask-sqlalchemy werkzeug python-dotenv stripe amadeus
```

### Step 2: Initialize Database

```bash
# Navigate to project directory
cd Flight-1

# Initialize database with new admin models
flask init-db
```

### Step 3: Create Admin User

```bash
# Run the admin creation script
python create_admin.py
```

**Default credentials created:**
- Email: `admin@skyela.com`
- Password: `admin123`

### Step 4: Start the Server

```bash
# Run Flask development server
python app.py
```

### Step 5: Access Admin Dashboard

Open your browser and navigate to:
```
http://localhost:5000/admin/dashboard
```

Login with the credentials from Step 3.

## 📋 What's Included

### Pages
✅ Dashboard Home (metrics + charts)
✅ Bookings Manager (with detail modal)
✅ Users Manager
✅ Payments Viewer
✅ Refunds Manager
✅ Flight API Manager
✅ System Settings
✅ API Logs Viewer

### Features
✅ Responsive design (mobile + desktop)
✅ RESTful API architecture
✅ Secure payment handling (no CVV/PAN storage)
✅ Real-time metrics
✅ Data pagination
✅ Advanced filters
✅ Chart visualizations (ApexCharts)

## 🔑 Creating Additional Admin Users

### Method 1: Use the script

```bash
python create_admin.py
```

Follow the prompts to create a new admin user.

### Method 2: Use Flask shell

```bash
flask shell
```

```python
from models import User, db
from werkzeug.security import generate_password_hash

admin = User(
    name='Your Name',
    email='your@email.com',
    password_hash=generate_password_hash('yourpassword'),
    is_admin=True
)
db.session.add(admin)
db.session.commit()
exit()
```

## 🧪 Testing the Dashboard

### 1. Create Test Data

You can create sample bookings, payments, and users through the main website interface, or use the Flask shell:

```python
flask shell
```

```python
from models import *
from datetime import datetime

# Create a test booking
booking = Booking(
    user_id=1,
    pnr='ABC123',
    origin='JFK',
    destination='LAX',
    departure_date=datetime.utcnow(),
    airline='AA',
    passengers_json='[{"first_name": "John", "last_name": "Doe"}]',
    base_price=250.00,
    taxes=50.00,
    total_amount=300.00,
    currency='USD',
    status='confirmed',
    api_provider='Amadeus'
)
db.session.add(booking)
db.session.commit()
```

### 2. Test API Provider

1. Go to **Flight API Manager**
2. Click "Add Provider"
3. Fill in details:
   - Name: `Test Provider`
   - API Key: `test_key_123`
   - API Secret: `test_secret_456`
   - Markup: `5.0`
4. Click "Test Connection"

### 3. Test Refund Processing

1. Go to **Bookings Manager**
2. Click "View" on any confirmed booking
3. Click "Process Refund"
4. Check **Refunds** page to see the refund request

## 📊 Dashboard Features Overview

### Dashboard Metrics
- **Total Bookings**: Lifetime booking count
- **Total Revenue**: Sum of completed payments
- **Today's Bookings**: Bookings created today
- **Pending Bookings**: Awaiting confirmation

### Bookings Manager
- Filter by status (pending/confirmed/cancelled/refunded)
- View complete booking details
- Process refunds with one click
- See passenger information
- View API logs for each booking

### Users Manager
- See all registered users
- View total spending per user
- Track booking counts
- See saved payment methods (tokenized)

### Payments
- All payment transactions
- Filter by status
- View payment provider details
- See card info (last 4 digits only)

### Refunds
- Manage refund requests
- Approve/deny/process refunds
- Add admin notes
- Track refund status

### Flight API Manager
- Add multiple API providers
- Configure API credentials
- Set markup percentages
- Test connections
- Enable/disable providers

### System Settings
- Configure app name and logo
- Set default currency
- Configure SMTP for emails
- Configure SMS provider
- Set global markup

### API Logs
- View all API requests
- Filter by type (search/book/webhook)
- See response codes
- Track errors
- Debug integration issues

## 🔒 Security Notes

### Payment Security
- ✅ NO CVV stored anywhere
- ✅ NO full card numbers stored
- ✅ Only last 4 digits + payment tokens
- ✅ Uses payment_method_id for off-session charges

### Admin Access
- ✅ Protected routes with `@admin_required`
- ✅ Session-based authentication
- ✅ Password hashing with werkzeug
- ✅ Admin flag in User model

## 🛠️ Troubleshooting

### Issue: "Admin access required" error

**Solution:** Make sure the user has `is_admin=True`:

```python
flask shell
```

```python
from models import User, db
user = User.query.filter_by(email='admin@skyela.com').first()
user.is_admin = True
db.session.commit()
```

### Issue: "Module not found" errors

**Solution:** Install missing dependencies:

```bash
pip install flask flask-sqlalchemy werkzeug
```

### Issue: Database errors

**Solution:** Re-initialize the database:

```bash
flask init-db
```

### Issue: Can't access /admin/dashboard

**Solution:** Make sure the blueprint is registered in app.py and the server is running.

## 📁 File Structure

```
Flight-1/
├── admin_routes.py              # Admin API routes
├── create_admin.py              # Admin user creation script
├── models.py                    # Database models (updated)
├── app.py                       # Main app (blueprint registered)
├── static/
│   └── css/
│       └── admin_dashboard.css  # Admin styles
└── templates/
    ├── admin_base.html          # Base template
    ├── admin_login.html         # Login page
    ├── admin_dashboard.html     # Dashboard home
    ├── admin_bookings.html      # Bookings manager
    ├── admin_users.html         # Users manager
    ├── admin_payments.html      # Payments
    ├── admin_refunds.html       # Refunds
    ├── admin_flight_api.html    # API manager
    ├── admin_settings.html      # Settings
    └── admin_logs.html          # Logs
```

## 🎯 Next Steps

1. **Customize Branding**: Update logo and colors in settings
2. **Configure API Providers**: Add your Amadeus/Duffel credentials
3. **Set up SMTP**: Enable email notifications
4. **Add More Admins**: Create additional admin users
5. **Review Security**: Change default admin password
6. **Test Thoroughly**: Create test bookings and payments

## 💡 Tips

- Use **Chrome DevTools** (F12) to debug JavaScript issues
- Check **Flask console** for backend errors
- Use **Network tab** to inspect API calls
- **Pagination** shows 50 items per page by default
- **Charts** use ApexCharts library (no setup needed)

## 📞 Support

For issues or questions:
1. Check this guide
2. Review ADMIN_DASHBOARD.md
3. Check Flask console for errors
4. Verify database migrations

---

**Ready to use! 🎉**

Navigate to http://localhost:5000/admin/dashboard and start managing your flight booking platform!
