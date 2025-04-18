import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import datetime
import base64
from io import StringIO

from utils.data_fetcher import fetch_stock_data
from utils.pattern_detection import (
    detect_double_bottom, detect_double_top, detect_head_and_shoulders,
    detect_inverse_head_and_shoulders, detect_triangle, find_support_resistance
)
from utils.technical_indicators import (
    calculate_rsi, calculate_macd, calculate_bollinger_bands, calculate_moving_averages
)
from utils.chart_utils import add_pattern_shapes, create_candlestick_chart
from utils.sharing import create_shareable_image, export_pattern_data, get_social_share_html, get_sharing_link

# Import database functions
from database import (
    initialize_database, get_user, get_watchlists, add_to_watchlist, 
    remove_from_watchlist, record_trade, get_trades, get_positions,
    get_user_preferences, update_user_preferences, save_pattern_detection,
    get_recent_pattern_detections
)

# Set page config
st.set_page_config(
    page_title="Stock Pattern Detector",
    page_icon="📈",
    layout="wide"
)

# Initialize database on first run
if 'db_initialized' not in st.session_state:
    initialize_database()
    st.session_state.db_initialized = True

# Add database status state
if 'db_status' not in st.session_state:
    st.session_state.db_status = 'connected'

# Initialize session state variables with error handling
try:
    if 'user_id' not in st.session_state:
        # Get the default user
        user = get_user("default_user")
        st.session_state.user_id = user["id"]
        st.session_state.username = user["username"]
        st.session_state.balance = user["balance"]
    
    # Cache the user's positions and trades (we'll refresh these when needed)
    if 'positions' not in st.session_state:
        st.session_state.positions = get_positions(st.session_state.user_id)
    if 'trades' not in st.session_state:
        st.session_state.trades = get_trades(st.session_state.user_id)
    
    # Successful database access - reset error status if it was set
    st.session_state.db_status = 'connected'
except Exception as e:
    import logging
    logging.error(f"Database connection error: {str(e)}")
    st.session_state.db_status = 'error'
    
    # Initialize with defaults if needed
    if 'user_id' not in st.session_state:
        st.session_state.user_id = 1
        st.session_state.username = "default_user"
        st.session_state.balance = 10000.0
    if 'positions' not in st.session_state:
        st.session_state.positions = []
    if 'trades' not in st.session_state:
        st.session_state.trades = []
try:
    if 'preferences' not in st.session_state:
        st.session_state.preferences = get_user_preferences(st.session_state.user_id)
except Exception as e:
    import logging
    logging.error(f"Error loading user preferences: {str(e)}")
    # Default preferences
    st.session_state.preferences = {
        "default_chart_type": "candlestick",
        "default_time_period": "1y",
        "default_symbol": "BTC-USD",
        "pattern_sensitivity": 5,
        "show_volume": True,
        "show_moving_averages": True,
        "theme": "light"
    }

# App title and description
st.title("📊 Stock & Crypto Pattern Detector")
st.markdown("""
This application helps you identify chart patterns, visualize technical indicators, 
and analyze trading opportunities in stocks and cryptocurrencies.
""")

# Sidebar
with st.sidebar:
    st.header("Input Parameters")
    
    # Get user watchlists with error handling
    try:
        watchlists = get_watchlists(st.session_state.user_id)
        st.session_state.db_status = 'connected'
    except Exception as e:
        import logging
        logging.error(f"Error getting watchlists: {str(e)}")
        watchlists = []
        st.session_state.db_status = 'error'
        # Show database error message
        st.error("⚠️ Database connection error. Some features may be unavailable.")
    
    # Combine symbols from all watchlists for selection
    all_watchlist_symbols = []
    for watchlist in watchlists:
        all_watchlist_symbols.extend(watchlist["symbols"])
    
    # Remove duplicates
    all_watchlist_symbols = list(set(all_watchlist_symbols))
    
    # Symbol input with watchlist selection
    st.subheader("Symbol Selection")
    symbol_selection_method = st.radio("Select source:", ["Enter Symbol", "From Watchlist"])
    
    if symbol_selection_method == "Enter Symbol":
        symbol = st.text_input("Enter Symbol (e.g., AAPL, BTC-USD):", value="AAPL")
        
        # Add to watchlist option
        add_to_watchlist_option = st.checkbox("Add to watchlist")
        if add_to_watchlist_option:
            # Get available watchlists or create new one
            watchlist_names = [w["name"] for w in watchlists]
            if not watchlist_names:
                watchlist_names = ["Default Watchlist"]
            
            selected_watchlist = st.selectbox("Select watchlist", watchlist_names)
            if st.button("Add Symbol to Watchlist"):
                try:
                    if add_to_watchlist(st.session_state.user_id, selected_watchlist, symbol):
                        st.success(f"Added {symbol} to {selected_watchlist}")
                        st.session_state.db_status = 'connected'
                    else:
                        st.info(f"{symbol} is already in {selected_watchlist}")
                except Exception as e:
                    import logging
                    logging.error(f"Error adding to watchlist: {str(e)}")
                    st.error(f"Unable to add {symbol} to watchlist due to database error.")
                    st.session_state.db_status = 'error'
    else:
        # Filter out empty watchlists
        populated_watchlists = [w for w in watchlists if w["symbols"]]
        
        if populated_watchlists:
            # If we have symbols in the watchlists, allow selection
            symbol = st.selectbox("Select from watchlist:", all_watchlist_symbols) if all_watchlist_symbols else "AAPL"
        else:
            st.info("Your watchlists are empty. Please add symbols first.")
            symbol = "AAPL"
    
    # Date range
    st.subheader("Time Period")
    end_date = datetime.datetime.now().date()
    start_date = end_date - datetime.timedelta(days=365)
    
    start_date = st.date_input("Start Date", value=start_date)
    end_date = st.date_input("End Date", value=end_date)
    
    # Indicators selection
    st.subheader("Technical Indicators")
    show_rsi = st.checkbox("RSI", value=True)
    show_macd = st.checkbox("MACD", value=True)
    show_bollinger = st.checkbox("Bollinger Bands", value=True)
    show_ma = st.checkbox("Moving Averages", value=True)
    
    # Pattern detection selection
    st.subheader("Pattern Detection")
    detect_double_bottoms = st.checkbox("Double Bottom", value=True)
    detect_double_tops = st.checkbox("Double Top", value=True)
    detect_head_shoulders = st.checkbox("Head and Shoulders", value=True)
    detect_inv_head_shoulders = st.checkbox("Inverse Head and Shoulders", value=True)
    detect_triangles = st.checkbox("Triangle Patterns", value=True)
    detect_support_resistance = st.checkbox("Support/Resistance", value=True)
    
    # Pattern detection sensitivity
    st.subheader("Detection Sensitivity")
    sensitivity = st.slider("Sensitivity", min_value=1, max_value=10, value=5)
    
    # Button to fetch data
    fetch_button = st.button("Fetch & Analyze Data")

