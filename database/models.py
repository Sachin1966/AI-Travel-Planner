import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from database.db import Base

class User(Base):
    """
    User model to track active planners in the database.
    """
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Trip(Base):
    """
    Trip model storing search criteria, fetched weather, accommodation, and the full day-by-day JSON plan.
    """
    __tablename__ = "trips"
    
    id = Column(Integer, primary_key=True, index=True)
    destination = Column(String, nullable=False)
    duration = Column(Integer, nullable=False)
    budget = Column(String, nullable=False)
    travelers = Column(Integer, default=1)
    style = Column(String, default="Adventure")
    interests = Column(String, default="")  # Stored as comma-separated values (e.g. "Beaches,Food")
    
    # Generated elements
    total_budget_est = Column(String, nullable=True)
    budget_breakdown_json = Column(Text, nullable=True) # JSON representation of category allocations
    weather_json = Column(Text, nullable=True)          # JSON weather stats & forecast
    itinerary_json = Column(Text, nullable=False)        # JSON string storing full timeline of activities
    accommodations_json = Column(Text, nullable=True)   # JSON string storing lodging recommendations
    local_flavors_json = Column(Text, nullable=True)     # JSON string storing dishes, sips, hotspots
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Relationship to chats
    chats = relationship("ChatMessage", back_populates="trip", cascade="all, delete-orphan")

class ChatMessage(Base):
    """
    ChatMessage model storing conversations linked to a specific travel plan.
    """
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    trip_id = Column(ForeignKey("trips.id"), nullable=False)
    role = Column(String, nullable=False)  # "user" or "assistant"
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Relationship back to Trip
    trip = relationship("Trip", back_populates="chats")
