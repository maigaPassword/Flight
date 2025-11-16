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
