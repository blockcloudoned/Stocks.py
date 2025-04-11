import os
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
import datetime

# Create database connection
DATABASE_URL = os.environ.get('DATABASE_URL')
engine = create_engine(DATABASE_URL)
Base = declarative_base()
Session = sessionmaker(bind=engine)

class User(Base):
    """User profile for saving preferences and trading history"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True)
    balance = Column(Float, default=10000.0)  # Default virtual balance of $10,000
    created_at = Column(DateTime, default=datetime.datetime.now)
    
    # Relationships
    watchlists = relationship("Watchlist", back_populates="user", cascade="all, delete-orphan")
    trades = relationship("Trade", back_populates="user", cascade="all, delete-orphan")
    preferences = relationship("UserPreference", back_populates="user", uselist=False, cascade="all, delete-orphan")
    positions = relationship("Position", back_populates="user", cascade="all, delete-orphan")

class Watchlist(Base):
    """Watchlists to track multiple symbols"""
    __tablename__ = 'watchlists'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'))
    created_at = Column(DateTime, default=datetime.datetime.now)
    
    # Relationships
    user = relationship("User", back_populates="watchlists")
    symbols = relationship("WatchlistSymbol", back_populates="watchlist", cascade="all, delete-orphan")

class WatchlistSymbol(Base):
    """Symbols in a watchlist"""
    __tablename__ = 'watchlist_symbols'
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), nullable=False)
    watchlist_id = Column(Integer, ForeignKey('watchlists.id'))
    added_at = Column(DateTime, default=datetime.datetime.now)
    notes = Column(Text)
    
    # Relationships
    watchlist = relationship("Watchlist", back_populates="symbols")

class Trade(Base):
    """Record of all virtual trades"""
    __tablename__ = 'trades'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    symbol = Column(String(20), nullable=False)
    action = Column(String(10), nullable=False)  # 'Buy' or 'Sell'
    quantity = Column(Float, nullable=False)
    price = Column(Float, nullable=False)
    total_value = Column(Float, nullable=False)
    trade_time = Column(DateTime, default=datetime.datetime.now)
    notes = Column(Text)
    
    # Relationships
    user = relationship("User", back_populates="trades")

class Position(Base):
    """Current positions/holdings"""
    __tablename__ = 'positions'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    symbol = Column(String(20), nullable=False)
    quantity = Column(Float, nullable=False)
    average_price = Column(Float, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="positions")

class PatternDetection(Base):
    """Saved pattern detections"""
    __tablename__ = 'pattern_detections'
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), nullable=False)
    pattern_type = Column(String(50), nullable=False)  # e.g., 'Double Bottom', 'Head and Shoulders'
    detection_date = Column(DateTime, default=datetime.datetime.now)
    price_at_detection = Column(Float)
    confidence = Column(Float)  # 0-1 scale of confidence in the pattern
    notes = Column(Text)
    is_validated = Column(Boolean, default=False)  # Was the pattern confirmed by price action?

class UserPreference(Base):
    """User preferences for the app"""
    __tablename__ = 'user_preferences'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), unique=True)
    default_chart_type = Column(String(20), default='candlestick')  # 'candlestick' or 'ohlc'
    default_time_period = Column(String(10), default='1y')  # e.g., '1d', '1mo', '1y'
    default_symbol = Column(String(20), default='BTC-USD')
    pattern_sensitivity = Column(Integer, default=5)  # 1-10 scale
    show_volume = Column(Boolean, default=True)
    show_moving_averages = Column(Boolean, default=True)
    theme = Column(String(10), default='light')  # 'light' or 'dark'
    
    # Relationships
    user = relationship("User", back_populates="preferences")

# Create all tables in the database
def init_db():
    Base.metadata.create_all(engine)

# Get a database session
def get_session():
    return Session()