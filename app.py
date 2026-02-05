import streamlit as st
import requests
import pandas as pd
from streamlit_autorefresh import st_autorefresh

# --- 1. PRIVATE ACCESS ---
PASSWORD = "benja123"
st.sidebar.title("🏀 NBA PRIVATE ACCESS")
password = st.sidebar.text_input("Password", type="password")

if password != PASSWORD:
    st.warning("Locked. Enter password to view NBA data.")
    st.stop()

# Auto-refresh every 20 mins to conserve your new 500 credits
st_autorefresh(interval=1200000, key="nba_sync") 

# --- 2. CONFIG ---
st.set_page_config(page_title="NBA TRUSTED OVERS", layout="wide", page_icon="🏀")
NEW_API_KEY = "27970d14c8e8eb9f2a217c775db6571f" 

# --- 3. CACHED DATA FETCHING (FUEL SAVER) ---
@st.cache_data(ttl=1200) # Freezes data for 20 mins so clicks don't waste credits
def get_nba_totals(api_key):
    url = f"https://api.the-odds-api.com/v4/sports/basketball_nba/odds/?apiKey={api_key}&regions=us&markets=totals&oddsFormat=decimal"
    try:
        r = requests.get(url)
        if r.status_code == 200:
            return r.json(), r.headers.get('x-requests-remaining', 'N/A')
        return None, "Error"
    except:
        return None, "Offline"

# --- 4. MAIN INTERFACE ---
st.title("🏀 NBA LIVE COMMAND: TRUSTED OVERS")
st.markdown(f"**Date:** {pd.Timestamp.now().strftime('%B %d, %Y')}")

nba_data, credits_left = get_nba_totals(NEW_API_KEY)
st.sidebar.metric("API Credits Left", credits_left)

if nba_data:
    st.write(f"🔍 **Scanner Status:** Connected. Monitoring {len(nba_data)} live markets.")
    found_play = False

    for game in nba_data:
        try:
            home, away = game['home_team'], game['away_team']
            bookie = game['bookmakers'][0] # Grabs FanDuel/DraftKings
            market = next(m for m in bookie['markets'] if m['key'] == 'totals')
            over = next(o for o in market['outcomes'] if o['name'] == 'Over')
            
            line = over['point']
            price = over['price']

            # --- TRUSTED LOGIC ---
            # Flagging high-value overs based on today's specific game lines
            # Example: 241.5 for Hawks/Jazz is very high, implying a massive shootout.
            if line > 230 or price < 1.90:
                found_play = True
                with st.expander(f"🔥 {home} vs {away}", expanded=True):
                    col1, col2 = st.columns(2)
                    col1.metric("Bookie Line", f"{line}")
                    col2.metric("Over Odds", f"{price}")
                    st.success(f"**TRUSTED ACTION:** Bet the OVER {line}")
        except:
            continue

    if not found_play:
        st.info("Scanner Active: No 'Extreme Value' overs detected yet. Markets update closer to tip-off.")
else:
    st.error("API Connection Failed. Your new key might not be fully activated yet (takes 5-10 mins).")
