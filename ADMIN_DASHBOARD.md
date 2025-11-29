# Skyela Admin Dashboard

Complete admin dashboard for the Skyela flight booking platform.

## Features

### Dashboard Home
- **Metrics Cards**: Total bookings, revenue, today's bookings, pending bookings
- **Charts**: 7-day bookings trend visualization (ApexCharts)
- **Recent Bookings Table**: Last 10 bookings with quick overview

### Bookings Manager
- **List View**: All flight bookings with pagination
- **Filters**: Filter by status (pending, confirmed, cancelled, refunded)
- **Detail Modal**: Complete booking information including:
  - Customer details
  - Flight information
  - Passenger list
  - Fare breakdown
  - Payment information
  - API logs
- **Refund Processing**: One-click refund functionality

### Users Manager
- **User List**: All registered users with statistics
- **User Metrics**: Total spent, booking count, saved payment methods
- **Pagination**: Efficient navigation through large user bases

### Payments
- **Transaction List**: All payment transactions
- **Filter by Status**: completed, pending, failed, refunded
- **Payment Details**: Provider, transaction ID, card info (last 4 digits only)

### Refunds
- **Refund Requests**: All refund requests with status tracking
- **Admin Actions**: Approve, deny, or process refunds
- **Status Management**: pending, approved, denied, processed

### Flight API Manager
- **Provider Management**: Add/edit flight API providers (Amadeus, Duffel, etc.)
- **Configuration**: API keys, secrets, markup percentages
- **Test Connection**: Verify API connectivity with sample data
- **Enable/Disable**: Toggle provider availability

### System Settings
- **General**: App name, logo, default currency
- **Pricing**: Global markup percentage
- **SMTP**: Email server configuration
- **SMS**: SMS provider settings

### API Logs
- **Log Viewer**: All API requests and webhook calls
- **Filter by Type**: flight_search, flight_book, webhook
- **Error Tracking**: View failed requests with error messages
- **Pagination**: Browse through extensive log history

## Database Models

### New Models Added

```python
# Admin user flag
User.is_admin (Boolean)

# Booking management
Booking - Flight bookings with PNR, passengers, pricing, status

# Payment processing
Payment - Transaction records (NO CVV, NO full PAN stored)

# Refund handling
RefundRequest - Refund requests with admin workflow

# API provider management
FlightAPIProvider - API credentials and configuration

# System configuration
SystemSettings - App-wide settings

# Logging
APILog - API request/response logs
```

## API Endpoints

### Metrics & Dashboard
- `GET /admin/api/metrics` - Dashboard metrics and charts data

### Bookings
- `GET /admin/api/bookings` - List all bookings (with filters)
- `GET /admin/api/bookings/<id>` - Get booking details
- `POST /admin/api/bookings/<id>/refund` - Process refund

### Users
- `GET /admin/api/users` - List all users with statistics

### Payments
- `GET /admin/api/payments` - List all payment transactions

### Refunds
- `GET /admin/api/refunds` - List all refund requests
- `PUT /admin/api/refunds/<id>` - Update refund status

### Flight API Providers
- `GET /admin/api/flight-api` - List all providers
- `POST /admin/api/flight-api` - Add new provider
- `PUT /admin/api/flight-api/<id>` - Update provider
- `POST /admin/api/flight-api/<id>/test` - Test connection

### Settings
- `GET /admin/api/settings` - Get system settings
- `PUT /admin/api/settings` - Update settings

### Logs
- `GET /admin/api/logs` - Get API logs (with filters)

## Security

### Admin Authentication
- All admin routes protected with `@admin_required` decorator
- Checks user session and admin flag
- Returns 401 (unauthorized) or 403 (forbidden) for non-admin users

### Payment Security
- **NO CVV storage** - Never stored in database
- **NO full card numbers** - Only last 4 digits stored
- **Tokenization** - Uses payment_method_id tokens for off-session charges
- **Provider Integration** - Supports Stripe, Checkout.com, Flutterwave

## Setup Instructions

### 1. Database Migration

```bash
# Initialize database with new models
flask init-db
```

### 2. Create Admin User

```python
from app import app, db
from models import User
from werkzeug.security import generate_password_hash

with app.app_context():
    admin = User(
        name='Admin User',
        email='admin@skyela.com',
        password_hash=generate_password_hash('admin123'),
        is_admin=True
    )
    db.session.add(admin)
    db.session.commit()
    print('Admin user created!')
```

### 3. Access Dashboard

Navigate to: `http://localhost:5000/admin/dashboard`

Default credentials:
- Email: `admin@skyela.com`
- Password: `admin123`

## File Structure

```
Flight-1/
├── admin_routes.py              # Admin API endpoints and routes
├── models.py                    # Database models (updated)
├── app.py                       # Main Flask app (blueprint registered)
├── static/
│   └── css/
│       └── admin_dashboard.css  # Admin dashboard styles
└── templates/
    ├── admin_base.html          # Base layout with sidebar
    ├── admin_login.html         # Admin login page
    ├── admin_dashboard.html     # Dashboard home
    ├── admin_bookings.html      # Bookings manager
    ├── admin_users.html         # Users manager
    ├── admin_payments.html      # Payments viewer
    ├── admin_refunds.html       # Refunds manager
    ├── admin_flight_api.html    # API providers
    ├── admin_settings.html      # System settings
    └── admin_logs.html          # API logs viewer
```

## Technologies Used

- **Backend**: Flask, SQLAlchemy
- **Frontend**: HTML5, CSS3, JavaScript (Vanilla)
- **Charts**: ApexCharts
- **Icons**: Font Awesome 6
- **Database**: SQLite (production: MySQL/PostgreSQL)

## Features Summary

✅ Modern, responsive admin interface
✅ Dark sidebar navigation
✅ Metrics cards with icons
✅ Data tables with pagination
✅ Modal dialogs for details
✅ Chart visualizations
✅ RESTful API architecture
✅ Secure payment handling (no sensitive data storage)
✅ API provider management
✅ Comprehensive logging
✅ Filter and search capabilities
✅ Mobile-responsive design

## API Provider Examples

### Add Amadeus Provider

```json
{
  "name": "Amadeus",
  "api_key": "your_amadeus_api_key",
  "api_secret": "your_amadeus_api_secret",
  "markup_percentage": 5.0,
  "is_active": true
}
```

### Add Duffel Provider

```json
{
  "name": "Duffel",
  "api_key": "duffel_live_xxxxx",
  "api_secret": "duffel_secret_xxxxx",
  "markup_percentage": 3.5,
  "is_active": true
}
```

## Notes

- **No Agent System**: This dashboard is for admins only, no agent/commission features
- **Flight Focus**: Only flight bookings, no hotels or tours
- **Payment Tokens**: All payments use tokenized payment methods for security
- **Off-Session Charges**: Admins can trigger charges using stored payment_method_id tokens
- **Responsive**: Works on desktop, tablet, and mobile devices

## Support

For issues or questions about the admin dashboard, check:
1. Database migrations are up to date
2. Admin user is created with `is_admin=True`
3. All dependencies are installed
4. Flask server is running in debug mode for development

---

**Built for Skyela Flight Booking Platform**
