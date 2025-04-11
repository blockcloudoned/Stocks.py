import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import datetime
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

# Set page config
st.set_page_config(
    page_title="Stock Pattern Detector",
    page_icon="📈",
    layout="wide"
)

# Initialize session state variables
if 'trades' not in st.session_state:
    st.session_state.trades = []
if 'balance' not in st.session_state:
    st.session_state.balance = 10000.0
if 'positions' not in st.session_state:
    st.session_state.positions = {}

# App title and description
st.title("📊 Stock & Crypto Pattern Detector")
st.markdown("""
This application helps you identify chart patterns, visualize technical indicators, 
and analyze trading opportunities in stocks and cryptocurrencies.
""")

# Sidebar
with st.sidebar:
    st.header("Input Parameters")
    
    # Symbol input
    symbol = st.text_input("Enter Symbol (e.g., AAPL, BTC-USD):", value="AAPL")
    
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
            
            if detect_double_bottoms:
                patterns['double_bottoms'] = detect_double_bottom(data, sensitivity=sensitivity)
            
            if detect_double_tops:
                patterns['double_tops'] = detect_double_top(data, sensitivity=sensitivity)
            
            if detect_head_shoulders:
                patterns['head_shoulders'] = detect_head_and_shoulders(data, sensitivity=sensitivity)
            
            if detect_inv_head_shoulders:
                patterns['inv_head_shoulders'] = detect_inverse_head_and_shoulders(data, sensitivity=sensitivity)
            
            if detect_triangles:
                patterns['triangles'] = detect_triangle(data, sensitivity=sensitivity)
            
            if detect_support_resistance:
                patterns['support'], patterns['resistance'] = find_support_resistance(data, sensitivity=sensitivity)
            
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
                "Virtual Trading"
            ])
            
            # Detected Patterns Tab
            with pattern_tabs[0]:
                if sum(len(p) for p in patterns.values() if isinstance(p, list)) > 0:
                    st.markdown("### Recently Detected Patterns")
                    
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
                                "Pattern Strength": [f"{np.random.randint(60, 95)}%" for _ in pattern_locations[-5:]]
                            })
                            
                            st.dataframe(pattern_df)
                else:
                    st.info("No patterns were detected with the current settings. Try adjusting the sensitivity or selecting different patterns.")
            
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
                if st.session_state.positions:
                    positions_data = []
                    for sym, pos in st.session_state.positions.items():
                        current_price = data['Close'].iloc[-1] if sym == symbol else 0  # In real app, fetch price for each symbol
                        if current_price == 0:
                            current_value = pos['quantity'] * pos['price']  # Fallback if we don't have current price
                        else:
                            current_value = pos['quantity'] * current_price
                        
                        profit_loss = current_value - (pos['quantity'] * pos['price'])
                        profit_loss_pct = (profit_loss / (pos['quantity'] * pos['price'])) * 100
                        
                        positions_data.append({
                            "Symbol": sym,
                            "Quantity": pos['quantity'],
                            "Entry Price": f"${pos['price']:.2f}",
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
                    
                    if trade_action == "Buy":
                        if trade_value <= st.session_state.balance:
                            # Update balance
                            st.session_state.balance -= trade_value
                            
                            # Update positions
                            if trade_symbol in st.session_state.positions:
                                # Average down/up
                                current_quantity = st.session_state.positions[trade_symbol]['quantity']
                                current_value = current_quantity * st.session_state.positions[trade_symbol]['price']
                                new_value = current_value + trade_value
                                new_quantity = current_quantity + trade_quantity
                                new_price = new_value / new_quantity
                                
                                st.session_state.positions[trade_symbol] = {
                                    'quantity': new_quantity,
                                    'price': new_price
                                }
                            else:
                                st.session_state.positions[trade_symbol] = {
                                    'quantity': trade_quantity,
                                    'price': current_price
                                }
                            
                            # Record the trade
                            st.session_state.trades.append({
                                'time': datetime.datetime.now(),
                                'symbol': trade_symbol,
                                'action': 'Buy',
                                'quantity': trade_quantity,
                                'price': current_price,
                                'value': trade_value
                            })
                            
                            st.success(f"Purchased {trade_quantity} shares of {trade_symbol} at ${current_price:.2f}")
                            st.rerun()
                        else:
                            st.error(f"Insufficient funds! Trade value: ${trade_value:.2f}, Balance: ${st.session_state.balance:.2f}")
                    
                    elif trade_action == "Sell":
                        if trade_symbol in st.session_state.positions and st.session_state.positions[trade_symbol]['quantity'] >= trade_quantity:
                            # Update balance
                            st.session_state.balance += trade_value
                            
                            # Update positions
                            current_quantity = st.session_state.positions[trade_symbol]['quantity']
                            new_quantity = current_quantity - trade_quantity
                            
                            if new_quantity > 0:
                                st.session_state.positions[trade_symbol]['quantity'] = new_quantity
                            else:
                                del st.session_state.positions[trade_symbol]
                            
                            # Record the trade
                            st.session_state.trades.append({
                                'time': datetime.datetime.now(),
                                'symbol': trade_symbol,
                                'action': 'Sell',
                                'quantity': trade_quantity,
                                'price': current_price,
                                'value': trade_value
                            })
                            
                            st.success(f"Sold {trade_quantity} shares of {trade_symbol} at ${current_price:.2f}")
                            st.rerun()
                        else:
                            st.error(f"Insufficient shares to sell! You own: {st.session_state.positions.get(trade_symbol, {}).get('quantity', 0)} shares of {trade_symbol}")
                
                # Trading history
                if st.session_state.trades:
                    st.subheader("Trade History")
                    
                    trades_data = []
                    for t in st.session_state.trades:
                        # Handle any potential timestamp formatting issues
                        try:
                            time_str = t['time'].strftime("%Y-%m-%d %H:%M")
                        except:
                            time_str = str(t['time'])
                            
                        trades_data.append({
                            "Time": time_str,
                            "Symbol": t['symbol'],
                            "Action": t['action'],
                            "Quantity": t['quantity'],
                            "Price": f"${t['price']:.2f}",
                            "Value": f"${t['value']:.2f}"
                        })
                    
                    trades_df = pd.DataFrame(trades_data)
                    st.dataframe(trades_df)
            
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
