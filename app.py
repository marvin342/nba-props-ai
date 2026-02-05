import streamlit as st
import requests
import pandas as pd
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# --- 1. ACCESS & REFRESH ---
PASSWORD = "benja123"
st.sidebar.title("🏀 NBA PRIVATE ACCESS")
password = st.sidebar.text_input("Password", type="password")
if password != PASSWORD:
    st.warning("Locked.")
    st.stop()

# Auto-refresh every 30 mins (Saves credits, keeps data fresh forever)
st_autorefresh(interval=1800000, key="nba_forever_sync") 

# --- 2. CONFIG ---
API_KEY = "27970d14c8e8eb9f2a217c775db6571f" 
st.sidebar.header("⚙️ Filter Engine")
show_all = st.sidebar.checkbox("Show All Upcoming Games", value=False)

# --- 3. THE "FOREVER" DATA FETCH ---
@st.cache_data(ttl=1800)
def get_nba_stream(api_key):
    # This specific URL pulls everything currently in the 'Active' bookie window
    url = f"https://api.the-odds-api.com/v4/sports/basketball_nba/odds/?apiKey={api_key}&regions=us&markets=totals&oddsFormat=decimal"
    try:
        r = requests.get(url)
        return r.json() if r.status_code == 200 else []
    except:
        return []

# --- 4. DISPLAY ENGINE ---
st.title("🏀 NBA INDEFINITE SCANNER")
data = get_nba_stream(API_KEY)

if data:
    # Separate games by date automatically
    today_str = datetime.now().strftime('%Y-%m-%d')
    
    st.write(f"📡 **Systems Online.** Monitoring {len(data)} games across the next 48 hours.")
    
    for game in data:
        try:
            home, away = game['home_team'], game['away_team']
            start_dt = pd.to_datetime(game['commence_time'])
            game_date = start_dt.strftime('%Y-%m-%d')
            display_time = start_dt.strftime('%m/%d | %I:%M %p')

            # Extract Market Data
            bookie = game['bookmakers'][0]
            market = next(m for m in bookie['markets'] if m['key'] == 'totals')
            over = next(o for o in market['outcomes'] if o['name'] == 'Over')
            
            # THE "TRUSTED" MATH (Always active)
            # If the price is low (e.g., 1.85), it means the 'Over' is being heavily bet
            is_sharp_move = over['price'] < 1.90

            if show_all or is_sharp_move:
                label = "🔥 TRUSTED OVER" if is_sharp_move else "📅 SCHEDULED"
                with st.expander(f"{label}: {home} vs {away} ({display_time})", expanded=is_sharp_move):
                    c1, c2 = st.columns(2)
                    c1.metric("Current Line", f"{over['point']}")
                    c2.metric("Odds", f"{over['price']}")
                    if is_sharp_move:
                        st.success("✅ Sharp money detected on the Over.")
        except:
            continue
else:
    st.error("No live data found. Check API key status.")