# Main content
if fetch_button or 'data' in st.session_state:
    # Display a spinner while fetching and processing data
    with st.spinner("Fetching and analyzing data..."):
        # Fetch data
        try:
            if fetch_button:
                data = fetch_stock_data(symbol, start_date, end_date)
                st.session_state.data = data
                st.session_state.symbol = symbol
            else:
                data = st.session_state.data
                symbol = st.session_state.symbol
            
            # Calculate indicators
            if show_rsi:
                data['RSI'] = calculate_rsi(data['Close'])
            
            if show_macd:
                data['MACD'], data['MACD_Signal'], data['MACD_Histogram'] = calculate_macd(data['Close'])
            
            if show_bollinger:
                data['BB_Upper'], data['BB_Middle'], data['BB_Lower'] = calculate_bollinger_bands(data['Close'])
            
            if show_ma:
                data['SMA_20'], data['SMA_50'], data['SMA_200'] = calculate_moving_averages(data['Close'])
            
            # Detect patterns
            patterns = {}
            detected_patterns = []
            
            if detect_double_bottoms:
                patterns['double_bottoms'] = detect_double_bottom(data, sensitivity=sensitivity)
                if patterns['double_bottoms']:
                    # Store pattern detection in the database
                    for idx in patterns['double_bottoms'][-3:]:  # Store only the most recent ones
                        idx_val = idx[-1] if isinstance(idx, list) else idx
                        pattern_price = float(data['Close'].iloc[idx_val])
                        try:
                            save_pattern_detection(
                                symbol=symbol,
                                pattern_type="Double Bottom",
                                price=pattern_price,
                                confidence=sensitivity / 10.0,
                                notes=f"Detected at price ${pattern_price:.2f} with sensitivity {sensitivity}"
                            )
                            st.session_state.db_status = 'connected'
                        except Exception as e:
                            import logging
                            logging.error(f"Error saving pattern detection: {str(e)}")
                            st.session_state.db_status = 'error'
                        detected_patterns.append("Double Bottom")
            
            if detect_double_tops:
                patterns['double_tops'] = detect_double_top(data, sensitivity=sensitivity)
                if patterns['double_tops']:
                    # Store pattern detection in the database
                    for idx in patterns['double_tops'][-3:]:  # Store only the most recent ones
                        idx_val = idx[-1] if isinstance(idx, list) else idx
                        pattern_price = float(data['Close'].iloc[idx_val])
                        try:
                            save_pattern_detection(
                                symbol=symbol,
                                pattern_type="Double Top",
                                price=pattern_price,
                                confidence=sensitivity / 10.0,
                                notes=f"Detected at price ${pattern_price:.2f} with sensitivity {sensitivity}"
                            )
                            st.session_state.db_status = 'connected'
                        except Exception as e:
                            import logging
                            logging.error(f"Error saving pattern detection: {str(e)}")
                            st.session_state.db_status = 'error'
                        detected_patterns.append("Double Top")
            
            if detect_head_shoulders:
                patterns['head_shoulders'] = detect_head_and_shoulders(data, sensitivity=sensitivity)
                if patterns['head_shoulders']:
                    # Store pattern detection in the database
                    for idx in patterns['head_shoulders'][-3:]:  # Store only the most recent ones
                        idx_val = idx[-1] if isinstance(idx, list) else idx
                        pattern_price = float(data['Close'].iloc[idx_val])
                        try:
                            save_pattern_detection(
                                symbol=symbol,
                                pattern_type="Head and Shoulders",
                                price=pattern_price,
                                confidence=sensitivity / 10.0,
                                notes=f"Detected at price ${pattern_price:.2f} with sensitivity {sensitivity}"
                            )
                            st.session_state.db_status = 'connected'
                        except Exception as e:
                            import logging
                            logging.error(f"Error saving pattern detection: {str(e)}")
                            st.session_state.db_status = 'error'
                        detected_patterns.append("Head and Shoulders")
            
            if detect_inv_head_shoulders:
                patterns['inv_head_shoulders'] = detect_inverse_head_and_shoulders(data, sensitivity=sensitivity)
                if patterns['inv_head_shoulders']:
                    # Store pattern detection in the database
                    for idx in patterns['inv_head_shoulders'][-3:]:  # Store only the most recent ones
                        idx_val = idx[-1] if isinstance(idx, list) else idx
                        pattern_price = float(data['Close'].iloc[idx_val])
                        try:
                            save_pattern_detection(
                                symbol=symbol,
                                pattern_type="Inverse Head and Shoulders",
                                price=pattern_price,
                                confidence=sensitivity / 10.0,
                                notes=f"Detected at price ${pattern_price:.2f} with sensitivity {sensitivity}"
                            )
                            st.session_state.db_status = 'connected'
                        except Exception as e:
                            import logging
                            logging.error(f"Error saving pattern detection: {str(e)}")
                            st.session_state.db_status = 'error'
                        detected_patterns.append("Inverse Head and Shoulders")
            
            if detect_triangles:
                patterns['triangles'] = detect_triangle(data, sensitivity=sensitivity)
                if patterns['triangles']:
                    # Store pattern detection in the database
                    for triangle in patterns['triangles'][-3:]:  # Store only the most recent ones
                        pattern_price = float(data['Close'].iloc[triangle['end_idx']])
                        triangle_type = triangle.get('type', 'Triangle')
                        try:
                            save_pattern_detection(
                                symbol=symbol,
                                pattern_type=f"{triangle_type} Triangle",
                                price=pattern_price,
                                confidence=sensitivity / 10.0,
                                notes=f"Detected at price ${pattern_price:.2f} with sensitivity {sensitivity}"
                            )
                            st.session_state.db_status = 'connected'
                        except Exception as e:
                            import logging
                            logging.error(f"Error saving pattern detection: {str(e)}")
                            st.session_state.db_status = 'error'
                        detected_patterns.append(f"{triangle_type} Triangle")
            
            if detect_support_resistance:
                patterns['support'], patterns['resistance'] = find_support_resistance(data, sensitivity=sensitivity)
                
            # Show notification if new patterns were detected
            if detected_patterns:
                st.success(f"Detected and saved the following patterns: {', '.join(set(detected_patterns))}")
            
            # Display data summary
            st.header(f"{symbol} Data Summary")
            metrics_col1, metrics_col2, metrics_col3, metrics_col4 = st.columns(4)
            
            with metrics_col1:
                current_price = data['Close'].iloc[-1]
                previous_price = data['Close'].iloc[-2]
                price_change = ((current_price - previous_price) / previous_price) * 100
                st.metric("Current Price", f"${current_price:.2f}", f"{price_change:.2f}%")
            
            with metrics_col2:
                price_min = data['Low'].min()
                price_max = data['High'].max()
                st.metric("Price Range", f"${price_min:.2f} - ${price_max:.2f}")
            
            with metrics_col3:
                volume_avg = data['Volume'].mean()
                st.metric("Avg. Volume", f"{volume_avg:.0f}")
            
            with metrics_col4:
                total_patterns = sum(len(p) for p in patterns.values() if isinstance(p, list))
                st.metric("Patterns Detected", total_patterns)

            # Create the main chart
            st.subheader("Interactive Price Chart with Patterns")
            
            # Create the chart
            fig = create_candlestick_chart(data, symbol)

            # Add technical indicators
            if show_ma:
                fig.add_trace(go.Scatter(x=data.index, y=data['SMA_20'], name='SMA 20', line=dict(color='blue', width=1)))
                fig.add_trace(go.Scatter(x=data.index, y=data['SMA_50'], name='SMA 50', line=dict(color='orange', width=1)))
                fig.add_trace(go.Scatter(x=data.index, y=data['SMA_200'], name='SMA 200', line=dict(color='red', width=1)))
            
            if show_bollinger:
                fig.add_trace(go.Scatter(x=data.index, y=data['BB_Upper'], name='BB Upper', line=dict(color='rgba(173, 204, 255, 0.7)', width=1)))
                fig.add_trace(go.Scatter(x=data.index, y=data['BB_Lower'], name='BB Lower', line=dict(color='rgba(173, 204, 255, 0.7)', width=1)))
                fig.add_trace(go.Scatter(x=data.index, y=data['BB_Middle'], name='BB Middle', line=dict(color='rgba(173, 204, 255, 1)', width=1)))
                
                # Fill between the bands
                fig.add_trace(go.Scatter(
                    x=data.index.tolist() + data.index.tolist()[::-1],
                    y=data['BB_Upper'].tolist() + data['BB_Lower'].tolist()[::-1],
                    fill='toself',
                    fillcolor='rgba(173, 204, 255, 0.2)',
                    line=dict(width=0),
                    hoverinfo='skip',
                    showlegend=False
                ))
            
            # Add pattern annotations to the chart
            fig = add_pattern_shapes(fig, data, patterns)

            # Display the chart
            st.plotly_chart(fig, use_container_width=True)
            
            # Additional sub-charts for indicators
            if show_rsi or show_macd:
                st.subheader("Technical Indicators")
                
                # Create tabs for different indicators
                indicator_tabs = st.tabs(["RSI", "MACD"])
                
                # RSI Tab
                with indicator_tabs[0]:
                    if show_rsi:
                        fig_rsi = go.Figure()
                        fig_rsi.add_trace(go.Scatter(x=data.index, y=data['RSI'], name='RSI', line=dict(color='purple', width=2)))
                        
                        # Add overbought/oversold lines
                        fig_rsi.add_shape(type="line", x0=data.index[0], x1=data.index[-1], y0=70, y1=70,
                                         line=dict(color="red", width=1, dash="dash"))
                        fig_rsi.add_shape(type="line", x0=data.index[0], x1=data.index[-1], y0=30, y1=30,
                                         line=dict(color="green", width=1, dash="dash"))
                        
                        fig_rsi.update_layout(
                            title="Relative Strength Index (RSI)",
                            xaxis_title="Date",
                            yaxis_title="RSI",
                            height=300,
                            margin=dict(l=0, r=0, t=30, b=0),
                            yaxis=dict(range=[0, 100])
                        )
                        st.plotly_chart(fig_rsi, use_container_width=True)
                    else:
                        st.info("Enable RSI in the sidebar to see this indicator.")
                
                # MACD Tab
                with indicator_tabs[1]:
                    if show_macd:
                        fig_macd = go.Figure()
                        fig_macd.add_trace(go.Scatter(x=data.index, y=data['MACD'], name='MACD', line=dict(color='blue', width=2)))
                        fig_macd.add_trace(go.Scatter(x=data.index, y=data['MACD_Signal'], name='Signal', line=dict(color='red', width=1)))
                        
                        # Add histogram
                        colors = ['green' if val >= 0 else 'red' for val in data['MACD_Histogram']]
                        fig_macd.add_trace(go.Bar(x=data.index, y=data['MACD_Histogram'], name='Histogram', marker_color=colors))
                        
                        fig_macd.update_layout(
                            title="Moving Average Convergence Divergence (MACD)",
                            xaxis_title="Date",
                            yaxis_title="Value",
                            height=300,
                            margin=dict(l=0, r=0, t=30, b=0)
                        )
                        st.plotly_chart(fig_macd, use_container_width=True)
                    else:
                        st.info("Enable MACD in the sidebar to see this indicator.")
            
            # Pattern analysis and statistics
            st.header("Pattern Analysis")
            
            pattern_tabs = st.tabs([
                "Detected Patterns", 
                "Pattern Statistics", 
                "Trading Signals",
                "Virtual Trading",
                "Share & Export"
            ])
            
            # Detected Patterns Tab
            with pattern_tabs[0]:
                st.markdown("### Recently Detected Patterns")
                
                # Create tabs for current detection and historical detections
                detection_tabs = st.tabs(["Current Analysis", "Historical Detections"])
                
                # Current Analysis Tab - shows patterns detected in the current chart
                with detection_tabs[0]:
                    if sum(len(p) for p in patterns.values() if isinstance(p, list)) > 0:
                        for pattern_name, pattern_locations in patterns.items():
                            if isinstance(pattern_locations, tuple):
                                # Handle support/resistance which returns a tuple
                                continue
                            
                            if pattern_locations and len(pattern_locations) > 0:
                                formatted_name = pattern_name.replace('_', ' ').title()
                                st.subheader(f"{formatted_name}")
                                
                                pattern_df = pd.DataFrame({
                                    "Date": [data.index[idx[-1]] if isinstance(idx, list) else data.index[idx] for idx in pattern_locations[-5:]],
                                    "Price at Pattern": [data['Close'][idx[-1]] if isinstance(idx, list) else data['Close'][idx] for idx in pattern_locations[-5:]],
                                    "Pattern Strength": [f"{(sensitivity / 10.0 * 100):.0f}%" for _ in pattern_locations[-5:]]
                                })
                                
                                st.dataframe(pattern_df)
                    else:
                        st.info("No patterns were detected with the current settings. Try adjusting the sensitivity or selecting different patterns.")
                
                # Historical Detections Tab - shows patterns from the database
                with detection_tabs[1]:
                    # Get recent pattern detections for this symbol from the database
                    try:
                        recent_patterns = get_recent_pattern_detections(symbol)
                        st.session_state.db_status = 'connected'
                    except Exception as e:
                        import logging
                        logging.error(f"Error retrieving pattern detections: {str(e)}")
                        recent_patterns = []
                        st.session_state.db_status = 'error'
                        st.error("⚠️ Unable to retrieve historical pattern data due to database error.")
                    
                    if recent_patterns:
                        # Group by pattern type
                        pattern_types = {}
                        for p in recent_patterns:
                            pattern_type = p['pattern_type']
                            if pattern_type not in pattern_types:
                                pattern_types[pattern_type] = []
                            pattern_types[pattern_type].append(p)
                        
                        # Display each pattern type
                        for pattern_type, patterns_list in pattern_types.items():
                            st.subheader(f"{pattern_type}")
                            
                            pattern_data = []
                            for p in patterns_list:
                                # Format the date
                                detection_date = p['detection_date']
                                if hasattr(detection_date, 'strftime'):
                                    date_str = detection_date.strftime("%Y-%m-%d %H:%M")
                                else:
                                    date_str = str(detection_date)
                                    
                                pattern_data.append({
                                    "Date": date_str,
                                    "Price": f"${p['price_at_detection']:.2f}",
                                    "Confidence": f"{(p['confidence'] * 100):.0f}%"
                                })
                            
                            st.dataframe(pd.DataFrame(pattern_data))
                    else:
                        st.info(f"No historical pattern detections for {symbol} in the database. Analyze the chart to save patterns.")
            
            # Pattern Statistics Tab
            with pattern_tabs[1]:
                st.markdown("### Historical Pattern Performance")
                
                # Create a mock statistics table for demonstration
                pattern_types = [p.replace('_', ' ').title() for p in patterns.keys() if isinstance(patterns[p], list) and len(patterns[p]) > 0]
                
                if pattern_types:
                    stats_data = {
                        "Pattern Type": pattern_types,
                        "Occurrences": [len(patterns[p.lower().replace(' ', '_')]) for p in pattern_types],
                        "Success Rate": [f"{np.random.randint(40, 85)}%" for _ in pattern_types],
                        "Avg. Price Change": [f"{np.random.uniform(-5, 15):.2f}%" for _ in pattern_types],
                        "Avg. Duration": [f"{np.random.randint(3, 30)} days" for _ in pattern_types]
                    }
                    
                    stats_df = pd.DataFrame(stats_data)
                    st.dataframe(stats_df)
                else:
                    st.info("No patterns were detected to analyze statistics.")
            
            # Trading Signals Tab
            with pattern_tabs[2]:
                st.markdown("### Recent Trading Signals")
                
                # Generate trading signals based on detected patterns
                signals = []
                
                # Check for bullish patterns
                bullish_patterns = []
                if 'double_bottoms' in patterns and patterns['double_bottoms']:
                    bullish_patterns.extend([('Double Bottom', idx) for idx in patterns['double_bottoms'][-3:]])
                
                if 'inv_head_shoulders' in patterns and patterns['inv_head_shoulders']:
                    bullish_patterns.extend([('Inverse Head and Shoulders', idx) for idx in patterns['inv_head_shoulders'][-3:]])
                
                # Check for bearish patterns
                bearish_patterns = []
                if 'double_tops' in patterns and patterns['double_tops']:
                    bearish_patterns.extend([('Double Top', idx) for idx in patterns['double_tops'][-3:]])
                
                if 'head_shoulders' in patterns and patterns['head_shoulders']:
                    bearish_patterns.extend([('Head and Shoulders', idx) for idx in patterns['head_shoulders'][-3:]])
                
                # Add signals
                for pattern_name, idx in bullish_patterns:
                    idx_val = idx[-1] if isinstance(idx, list) else idx
                    if idx_val < len(data) - 5:  # Only include if not too recent
                        signal_date = data.index[idx_val]
                        price = data['Close'][idx_val]
                        signals.append({
                            "Date": signal_date,
                            "Pattern": pattern_name,
                            "Signal": "Buy",
                            "Price": price,
                            "Current Result": f"{((data['Close'].iloc[-1] - price) / price * 100):.2f}%"
                        })
                
                for pattern_name, idx in bearish_patterns:
                    idx_val = idx[-1] if isinstance(idx, list) else idx
                    if idx_val < len(data) - 5:  # Only include if not too recent
                        signal_date = data.index[idx_val]
                        price = data['Close'][idx_val]
                        signals.append({
                            "Date": signal_date,
                            "Pattern": pattern_name,
                            "Signal": "Sell",
                            "Price": price,
                            "Current Result": f"{((price - data['Close'].iloc[-1]) / price * 100):.2f}%"
                        })
                
                # Sort by date (newest first)
                signals = sorted(signals, key=lambda x: x["Date"], reverse=True)
                
                if signals:
                    # Convert datetime index to string to avoid format errors
                    for signal in signals:
                        if isinstance(signal["Date"], pd.Timestamp):
                            signal["Date"] = signal["Date"].strftime('%Y-%m-%d')
                    
                    signals_df = pd.DataFrame(signals)
                    st.dataframe(signals_df)
                else:
                    st.info("No trading signals were generated from the detected patterns.")

            # Virtual Trading Tab
            with pattern_tabs[3]:
                st.markdown("### Virtual Trading Platform")
                
                # Display current balance
                st.metric("Account Balance", f"${st.session_state.balance:.2f}")
                
                # Display current positions
                # Refresh positions data from database
                try:
                    positions = get_positions(st.session_state.user_id)
                    st.session_state.positions = positions
                    st.session_state.db_status = 'connected'
                except Exception as e:
                    import logging
                    logging.error(f"Error getting positions: {str(e)}")
                    positions = st.session_state.positions  # Use cached positions
                    st.session_state.db_status = 'error'
                    st.error("⚠️ Unable to refresh positions due to database error.")
                
                if positions:
                    positions_data = []
                    for pos in positions:
                        # Handle both dict format and database object format
                        if isinstance(pos, dict):
                            sym = pos['symbol']
                            quantity = pos['quantity']
                            avg_price = pos['average_price']
                        else:
                            sym = pos.symbol
                            quantity = pos.quantity
                            avg_price = pos.average_price
                        
                        # Get current price for the symbol
                        current_price = data['Close'].iloc[-1] if sym == symbol else 0
                        
                        # Calculate position value
                        if current_price == 0:
                            current_value = quantity * avg_price  # Fallback if we don't have current price
                        else:
                            current_value = quantity * current_price
                        
                        # Calculate profit/loss
                        profit_loss = current_value - (quantity * avg_price)
                        profit_loss_pct = (profit_loss / (quantity * avg_price)) * 100 if (quantity * avg_price) > 0 else 0
                        
                        positions_data.append({
                            "Symbol": sym,
                            "Quantity": quantity,
                            "Entry Price": f"${avg_price:.2f}",
                            "Current Price": f"${current_price:.2f}" if current_price > 0 else "Unknown",
                            "Current Value": f"${current_value:.2f}",
                            "Profit/Loss": f"${profit_loss:.2f} ({profit_loss_pct:.2f}%)"
                        })
                    
                    st.subheader("Current Positions")
                    st.dataframe(pd.DataFrame(positions_data))
                else:
                    st.info("You have no open positions.")
                
                # Trading form
                st.subheader("Place a Trade")
                with st.form("trade_form"):
                    trade_cols = st.columns(3)
                    with trade_cols[0]:
                        trade_symbol = st.text_input("Symbol", value=symbol)
                    with trade_cols[1]:
                        trade_action = st.selectbox("Action", ["Buy", "Sell"])
                    with trade_cols[2]:
                        trade_quantity = st.number_input("Quantity", min_value=1, value=1)
                    
                    submit_trade = st.form_submit_button("Execute Trade")
                
                if submit_trade:
                    # Get current price (in a real app, fetch the latest price)
                    current_price = data['Close'].iloc[-1] if trade_symbol == symbol else 100.0
                    
                    trade_value = current_price * trade_quantity
                    
                    # Save trade in database
                    try:
                        trade_result = record_trade(
                            st.session_state.user_id,
                            trade_symbol,
                            trade_action,
                            trade_quantity,
                            current_price,
                            notes=f"Trade executed from pattern detector app"
                        )
                        st.session_state.db_status = 'connected'
                    except Exception as e:
                        import logging
                        logging.error(f"Error recording trade: {str(e)}")
                        st.session_state.db_status = 'error'
                        trade_result = {
                            "success": False,
                            "message": f"Could not execute trade due to database error: {str(e)}",
                            "new_balance": st.session_state.balance
                        }
                    
                    if trade_result["success"]:
                        # Update local session state
                        st.session_state.balance = trade_result["new_balance"]
                        
                        # Refresh positions from database
                        try:
                            st.session_state.positions = get_positions(st.session_state.user_id)
                            st.session_state.db_status = 'connected'
                        except Exception as e:
                            import logging
                            logging.error(f"Error getting positions after trade: {str(e)}")
                            # Positions already updated in trade_result
                            st.session_state.db_status = 'error'
                        
                        # Refresh trades from database
                        try:
                            st.session_state.trades = get_trades(st.session_state.user_id)
                            st.session_state.db_status = 'connected'
                        except Exception as e:
                            import logging
                            logging.error(f"Error getting trades after trade: {str(e)}")
                            # Use existing trades data as fallback
                            st.session_state.db_status = 'error'
                        
                        st.success(trade_result["message"])
                        st.rerun()
                    else:
                        st.error(trade_result["message"])
                
                # Trading history
                if st.session_state.trades:
                    st.subheader("Trade History")
                    
                    trades_data = []
                    for t in st.session_state.trades:
                        # Format trade data from database records
                        try:
                            if isinstance(t, dict):
                                # Handle old format from session state
                                time_str = t['time'].strftime("%Y-%m-%d %H:%M") if hasattr(t['time'], 'strftime') else str(t['time'])
                                symbol = t['symbol']
                                action = t['action']
                                quantity = t['quantity']
                                price = t['price']
                                value = t['value']
                            else:
                                # Handle database record format
                                time_str = t.trade_time.strftime("%Y-%m-%d %H:%M") if hasattr(t.trade_time, 'strftime') else str(t.trade_time)
                                symbol = t.symbol
                                action = t.action
                                quantity = t.quantity
                                price = t.price
                                value = t.total_value
                        except Exception as e:
                            # Fallback with basic formatting if there's an error
                            st.warning(f"Error formatting trade: {str(e)}")
                            time_str = str(getattr(t, 'trade_time', 'Unknown'))
                            symbol = getattr(t, 'symbol', 'Unknown')
                            action = getattr(t, 'action', 'Unknown')
                            quantity = getattr(t, 'quantity', 0)
                            price = getattr(t, 'price', 0)
                            value = getattr(t, 'total_value', 0)
                            
                        trades_data.append({
                            "Time": time_str,
                            "Symbol": symbol,
                            "Action": action,
                            "Quantity": quantity,
                            "Price": f"${price:.2f}",
                            "Value": f"${value:.2f}"
                        })
                    
                    trades_df = pd.DataFrame(trades_data)
                    st.dataframe(trades_df)
            
            # Share & Export Tab
            with pattern_tabs[4]:
                st.markdown("### Share & Export Detected Patterns")
                
                # Create tabs for different sharing/export options
                share_tabs = st.tabs(["Social Sharing", "Export Options", "Generate Image"])
                
                # Social Sharing Tab
                with share_tabs[0]:
                    st.subheader("Share Your Analysis")
                    
                    # Select pattern to share
                    detected_pattern_types = []
                    
                    # Collect all detected pattern types
                    for pattern_name, pattern_locations in patterns.items():
                        if isinstance(pattern_locations, tuple):
                            # Skip support/resistance which returns a tuple
                            continue
                        
                        if pattern_locations and len(pattern_locations) > 0:
                            formatted_name = pattern_name.replace('_', ' ').title()
                            detected_pattern_types.append(formatted_name)
                    
                    if detected_pattern_types:
                        share_pattern_type = st.selectbox("Select pattern to share:", detected_pattern_types)
                        
                        # Create a sharing link
                        share_link = get_sharing_link(symbol, share_pattern_type, f"{start_date.strftime('%Y-%m-%d')}_{end_date.strftime('%Y-%m-%d')}")
                        
                        # Custom sharing message
                        share_title = f"I found a {share_pattern_type} pattern for {symbol}!"
                        share_description = st.text_area("Customize your message:", 
                            value=f"I detected a {share_pattern_type} pattern for {symbol} using Chart Pattern Detector. Current price: ${data['Close'].iloc[-1]:.2f}")
                        
                        # Display sharing buttons
                        st.markdown("### Share on Social Media")
                        st.markdown(get_social_share_html(share_title, share_description, url=share_link), unsafe_allow_html=True)
                        
                        # Copy link option
                        st.text_input("Or copy this link:", value=share_link)
                    else:
                        st.info("No patterns were detected to share. Try adjusting the pattern detection settings.")
                
                # Export Options Tab
                with share_tabs[1]:
                    st.subheader("Export Data and Analysis")
                    
                    # Export current chart data
                    st.markdown("### Export Chart Data")
                    
                    export_options = st.multiselect("Select what to export:", 
                        ["Price Data", "Detected Patterns", "Technical Indicators"], 
                        default=["Price Data"])
                    
                    export_format = st.radio("Export format:", ["CSV", "JSON", "Excel"])
                    
                    if st.button("Generate Export"):
                        # Prepare export data
                        export_data = data.copy()
                        
                        # Filter columns based on selection
                        selected_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
                        
                        if "Technical Indicators" in export_options:
                            if 'RSI' in export_data.columns:
                                selected_columns.append('RSI')
                            if 'MACD' in export_data.columns:
                                selected_columns.extend(['MACD', 'MACD_Signal', 'MACD_Histogram'])
                            if 'BB_Upper' in export_data.columns:
                                selected_columns.extend(['BB_Upper', 'BB_Middle', 'BB_Lower'])
                            if 'SMA_20' in export_data.columns:
                                selected_columns.extend(['SMA_20', 'SMA_50', 'SMA_200'])
                        
                        # Adjust for different formats
                        if export_format == "CSV":
                            csv_buffer = StringIO()
                            export_data[selected_columns].to_csv(csv_buffer)
                            export_bytes = csv_buffer.getvalue().encode()
                            mime_type = "text/csv"
                            file_extension = "csv"
                        elif export_format == "JSON":
                            export_bytes = export_data[selected_columns].to_json(date_format='iso').encode()
                            mime_type = "application/json"
                            file_extension = "json"
                        else:  # Excel
                            # For Excel we use CSV as a fallback
                            csv_buffer = StringIO()
                            export_data[selected_columns].to_csv(csv_buffer)
                            export_bytes = csv_buffer.getvalue().encode()
                            mime_type = "text/csv"
                            file_extension = "csv"
                        
                        # Create download button
                        st.download_button(
                            label=f"Download {symbol} data as {export_format}",
                            data=export_bytes,
                            file_name=f"{symbol}_analysis.{file_extension}",
                            mime=mime_type
                        )
                
                # Generate Image Tab
                with share_tabs[2]:
                    st.subheader("Generate Shareable Image")
                    
                    # Select pattern for image
                    if detected_pattern_types:
                        image_pattern_type = st.selectbox("Select pattern for image:", detected_pattern_types, key="image_pattern_select")
                        
                        # Get pattern-specific data
                        orig_pattern_name = image_pattern_type.lower().replace(' ', '_')
                        if orig_pattern_name in patterns and patterns[orig_pattern_name]:
                            # For standard patterns
                            pattern_locations = patterns[orig_pattern_name]
                            if pattern_locations:
                                if isinstance(pattern_locations[0], list):
                                    idx_val = pattern_locations[-1][-1]
                                else:
                                    idx_val = pattern_locations[-1]
                                
                                pattern_price = float(data['Close'].iloc[idx_val])
                                pattern_date = data.index[idx_val].strftime('%Y-%m-%d')
                                
                                # Customize image notes
                                image_notes = st.text_area("Add notes to the image:", 
                                    value=f"Pattern detected with {sensitivity}/10 sensitivity", key="image_notes")
                                
                                # Generate the image
                                if st.button("Generate Image"):
                                    # Create a copy of the figure for the image
                                    img_fig = create_candlestick_chart(data, symbol)
                                    img_fig = add_pattern_shapes(img_fig, data, patterns)
                                    
                                    # Create the shareable image
                                    img_b64 = create_shareable_image(
                                        img_fig, 
                                        symbol, 
                                        image_pattern_type, 
                                        pattern_price, 
                                        pattern_date,
                                        image_notes
                                    )
                                    
                                    # Display the image
                                    st.markdown("### Your Shareable Image")
                                    st.markdown(f"<img src='data:image/png;base64,{img_b64}' style='width:100%'>", unsafe_allow_html=True)
                                    
                                    # Download option
                                    image_bytes = base64.b64decode(img_b64)
                                    st.download_button(
                                        label="Download Image",
                                        data=image_bytes,
                                        file_name=f"{symbol}_{image_pattern_type.replace(' ', '_')}.png",
                                        mime="image/png"
                                    )
                        else:
                            st.info(f"No specific data available for {image_pattern_type} pattern.")
                    else:
                        st.info("No patterns were detected to generate an image. Try adjusting the pattern detection settings.")
            
            # Data table with download option
            st.header("Historical Data")
            st.dataframe(data)
            
            # Download button for CSV
            csv_buffer = StringIO()
            data.to_csv(csv_buffer)
            csv_str = csv_buffer.getvalue()
            
            st.download_button(
                label="Download Data as CSV",
                data=csv_str,
                file_name=f"{symbol}_data.csv",
                mime="text/csv"
            )
            
            # Educational section
            st.header("Chart Pattern Education")
            
            pattern_info = {
                "Double Bottom": {
                    "description": "A reversal pattern that forms after a downtrend and signals a potential upward reversal.",
                    "identification": "Look for two lows at approximately the same price level with a moderate peak in between.",
                    "trading_strategy": "Entry point is typically when the price breaks above the peak between the two bottoms."
                },
                "Double Top": {
                    "description": "A reversal pattern that forms after an uptrend and signals a potential downward reversal.",
                    "identification": "Look for two peaks at approximately the same price level with a moderate trough in between.",
                    "trading_strategy": "Entry point is typically when the price breaks below the trough between the two tops."
                },
                "Head and Shoulders": {
                    "description": "A reversal pattern that signals a bullish-to-bearish trend change.",
                    "identification": "Look for three peaks with the middle peak (head) higher than the two surrounding peaks (shoulders).",
                    "trading_strategy": "Entry point is when price breaks below the neckline drawn connecting the lows between the peaks."
                },
                "Inverse Head and Shoulders": {
                    "description": "A reversal pattern that signals a bearish-to-bullish trend change.",
                    "identification": "Look for three troughs with the middle trough (head) lower than the two surrounding troughs (shoulders).",
                    "trading_strategy": "Entry point is when price breaks above the neckline drawn connecting the highs between the troughs."
                },
                "Triangle Patterns": {
                    "description": "Continuation or reversal patterns that form as price consolidates within converging trend lines.",
                    "identification": "Symmetrical: Lower highs and higher lows. Ascending: Higher lows with horizontal resistance. Descending: Lower highs with horizontal support.",
                    "trading_strategy": "Entry point is typically when price breaks out of the triangle pattern."
                }
            }
            
            pattern_educ_tabs = st.tabs(list(pattern_info.keys()))
            
            for i, (pattern_name, info) in enumerate(pattern_info.items()):
                with pattern_educ_tabs[i]:
                    st.markdown(f"### {pattern_name}")
                    st.markdown(f"**Description:** {info['description']}")
                    st.markdown(f"**How to Identify:** {info['identification']}")
                    st.markdown(f"**Trading Strategy:** {info['trading_strategy']}")

        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
else:
    # Initial state instructions
    st.info("👈 Enter a stock symbol and configure parameters in the sidebar, then click 'Fetch & Analyze Data' to get started.")
    
    # Show example of what the app can do
    st.markdown("""
    ## Features of this application:
    
    - **Real-time Data**: Fetch the latest stock and cryptocurrency data from Yahoo Finance
    - **Pattern Detection**: Automatically identify common chart patterns like double bottoms, head and shoulders, etc.
    - **Technical Analysis**: View popular indicators including RSI, MACD, and Bollinger Bands
    - **Interactive Charts**: Zoom, pan, and hover to explore the data in detail
    - **Virtual Trading**: Test trading strategies based on detected patterns without risking real money
    - **Educational Resources**: Learn about different chart patterns and their significance
    """)
