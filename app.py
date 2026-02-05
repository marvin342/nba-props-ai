import streamlit as st
import requests
import pandas as pd
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# --- 1. ACCESS & SECURITY ---
PASSWORD = "benja123"
st.sidebar.title("🦾 NBA THE CLOSER")
password = st.sidebar.text_input("Password", type="password")
if password != PASSWORD:
    st.warning("Locked.")
    st.stop()

st_autorefresh(interval=1200000, key="nba_master_sync") 

# --- 2. CONFIG ---
st.set_page_config(page_title="NBA THE CLOSER", layout="wide", page_icon="🏀")
API_KEY = "27970d14c8e8eb9f2a217c775db6571f" 

# --- 3. QUANT ENGINES ---
def calculate_no_vig(o_price, u_price):
    # Removes the vig to find the "Fair Value" win %
    implied_o = 1 / o_price
    implied_u = 1 / u_price
    fair_prob = implied_o / (implied_o + implied_u)
    return round(fair_prob * 100, 2)

@st.cache_data(ttl=1200)
def get_data(api_key, category="totals", event_id=None):
    if event_id:
        url = f"https://api.the-odds-api.com/v4/sports/basketball_nba/events/{event_id}/odds?apiKey={api_key}&regions=us&markets=player_points,player_rebounds,player_assists&oddsFormat=decimal"
    else:
        url = f"https://api.the-odds-api.com/v4/sports/basketball_nba/odds/?apiKey={api_key}&regions=us&markets={category}&oddsFormat=decimal"
    try:
        r = requests.get(url)
        return r.json()
    except: return None

# --- 4. MAIN INTERFACE ---
st.title("🏀 THE CLOSER: NBA BETTING SIGNALS")
search_query = st.text_input("🔍 Search Teams", "").lower()

nba_data = get_data(API_KEY)

if nba_data:
    filtered_data = [g for g in nba_data if search_query in g['home_team'].lower() or search_query in g['away_team'].lower()]

    for game in filtered_data:
        home, away = game['home_team'], game['away_team']
        event_id, commence_time = game['id'], pd.to_datetime(game['commence_time']).strftime('%m/%d | %I:%M %p')
        
        try:
            mkt = next(m for m in game['bookmakers'][0]['markets'] if m['key'] == 'totals')
            over, under = mkt['outcomes'][0], mkt['outcomes'][1]
            
            # --- FIND THE EDGE ---
            over_fair = calculate_no_vig(over['price'], under['price'])
            under_fair = 100 - over_fair
            
            # Determine the AI's preferred side
            if over_fair > 53.5:
                verdict, confidence, color = f"🔥 OVER {over['point']}", over_fair, "green"
            elif under_fair > 53.5:
                verdict, confidence, color = f"❄️ UNDER {under['point']}", under_fair, "red"
            else:
                verdict, confidence, color = f"⚖️ LEAN {'OVER' if over_fair > 50 else 'UNDER'} {over['point']}", max(over_fair, under_fair), "gray"

            with st.expander(f"{verdict} | {away} @ {home} ({commence_time})"):
                c1, c2, c3 = st.columns(3)
                c1.metric("Game Line", f"{over['point']}")
                c2.metric("AI Confidence", f"{confidence}%")
                c3.write(f"**Recommended Action:** {'High Stake' if confidence > 55 else 'Standard Unit'}")
                
                # --- PLAYER PROP "BEST OF" SCANNER ---
                if st.button(f"🚀 FIND TOP 3 PLAYER PROPS: {away} vs {home}", key=f"btn_{event_id}"):
                    prop_data = get_data(API_KEY, event_id=event_id)
                    if prop_data:
                        all_props = []
                        for b in prop_data['bookmakers']:
                            for m in b['markets']:
                                players = {}
                                for out in m['outcomes']:
                                    n = out['description']
                                    if n not in players: players[n] = {}
                                    players[n][out['name']] = {'point': out['point'], 'price': out['price']}
                                
                                for p_name, p_data in players.items():
                                    if 'Over' in p_data and 'Under' in p_data:
                                        prob = calculate_no_vig(p_data['Over']['price'], p_data['Under']['price'])
                                        side = "OVER" if prob > 50 else "UNDER"
                                        conf = prob if prob > 50 else 100 - prob
                                        all_props.append({'name': p_name, 'type': m['key'], 'line': p_data['Over']['point'], 'conf': conf, 'side': side})
                        
                        # Sort by confidence and show only the absolute best
                        top_props = sorted(all_props, key=lambda x: x['conf'], reverse=True)[:3]
                        for p in top_props:
                            if p['conf'] > 55:
                                st.success(f"✅ **BEST PROP:** {p['name']} {p['side']} {p['line']} ({p['conf']}% Confidence)")
                            else:
                                st.write(f"👤 {p['name']} {p['side']} {p['line']} (Lean: {p['conf']}%)")
                    else: st.info("Props release closer to tip-off.")
        except: continue
else: st.error("Sync Failed.")
