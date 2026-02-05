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

st_autorefresh(interval=1200000, key="nba_master_sync") 

# --- 2. CONFIG ---
st.set_page_config(page_title="NBA MASTER COMMAND", layout="wide", page_icon="🏀")
API_KEY = "27970d14c8e8eb9f2a217c775db6571f" 

# --- 3. DATA ENGINES ---
@st.cache_data(ttl=1200)
def get_all_nba_games(api_key):
    url = f"https://api.the-odds-api.com/v4/sports/basketball_nba/odds/?apiKey={api_key}&regions=us&markets=totals&oddsFormat=decimal"
    try:
        r = requests.get(url)
        return r.json(), r.headers.get('x-requests-remaining', 'N/A')
    except:
        return None, "Error"

@st.cache_data(ttl=1200)
def get_extended_props(api_key, event_id):
    url = f"https://api.the-odds-api.com/v4/sports/basketball_nba/events/{event_id}/odds?apiKey={api_key}&regions=us&markets=player_points,player_rebounds,player_assists&oddsFormat=decimal"
    try:
        r = requests.get(url)
        return r.json()
    except:
        return None

# --- 4. DISPLAY ---
st.title("🏀 NBA MASTER COMMAND: AI ADVISOR")
search_query = st.text_input("🔍 Search Team", "").lower()

nba_data, credits_left = get_all_nba_games(API_KEY)
st.sidebar.metric("API Credits Left", credits_left)

if nba_data:
    nba_data = sorted(nba_data, key=lambda x: x['commence_time'])
    filtered_data = [g for g in nba_data if search_query in g['home_team'].lower() or search_query in g['away_team'].lower()]

    for game in filtered_data:
        home, away = game['home_team'], game['away_team']
        event_id = game['id']
        commence_time = pd.to_datetime(game['commence_time']).strftime('%m/%d | %I:%M %p')
        
        try:
            # --- GAME TOTALS ---
            bookie = game['bookmakers'][0]
            mkt = next(m for m in bookie['markets'] if m['key'] == 'totals')
            over = next(o for o in mkt['outcomes'] if o['name'] == 'Over')
            under = next(u for u in mkt['outcomes'] if u['name'] == 'Under')
            
            is_trusted_over = over['point'] > 232 or over['price'] < 1.85
            is_trusted_under = over['point'] < 218 or under['price'] < 1.85
            
            icon = "🔥" if (is_trusted_over or is_trusted_under) else "📅"
            with st.expander(f"{icon} {away} @ {home} ({commence_time})"):
                c1, c2, c3 = st.columns(3)
                c1.metric("Line", f"{over['point']}")
                c2.metric("Over", f"{over['price']}", delta="TRUSTED" if is_trusted_over else None)
                c3.metric("Under", f"{under['price']}", delta="TRUSTED" if is_trusted_under else None, delta_color="inverse")
                
                # --- PLAYER PROPS WITH AI ADVICE ---
                st.markdown("---")
                if st.button(f"Analyze Props: {away} vs {home}", key=f"btn_{event_id}"):
                    prop_data = get_extended_props(API_KEY, event_id)
                    if prop_data and 'bookmakers' in prop_data:
                        for b in prop_data['bookmakers']:
                            for mkt in b['markets']:
                                label = mkt['key'].replace('player_', '').replace('_', ' ').title()
                                st.write(f"**📍 {label}**")
                                
                                # Group outcomes by player to compare Over vs Under
                                players = {}
                                for out in mkt['outcomes']:
                                    name = out['description']
                                    if name not in players: players[name] = {}
                                    players[name][out['name']] = {'point': out['point'], 'price': out['price']}
                                
                                for p_name, p_data in players.items():
                                    if 'Over' in p_data and 'Under' in p_data:
                                        o_p, u_p = p_data['Over']['price'], p_data['Under']['price']
                                        line = p_data['Over']['point']
                                        
                                        # AI ADVICE LOGIC: If one side is significantly favored by the bookie
                                        if o_p < 1.80:
                                            st.success(f"🌟 **{p_name}**: TAKE THE OVER {line} (High Confidence)")
                                        elif u_p < 1.80:
                                            st.warning(f"📉 **{p_name}**: TAKE THE UNDER {line} (Sharp Move)")
                                        else:
                                            st.write(f"👤 {p_name}: Over/Under {line} (No clear advantage)")
                    else:
                        st.info("Props release 2-4 hours before tip-off.")
        except:
            continue
else:
    st.error("Connection Failed. Check API Credits.")
