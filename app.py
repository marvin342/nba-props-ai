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

# --- 3. DATA FETCHING ---
@st.cache_data(ttl=1200)
def get_nba_data(api_key):
    # Fetches Game Totals for all live/upcoming games
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
    # Fetches Points, Rebounds, and Assists for a specific game
    # Markets: player_points, player_rebounds, player_assists
    markets = "player_points,player_rebounds,player_assists"
    url = f"https://api.the-odds-api.com/v4/sports/basketball_nba/events/{event_id}/odds?apiKey={api_key}&regions=us&markets={markets}&oddsFormat=decimal"
    try:
        r = requests.get(url)
        return r.json() if r.status_code == 200 else None
    except:
        return None

# --- 4. MAIN INTERFACE ---
st.title("🏀 NBA LIVE COMMAND: GAME & PLAYER PROPS")
st.markdown(f"**Current Date:** {pd.Timestamp.now().strftime('%B %d, %Y')}")

nba_data, credits_left = get_nba_data(NEW_API_KEY)
st.sidebar.metric("API Credits Left", credits_left)

if nba_data:
    st.write(f"🔍 **Scanner Status:** Monitoring {len(nba_data)} games (Today & Upcoming).")
    
    for game in nba_data:
        home, away = game['home_team'], game['away_team']
        event_id = game['id']
        commence_time = pd.to_datetime(game['commence_time']).strftime('%m/%d | %I:%M %p')
        
        try:
            # --- EXTRACT GAME TOTALS ---
            bookie = game['bookmakers'][0]
            market = next(m for m in bookie['markets'] if m['key'] == 'totals')
            over = next(o for o in market['outcomes'] if o['name'] == 'Over')
            line, price = over['point'], over['price']
            
            # Trusted Logic (Overs > 230 or heavy juice < 1.90)
            is_trusted = line > 230 or price < 1.90
            
            with st.expander(f"{'🔥 TRUSTED: ' if is_trusted else '📅 '} {away} @ {home} ({commence_time})", expanded=is_trusted):
                col1, col2 = st.columns(2)
                col1.metric("Game Total", f"{line}")
                col2.metric("Over Odds", f"{price}")
                
                if is_trusted:
                    st.success(f"**AI CONFIDENCE:** High scoring matchup. Over {line} recommended.")

                st.markdown("---")
                st.subheader("🎯 Elite Player Prop Targets")
                
                # Dynamic Button for Props
                if st.button(f"Scan Props: {away} vs {home}", key=f"btn_{event_id}"):
                    with st.spinner("Fetching player markets..."):
                        prop_data = get_player_props(NEW_API_KEY, event_id)
                        
                        if prop_data and 'bookmakers' in prop_data:
                            found_any_prop = False
                            for b in prop_data['bookmakers']:
                                for mkt in b['markets']:
                                    # Translate market keys to readable headers
                                    mkt_name = mkt['key'].replace('player_', '').capitalize()
                                    st.write(f"**📍 Market: {mkt_name}**")
                                    
                                    # Show the first 5 outcomes to keep it clean
                                    for outcome in mkt['outcomes'][:8]:
                                        if outcome['name'] == 'Over':
                                            found_any_prop = True
                                            st.write(f"👤 {outcome['description']}: Over {outcome['point']} @ {outcome['price']}")
                            
                            if not found_any_prop:
                                st.warning("No specific player props found yet for this game.")
                        else:
                            st.info("Bookmakers haven't released props for this game yet. Check 2 hours before tip-off.")
        except Exception as e:
            continue
else:
    st.error("Connection Failed. Verify if your API key is active.")
