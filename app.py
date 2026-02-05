import streamlit as st
import requests
import pandas as pd
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# --- 1. ACCESS & SECURITY ---
PASSWORD = "benja123"
st.sidebar.title("🚀 NBA OVER-SPECIALIST")
password = st.sidebar.text_input("Password", type="password")
if password != PASSWORD:
    st.warning("Locked.")
    st.stop()

st_autorefresh(interval=1200000, key="nba_master_sync") 

# --- 2. CONFIG ---
st.set_page_config(page_title="NBA OVER SPECIALIST", layout="wide", page_icon="🔥")
API_KEY = "27970d14c8e8eb9f2a217c775db6571f" 

# --- 3. THE "SHOOTOUT" ENGINE ---
def get_over_confidence(o_price, u_price):
    # Focuses purely on the likelihood of the OVER
    implied_o = 1 / o_price
    implied_u = 1 / u_price
    total = implied_o + implied_u
    over_prob = implied_o / total
    return round(over_prob * 100, 2)

@st.cache_data(ttl=1200)
def get_data(api_key, event_id=None):
    if event_id:
        url = f"https://api.the-odds-api.com/v4/sports/basketball_nba/events/{event_id}/odds?apiKey={api_key}&regions=us&markets=player_points,player_rebounds,player_assists&oddsFormat=decimal"
    else:
        url = f"https://api.the-odds-api.com/v4/sports/basketball_nba/odds/?apiKey={api_key}&regions=us&markets=totals&oddsFormat=decimal"
    try:
        r = requests.get(url)
        return r.json()
    except: return None

# --- 4. INTERFACE ---
st.title("🏀 OVER-SPECIALIST: HIGH-SCORING SIGNALS")
search_query = st.text_input("🔍 Search Teams", "").lower()

nba_data = get_data(API_KEY)

if nba_data:
    processed_games = []
    for g in nba_data:
        try:
            mkt = next(m for m in g['bookmakers'][0]['markets'] if m['key'] == 'totals')
            o, u = mkt['outcomes'][0], mkt['outcomes'][1]
            o_conf = get_over_confidence(o['price'], u['price'])
            processed_games.append({**g, 'o_conf': o_conf, 'line': o['point']})
        except: continue
    
    # Sort so the highest "Over" probabilities are at the top
    processed_games = sorted(processed_games, key=lambda x: x['o_conf'], reverse=True)
    filtered_data = [g for g in processed_games if search_query in g['home_team'].lower() or search_query in g['away_team'].lower()]

    for game in filtered_data:
        home, away = game['home_team'], game['away_team']
        event_id, o_conf = game['id'], game['o_conf']
        
        # ELITE OVER SIGNAL: High confidence + High scoring matchup
        is_shootout = o_conf > 52.5
        status = "🔥 MAX STRENGTH OVER" if is_shootout else "⚖️ NEUTRAL OVER"
        
        with st.expander(f"{status} | {away} @ {home} (Line: {game['line']})", expanded=is_shootout):
            c1, c2 = st.columns(2)
            c1.metric("Over Confidence", f"{o_conf}%")
            c2.success(f"**Strategy:** {'STAKE THE OVER' if is_shootout else 'Check Line Value'}")
            
            # --- PLAYER OVER-PROP SCANNER ---
            if st.button(f"🚀 FIND BEST PLAYER OVERS: {away} vs {home}", key=f"btn_{event_id}"):
                prop_data = get_data(API_KEY, event_id=event_id)
                if prop_data:
                    over_props = []
                    for b in prop_data['bookmakers']:
                        for m in b['markets']:
                            players = {}
                            for out in m['outcomes']:
                                n = out['description']
                                if n not in players: players[n] = {}
                                players[n][out['name']] = {'point': out['point'], 'price': out['price']}
                            
                            for p_name, p_data in players.items():
                                if 'Over' in p_data:
                                    p_o_conf = get_over_confidence(p_data['Over']['price'], p_data['Under']['price'])
                                    over_props.append({'name': p_name, 'type': m['key'], 'line': p_data['Over']['point'], 'conf': p_o_conf})
                    
                    # Focus ONLY on Overs with > 53% Confidence
                    best_overs = [p for p in over_props if p['conf'] > 53]
                    if best_overs:
                        for p in sorted(best_overs, key=lambda x: x['conf'], reverse=True):
                            st.success(f"✅ **HIGH-STRENGTH OVER:** {p['name']} {p['line']} {p['type'].replace('player_', '').title()} ({p['conf']}% Confidence)")
                    else:
                        st.info("No 'High Strength' player overs found yet. Market is efficient right now.")
                else: st.info("Props loading... Check closer to tip-off.")
else: st.error("Sync Failed.")
