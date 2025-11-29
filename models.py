"""
Database models and helpers for the Flight project.
Uses SQLite by default (instance/flight.db).

Schema aligns with the project needs and your provided spec, with secure handling of card data
(no CVV or full PAN stored). Foreign keys are enabled via SQLite PRAGMA (see app setup).
"""
from __future__ import annotations

import os
from datetime import datetime
from typing import Optional

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import String, Integer, DateTime, Float, Text, Boolean

# SQLAlchemy extension (initialized in app.py)
db = SQLAlchemy()


# --------------------
# Core Entities
# --------------------
class User(db.Model):
    __tablename__ = "User"
    user_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    cards = relationship("UserCardInformation", back_populates="user", cascade="all, delete-orphan")
    passports = relationship("Passport", back_populates="user", cascade="all, delete-orphan")
    searches = relationship("Search", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<User {self.email}>"


class UserCardInformation(db.Model):
    __tablename__ = "User_card_information"
    User_card_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # SECURE STORAGE: store only non-sensitive card info
    last4: Mapped[str] = mapped_column(String(4), nullable=False)
    brand: Mapped[Optional[str]] = mapped_column(String(32))
    exp_month: Mapped[Optional[int]] = mapped_column(Integer)
    exp_year: Mapped[Optional[int]] = mapped_column(Integer)
    # Link to Stripe PaymentMethod id (if used)
    payment_method_id: Mapped[Optional[str]] = mapped_column(String(64))

    user_id: Mapped[int] = mapped_column(Integer, db.ForeignKey("User.user_id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="cards")


class Passport(db.Model):
    __tablename__ = "Passport"
    Passport_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, db.ForeignKey("User.user_id", ondelete="CASCADE"), nullable=False)
    First_name: Mapped[str] = mapped_column(String(120), nullable=False)
    last_name: Mapped[str] = mapped_column(String(120), nullable=False)
    passport_number: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="passports")


class Flight(db.Model):
    __tablename__ = "Flight"
    flight_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    flight_number: Mapped[Optional[str]] = mapped_column(String(32))  # May be unknown for multi-segment offers
    departure_airport: Mapped[str] = mapped_column(String(3), nullable=False)
    arrival_airport: Mapped[str] = mapped_column(String(3), nullable=False)
    departure_time: Mapped[Optional[datetime]] = mapped_column(DateTime)
    arrival_time: Mapped[Optional[datetime]] = mapped_column(DateTime)
    duration: Mapped[Optional[int]] = mapped_column(Integer)  # minutes


class FlightOffer(db.Model):
    """Single flight offer returned from a user search.

    Stored separately from Flight because offers can be multi-segment and
    contain pricing variants; we capture a snapshot summary for analytics.
    """
    __tablename__ = "FlightOffer"
    offer_id_pk: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    search_id: Mapped[int] = mapped_column(Integer, db.ForeignKey("Search.search_id", ondelete="CASCADE"), nullable=False)
    offer_id: Mapped[str] = mapped_column(String(64), nullable=False)  # Amadeus offer id
    airline_name: Mapped[Optional[str]] = mapped_column(String(255))
    origin: Mapped[str] = mapped_column(String(3), nullable=False)
    destination: Mapped[str] = mapped_column(String(3), nullable=False)
    departure: Mapped[Optional[datetime]] = mapped_column(DateTime)
    arrival: Mapped[Optional[datetime]] = mapped_column(DateTime)
    duration_text: Mapped[Optional[str]] = mapped_column(String(32))  # e.g. "5h 12m"
    stops_text: Mapped[Optional[str]] = mapped_column(String(32))
    lowest_price: Mapped[Optional[float]] = mapped_column(Float)
    currency: Mapped[Optional[str]] = mapped_column(String(8))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    # Index to avoid duplicates for same search
    __table_args__ = (
        db.UniqueConstraint('search_id', 'offer_id', name='uq_search_offer'),
    )

    search = relationship("Search", back_populates="offers")


class Search(db.Model):
    __tablename__ = "Search"
    search_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[Optional[int]] = mapped_column(Integer, db.ForeignKey("User.user_id", ondelete="SET NULL"))
    origin: Mapped[str] = mapped_column(String(3), nullable=False)
    destination: Mapped[str] = mapped_column(String(3), nullable=False)
    departure_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    return_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    target_price: Mapped[Optional[float]] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="searches")
    offers = relationship("FlightOffer", back_populates="search", cascade="all, delete-orphan")


