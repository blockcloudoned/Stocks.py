"""
Utility functions for social sharing features
"""
import io
import base64
import json
from datetime import datetime
from typing import Dict, Any, Optional
import pandas as pd
import plotly.graph_objects as go
from PIL import Image, ImageDraw, ImageFont
import streamlit as st

def get_sharing_link(symbol: str, pattern_type: str, timeframe: str) -> str:
    """
    Generate a shareable link to the application with pre-filled parameters.
    
    Args:
        symbol: The ticker symbol
        pattern_type: The detected pattern type
        timeframe: The chart timeframe (e.g., '1y', '6mo')
    
    Returns:
        Shareable URL
    """
    base_url = "https://chart-pattern-detector.replit.app/"
    query_params = f"?symbol={symbol}&pattern={pattern_type}&timeframe={timeframe}"
    return base_url + query_params


def create_shareable_image(
    fig: go.Figure, 
    symbol: str, 
    pattern_type: str, 
    price: float, 
    date: Optional[str] = None,
    notes: Optional[str] = None
) -> str:
    """
    Create a shareable image for social media from a plotly figure.
    
    Args:
        fig: Plotly figure of the chart
        symbol: The ticker symbol
        pattern_type: The type of pattern detected
        price: The price at the pattern
        date: Optional date of the pattern detection
        notes: Optional notes about the pattern
    
    Returns:
        Base64 encoded image string
    """
    # Convert Plotly figure to image
    img_bytes = fig.to_image(format="png", width=1200, height=800, scale=2)
    img = Image.open(io.BytesIO(img_bytes))
    
    # Add attribution and pattern info
    draw = ImageDraw.Draw(img)
    
    # Try to load a font, with fallback to default
    try:
        font_large = ImageFont.truetype("DejaVuSans.ttf", 36)
        font_regular = ImageFont.truetype("DejaVuSans.ttf", 24)
    except IOError:
        font_large = ImageFont.load_default()
        font_regular = ImageFont.load_default()
    
    # Add header with pattern info
    header = f"{symbol}: {pattern_type} Detected"
    draw.text((50, 30), header, fill=(255, 255, 255), font=font_large)
    
    # Add details
    details = [
        f"Price: ${price:.2f}",
        f"Date: {date or datetime.now().strftime('%Y-%m-%d')}"
    ]
    
    if notes:
        details.append(f"Notes: {notes}")
        
    details.append("Generated by Chart Pattern Detector")
    
    y_pos = 80
    for line in details:
        draw.text((50, y_pos), line, fill=(255, 255, 255), font=font_regular)
        y_pos += 30
    
    # Convert back to bytes
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    
    # Convert to base64 for embedding
    img_str = base64.b64encode(buffer.getvalue()).decode('utf-8')
    return img_str


def export_pattern_data(
    pattern_data: Dict[str, Any], 
    include_chart_data: bool = False, 
    chart_data: Optional[pd.DataFrame] = None
) -> Dict[str, Any]:
    """
    Export pattern data in a structured format for sharing or downloading
    
    Args:
        pattern_data: Dictionary with pattern information
        include_chart_data: Whether to include the chart data
        chart_data: DataFrame with chart data (required if include_chart_data is True)
        
    Returns:
        Dictionary with formatted pattern data for export
    """
    export_data = {
        "symbol": pattern_data.get("symbol", ""),
        "pattern_type": pattern_data.get("pattern_type", ""),
        "detection_date": pattern_data.get("detection_date", datetime.now().isoformat()),
        "price": pattern_data.get("price", 0.0),
        "confidence": pattern_data.get("confidence", 0.0),
        "notes": pattern_data.get("notes", ""),
        "generated_by": "Chart Pattern Detector"
    }
    
    if include_chart_data and chart_data is not None:
        # Convert the DataFrame to dict for JSON serialization
        export_data["chart_data"] = json.loads(chart_data.reset_index().to_json(orient="records", date_format="iso"))
        
    return export_data


def get_social_share_html(
    title: str, 
    description: str, 
    image_url: Optional[str] = None, 
    url: Optional[str] = None
) -> str:
    """
    Generate HTML for social sharing buttons
    
    Args:
        title: The title to share
        description: The description to share
        image_url: URL to an image to share (optional)
        url: URL to share (optional)
        
    Returns:
        HTML string with social sharing buttons
    """
    # Encode parameters for URLs
    encoded_title = title.replace(" ", "%20")
    encoded_desc = description.replace(" ", "%20")
    
    # Current URL if not provided
    if not url:
        url = "https://chart-pattern-detector.replit.app/"
    
    encoded_url = url.replace(":", "%3A").replace("/", "%2F")
    
    # Generate share buttons
    twitter_url = f"https://twitter.com/intent/tweet?text={encoded_desc}&url={encoded_url}"
    linkedin_url = f"https://www.linkedin.com/shareArticle?mini=true&url={encoded_url}&title={encoded_title}&summary={encoded_desc}"
    facebook_url = f"https://www.facebook.com/sharer/sharer.php?u={encoded_url}"
    
    # Create HTML for buttons
    html = f"""
    <div style="display: flex; gap: 10px; margin-top: 10px;">
        <a href="{twitter_url}" target="_blank" style="text-decoration: none;">
            <div style="background-color: #1DA1F2; color: white; padding: 8px 16px; border-radius: 4px; font-weight: bold;">
                Twitter
            </div>
        </a>
        <a href="{linkedin_url}" target="_blank" style="text-decoration: none;">
            <div style="background-color: #0077B5; color: white; padding: 8px 16px; border-radius: 4px; font-weight: bold;">
                LinkedIn
            </div>
        </a>
        <a href="{facebook_url}" target="_blank" style="text-decoration: none;">
            <div style="background-color: #3b5998; color: white; padding: 8px 16px; border-radius: 4px; font-weight: bold;">
                Facebook
            </div>
        </a>
    </div>
    """
    
    return html