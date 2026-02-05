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

st_autorefresh(interval=300000, key="nba_live_sync") 

# --- 2. CONFIG ---
st.set_page_config(page_title="NBA TRUSTED OVERS", layout="wide", page_icon="🏀")
API_KEY = "2bbe95bafab32dd8fa0be8ae23608feb" 

# Season Scoring Averages
TEAM_PPG = {
    "Detroit Pistons": 116.9, "Washington Wizards": 111.5, "Orlando Magic": 112.5, 
    "Brooklyn Nets": 107.1, "Toronto Raptors": 113.8, "Chicago Bulls": 114.2,
    "Atlanta Hawks": 118.5, "Utah Jazz": 115.6, "Dallas Mavericks": 118.8, 
    "San Antonio Spurs": 116.9, "Philadelphia 76ers": 114.3, "Los Angeles Lakers": 116.3,
    "Phoenix Suns": 116.5, "Golden State Warriors": 117.8, "Houston Rockets": 114.0,
    "Charlotte Hornets": 110.2
}

def get_nba_edge(home_team, away_team, bookie_line, price):
    h_avg = TEAM_PPG.get(home_team, 115.0)
    a_avg = TEAM_PPG.get(away_team, 115.0)
    base_projection = h_avg + a_avg
    z_score = (bookie_line - base_projection) / 12.0
    prob_over = 1 - norm.cdf(z_score)
    edge = prob_over - (1 / price)
    return base_projection, prob_over, edge

# --- 3. LIVE FEED & ERROR CATCHER ---
st.title("🏀 NBA LIVE COMMAND: TRUSTED OVERS")

url = f"https://api.the-odds-api.com/v4/sports/basketball_nba/odds/?apiKey={API_KEY}&regions=us&markets=totals&oddsFormat=decimal"

try:
    response = requests.get(url)
    data = response.json()

    # CHECK IF API SENT AN ERROR MESSAGE INSTEAD OF DATA
    if isinstance(data, dict) and "msg" in data:
        st.error(f"🚫 API Error: {data['msg']}")
        st.stop()
    
    if not isinstance(data, list):
        st.error("🚫 Unexpected API response. Please check your API Key subscription.")
        st.stop()

    found_play = False
    for game in data:
        try:
            home, away = game['home_team'], game['away_team']
            bookmaker = game['bookmakers'][0]
            market = next(m for m in bookmaker['markets'] if m['key'] == 'totals')
            over_outcome = next(o for o in market['outcomes'] if o['name'] == 'Over')
            
            line, price = over_outcome['point'], over_outcome['price']
            proj, prob, edge = get_nba_edge(home, away, line, price)

            if edge > 0.02:
                found_play = True
                with st.expander(f"🔥 {home} vs {away}", expanded=True):
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Bookie Line", f"{line}")
                    c2.metric("AI Projection", f"{proj:.1f}")
                    c3.metric("Edge", f"{edge:+.1%}")
                    st.success(f"**Play:** Take the OVER {line}")
        except: continue

    if not found_play:
        st.info("No 'Trusted' Over plays currently detected. Markets usually populate fully 1-2 hours before tip-off.")

except Exception as e:
    st.error(f"System Error: {e}")
