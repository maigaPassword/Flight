"""
Admin Dashboard Routes for Skyela Flight Booking Platform
==========================================================
RESTful API endpoints for admin dashboard functionality.
All routes require admin authentication.
"""

from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from functools import wraps
from datetime import datetime, timedelta
from sqlalchemy import func, desc
import json

from models import (
    db, User, Booking, Payment, RefundRequest, FlightAPIProvider,
    SystemSettings, APILog, Search, BudgetBuyRequest, UserCardInformation
)

# Create Blueprint
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# =========================
# Admin Authentication Decorator
# =========================
def admin_required(f):
    """Decorator to require admin authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('user_id'):
            # Check if this is an API request or page request
            if request.path.startswith('/admin/api/'):
                return jsonify({'error': 'Authentication required'}), 401
            else:
                # Redirect to login page for HTML page requests
                return redirect(url_for('login'))
        
        user = User.query.get(session.get('user_id'))
        if not user or not user.is_admin:
            # Check if this is an API request or page request
            if request.path.startswith('/admin/api/'):
                return jsonify({'error': 'Admin access required'}), 403
            else:
                # Redirect to login with error message
                from flask import flash
                flash('Admin access required. Please login with an admin account.', 'error')
                return redirect(url_for('login'))
        
        return f(*args, **kwargs)
    return decorated_function


# =========================
# Admin Pages (HTML Templates)
# =========================

@admin_bp.route('/login')
def login_page():
    """Admin login page"""
    return render_template('admin_login.html')


@admin_bp.route('/dashboard')
@admin_required
def dashboard_page():
    """Admin dashboard home"""
    return render_template('admin_dashboard.html')


@admin_bp.route('/bookings')
@admin_required
def bookings_page():
    """Bookings management page"""
    return render_template('admin_bookings.html')


@admin_bp.route('/users')
@admin_required
def users_page():
    """Users management page"""
    return render_template('admin_users.html')


@admin_bp.route('/payments')
@admin_required
def payments_page():
    """Payments management page"""
    return render_template('admin_payments.html')


@admin_bp.route('/refunds')
@admin_required
def refunds_page():
    """Refunds management page"""
    return render_template('admin_refunds.html')


@admin_bp.route('/flight-api')
@admin_required
def flight_api_page():
    """Flight API providers management page"""
    return render_template('admin_flight_api.html')


@admin_bp.route('/settings')
@admin_required
def settings_page():
    """System settings page"""
    return render_template('admin_settings.html')


@admin_bp.route('/logs')
@admin_required
def logs_page():
    """API logs viewer page"""
    return render_template('admin_logs.html')


# =========================
# API Endpoints
# =========================

@admin_bp.route('/api/metrics')
@admin_required
def get_metrics():
    """Get dashboard metrics"""
    try:
        # Date ranges
        today = datetime.utcnow().date()
        week_ago = today - timedelta(days=7)
        
        # Total bookings
        total_bookings = Booking.query.count()
        
        # Total revenue
        total_revenue = db.session.query(func.sum(Payment.amount)).filter(
            Payment.status == 'completed'
        ).scalar() or 0
        
        # Today's bookings
        today_bookings = Booking.query.filter(
            func.date(Booking.created_at) == today
        ).count()
        
        # Pending bookings
        pending_bookings = Booking.query.filter_by(status='pending').count()
        
        # Last 7 days data for chart
        daily_bookings = []
        for i in range(7):
            date = today - timedelta(days=6-i)
            count = Booking.query.filter(
                func.date(Booking.created_at) == date
            ).count()
            daily_bookings.append({
                'date': date.strftime('%Y-%m-%d'),
                'count': count
            })
        
        # Recent bookings
        recent_bookings = Booking.query.order_by(desc(Booking.created_at)).limit(10).all()
        recent_list = []
        for booking in recent_bookings:
            user = User.query.get(booking.user_id)
            recent_list.append({
                'booking_id': booking.booking_id,
                'pnr': booking.pnr,
                'user_name': user.name if user else 'Unknown',
                'route': f"{booking.origin} → {booking.destination}",
                'date': booking.departure_date.strftime('%Y-%m-%d'),
                'amount': booking.total_amount,
                'currency': booking.currency,
                'status': booking.status,
                'created_at': booking.created_at.strftime('%Y-%m-%d %H:%M')
            })
        
        return jsonify({
            'total_bookings': total_bookings,
            'total_revenue': round(total_revenue, 2),
            'today_bookings': today_bookings,
            'pending_bookings': pending_bookings,
            'daily_bookings': daily_bookings,
            'recent_bookings': recent_list
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/api/bookings')
@admin_required
def get_bookings():
    """Get all bookings with optional filters"""
    try:
        # Filters
        status_filter = request.args.get('status')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 50))
        
        # Query
        query = Booking.query
        
        if status_filter and status_filter != 'all':
            query = query.filter_by(status=status_filter)
        
        # Pagination
        bookings_paginated = query.order_by(desc(Booking.created_at)).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        bookings_list = []
        for booking in bookings_paginated.items:
            user = User.query.get(booking.user_id)
            bookings_list.append({
                'booking_id': booking.booking_id,
                'pnr': booking.pnr,
                'user_name': user.name if user else 'Unknown',
                'user_email': user.email if user else '',
                'origin': booking.origin,
                'destination': booking.destination,
                'route': f"{booking.origin} → {booking.destination}",
                'departure_date': booking.departure_date.strftime('%Y-%m-%d %H:%M'),
                'return_date': booking.return_date.strftime('%Y-%m-%d %H:%M') if booking.return_date else None,
                'airline': booking.airline,
                'flight_number': booking.flight_number,
                'total_amount': booking.total_amount,
                'currency': booking.currency,
                'status': booking.status,
                'api_provider': booking.api_provider,
                'created_at': booking.created_at.strftime('%Y-%m-%d %H:%M')
            })
        
        return jsonify({
            'bookings': bookings_list,
            'total': bookings_paginated.total,
            'pages': bookings_paginated.pages,
            'current_page': page
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/api/bookings/<int:booking_id>')
@admin_required
def get_booking_detail(booking_id):
    """Get detailed booking information"""
    try:
        booking = Booking.query.get(booking_id)
        if not booking:
            return jsonify({'error': 'Booking not found'}), 404
        
        user = User.query.get(booking.user_id)
        payment = Payment.query.get(booking.payment_id) if booking.payment_id else None
        
        # Parse passengers JSON
        passengers = json.loads(booking.passengers_json) if booking.passengers_json else []
        
        # Get API logs
        api_logs = APILog.query.filter_by(booking_id=booking_id).order_by(desc(APILog.created_at)).all()
        logs_list = [{
            'log_id': log.log_id,
            'log_type': log.log_type,
            'provider': log.provider,
            'status_code': log.status_code,
            'error_message': log.error_message,
            'created_at': log.created_at.strftime('%Y-%m-%d %H:%M:%S')
        } for log in api_logs]
        
        booking_detail = {
            'booking_id': booking.booking_id,
            'pnr': booking.pnr,
            'user': {
                'user_id': user.user_id,
                'name': user.name,
                'email': user.email
            } if user else None,
            'flight': {
                'origin': booking.origin,
                'destination': booking.destination,
                'departure_date': booking.departure_date.strftime('%Y-%m-%d %H:%M'),
                'return_date': booking.return_date.strftime('%Y-%m-%d %H:%M') if booking.return_date else None,
                'airline': booking.airline,
                'flight_number': booking.flight_number
            },
            'passengers': passengers,
            'pricing': {
                'base_price': booking.base_price,
                'taxes': booking.taxes,
                'total_amount': booking.total_amount,
                'currency': booking.currency
            },
            'status': booking.status,
            'api_provider': booking.api_provider,
            'api_booking_reference': booking.api_booking_reference,
            'payment': {
                'payment_id': payment.payment_id,
                'transaction_id': payment.transaction_id,
                'provider': payment.provider,
                'status': payment.status,
                'card_last4': payment.card_last4,
                'card_brand': payment.card_brand
            } if payment else None,
            'api_logs': logs_list,
            'created_at': booking.created_at.strftime('%Y-%m-%d %H:%M'),
            'updated_at': booking.updated_at.strftime('%Y-%m-%d %H:%M')
        }
        
        return jsonify(booking_detail)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/api/bookings/<int:booking_id>/refund', methods=['POST'])
@admin_required
def process_refund(booking_id):
    """Process refund for a booking"""
    try:
        booking = Booking.query.get(booking_id)
        if not booking:
            return jsonify({'error': 'Booking not found'}), 404
        
        data = request.get_json()
        refund_amount = data.get('refund_amount', booking.total_amount)
        reason = data.get('reason', '')
        
        # Create refund request
        refund = RefundRequest(
            booking_id=booking_id,
            user_id=booking.user_id,
            payment_id=booking.payment_id,
            refund_amount=refund_amount,
            currency=booking.currency,
            reason=reason,
            status='processed',
            processed_at=datetime.utcnow()
        )
        
        # Update booking status
        booking.status = 'refunded'
        
        db.session.add(refund)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'refund_id': refund.refund_id,
            'message': 'Refund processed successfully'
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/api/users')
@admin_required
def get_users():
    """Get all users with statistics"""
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 50))
        
        users_paginated = User.query.order_by(desc(User.created_at)).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        users_list = []
        for user in users_paginated.items:
            # Calculate total spent
            total_spent = db.session.query(func.sum(Payment.amount)).filter(
                Payment.user_id == user.user_id,
                Payment.status == 'completed'
            ).scalar() or 0
            
            # Count bookings
            bookings_count = Booking.query.filter_by(user_id=user.user_id).count()
            
            # Get saved payment methods count
            saved_cards = UserCardInformation.query.filter_by(user_id=user.user_id).count()
            
            users_list.append({
                'user_id': user.user_id,
                'name': user.name,
                'email': user.email,
                'is_admin': user.is_admin,
                'total_spent': round(total_spent, 2),
                'bookings_count': bookings_count,
                'saved_cards': saved_cards,
                'created_at': user.created_at.strftime('%Y-%m-%d %H:%M')
            })
        
        return jsonify({
            'users': users_list,
            'total': users_paginated.total,
            'pages': users_paginated.pages,
            'current_page': page
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/api/payments')
@admin_required
def get_payments():
    """Get all payment transactions"""
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 50))
        status_filter = request.args.get('status')
        
        query = Payment.query
        if status_filter and status_filter != 'all':
            query = query.filter_by(status=status_filter)
        
        payments_paginated = query.order_by(desc(Payment.created_at)).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        payments_list = []
        for payment in payments_paginated.items:
            user = User.query.get(payment.user_id)
            payments_list.append({
                'payment_id': payment.payment_id,
                'user_name': user.name if user else 'Unknown',
                'user_email': user.email if user else '',
                'amount': payment.amount,
                'currency': payment.currency,
                'status': payment.status,
                'provider': payment.provider,
                'transaction_id': payment.transaction_id,
                'card_last4': payment.card_last4,
                'card_brand': payment.card_brand,
                'created_at': payment.created_at.strftime('%Y-%m-%d %H:%M'),
                'completed_at': payment.completed_at.strftime('%Y-%m-%d %H:%M') if payment.completed_at else None
            })
        
        return jsonify({
            'payments': payments_list,
            'total': payments_paginated.total,
            'pages': payments_paginated.pages,
            'current_page': page
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/api/refunds')
@admin_required
def get_refunds():
    """Get all refund requests"""
    try:
        status_filter = request.args.get('status')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 50))
        
        query = RefundRequest.query
        if status_filter and status_filter != 'all':
            query = query.filter_by(status=status_filter)
        
        refunds_paginated = query.order_by(desc(RefundRequest.created_at)).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        refunds_list = []
        for refund in refunds_paginated.items:
            user = User.query.get(refund.user_id)
            booking = Booking.query.get(refund.booking_id)
            
            refunds_list.append({
                'refund_id': refund.refund_id,
                'booking_pnr': booking.pnr if booking else 'N/A',
                'user_name': user.name if user else 'Unknown',
                'refund_amount': refund.refund_amount,
                'currency': refund.currency,
                'reason': refund.reason,
                'status': refund.status,
                'admin_notes': refund.admin_notes,
                'created_at': refund.created_at.strftime('%Y-%m-%d %H:%M'),
                'processed_at': refund.processed_at.strftime('%Y-%m-%d %H:%M') if refund.processed_at else None
            })
        
        return jsonify({
            'refunds': refunds_list,
            'total': refunds_paginated.total,
            'pages': refunds_paginated.pages,
            'current_page': page
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/api/refunds/<int:refund_id>', methods=['PUT'])
@admin_required
def update_refund(refund_id):
    """Update refund request status"""
    try:
        refund = RefundRequest.query.get(refund_id)
        if not refund:
            return jsonify({'error': 'Refund not found'}), 404
        
        data = request.get_json()
        status = data.get('status')
        admin_notes = data.get('admin_notes')
        
        if status:
            refund.status = status
            if status in ['approved', 'processed']:
                refund.processed_at = datetime.utcnow()
        
        if admin_notes:
            refund.admin_notes = admin_notes
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Refund updated successfully'
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/api/flight-api')
@admin_required
def get_flight_api_providers():
    """Get all flight API providers"""
    try:
        providers = FlightAPIProvider.query.all()
        providers_list = [{
            'provider_id': p.provider_id,
            'name': p.name,
            'markup_percentage': p.markup_percentage,
            'is_active': p.is_active,
            'last_test_at': p.last_test_at.strftime('%Y-%m-%d %H:%M') if p.last_test_at else None,
            'last_test_status': p.last_test_status,
            'created_at': p.created_at.strftime('%Y-%m-%d %H:%M')
        } for p in providers]
        
        return jsonify({'providers': providers_list})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/api/flight-api', methods=['POST'])
@admin_required
def add_flight_api_provider():
    """Add new flight API provider"""
    try:
        data = request.get_json()
        
        provider = FlightAPIProvider(
            name=data['name'],
            api_key=data['api_key'],
            api_secret=data['api_secret'],
            markup_percentage=data.get('markup_percentage', 0.0),
            is_active=data.get('is_active', True)
        )
        
        db.session.add(provider)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'provider_id': provider.provider_id,
            'message': 'Provider added successfully'
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/api/flight-api/<int:provider_id>', methods=['PUT'])
@admin_required
def update_flight_api_provider(provider_id):
    """Update flight API provider"""
    try:
        provider = FlightAPIProvider.query.get(provider_id)
        if not provider:
            return jsonify({'error': 'Provider not found'}), 404
        
        data = request.get_json()
        
        if 'name' in data:
            provider.name = data['name']
        if 'api_key' in data:
            provider.api_key = data['api_key']
        if 'api_secret' in data:
            provider.api_secret = data['api_secret']
        if 'markup_percentage' in data:
            provider.markup_percentage = data['markup_percentage']
        if 'is_active' in data:
            provider.is_active = data['is_active']
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Provider updated successfully'
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/api/flight-api/<int:provider_id>/test', methods=['POST'])
@admin_required
def test_flight_api_connection(provider_id):
    """Test connection to flight API provider"""
    try:
        provider = FlightAPIProvider.query.get(provider_id)
        if not provider:
            return jsonify({'error': 'Provider not found'}), 404
        
        # Mock test - in production, make actual API call
        # For demonstration, simulate a successful test
        import random
        test_success = random.choice([True, True, True, False])  # 75% success rate
        
        provider.last_test_at = datetime.utcnow()
        provider.last_test_status = 'success' if test_success else 'failed'
        db.session.commit()
        
        if test_success:
            # Return sample flight data
            sample_data = {
                'flights': [
                    {
                        'origin': 'JFK',
                        'destination': 'LAX',
                        'departure': '2025-12-01T08:00:00',
                        'arrival': '2025-12-01T11:30:00',
                        'price': 299.99,
                        'currency': 'USD'
                    }
                ]
            }
            return jsonify({
                'success': True,
                'message': 'Connection test successful',
                'sample_data': sample_data
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Connection test failed - Invalid credentials'
            }), 400
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/api/settings')
@admin_required
def get_settings():
    """Get system settings"""
    try:
        settings = SystemSettings.query.first()
        if not settings:
            # Create default settings
            settings = SystemSettings()
            db.session.add(settings)
            db.session.commit()
        
        settings_data = {
            'app_name': settings.app_name,
            'app_logo': settings.app_logo,
            'default_currency': settings.default_currency,
            'global_markup_percentage': settings.global_markup_percentage,
            'smtp_host': settings.smtp_host,
            'smtp_port': settings.smtp_port,
            'smtp_username': settings.smtp_username,
            'sms_provider': settings.sms_provider
        }
        
        return jsonify(settings_data)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/api/settings', methods=['PUT'])
@admin_required
def update_settings():
    """Update system settings"""
    try:
        settings = SystemSettings.query.first()
        if not settings:
            settings = SystemSettings()
            db.session.add(settings)
        
        data = request.get_json()
        
        if 'app_name' in data:
            settings.app_name = data['app_name']
        if 'app_logo' in data:
            settings.app_logo = data['app_logo']
        if 'default_currency' in data:
            settings.default_currency = data['default_currency']
        if 'global_markup_percentage' in data:
            settings.global_markup_percentage = data['global_markup_percentage']
        if 'smtp_host' in data:
            settings.smtp_host = data['smtp_host']
        if 'smtp_port' in data:
            settings.smtp_port = data['smtp_port']
        if 'smtp_username' in data:
            settings.smtp_username = data['smtp_username']
        if 'smtp_password' in data:
            settings.smtp_password = data['smtp_password']
        if 'sms_provider' in data:
            settings.sms_provider = data['sms_provider']
        if 'sms_api_key' in data:
            settings.sms_api_key = data['sms_api_key']
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Settings updated successfully'
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/api/logs')
@admin_required
def get_logs():
    """Get API logs"""
    try:
        log_type = request.args.get('type')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 100))
        
        query = APILog.query
        if log_type and log_type != 'all':
            query = query.filter_by(log_type=log_type)
        
        logs_paginated = query.order_by(desc(APILog.created_at)).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        logs_list = []
        for log in logs_paginated.items:
            logs_list.append({
                'log_id': log.log_id,
                'log_type': log.log_type,
                'provider': log.provider,
                'endpoint': log.endpoint,
                'status_code': log.status_code,
                'error_message': log.error_message,
                'user_id': log.user_id,
                'booking_id': log.booking_id,
                'created_at': log.created_at.strftime('%Y-%m-%d %H:%M:%S')
            })
        
        return jsonify({
            'logs': logs_list,
            'total': logs_paginated.total,
            'pages': logs_paginated.pages,
            'current_page': page
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500
