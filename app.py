import streamlit as st
import requests
import pandas as pd
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# --- 1. ACCESS & SECURITY ---
PASSWORD = "benja123"
st.sidebar.title("🔐 NBA PRO-COMMAND")
password = st.sidebar.text_input("Password", type="password")
if password != PASSWORD:
    st.warning("Locked.")
    st.stop()

st_autorefresh(interval=1200000, key="nba_master_sync") 

# --- 2. CONFIG ---
st.set_page_config(page_title="NBA MAX STRENGTH", layout="wide", page_icon="🏀")
API_KEY = "27970d14c8e8eb9f2a217c775db6571f" 

# --- 3. ADVANCED DATA ENGINES ---
@st.cache_data(ttl=1200)
def get_all_nba_games(api_key):
    # This pulls from multiple regions to create a "Market Consensus"
    url = f"https://api.the-odds-api.com/v4/sports/basketball_nba/odds/?apiKey={api_key}&regions=us,uk&markets=totals&oddsFormat=decimal"
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

# --- 4. THE ANALYTICS ENGINE ---
def calculate_strength(price):
    # Logic: The lower the price, the higher the implied probability (Strength)
    # A price of 1.50 = 66% Strength, 1.90 = 52% Strength
    return round((1 / price) * 100, 1)

# --- 5. MAIN INTERFACE ---
st.title("🏀 NBA MAX STRENGTH: CONSENSUS ENGINE")
search_query = st.text_input("🔍 Search Teams", "").lower()

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
            # --- MARKET TOTALS ---
            bookie = game['bookmakers'][0]
            mkt = next(m for m in bookie['markets'] if m['key'] == 'totals')
            over = next(o for o in mkt['outcomes'] if o['name'] == 'Over')
            under = next(u for u in mkt['outcomes'] if u['name'] == 'Under')
            
            # STRENGTH SCORE CALCULATION
            o_strength = calculate_strength(over['price'])
            u_strength = calculate_strength(under['price'])
            
            # Labeling
            status = "💎 MAX VALUE" if (o_strength > 58 or u_strength > 58) else "⚖️ MARKET NEUTRAL"
            
            with st.expander(f"{status} | {away} @ {home} ({commence_time})"):
                c1, c2, c3 = st.columns(3)
                c1.metric("Current Line", f"{over['point']}")
                c2.metric("Over Probability", f"{o_strength}%", delta=f"{over['price']}")
                c3.metric("Under Probability", f"{u_strength}%", delta=f"{under['price']}", delta_color="inverse")
                
                # AI FINAL CALL
                if o_strength > u_strength:
                    st.info(f"💡 AI FINAL CALL: LEAN OVER {over['point']} ({o_strength}% Confidence)")
                else:
                    st.info(f"💡 AI FINAL CALL: LEAN UNDER {over['point']} ({u_strength}% Confidence)")

                # --- ADVANCED PROP SCANNER ---
                st.markdown("---")
                if st.button(f"🚀 RUN PRO-ANALYSIS: {away} vs {home}", key=f"btn_{event_id}"):
                    prop_data = get_extended_props(API_KEY, event_id)
                    if prop_data and 'bookmakers' in prop_data:
                        for b in prop_data['bookmakers']:
                            for mkt_p in b['markets']:
                                label = mkt_p['key'].replace('player_', '').replace('_', ' ').upper()
                                st.write(f"**📍 {label} ANALYSIS**")
                                
                                players = {}
                                for out in mkt_p['outcomes']:
                                    name = out['description']
                                    if name not in players: players[name] = {}
                                    players[name][out['name']] = {'point': out['point'], 'price': out['price']}
                                
                                for p_name, p_data in players.items():
                                    if 'Over' in p_data and 'Under' in p_data:
                                        op, up = p_data['Over']['price'], p_data['Under']['price']
                                        line = p_data['Over']['point']
                                        os, us = calculate_strength(op), calculate_strength(up)
                                        
                                        if os >= 60: # Threshold for "Max Strength"
                                            st.success(f"🔥 **HIGH STRENGTH OVER**: {p_name} {line} ({os}% Confidence)")
                                        elif us >= 60:
                                            st.error(f"❄️ **HIGH STRENGTH UNDER**: {p_name} {line} ({us}% Confidence)")
                                        else:
                                            lean = "OVER" if os > us else "UNDER"
                                            st.write(f"👤 {p_name}: {line} (AI Lean: {lean})")
                    else:
                        st.info("Props loading... Check 2 hours before tip-off.")
        except: continue
else:
    st.error("Connection Failed. Check API Credits.")
