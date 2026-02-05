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
    st.warning("Locked. Enter password to view NBA data.")
    st.stop()

# Auto-refresh every 20 mins to stay under the 500-request monthly limit
st_autorefresh(interval=1200000, key="nba_master_sync") 

# --- 2. CONFIG ---
st.set_page_config(page_title="NBA MASTER COMMAND", layout="wide", page_icon="🏀")
API_KEY = "27970d14c8e8eb9f2a217c775db6571f" 

# --- 3. DATA FETCHING ---
@st.cache_data(ttl=1200)
def get_nba_data(api_key):
    # This pulls ALL upcoming/live games (Today + Next 7 days)
    url = f"https://api.the-odds-api.com/v4/sports/basketball_nba/odds/?apiKey={api_key}&regions=us&markets=totals&oddsFormat=decimal"
    try:
        r = requests.get(url)
        if r.status_code == 200:
            return r.json(), r.headers.get('x-requests-remaining', 'N/A')
        return None, f"Error {r.status_code}"
    except Exception as e:
        return None, str(e)

@st.cache_data(ttl=1200)
def get_full_props(api_key, event_id):
    # Fetches Points, Rebounds, Assists (Over/Under)
    markets = "player_points,player_rebounds,player_assists"
    url = f"https://api.the-odds-api.com/v4/sports/basketball_nba/events/{event_id}/odds?apiKey={api_key}&regions=us&markets={markets}&oddsFormat=decimal"
    try:
        r = requests.get(url)
        return r.json() if r.status_code == 200 else None
    except:
        return None

# --- 4. MAIN INTERFACE ---
st.title("🏀 NBA MASTER COMMAND CENTER")
st.markdown(f"**Scanner Active:** {pd.Timestamp.now().strftime('%B %d, %Y')}")

nba_data, credits_left = get_nba_data(API_KEY)
st.sidebar.metric("API Credits Left", credits_left)

if nba_data:
    # Sort games by time (Soonest first)
    nba_data = sorted(nba_data, key=lambda x: x['commence_time'])
    st.write(f"📡 Found {len(nba_data)} games on the schedule.")

    for game in nba_data:
        home, away = game['home_team'], game['away_team']
        event_id = game['id']
        commence_dt = pd.to_datetime(game['commence_time'])
        display_time = commence_dt.strftime('%m/%d | %I:%M %p')
        
        try:
            # --- GAME TOTALS LOGIC ---
            bookie = game['bookmakers'][0]
            market = next(m for m in bookie['markets'] if m['key'] == 'totals')
            over_out = next(o for o in market['outcomes'] if o['name'] == 'Over')
            under_out = next(o for o in market['outcomes'] if o['name'] == 'Under')
            
            line = over_out['point']
            o_price, u_price = over_out['price'], under_out['price']
            
            # --- TRUSTED LOGIC ---
            # Flagging high confidence for Over or Under
            is_over = line > 232 or o_price < 1.85
            is_under = line < 218 or u_price < 1.85
            
            status_icon = "🔥" if (is_over or is_under) else "📅"
            header = f"{status_icon} {away} @ {home} ({display_time})"
            
            with st.expander(header, expanded=is_over or is_under):
                c1, c2, c3 = st.columns(3)
                c1.metric("Game Line", f"{line}")
                c2.metric("Over Odds", f"{o_price}", delta="TRUSTED OVER" if is_over else None)
                c3.metric("Under Odds", f"{u_price}", delta="TRUSTED UNDER" if is_under else None, delta_color="inverse")
                
                # --- PLAYER PROPS ---
                st.markdown("---")
                if st.button(f"Scan Player Props: {away} @ {home}", key=f"btn_{event_id}"):
                    props = get_full_props(API_KEY, event_id)
                    if props and 'bookmakers' in props:
                        for b in props['bookmakers']:
                            for mkt in b['markets']:
                                m_label = mkt['key'].replace('player_', '').replace('_', ' ').title()
                                st.write(f"**📍 Target: {m_label}**")
                                for out in mkt['outcomes']:
                                    icon = "🟢" if out['name'] == 'Over' else "🔴"
                                    st.write(f"{icon} {out['description']}: {out['name']} {out['point']} @ {out['price']}")
                    else:
                        st.info("No player props available for this game yet (Check 2h before tip).")
        except:
            continue
else:
    st.error("Failed to connect to NBA feed. Check your API key or usage limit.")
