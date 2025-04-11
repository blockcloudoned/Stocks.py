import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from typing import Dict, List, Any

def create_candlestick_chart(data: pd.DataFrame, title: str = "Price Chart") -> go.Figure:
    """
    Create a candlestick chart with volume bars.
    
    Args:
        data: DataFrame with OHLC price data
        title: Chart title
    
    Returns:
        Plotly Figure object
    """
    # Create subplot with 2 rows
    fig = make_subplots(
        rows=2, 
        cols=1, 
        shared_xaxes=True,
        vertical_spacing=0.05,
        row_heights=[0.8, 0.2]  # Main chart 80%, volume 20%
    )
    
    # Add candlestick trace
    fig.add_trace(
        go.Candlestick(
            x=data.index,
            open=data['Open'],
            high=data['High'],
            low=data['Low'],
            close=data['Close'],
            name="Price"
        ),
        row=1, col=1
    )
    
    # Add volume bar chart
    fig.add_trace(
        go.Bar(
            x=data.index,
            y=data['Volume'],
            name="Volume",
            marker_color='rgba(0, 0, 255, 0.3)'
        ),
        row=2, col=1
    )
    
    # Update layout
    fig.update_layout(
        title=title,
        xaxis_title="Date",
        yaxis_title="Price",
        xaxis_rangeslider_visible=False,
        height=800,
        template="plotly_white",
        hovermode="x unified",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    # Update y-axis labels
    fig.update_yaxes(title_text="Price", row=1, col=1)
    fig.update_yaxes(title_text="Volume", row=2, col=1)
    
    return fig

def add_pattern_shapes(fig: go.Figure, data: pd.DataFrame, patterns: Dict[str, Any]) -> go.Figure:
    """
    Add pattern visualization shapes to the chart.
    
    Args:
        fig: Plotly Figure object
        data: DataFrame with OHLC price data
        patterns: Dictionary with detected patterns
    
    Returns:
        Updated Plotly Figure
    """
    # Add double bottoms
    if 'double_bottoms' in patterns and patterns['double_bottoms']:
        for bottom_idx in patterns['double_bottoms']:
            if isinstance(bottom_idx, list) and len(bottom_idx) == 2:
                idx1, idx2 = bottom_idx
                
                # Draw lines connecting the bottoms
                fig.add_shape(
                    type="line",
                    x0=data.index[idx1],
                    y0=data['Low'][idx1],
                    x1=data.index[idx2],
                    y1=data['Low'][idx2],
                    line=dict(color="green", width=2, dash="dash"),
                    row=1, col=1
                )
                
                # Add annotation
                fig.add_annotation(
                    x=data.index[idx2],
                    y=data['Low'][idx2],
                    text="Double Bottom",
                    showarrow=True,
                    arrowhead=1,
                    arrowcolor="green",
                    arrowsize=1,
                    arrowwidth=2,
                    ax=0,
                    ay=40,
                    row=1, col=1
                )
    
    # Add double tops
    if 'double_tops' in patterns and patterns['double_tops']:
        for top_idx in patterns['double_tops']:
            if isinstance(top_idx, list) and len(top_idx) == 2:
                idx1, idx2 = top_idx
                
                # Draw lines connecting the tops
                fig.add_shape(
                    type="line",
                    x0=data.index[idx1],
                    y0=data['High'][idx1],
                    x1=data.index[idx2],
                    y1=data['High'][idx2],
                    line=dict(color="red", width=2, dash="dash"),
                    row=1, col=1
                )
                
                # Add annotation
                fig.add_annotation(
                    x=data.index[idx2],
                    y=data['High'][idx2],
                    text="Double Top",
                    showarrow=True,
                    arrowhead=1,
                    arrowcolor="red",
                    arrowsize=1,
                    arrowwidth=2,
                    ax=0,
                    ay=-40,
                    row=1, col=1
                )
    
    # Add head and shoulders
    if 'head_shoulders' in patterns and patterns['head_shoulders']:
        for hs_idx in patterns['head_shoulders']:
            if isinstance(hs_idx, list) and len(hs_idx) == 5:
                peak1_idx, trough1_idx, peak2_idx, trough2_idx, peak3_idx = hs_idx
                
                # Draw lines connecting the pattern points
                fig.add_shape(
                    type="path",
                    path=f"M {data.index[peak1_idx]},{data['High'][peak1_idx]} L {data.index[trough1_idx]},{data['Low'][trough1_idx]} L {data.index[peak2_idx]},{data['High'][peak2_idx]} L {data.index[trough2_idx]},{data['Low'][trough2_idx]} L {data.index[peak3_idx]},{data['High'][peak3_idx]}",
                    line=dict(color="red", width=2),
                    row=1, col=1
                )
                
                # Add neckline
                fig.add_shape(
                    type="line",
                    x0=data.index[trough1_idx],
                    y0=data['Low'][trough1_idx],
                    x1=data.index[trough2_idx],
                    y1=data['Low'][trough2_idx],
                    line=dict(color="red", width=2, dash="dash"),
                    row=1, col=1
                )
                
                # Extend neckline
                if peak3_idx + 5 < len(data):
                    neckline_slope = (data['Low'][trough2_idx] - data['Low'][trough1_idx]) / (trough2_idx - trough1_idx)
                    extended_y = data['Low'][trough2_idx] + neckline_slope * (peak3_idx + 5 - trough2_idx)
                    
                    fig.add_shape(
                        type="line",
                        x0=data.index[trough2_idx],
                        y0=data['Low'][trough2_idx],
                        x1=data.index[peak3_idx + 5],
                        y1=extended_y,
                        line=dict(color="red", width=2, dash="dot"),
                        row=1, col=1
                    )
                
                # Add annotation
                fig.add_annotation(
                    x=data.index[peak2_idx],
                    y=data['High'][peak2_idx],
                    text="H&S",
                    showarrow=True,
                    arrowhead=1,
                    arrowcolor="red",
                    arrowsize=1,
                    arrowwidth=2,
                    ax=0,
                    ay=-40,
                    row=1, col=1
                )
    
    # Add inverse head and shoulders
    if 'inv_head_shoulders' in patterns and patterns['inv_head_shoulders']:
        for ihs_idx in patterns['inv_head_shoulders']:
            if isinstance(ihs_idx, list) and len(ihs_idx) == 5:
                trough1_idx, peak1_idx, trough2_idx, peak2_idx, trough3_idx = ihs_idx
                
                # Draw lines connecting the pattern points
                fig.add_shape(
                    type="path",
                    path=f"M {data.index[trough1_idx]},{data['Low'][trough1_idx]} L {data.index[peak1_idx]},{data['High'][peak1_idx]} L {data.index[trough2_idx]},{data['Low'][trough2_idx]} L {data.index[peak2_idx]},{data['High'][peak2_idx]} L {data.index[trough3_idx]},{data['Low'][trough3_idx]}",
                    line=dict(color="green", width=2),
                    row=1, col=1
                )
                
                # Add neckline
                fig.add_shape(
                    type="line",
                    x0=data.index[peak1_idx],
                    y0=data['High'][peak1_idx],
                    x1=data.index[peak2_idx],
                    y1=data['High'][peak2_idx],
                    line=dict(color="green", width=2, dash="dash"),
                    row=1, col=1
                )
                
                # Extend neckline
                if trough3_idx + 5 < len(data):
                    neckline_slope = (data['High'][peak2_idx] - data['High'][peak1_idx]) / (peak2_idx - peak1_idx)
                    extended_y = data['High'][peak2_idx] + neckline_slope * (trough3_idx + 5 - peak2_idx)
                    
                    fig.add_shape(
                        type="line",
                        x0=data.index[peak2_idx],
                        y0=data['High'][peak2_idx],
                        x1=data.index[trough3_idx + 5],
                        y1=extended_y,
                        line=dict(color="green", width=2, dash="dot"),
                        row=1, col=1
                    )
                
                # Add annotation
                fig.add_annotation(
                    x=data.index[trough2_idx],
                    y=data['Low'][trough2_idx],
                    text="Inv H&S",
                    showarrow=True,
                    arrowhead=1,
                    arrowcolor="green",
                    arrowsize=1,
                    arrowwidth=2,
                    ax=0,
                    ay=40,
                    row=1, col=1
                )
    
    # Add triangles
    if 'triangles' in patterns and patterns['triangles']:
        for triangle in patterns['triangles']:
            points = triangle['points']
            triangle_type = triangle['type']
            
            if len(points) == 5:
                # Draw the triangle pattern
                if triangle_type == "Symmetric":
                    # Draw upper line (descending)
                    fig.add_shape(
                        type="line",
                        x0=data.index[points[0]],
                        y0=data['High'][points[0]],
                        x1=data.index[points[4]],
                        y1=data['High'][points[4]],
                        line=dict(color="purple", width=2, dash="dash"),
                        row=1, col=1
                    )
                    
                    # Draw lower line (ascending)
                    fig.add_shape(
                        type="line",
                        x0=data.index[points[1]],
                        y0=data['Low'][points[1]],
                        x1=data.index[points[3]],
                        y1=data['Low'][points[3]],
                        line=dict(color="purple", width=2, dash="dash"),
                        row=1, col=1
                    )
                
                elif triangle_type == "Ascending":
                    # Draw horizontal resistance
                    fig.add_shape(
                        type="line",
                        x0=data.index[points[0]],
                        y0=data['High'][points[0]],
                        x1=data.index[points[4]],
                        y1=data['High'][points[4]],
                        line=dict(color="blue", width=2, dash="dash"),
                        row=1, col=1
                    )
                    
                    # Draw rising support
                    fig.add_shape(
                        type="line",
                        x0=data.index[points[1]],
                        y0=data['Low'][points[1]],
                        x1=data.index[points[3]],
                        y1=data['Low'][points[3]],
                        line=dict(color="blue", width=2, dash="dash"),
                        row=1, col=1
                    )
                
                elif triangle_type == "Descending":
                    # Draw falling resistance
                    fig.add_shape(
                        type="line",
                        x0=data.index[points[0]],
                        y0=data['High'][points[0]],
                        x1=data.index[points[2]],
                        y1=data['High'][points[2]],
                        line=dict(color="orange", width=2, dash="dash"),
                        row=1, col=1
                    )
                    
                    # Draw horizontal support
                    fig.add_shape(
                        type="line",
                        x0=data.index[points[1]],
                        y0=data['Low'][points[1]],
                        x1=data.index[points[4]],
                        y1=data['Low'][points[4]],
                        line=dict(color="orange", width=2, dash="dash"),
                        row=1, col=1
                    )
                
                # Add annotation
                fig.add_annotation(
                    x=data.index[points[2]],
                    y=data[['High', 'Low']].iloc[points[2]].mean(),
                    text=f"{triangle_type} Triangle",
                    showarrow=True,
                    arrowhead=1,
                    arrowsize=1,
                    arrowwidth=2,
                    ax=0,
                    ay=30,
                    row=1, col=1
                )
    
    # Add support levels
    if 'support' in patterns and patterns['support']:
        for support_idx in patterns['support']:
            support_price = data['Low'][support_idx]
            
            # Draw horizontal support line
            fig.add_shape(
                type="line",
                x0=data.index[0],
                y0=support_price,
                x1=data.index[-1],
                y1=support_price,
                line=dict(color="green", width=1, dash="dot"),
                row=1, col=1
            )
            
            # Add annotation
            fig.add_annotation(
                x=data.index[support_idx],
                y=support_price,
                text="Support",
                showarrow=True,
                arrowhead=1,
                arrowcolor="green",
                arrowsize=1,
                arrowwidth=1,
                ax=20,
                ay=20,
                row=1, col=1
            )
    
    # Add resistance levels
    if 'resistance' in patterns and patterns['resistance']:
        for resistance_idx in patterns['resistance']:
            resistance_price = data['High'][resistance_idx]
            
            # Draw horizontal resistance line
            fig.add_shape(
                type="line",
                x0=data.index[0],
                y0=resistance_price,
                x1=data.index[-1],
                y1=resistance_price,
                line=dict(color="red", width=1, dash="dot"),
                row=1, col=1
            )
            
            # Add annotation
            fig.add_annotation(
                x=data.index[resistance_idx],
                y=resistance_price,
                text="Resistance",
                showarrow=True,
                arrowhead=1,
                arrowcolor="red",
                arrowsize=1,
                arrowwidth=1,
                ax=20,
                ay=-20,
                row=1, col=1
            )
    
    return fig

def create_ohlc_chart(data: pd.DataFrame, title: str = "Price Chart") -> go.Figure:
    """
    Create an OHLC chart with volume bars.
    
    Args:
        data: DataFrame with OHLC price data
        title: Chart title
    
    Returns:
        Plotly Figure object
    """
    # Create subplot with 2 rows
    fig = make_subplots(
        rows=2, 
        cols=1, 
        shared_xaxes=True,
        vertical_spacing=0.05,
        row_heights=[0.8, 0.2]  # Main chart 80%, volume 20%
    )
    
    # Add OHLC trace
    fig.add_trace(
        go.Ohlc(
            x=data.index,
            open=data['Open'],
            high=data['High'],
            low=data['Low'],
            close=data['Close'],
            name="Price"
        ),
        row=1, col=1
    )
    
    # Add volume bar chart
    fig.add_trace(
        go.Bar(
            x=data.index,
            y=data['Volume'],
            name="Volume",
            marker_color='rgba(0, 0, 255, 0.3)'
        ),
        row=2, col=1
    )
    
    # Update layout
    fig.update_layout(
        title=title,
        xaxis_title="Date",
        yaxis_title="Price",
        xaxis_rangeslider_visible=False,
        height=800,
        template="plotly_white",
        hovermode="x unified",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    # Update y-axis labels
    fig.update_yaxes(title_text="Price", row=1, col=1)
    fig.update_yaxes(title_text="Volume", row=2, col=1)
    
    return fig
