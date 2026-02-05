import streamlit as st
import requests
import pandas as pd
import numpy as np
from scipy.stats import norm
from streamlit_autorefresh import st_autorefresh

# --- 1. ACCESS & REFRESH ---
PASSWORD = "benja123"
st.sidebar.title("🔒 NBA PRIVATE ACCESS")
password = st.sidebar.text_input("Password", type="password")

if password != PASSWORD:
    st.warning("Please enter the correct access key.")
    st.stop()

# Auto-refresh every 5 minutes to catch line movement
st_autorefresh(interval=300000, key="nba_live_sync") 

# --- 2. THE-ODDS-API CONFIG ---
st.set_page_config(page_title="NBA TRUSTED OVERS", layout="wide", page_icon="🏀")
API_KEY = "2bbe95bafab32dd8fa0be8ae23608feb" # Your Active Key

# Season Scoring Averages for Feb 2026 Context
TEAM_PPG = {
    "Detroit Pistons": 116.9, "Washington Wizards": 111.5,
    "Orlando Magic": 112.5, "Brooklyn Nets": 107.1,
    "Toronto Raptors": 113.8, "Chicago Bulls": 114.2,
    "Atlanta Hawks": 118.5, "Utah Jazz": 115.6,
    "Dallas Mavericks": 118.8, "San Antonio Spurs": 116.9,
    "Philadelphia 76ers": 114.3, "Los Angeles Lakers": 116.3,
    "Phoenix Suns": 116.5, "Golden State Warriors": 117.8
}

def get_nba_edge(home_team, away_team, bookie_line, price):
    # Base Projection: Combined Season Averages
    h_avg = TEAM_PPG.get(home_team, 115.0)
    a_avg = TEAM_PPG.get(away_team, 115.0)
    base_projection = h_avg + a_avg
    
    # Normal Distribution Simulation
    std_dev = 12.0 # Standard NBA variance
    z_score = (bookie_line - base_projection) / std_dev
    prob_over = 1 - norm.cdf(z_score)
    edge = prob_over - (1 / price)
    return base_projection, prob_over, edge

# --- 3. THE LIVE FEED ---
st.title("🏀 NBA LIVE COMMAND: TRUSTED OVERS")
st.info(f"Scanning Live Markets for {pd.Timestamp.now().strftime('%H:%M')}")

# Targeting 'totals' market for Over/Under plays
url = f"https://api.the-odds-api.com/v4/sports/basketball_nba/odds/?apiKey={API_KEY}&regions=us&markets=totals&oddsFormat=decimal"

try:
    response = requests.get(url)
    data = response.json()
    found_play = False

    for game in data:
        try:
            home, away = game['home_team'], game['away_team']
            
            # Extract first available bookmaker (usually FanDuel or DraftKings)
            bookmaker = game['bookmakers'][0]
            market = next(m for m in bookmaker['markets'] if m['key'] == 'totals')
            over_outcome = next(o for o in market['outcomes'] if o['name'] == 'Over')
            
            line = over_outcome['point']
            price = over_outcome['price']
            
            # Run AI Math
            proj, prob, edge = get_nba_edge(home, away, line, price)

            # --- DISPLAY FILTER: EDGE > 2% ---
            if edge > 0.02:
                found_play = True
                with st.expander(f"🔥 {home} vs {away}", expanded=True):
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("Bookie Line", f"{line}")
                    c2.metric("AI Projection", f"{proj:.1f}")
                    c3.metric("Win Prob", f"{prob:.1%}")
                    c4.metric("Edge", f"{edge:+.1%}")
                    
                    if edge > 0.06:
                        st.error(f"☢️ HIGH VALUE DETECTED: TAKE OVER {line}")
                    else:
                        st.success(f"✅ RECOMMENDED: Over {line}")
        except (KeyError, IndexError, StopIteration):
            continue

    if not found_play:
        st.warning("No games currently meet the 'Trusted' edge criteria. Lowering your threshold may show more results.")

except Exception as e:
    st.error(f"API Error: {e}. Check if your key is active.")
