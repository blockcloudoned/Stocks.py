from models import (
    get_session,
    init_db,
    User,
    Watchlist,
    WatchlistSymbol,
    Trade,
    Position,
    PatternDetection,
    UserPreference,
    Session,
    logger
)
import datetime
import functools
import time
from sqlalchemy import exc

def safe_db_operation(max_retries=3, initial_delay=1):
    """
    Decorator for database operations with retry logic for transient errors.
    
    Args:
        max_retries (int): Maximum number of retry attempts
        initial_delay (int): Initial delay between retries in seconds (doubles on each retry)
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            delay = initial_delay
            last_error = None
            
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except exc.OperationalError as e:
                    last_error = e
                    error_msg = str(e)
                    logger.warning(f"Database operation error in {func.__name__} (attempt {attempt+1}/{max_retries}): {error_msg}")
                    
                    # Clean up any lingering sessions
                    Session.remove()
                    
                    if attempt < max_retries - 1:
                        logger.info(f"Retrying in {delay} seconds...")
                        time.sleep(delay)
                        delay *= 2
                except Exception as e:
                    # For non-operational errors, log and re-raise immediately
                    logger.error(f"Unexpected error in {func.__name__}: {str(e)}")
                    raise
            
            # If we get here, all retries failed
            logger.error(f"All {max_retries} attempts failed in {func.__name__}")
            raise last_error
        
        return wrapper
    return decorator

def initialize_database():
    """Initialize the database and create tables if they don't exist"""
    init_db()
    
    # Check if we need to create a default user
    session = get_session()
    default_user = session.query(User).filter_by(username="default_user").first()
    
    if not default_user:
        # Create a default user
        default_user = User(
            username="default_user",
            email="default@example.com",
            balance=10000.0  # Start with $10,000 of virtual money
        )
        session.add(default_user)
        
        # Create default preferences
        default_preferences = UserPreference(user=default_user)
        session.add(default_preferences)
        
        # Create a default watchlist
        default_watchlist = Watchlist(
            name="Default Watchlist",
            user=default_user
        )
        session.add(default_watchlist)
        
        # Add some popular stocks/crypto to watchlist
        popular_symbols = ["BTC-USD", "ETH-USD", "AAPL", "MSFT", "AMZN", "GOOGL"]
        for symbol in popular_symbols:
            watchlist_symbol = WatchlistSymbol(
                symbol=symbol,
                watchlist=default_watchlist
            )
            session.add(watchlist_symbol)
        
        session.commit()
    
    session.close()

def get_user(username="default_user"):
    """Get a user by username, or create if doesn't exist"""
    session = get_session()
    user = session.query(User).filter_by(username=username).first()
    
    if not user:
        user = User(
            username=username,
            balance=10000.0
        )
        session.add(user)
        session.commit()
    
    # Convert to dict before closing session
    user_data = {
        "id": user.id,
        "username": user.username,
        "balance": user.balance,
        "created_at": user.created_at
    }
    
    session.close()
    return user_data

@safe_db_operation()
def get_watchlists(user_id):
    """Get all watchlists for a user"""
    session = get_session()
    try:
        watchlists = session.query(Watchlist).filter_by(user_id=user_id).all()
        
        result = []
        for watchlist in watchlists:
            symbols = [ws.symbol for ws in watchlist.symbols]
            result.append({
                "id": watchlist.id,
                "name": watchlist.name,
                "symbols": symbols,
                "created_at": watchlist.created_at
            })
        
        return result
    except Exception as e:
        logger.error(f"Error in get_watchlists: {str(e)}")
        raise
    finally:
        session.close()

def add_to_watchlist(user_id, watchlist_name, symbol, notes=None):
    """Add a symbol to a watchlist, creating the watchlist if it doesn't exist"""
    session = get_session()
    
    # Find or create watchlist
    watchlist = session.query(Watchlist).filter_by(user_id=user_id, name=watchlist_name).first()
    if not watchlist:
        watchlist = Watchlist(user_id=user_id, name=watchlist_name)
        session.add(watchlist)
        session.flush()  # Generate ID before using it
    
    # Check if symbol already exists in watchlist
    existing_symbol = session.query(WatchlistSymbol).filter_by(
        watchlist_id=watchlist.id, symbol=symbol
    ).first()
    
    if not existing_symbol:
        watchlist_symbol = WatchlistSymbol(
            symbol=symbol,
            watchlist_id=watchlist.id,
            notes=notes
        )
        session.add(watchlist_symbol)
        session.commit()
        result = True
    else:
        result = False  # Symbol already exists
    
    session.close()
    return result

def remove_from_watchlist(user_id, watchlist_name, symbol):
    """Remove a symbol from a watchlist"""
    session = get_session()
    
    # Find watchlist
    watchlist = session.query(Watchlist).filter_by(user_id=user_id, name=watchlist_name).first()
    if not watchlist:
        session.close()
        return False
    
    # Find and remove symbol
    symbol_entry = session.query(WatchlistSymbol).filter_by(
        watchlist_id=watchlist.id, symbol=symbol
    ).first()
    
    if symbol_entry:
        session.delete(symbol_entry)
        session.commit()
        result = True
    else:
        result = False
    
    session.close()
    return result

