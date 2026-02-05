import streamlit as st
import requests
import pandas as pd
import numpy as np
from scipy.stats import norm, poisson
import math
from streamlit_autorefresh import st_autorefresh

# --- 1. PRIVATE ACCESS ---
PASSWORD = "benja123"
st.sidebar.title("🔒 Private Access")
password = st.sidebar.text_input("Password", type="password")
if password != PASSWORD:
    st.warning("Access denied")
    st.stop()

# --- 2. SETUP & REFRESH ---
st.set_page_config(page_title="ELITE COMMAND GLOBAL", layout="wide")
st_autorefresh(interval=600000, key="global_sync")

API_KEY = "2bbe95bafab32dd8fa0be8ae23608feb" 

# --- 3. THE ENGINES ---
def get_nba_proj(line, price):
    # NBA Normal Distribution
    ai_proj = line + (2.5 if price < 1.9 else -2.0)
    z = (line - ai_proj) / 12.0
    prob = 1 - norm.cdf(z)
    return ai_proj, prob

def get_soccer_proj(target_xg):
    # Soccer Poisson Distribution
    h_exp, a_exp = target_xg * 0.525, target_xg * 0.475
    prob_o25 = 1 - (poisson.pmf(0, h_exp) * poisson.pmf(0, a_exp) + 
                    poisson.pmf(1, h_exp) * poisson.pmf(0, a_exp) + 
                    poisson.pmf(0, h_exp) * poisson.pmf(1, a_exp) +
                    poisson.pmf(1, h_exp) * poisson.pmf(1, a_exp))
    return prob_o25

# --- 4. DASHBOARD ---
st.title("☢️ ELITE COMMAND: GLOBAL ML PREDICTOR")
st.sidebar.header("🛠️ Settings")
market_choice = st.sidebar.radio("Select Market", ["Soccer Global", "NBA Basketball"])
min_edge = st.sidebar.slider("Minimum Edge % (Lower this if empty!)", 0.01, 0.15, 0.03)

found_any = False

if market_choice == "Soccer Global":
    # Added Mexico and Argentina for Midweek Action!
    LEAGUES = {"EPL": "soccer_epl", "LaLiga": "soccer_spain_la_liga", "Mexico MX": "soccer_mexico_ligamx", "Argentina": "soccer_argentina_primera_division"}
    
    for label, lid in LEAGUES.items():
        url = f"https://api.the-odds-api.com/v4/sports/{lid}/odds/?apiKey={API_KEY}&regions=uk&markets=totals"
        try:
            res = requests.get(url).json()
            for m in res:
                bookie = m['bookmakers'][0]
                o25 = next(o for o in bookie['markets'][0]['outcomes'] if o['name'] == 'Over' and o['point'] == 2.5)
                target_xg = 2.45 + (1.28 / math.log(o25['price'] + 0.08))
                prob = get_soccer_proj(target_xg)
                edge = prob - (1/o25['price'])
                
                if edge >= min_edge:
                    found_any = True
                    with st.expander(f"⚽ {m['home_team']} vs {m['away_team']} ({label})"):
                        st.metric("Win Prob (O2.5)", f"{prob:.1%}", f"{edge:+.1%} Edge")
        except: continue

else: # NBA Logic
    url = f"https://api.the-odds-api.com/v4/sports/basketball_nba/odds/?apiKey={API_KEY}&regions=us&markets=totals"
    try:
        res = requests.get(url).json()
        for m in res:
            bookie = m['bookmakers'][0]
            over = next(o for o in bookie['markets'][0]['outcomes'] if o['name'] == 'Over')
            proj, prob = simulate_nba_game(over['point'], over['price'])
            edge = prob - (1/over['price'])
            
            if edge >= min_edge:
                found_any = True
                with st.expander(f"🏀 {m['home_team']} vs {m['away_team']}"):
                    st.metric("AI Projected Score", f"{proj:.1f}", f"{edge:+.1%} Edge")
    except: continue

if not found_any:
    st.info("Scanner Active: No games found with current Edge settings. Try lowering the 'Minimum Edge' slider in the sidebar.")
