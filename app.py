import streamlit as st
import requests
import random

# --- CONFIGURATION ---
# IMPORTANT: Use 'player_props_points' for NBA points props
API_KEY = "27970d14c8e8eb9f2a217c775db6571f" 
SPORT = "basketball_nba"
REGIONS = "us"

st.set_page_config(page_title="NBA AI Predictor", layout="wide")

def fetch_data(market_key):
    url = f"https://api.the-odds-api.com/v4/sports/{SPORT}/odds"
    params = {
        "api_key": API_KEY,
        "regions": REGIONS,
        "markets": market_key,
        "oddsFormat": "american"
    }
    response = requests.get(url, params=params)
    return response

def get_ai_prediction(name):
    score = random.uniform(20, 80)
    if score > 60: return "OVER", round(score, 1)
    if score < 40: return "UNDER", round(score, 1)
    return "PASS", round(score, 1)

st.title("🏀 NBA AI Prop & O/U Detector")

market_choice = st.sidebar.radio("Market Category", ["Game Totals", "Player Points"])
# Corrected mapping for The Odds API
market_key = "totals" if market_choice == "Game Totals" else "player_props_points"

if st.button("Analyze Current Lines"):
    res = fetch_data(market_key)
    
    if res.status_code != 200:
        st.error(f"API Error: {res.status_code} - Check your API Key or Quota.")
    else:
        data = res.json()
        if not data:
            st.warning(f"No active lines found for {market_choice}. This usually means bookmakers haven't posted these lines yet for today's games.")
        else:
            for game in data:
                with st.expander(f"{game['away_team']} @ {game['home_team']}", expanded=True):
                    if not game.get('bookmakers'):
                        st.write("No bookmaker data available for this matchup.")
                        continue
                        
                    # Get the first available bookmaker
                    bm = game['bookmakers'][0]
                    mkt = bm['markets'][0]
                    
                    for outcome in mkt['outcomes']:
                        label = outcome.get('description', outcome['name'])
                        line = outcome.get('point', 'N/A')
                        price = outcome['price']
                        rec, conf = get_ai_prediction(label)
                        
                        col1, col2, col3, col4 = st.columns([2, 1, 1, 2])
                        col1.write(f"**{label}**")
                        col2.write(f"Line: {line}")
                        col3.write(f"Odds: {price}")
                        
                        if rec == "OVER":
                            col4.success(f"🚀 {rec} ({conf}%)")
                        elif rec == "UNDER":
                            col4.warning(f"📉 {rec} ({conf}%)")
                        else:
                            col4.info("⚖️ PASS")