class Ticket(db.Model):
    __tablename__ = "Ticket"
    ticket_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    flight_id: Mapped[int] = mapped_column(Integer, db.ForeignKey("Flight.flight_id", ondelete="CASCADE"), nullable=False)
    search_id: Mapped[Optional[int]] = mapped_column(Integer, db.ForeignKey("Search.search_id", ondelete="SET NULL"))
    price: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(8), default='USD')
    fare_class: Mapped[Optional[str]] = mapped_column(String(32))
    Ticket_bought: Mapped[bool] = mapped_column(Boolean, default=False)
    scraped_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class BudgetBuyRequest(db.Model):
    """
    Budget Buy feature: Users set price alerts or auto-booking when flights match their budget.
    System monitors prices and either books automatically or sends alerts.
    """
    __tablename__ = "BudgetBuyRequest"
    request_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, db.ForeignKey("User.user_id", ondelete="CASCADE"), nullable=False)
    
    # Flight Details
    origin: Mapped[str] = mapped_column(String(3), nullable=False)
    destination: Mapped[str] = mapped_column(String(3), nullable=False)
    departure_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    return_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    trip_duration_weeks: Mapped[Optional[int]] = mapped_column(Integer)  # 2 weeks, 3 weeks, etc.
    
    # Preferences
    non_stop_only: Mapped[bool] = mapped_column(Boolean, default=False)
    max_stops: Mapped[Optional[int]] = mapped_column(Integer)
    preferred_time: Mapped[Optional[str]] = mapped_column(String(32))  # Morning/Afternoon/Night
    preferred_airline: Mapped[Optional[str]] = mapped_column(String(3))  # IATA code
    
    # Budget Range (ALWAYS a range)
    min_budget: Mapped[float] = mapped_column(Float, nullable=False)
    max_budget: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(8), default='USD')
    
    # Mode Selection
    mode: Mapped[str] = mapped_column(String(16), nullable=False)  # 'auto_book' or 'alert_only'
    
    # Status Tracking
    status: Mapped[str] = mapped_column(String(32), default='pending')  
    # Status values: pending, searching, price_found, booked, alert_sent, cancelled
    
    # Booking Information (if auto-booked)
    booked_ticket_id: Mapped[Optional[int]] = mapped_column(Integer, db.ForeignKey("Ticket.ticket_id", ondelete="SET NULL"))
    booked_price: Mapped[Optional[float]] = mapped_column(Float)
    booking_confirmation: Mapped[Optional[str]] = mapped_column(String(64))
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    last_checked_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    # Relationships
    user = relationship("User", backref="budget_requests")
    
    def __repr__(self) -> str:
        return f"<BudgetBuyRequest {self.origin}-{self.destination} ${self.min_budget}-${self.max_budget}>"


