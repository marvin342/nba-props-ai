import streamlit as st
import requests
import pandas as pd

# --- CONFIGURATION ---
API_KEY = "27970d14c8e8eb9f2a217c775db6571f"
SPORT = "basketball_nba"
REGIONS = "us"
MARKETS = "player_props_points,totals" # Focus on O/U for Points and Game Totals

st.set_page_config(page_title="NBA AI Over/Under Predictor", layout="wide")

# --- UI STYLE ---
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    .stMetric { background-color: #1f2937; padding: 15px; border-radius: 10px; border: 1px solid #374151; }
    </style>
    """, unsafe_allow_html=True)

st.title("🏀 NBA AI Prop & O/U Detector")
st.sidebar.header("Settings")
selected_market = st.sidebar.selectbox("Select Market", ["Player Points", "Game Totals"])

def fetch_odds(market_key):
    url = f"https://api.the-odds-api.com/v4/sports/{SPORT}/odds"
    params = {
        "api_key": API_KEY,
        "regions": REGIONS,
        "markets": market_key,
        "oddsFormat": "american"
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"Error fetching data: {response.status_code}")
        return []

# --- MOCK AI LOGIC (Replace with your ML model later) ---
def get_ai_prediction(player_name, line):
    # This is where you'd call a model trained on Box Scores
    # For now, we simulate a 'Confidence Score'
    import random
    score = random.uniform(50, 85)
    recommendation = "OVER" if score > 70 else "UNDER" if score < 30 else "PASS"
    return recommendation, round(score, 2)

# --- MAIN DASHBOARD ---
if st.button("Refresh Live Odds"):
    market_to_fetch = "player_props_points" if selected_market == "Player Points" else "totals"
    data = fetch_odds(market_to_fetch)
    
    if data:
        for game in data:
            with st.expander(f"{game['home_team']} vs {game['away_team']}"):
                cols = st.columns(3)
                
                # Iterate through bookmakers (using the first one for simplicity)
                bookie = game['bookmakers'][0]
                market = bookie['markets'][0]
                
                for outcome in market['outcomes']:
                    name = outcome.get('description', outcome['name'])
                    line = outcome['point']
                    price = outcome['price']
                    
                    # Call AI Logic
                    rec, conf = get_ai_prediction(name, line)
                    
                    with st.container():
                        c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
                        c1.write(f"**{name}**")
                        c2.write(f"Line: {line}")
                        c3.write(f"Odds: {price}")
                        
                        if rec == "OVER":
                            c4.success(f"🚀 {rec} ({conf}%)")
                        elif rec == "UNDER":
                            c4.warning(f"📉 {rec} ({conf}%)")
                        else:
                            c4.info("⚖️ NEUTRAL")
    else:
        st.write("No active lines found. Check if games are live!")
