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

# Heartbeat: Updates every 20 mins to keep your schedule fresh and save credits
st_autorefresh(interval=1200000, key="nba_master_sync") 

# --- 2. CONFIG ---
st.set_page_config(page_title="NBA MAX STRENGTH", layout="wide", page_icon="🏀")
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
    # Pulls Points, Rebounds, and Assists
    url = f"https://api.the-odds-api.com/v4/sports/basketball_nba/events/{event_id}/odds?apiKey={api_key}&regions=us&markets=player_points,player_rebounds,player_assists&oddsFormat=decimal"
    try:
        r = requests.get(url)
        return r.json()
    except:
        return None

# --- 4. DISPLAY ---
st.title("🏀 NBA MAX STRENGTH: BETTING COMMAND")
search_query = st.text_input("🔍 Search Team or Matchup", "").lower()

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
            # --- GAME TOTALS ANALYSIS ---
            bookie = game['bookmakers'][0]
            mkt = next(m for m in bookie['markets'] if m['key'] == 'totals')
            over = next(o for o in mkt['outcomes'] if o['name'] == 'Over')
            under = next(u for u in mkt['outcomes'] if u['name'] == 'Under')
            
            # STRENGTH LOGIC: We flag extreme outliers
            is_trusted_over = (over['point'] > 234) or (over['price'] < 1.80)
            is_trusted_under = (over['point'] < 216) or (under['price'] < 1.80)
            
            status_icon = "💣" if (is_trusted_over or is_trusted_under) else "📅"
            with st.expander(f"{status_icon} {away} @ {home} ({commence_time})", expanded=is_trusted_over or is_trusted_under):
                c1, c2, c3 = st.columns(3)
                c1.metric("Current Line", f"{over['point']}")
                c2.metric("Over Price", f"{over['price']}", delta="MAX STRENGTH OVER" if is_trusted_over else None)
                c3.metric("Under Price", f"{under['price']}", delta="MAX STRENGTH UNDER" if is_trusted_under else None, delta_color="inverse")
                
                # --- MAX STRENGTH PLAYER PROPS ---
                st.markdown("---")
                if st.button(f"🚀 RUN MAX ANALYSIS: {away} vs {home}", key=f"btn_{event_id}"):
                    prop_data = get_extended_props(API_KEY, event_id)
                    if prop_data and 'bookmakers' in prop_data:
                        st.subheader("🎯 High-Confidence Prop Targets")
                        for b in prop_data['bookmakers']:
                            for mkt in b['markets']:
                                label = mkt['key'].replace('player_', '').replace('_', ' ').upper()
                                
                                # Process outcomes
                                players = {}
                                for out in mkt['outcomes']:
                                    name = out['description']
                                    if name not in players: players[name] = {}
                                    players[name][out['name']] = {'point': out['point'], 'price': out['price']}
                                
                                for p_name, p_data in players.items():
                                    if 'Over' in p_data and 'Under' in p_data:
                                        o_p, u_p = p_data['Over']['price'], p_data['Under']['price']
                                        line = p_data['Over']['point']
                                        
                                        # MAX STRENGTH THRESHOLD: 1.72 or lower indicates massive bookmaker liability
                                        if o_p <= 1.72:
                                            st.success(f"🔥 **STAKE OVER**: {p_name} {label} ({line}) - Odds: {o_p}")
                                        elif u_p <= 1.72:
                                            st.error(f"❄️ **STAKE UNDER**: {p_name} {label} ({line}) - Odds: {u_p}")
                    else:
                        st.info("Market not yet mature. Check closer to tip-off for max strength signals.")
        except:
            continue
else:
    st.error("Connection Failed. Check API Credits.")
