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

st_autorefresh(interval=300000, key="nba_live_sync") # Refresh every 5 mins

# --- 2. CONFIG ---
st.set_page_config(page_title="NBA TRUSTED OVERS", layout="wide", page_icon="🏀")
API_KEY = "2bbe95bafab32dd8fa0be8ae23608feb" 

# --- 3. NBA SCORING AVERAGES (2025-26 Season) ---
# We use this to cross-reference if the Bookie total is "too high" or "too low"
TEAM_PPG = {
    "Detroit Pistons": 117.5, "Boston Celtics": 115.9, "Cleveland Cavaliers": 119.4,
    "Oklahoma City Thunder": 120.2, "Miami Heat": 119.9, "Orlando Magic": 115.0,
    "Brooklyn Nets": 107.1, "Toronto Raptors": 113.8, "Chicago Bulls": 117.2,
    "San Antonio Spurs": 116.9, "Dallas Mavericks": 113.8, "Los Angeles Lakers": 116.3
}

def get_nba_edge(home_team, away_team, bookie_line, price):
    # Calculate Base Projection from Season PPG
    h_avg = TEAM_PPG.get(home_team, 115.0)
    a_avg = TEAM_PPG.get(away_team, 115.0)
    base_projection = h_avg + a_avg
    
    # Normal Distribution (NBA std dev is ~12 pts)
    z_score = (bookie_line - base_projection) / 12.0
    prob_over = 1 - norm.cdf(z_score)
    edge = prob_over - (1 / price)
    return base_projection, prob_over, edge

# --- 4. MAIN INTERFACE ---
st.title("🏀 NBA LIVE COMMAND: TRUSTED OVERS")
st.subheader(f"Schedule for {pd.Timestamp.now().strftime('%B %d, %Y')}")

url = f"https://api.the-odds-api.com/v4/sports/basketball_nba/odds/?apiKey={API_KEY}&regions=us&markets=totals"

try:
    data = requests.get(url).json()
    found_play = False

    for m in data:
        try:
            home, away = m['home_team'], m['away_team']
            bookie = m['bookmakers'][0]
            market = next(mk for mk in bookie['markets'] if mk['key'] == 'totals')
            over = next(o for o in market['outcomes'] if o['name'] == 'Over')
            
            line, price = over['point'], over['price']
            proj, prob, edge = get_nba_edge(home, away, line, price)

            # --- DISPLAY TRUSTED PLAYS ONLY ---
            if edge > 0.03: # Filter for 3% edge or higher
                found_play = True
                with st.container():
                    st.markdown(f"### 🔥 {home} vs {away}")
                    col1, col2, col3, col4 = st.columns(4)
                    
                    col1.metric("Bookie Total", f"{line}")
                    col2.metric("AI Projection", f"{proj:.1f}")
                    col3.metric("Win Prob", f"{prob:.1%}")
                    col4.metric("Edge", f"{edge:+.1%}")
                    
                    if edge > 0.07:
                        st.error(f"☢️ HIGH CONFIDENCE: Take the OVER {line}")
                    else:
                        st.success(f"✅ TRUSTED: Over {line} has value")
                    st.divider()
        except:
            continue

    if not found_play:
        st.info("Scanner active. No high-value 'Over' plays detected yet. Check back 1 hour before tip-off.")

except Exception as e:
    st.error("Connection Error. Ensure your API key is active for NBA markets.")