def record_trade(user_id, symbol, action, quantity, price, notes=None):
    """Record a trade and update positions and balance"""
    session = get_session()
    
    # Get user
    user = session.query(User).filter_by(id=user_id).first()
    if not user:
        session.close()
        return {"success": False, "message": "User not found"}
    
    total_value = quantity * price
    
    if action == "Buy":
        # Check if user has enough balance
        if user.balance < total_value:
            session.close()
            return {
                "success": False,
                "message": f"Insufficient funds! Trade value: ${total_value:.2f}, Balance: ${user.balance:.2f}"
            }
        
        # Update balance
        user.balance -= total_value
        
        # Update position
        position = session.query(Position).filter_by(user_id=user_id, symbol=symbol).first()
        if position:
            # Average down/up calculation
            new_quantity = position.quantity + quantity
            new_value = (position.quantity * position.average_price) + total_value
            new_price = new_value / new_quantity
            
            position.quantity = new_quantity
            position.average_price = new_price
        else:
            # Create new position
            position = Position(
                user_id=user_id,
                symbol=symbol,
                quantity=quantity,
                average_price=price
            )
            session.add(position)
    
    elif action == "Sell":
        # Check if user has the position and enough quantity
        position = session.query(Position).filter_by(user_id=user_id, symbol=symbol).first()
        if not position or position.quantity < quantity:
            session.close()
            return {
                "success": False,
                "message": f"Insufficient shares to sell! You own: {position.quantity if position else 0} shares of {symbol}"
            }
        
        # Update balance
        user.balance += total_value
        
        # Update position
        new_quantity = position.quantity - quantity
        if new_quantity > 0:
            position.quantity = new_quantity
        else:
            session.delete(position)
    
    # Record the trade
    trade = Trade(
        user_id=user_id,
        symbol=symbol,
        action=action,
        quantity=quantity,
        price=price,
        total_value=total_value,
        notes=notes
    )
    session.add(trade)
    
    session.commit()
    
    result = {
        "success": True,
        "trade_id": trade.id,
        "new_balance": user.balance,
        "message": f"Successfully {'purchased' if action == 'Buy' else 'sold'} {quantity} shares of {symbol} at ${price:.2f}"
    }
    
    session.close()
    return result

def get_trades(user_id, limit=50):
    """Get trade history for a user"""
    session = get_session()
    
    trades = session.query(Trade).filter_by(user_id=user_id).order_by(Trade.trade_time.desc()).limit(limit).all()
    
    result = []
    for trade in trades:
        result.append({
            "id": trade.id,
            "symbol": trade.symbol,
            "action": trade.action,
            "quantity": trade.quantity,
            "price": trade.price,
            "total_value": trade.total_value,
            "trade_time": trade.trade_time,
            "notes": trade.notes
        })
    
    session.close()
    return result

@safe_db_operation()
def get_positions(user_id):
    """Get current positions for a user"""
    session = get_session()
    try:
        positions = session.query(Position).filter_by(user_id=user_id).all()
        
        result = []
        for position in positions:
            result.append({
                "id": position.id,
                "symbol": position.symbol,
                "quantity": position.quantity,
                "average_price": position.average_price,
                "current_value": position.quantity * position.average_price  # This will be updated with current price in UI
            })
        
        return result
    except Exception as e:
        logger.error(f"Error in get_positions: {str(e)}")
        raise
    finally:
        session.close()

def get_user_preferences(user_id):
    """Get user preferences"""
    session = get_session()
    
    preferences = session.query(UserPreference).filter_by(user_id=user_id).first()
    
    if not preferences:
        # Create default preferences if they don't exist
        preferences = UserPreference(user_id=user_id)
        session.add(preferences)
        session.commit()
    
    result = {
        "default_chart_type": preferences.default_chart_type,
        "default_time_period": preferences.default_time_period,
        "default_symbol": preferences.default_symbol,
        "pattern_sensitivity": preferences.pattern_sensitivity,
        "show_volume": preferences.show_volume,
        "show_moving_averages": preferences.show_moving_averages,
        "theme": preferences.theme
    }
    
    session.close()
    return result

def update_user_preferences(user_id, preferences_dict):
    """Update user preferences"""
    session = get_session()
    
    preferences = session.query(UserPreference).filter_by(user_id=user_id).first()
    
    if not preferences:
        preferences = UserPreference(user_id=user_id)
        session.add(preferences)
    
    # Update attributes that are in the dict
    for key, value in preferences_dict.items():
        if hasattr(preferences, key):
            setattr(preferences, key, value)
    
    session.commit()
    session.close()
    return True

@safe_db_operation()
def save_pattern_detection(symbol, pattern_type, price, confidence=0.5, notes=None):
    """Save a detected pattern to the database"""
    session = get_session()
    try:
        pattern = PatternDetection(
            symbol=symbol,
            pattern_type=pattern_type,
            price_at_detection=price,
            confidence=confidence,
            notes=notes
        )
        session.add(pattern)
        session.commit()
        
        result = {
            "id": pattern.id,
            "symbol": pattern.symbol,
            "pattern_type": pattern.pattern_type,
            "detection_date": pattern.detection_date,
            "price_at_detection": pattern.price_at_detection,
            "confidence": pattern.confidence
        }
        
        return result
    except Exception as e:
        logger.error(f"Error in save_pattern_detection: {str(e)}")
        raise
    finally:
        session.close()

@safe_db_operation()
def get_recent_pattern_detections(symbol=None, limit=20):
    """Get recently detected patterns"""
    session = get_session()
    try:
        query = session.query(PatternDetection).order_by(PatternDetection.detection_date.desc())
        if symbol:
            query = query.filter_by(symbol=symbol)
        
        patterns = query.limit(limit).all()
        
        result = []
        for pattern in patterns:
            result.append({
                "id": pattern.id,
                "symbol": pattern.symbol,
                "pattern_type": pattern.pattern_type,
                "detection_date": pattern.detection_date,
                "price_at_detection": pattern.price_at_detection,
                "confidence": pattern.confidence,
                "is_validated": pattern.is_validated,
                "notes": pattern.notes
            })
        
        return result
    except Exception as e:
        logger.error(f"Error in get_recent_pattern_detections: {str(e)}")
        raise
    finally:
        session.close()