class Booking(db.Model):
    """Admin-managed flight bookings"""
    __tablename__ = "Booking"
    booking_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, db.ForeignKey("User.user_id", ondelete="CASCADE"), nullable=False)
    pnr: Mapped[str] = mapped_column(String(10), unique=True, nullable=False)
    
    # Flight details
    origin: Mapped[str] = mapped_column(String(3), nullable=False)
    destination: Mapped[str] = mapped_column(String(3), nullable=False)
    departure_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    return_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    airline: Mapped[str] = mapped_column(String(3), nullable=False)
    flight_number: Mapped[Optional[str]] = mapped_column(String(32))
    
    # Passengers (JSON stored as text)
    passengers_json: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Pricing
    base_price: Mapped[float] = mapped_column(Float, nullable=False)
    taxes: Mapped[float] = mapped_column(Float, default=0.0)
    total_amount: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(8), default='USD')
    
    # Status tracking
    status: Mapped[str] = mapped_column(String(32), default='pending')  # pending, confirmed, cancelled, refunded
    
    # API provider info
    api_provider: Mapped[Optional[str]] = mapped_column(String(64))  # Amadeus, Duffel, etc.
    api_booking_reference: Mapped[Optional[str]] = mapped_column(String(128))
    
    # Payment
    payment_id: Mapped[Optional[int]] = mapped_column(Integer, db.ForeignKey("Payment.payment_id", ondelete="SET NULL"))
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    user = relationship("User", backref="bookings")
    payment = relationship("Payment", back_populates="bookings")
    
    def __repr__(self) -> str:
        return f"<Booking {self.pnr} {self.status}>"


class Payment(db.Model):
    """Payment transactions"""
    __tablename__ = "Payment"
    payment_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, db.ForeignKey("User.user_id", ondelete="CASCADE"), nullable=False)
    
    # Payment details
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(8), default='USD')
    status: Mapped[str] = mapped_column(String(32), default='pending')  # pending, completed, failed, refunded
    
    # Payment provider info
    provider: Mapped[str] = mapped_column(String(64), nullable=False)  # Stripe, Checkout, Flutterwave
    transaction_id: Mapped[Optional[str]] = mapped_column(String(128))
    payment_method_id: Mapped[Optional[str]] = mapped_column(String(128))  # Token for off-session charges
    
    # Card info (NO CVV, NO full PAN)
    card_last4: Mapped[Optional[str]] = mapped_column(String(4))
    card_brand: Mapped[Optional[str]] = mapped_column(String(32))
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    user = relationship("User", backref="payments")
    bookings = relationship("Booking", back_populates="payment")
    
    def __repr__(self) -> str:
        return f"<Payment {self.transaction_id} {self.status}>"


class RefundRequest(db.Model):
    """Refund requests for bookings"""
    __tablename__ = "RefundRequest"
    refund_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    booking_id: Mapped[int] = mapped_column(Integer, db.ForeignKey("Booking.booking_id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, db.ForeignKey("User.user_id", ondelete="CASCADE"), nullable=False)
    payment_id: Mapped[int] = mapped_column(Integer, db.ForeignKey("Payment.payment_id", ondelete="CASCADE"), nullable=False)
    
    # Refund details
    refund_amount: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(8), default='USD')
    reason: Mapped[Optional[str]] = mapped_column(Text)
    
    # Status
    status: Mapped[str] = mapped_column(String(32), default='pending')  # pending, approved, denied, processed
    admin_notes: Mapped[Optional[str]] = mapped_column(Text)
    
    # Provider refund info
    provider_refund_id: Mapped[Optional[str]] = mapped_column(String(128))
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    booking = relationship("Booking", backref="refund_requests")
    user = relationship("User", backref="refund_requests")
    payment = relationship("Payment", backref="refund_requests")
    
    def __repr__(self) -> str:
        return f"<RefundRequest {self.refund_id} {self.status}>"


class FlightAPIProvider(db.Model):
    """Flight API provider configurations"""
    __tablename__ = "FlightAPIProvider"
    provider_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Provider info
    name: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)  # Amadeus, Duffel, etc.
    api_key: Mapped[str] = mapped_column(String(255), nullable=False)
    api_secret: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Pricing
    markup_percentage: Mapped[float] = mapped_column(Float, default=0.0)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Connection test
    last_test_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    last_test_status: Mapped[Optional[str]] = mapped_column(String(32))  # success, failed
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def __repr__(self) -> str:
        return f"<FlightAPIProvider {self.name} {'active' if self.is_active else 'inactive'}>"


