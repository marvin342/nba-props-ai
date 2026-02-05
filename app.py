import streamlit as st
import requests
import pandas as pd
from scipy.stats import norm
from streamlit_autorefresh import st_autorefresh

# --- 1. ACCESS & REFRESH ---
PASSWORD = "benja123"
st.sidebar.title("🏀 NBA PRIVATE ACCESS")
password = st.sidebar.text_input("Password", type="password")
if password != PASSWORD:
    st.warning("Locked.")
    st.stop()

st_autorefresh(interval=300000, key="nba_sync") # 5 min refresh

# --- 2. THE-ODDS-API CONFIG ---
API_KEY = "2bbe95bafab32dd8fa0be8ae23608feb" 

# --- 3. QUOTA & STATUS ---
def get_status():
    r = requests.get(f"https://api.the-odds-api.com/v4/sports/basketball_nba/odds/?apiKey={API_KEY}&regions=us&markets=totals")
    if r.status_code != 200:
        return None, f"Error: {r.status_code}"
    data = r.json()
    remaining = r.headers.get('x-requests-remaining', 'N/A')
    return data, remaining

nba_data, credits = get_status()
st.sidebar.metric("API Credits Left", credits)

# --- 4. MAIN SCANNER ---
st.title("🏀 NBA LIVE: TRUSTED OVERS")

if nba_data is not None:
    st.write(f"🔍 Scanner active. Found **{len(nba_data)}** upcoming games.")
    
    found_play = False
    for game in nba_data:
        try:
            home, away = game['home_team'], game['away_team']
            
            # Look for the Totals market
            if not game.get('bookmakers'):
                continue
                
            bookie = game['bookmakers'][0]
            market = next((m for m in bookie['markets'] if m['key'] == 'totals'), None)
            
            if market:
                over = next(o for o in market['outcomes'] if o['name'] == 'Over')
                line, price = over['point'], over['price']
                
                # AI Logic: Highlight any Over with decent odds
                if price < 2.0: 
                    found_play = True
                    with st.expander(f"✅ LIVE LINE: {home} vs {away}", expanded=True):
                        st.success(f"**Market Total:** {line}")
                        st.info(f"AI Suggestion: Monitoring for Over value...")
        except:
            continue

    if not found_play:
        st.warning("Games found, but Bookmakers haven't released 'Over/Under' totals yet. Check back in 30-60 mins.")
else:
    st.error("Could not connect to NBA Odds. Check API key.")
