import streamlit as st
import requests
import pandas as pd
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# --- 1. ACCESS & SECURITY ---
PASSWORD = "benja123"
st.sidebar.title("🦾 NBA QUANT-ELITE")
password = st.sidebar.text_input("Password", type="password")
if password != PASSWORD:
    st.warning("Locked.")
    st.stop()

st_autorefresh(interval=1200000, key="nba_master_sync") 

# --- 2. CONFIG ---
st.set_page_config(page_title="NBA MAX STRENGTH", layout="wide", page_icon="🏀")
API_KEY = "27970d14c8e8eb9f2a217c775db6571f" 

# --- 3. QUANT ENGINES ---
def calculate_no_vig_fair_odds(o_price, u_price):
    # Mathematically removes the 'Juice' to find the True Probability
    implied_o = 1 / o_price
    implied_u = 1 / u_price
    total_implied = implied_o + implied_u
    fair_o_prob = implied_o / total_implied
    return round(fair_o_prob * 100, 1)

def kelly_criterion(fair_prob, odds):
    # Professional Bankroll Management Formula (Fractional Kelly 0.25)
    p = fair_prob / 100
    q = 1 - p
    b = odds - 1
    kelly_f = (b * p - q) / b
    # We use 1/4 Kelly to be safe and avoid big swings
    return max(0, round(kelly_f * 0.25 * 100, 2))

@st.cache_data(ttl=1200)
def get_all_nba_games(api_key):
    url = f"https://api.the-odds-api.com/v4/sports/basketball_nba/odds/?apiKey={api_key}&regions=us&markets=totals&oddsFormat=decimal"
    try:
        r = requests.get(url)
        return r.json(), r.headers.get('x-requests-remaining', 'N/A')
    except: return None, "Error"

@st.cache_data(ttl=1200)
def get_extended_props(api_key, event_id):
    url = f"https://api.the-odds-api.com/v4/sports/basketball_nba/events/{event_id}/odds?apiKey={api_key}&regions=us&markets=player_points,player_rebounds,player_assists&oddsFormat=decimal"
    try:
        r = requests.get(url)
        return r.json()
    except: return None

# --- 4. MAIN INTERFACE ---
st.title("🏀 NBA QUANT-ELITE: MAX STRENGTH ENGINE")
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
            bookie = game['bookmakers'][0]
            mkt = next(m for m in bookie['markets'] if m['key'] == 'totals')
            over = next(o for o in mkt['outcomes'] if o['name'] == 'Over')
            under = next(u for u in mkt['outcomes'] if u['name'] == 'Under')
            
            # --- QUANT CALCULATION ---
            fair_over_prob = calculate_no_vig_fair_odds(over['price'], under['price'])
            rec_stake = kelly_criterion(fair_over_prob, over['price']) if fair_over_prob > 52 else kelly_criterion(100-fair_over_prob, under['price'])
            
            # STRENGTH LABELS
            is_max = rec_stake > 2.5 # Anything suggesting over 2.5% of bankroll is a huge play
            status = "🧨 MAX QUANT STRENGTH" if is_max else "⚖️ CALCULATED LEAN"
            
            with st.expander(f"{status} | {away} @ {home} ({commence_time})", expanded=is_max):
                c1, c2, c3 = st.columns(3)
                c1.metric("Line", f"{over['point']}")
                c2.metric("True Win %", f"{fair_over_prob}%", help="No-Vig Probability")
                c3.metric("Rec. Stake", f"{rec_stake}%", help="Based on Kelly Criterion")

                # AI FINAL DIRECTIVE
                lean = "OVER" if fair_over_prob > 50 else "UNDER"
                st.info(f"🎯 **ELITE CALL:** TAKE THE {lean} {over['point']} | Strength: {rec_stake}%")

                # --- PRO-ANALYSIS ---
                st.markdown("---")
                if st.button(f"🚀 RUN QUANT PROP SCAN: {away} vs {home}", key=f"btn_{event_id}"):
                    prop_data = get_extended_props(API_KEY, event_id)
                    if prop_data and 'bookmakers' in prop_data:
                        for b in prop_data['bookmakers']:
                            for mkt_p in b['markets']:
                                label = mkt_p['key'].replace('player_', '').replace('_', ' ').upper()
                                st.write(f"**📍 {label} ANALYTICS**")
                                
                                players = {}
                                for out in mkt_p['outcomes']:
                                    n = out['description']
                                    if n not in players: players[n] = {}
                                    players[n][out['name']] = {'point': out['point'], 'price': out['price']}
                                
                                for p_name, p_data in players.items():
                                    if 'Over' in p_data and 'Under' in p_data:
                                        op, up = p_data['Over']['price'], p_data['Under']['price']
                                        line, fp = p_data['Over']['point'], calculate_no_vig_fair_odds(op, up)
                                        p_stake = kelly_criterion(fp if fp > 50 else 100-fp, op if fp > 50 else up)
                                        
                                        if p_stake >= 3.0: # Professional Grade Threshold
                                            st.success(f"🔥 **MAX STAKE**: {p_name} {line} ({'OVER' if fp > 50 else 'UNDER'}) - Stake: {p_stake}%")
                                        else:
                                            st.write(f"👤 {p_name}: {line} (Lean: {'OVER' if fp > 50 else 'UNDER'} | {p_stake}%)")
                    else: st.info("Props loading... Check closer to tip-off.")
        except: continue
else: st.error("Connection Failed. Check API Credits.")