class SystemSettings(db.Model):
    """System-wide settings"""
    __tablename__ = "SystemSettings"
    setting_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # App info
    app_name: Mapped[str] = mapped_column(String(128), default='Skyela')
    app_logo: Mapped[Optional[str]] = mapped_column(String(512))
    
    # Currency & pricing
    default_currency: Mapped[str] = mapped_column(String(8), default='USD')
    global_markup_percentage: Mapped[float] = mapped_column(Float, default=0.0)
    
    # SMTP settings
    smtp_host: Mapped[Optional[str]] = mapped_column(String(255))
    smtp_port: Mapped[Optional[int]] = mapped_column(Integer)
    smtp_username: Mapped[Optional[str]] = mapped_column(String(255))
    smtp_password: Mapped[Optional[str]] = mapped_column(String(255))
    
    # SMS settings
    sms_provider: Mapped[Optional[str]] = mapped_column(String(64))
    sms_api_key: Mapped[Optional[str]] = mapped_column(String(255))
    
    # Timestamps
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def __repr__(self) -> str:
        return f"<SystemSettings {self.app_name}>"


class APILog(db.Model):
    """API request/response logs"""
    __tablename__ = "APILog"
    log_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Log type
    log_type: Mapped[str] = mapped_column(String(32), nullable=False)  # flight_search, flight_book, webhook
    
    # Provider info
    provider: Mapped[Optional[str]] = mapped_column(String(64))
    
    # Request/Response
    endpoint: Mapped[Optional[str]] = mapped_column(String(512))
    request_payload: Mapped[Optional[str]] = mapped_column(Text)
    response_payload: Mapped[Optional[str]] = mapped_column(Text)
    status_code: Mapped[Optional[int]] = mapped_column(Integer)
    
    # Associated records
    user_id: Mapped[Optional[int]] = mapped_column(Integer, db.ForeignKey("User.user_id", ondelete="SET NULL"))
    booking_id: Mapped[Optional[int]] = mapped_column(Integer, db.ForeignKey("Booking.booking_id", ondelete="SET NULL"))
    
    # Error info
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    
    # Timestamp
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    
    user = relationship("User", backref="api_logs")
    booking = relationship("Booking", backref="api_logs")
    
    def __repr__(self) -> str:
        return f"<APILog {self.log_type} {self.provider}>"


# --------------------
# Reference Data
# --------------------
class Airline(db.Model):
    __tablename__ = "airlines"
    code: Mapped[str] = mapped_column(String(3), primary_key=True)  # IATA
    name: Mapped[Optional[str]] = mapped_column(String(255))
    logo: Mapped[Optional[str]] = mapped_column(String(512))


class Airport(db.Model):
    __tablename__ = "airports"
    iata: Mapped[str] = mapped_column(String(3), primary_key=True)
    name: Mapped[Optional[str]] = mapped_column(String(255))
    city: Mapped[Optional[str]] = mapped_column(String(255))
    country: Mapped[Optional[str]] = mapped_column(String(255))


def seed_airlines_airports(json_dir: str) -> None:
    """
    Seed airlines and airports tables from JSON files if tables are empty.
    json_dir should contain airlines.json and airports.json
    """
    import json

    try:
        # Only seed if empty
        if Airline.query.count() == 0:
            airlines_path = os.path.join(json_dir, 'airlines.json')
            if os.path.exists(airlines_path):
                with open(airlines_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for item in data:
                        code = (item.get('id') or '').strip()
                        if not code:
                            continue
                        db.session.merge(Airline(code=code, name=item.get('name'), logo=item.get('logo')))
                db.session.commit()

        if Airport.query.count() == 0:
            airports_path = os.path.join(json_dir, 'airports.json')
            if os.path.exists(airports_path):
                with open(airports_path, 'r', encoding='utf-8') as f:
                    airports_raw = json.load(f)
                    for _icao, info in airports_raw.items():
                        iata = (info.get('iata') or '').strip()
                        if not iata:
                            continue
                        db.session.merge(
                            Airport(
                                iata=iata,
                                name=info.get('name'),
                                city=info.get('city'),
                                country=info.get('country'),
                            )
                        )
                db.session.commit()
    except Exception as e:  # pragma: no cover
        # Non-fatal during startup — log and continue
        print(f"Seeding error: {e}")
