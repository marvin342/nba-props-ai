import streamlit as st
import requests
import pandas as pd
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# --- 1. ACCESS & SECURITY ---
PASSWORD = "benja123"
st.sidebar.title("🔐 NBA PRIVATE ACCESS")
password = st.sidebar.text_input("Password", type="password")
if password != PASSWORD:
    st.warning("Locked.")
    st.stop()

st_autorefresh(interval=1200000, key="nba_master_sync") 

# --- 2. CONFIG & STYLING ---
st.set_page_config(page_title="NBA ELITE COMMAND", layout="wide", page_icon="🏀")
API_KEY = "27970d14c8e8eb9f2a217c775db6571f" 

# Custom CSS for a clean "Dark Mode" betting look
st.markdown("""
    <style>
    .stMetric { background-color: #1e1e1e; padding: 10px; border-radius: 10px; border: 1px solid #333; }
    .stExpander { border: 1px solid #444 !important; border-radius: 10px !important; }
    </style>
""", unsafe_allow_html=True)

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

# --- 4. MAIN INTERFACE ---
st.title("🏀 NBA ELITE COMMAND CENTER")
col_search, col_stats = st.columns([2, 1])
with col_search:
    search_query = st.text_input("🔍 Search Teams", placeholder="e.g. Lakers...").lower()

nba_data, credits_left = get_all_nba_games(API_KEY)
with col_stats:
    st.metric("📡 Credits Left", credits_left)

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
            
            line, o_p, u_p = over['point'], over['price'], under['price']
            
            # HIGH STRENGTH LOGIC
            is_trusted_over = line > 233 or o_p < 1.82
            is_trusted_under = line < 217 or u_p < 1.82
            
            # AI LEAN LOGIC (For games without trusted tags)
            lean_text = "OVER" if o_p < u_p else "UNDER"
            lean_color = "green" if o_p < u_p else "red"

            status_label = "💣 TRUSTED" if (is_trusted_over or is_trusted_under) else f"💡 AI LEAN: {lean_text}"
            
            with st.expander(f"{status_label} | {away} @ {home} ({commence_time})"):
                c1, c2, c3 = st.columns(3)
                c1.metric("Game Line", f"{line}")
                c2.metric("Over", f"{o_p}", delta="HIGH VALUE" if is_trusted_over else None)
                c3.metric("Under", f"{u_p}", delta="HIGH VALUE" if is_trusted_under else None, delta_color="inverse")
                
                # --- MAX STRENGTH PLAYER PROPS ---
                st.markdown("---")
                if st.button(f"🚀 ANALYZE ALL PROPS: {away} vs {home}", key=f"btn_{event_id}"):
                    prop_data = get_extended_props(API_KEY, event_id)
                    if prop_data and 'bookmakers' in prop_data:
                        for b in prop_data['bookmakers']:
                            for prop_mkt in b['markets']:
                                label = prop_mkt['key'].replace('player_', '').replace('_', ' ').title()
                                st.write(f"**📍 {label} Targets**")
                                
                                players = {}
                                for out in prop_mkt['outcomes']:
                                    name = out['description']
                                    if name not in players: players[name] = {}
                                    players[name][out['name']] = {'point': out['point'], 'price': out['price']}
                                
                                for p_name, p_data in players.items():
                                    if 'Over' in p_data and 'Under' in p_data:
                                        o_p_val, u_p_val = p_data['Over']['price'], p_data['Under']['price']
                                        p_line = p_data['Over']['point']
                                        
                                        # STRONG VALUE FLAG
                                        if o_p_val <= 1.75:
                                            st.success(f"🔥 **STAKE OVER**: {p_name} {p_line} (@{o_p_val})")
                                        elif u_p_val <= 1.75:
                                            st.error(f"❄️ **STAKE UNDER**: {p_name} {p_line} (@{u_p_val})")
                                        else:
                                            # AI LEAN FOR PROPS
                                            p_lean = "OVER" if o_p_val < u_p_val else "UNDER"
                                            st.write(f"👤 {p_name}: {p_line} (AI Lean: {p_lean})")
                    else:
                        st.info("Props release closer to tip-off (2-4 hours).")
        except: continue
else:
    st.error("Connection Failed. Check API Credits.")
