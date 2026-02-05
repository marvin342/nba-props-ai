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

# Auto-refresh every 20 mins to conserve credits
st_autorefresh(interval=1200000, key="nba_sync") 

# --- 2. CONFIG ---
st.set_page_config(page_title="NBA COMMAND CENTER", layout="wide", page_icon="🏀")
NEW_API_KEY = "27970d14c8e8eb9f2a217c775db6571f" 

# --- 3. DATA FETCHING (GAME TOTALS + PROPS) ---
@st.cache_data(ttl=1200)
def get_nba_data(api_key):
    # This fetches Game Totals for ALL upcoming/live games
    url = f"https://api.the-odds-api.com/v4/sports/basketball_nba/odds/?apiKey={api_key}&regions=us&markets=totals&oddsFormat=decimal"
    try:
        r = requests.get(url)
        if r.status_code == 200:
            return r.json(), r.headers.get('x-requests-remaining', 'N/A')
        return None, "Error"
    except:
        return None, "Offline"

@st.cache_data(ttl=1200)
def get_player_props(api_key, event_id):
    # Fetches Player Points for a specific game
    url = f"https://api.the-odds-api.com/v4/sports/basketball_nba/events/{event_id}/odds?apiKey={api_key}&regions=us&markets=player_points&oddsFormat=decimal"
    try:
        r = requests.get(url)
        return r.json() if r.status_code == 200 else None
    except:
        return None

# --- 4. MAIN INTERFACE ---
st.title("🏀 NBA LIVE COMMAND: GAME & PLAYER PROPS")
st.markdown(f"**Current Date:** {pd.Timestamp.now().strftime('%B %d, %Y')}")

nba_data, credits_left = get_nba_totals(NEW_API_KEY)
st.sidebar.metric("API Credits Left", credits_left)

if nba_data:
    st.write(f"🔍 **Scanner Status:** Connected. Monitoring {len(nba_data)} Upcoming/Live Games.")
    
    for game in nba_data:
        home, away = game['home_team'], game['away_team']
        event_id = game['id']
        commence_time = pd.to_datetime(game['commence_time']).strftime('%m/%d %H:%M')
        
        # --- SECTION: GAME TOTALS (Your Original Logic) ---
        try:
            bookie = game['bookmakers'][0]
            market = next(m for m in bookie['markets'] if m['key'] == 'totals')
            over = next(o for o in market['outcomes'] if o['name'] == 'Over')
            line, price = over['point'], over['price']
            
            # Trusted Highlight
            is_trusted = line > 230 or price < 1.90
            
            with st.expander(f"{'🔥 TRUSTED: ' if is_trusted else '📅 '} {home} vs {away} ({commence_time})", expanded=is_trusted):
                col1, col2 = st.columns(2)
                col1.metric("Game Total", f"{line}")
                col2.metric("Over Odds", f"{price}")
                
                if is_trusted:
                    st.success(f"**AI TIP:** High scoring potential. Watch the OVER {line}")

                # --- NEW SECTION: PLAYER PROPS ---
                st.markdown("---")
                st.subheader("🎯 Player Prop Targets")
                
                if st.button(f"Scan Props for {away}@{home}", key=event_id):
                    prop_data = get_player_props(NEW_API_KEY, event_id)
                    if prop_data and 'bookmakers' in prop_data:
                        found_prop = False
                        # Look through bookies for player_points
                        for b in prop_data['bookmakers']:
                            p_market = next((m for m in b['markets'] if m['key'] == 'player_points'), None)
                            if p_market:
                                found_prop = True
                                # Filter to show only high-confidence player lines
                                for outcome in p_market['outcomes']:
                                    if outcome['name'] == 'Over':
                                        st.write(f"👤 **{outcome['description']}**: Over {outcome['point']} @ {outcome['price']}")
                        if not found_prop:
                            st.info("No player props released yet for this game.")
                    else:
                        st.info("Props pending bookmaker release.")
        except:
            continue
else:
    st.error("API Connection Failed. Verify key activity.")
