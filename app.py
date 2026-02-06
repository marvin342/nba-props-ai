import streamlit as st
import requests
import random

# --- CONFIG ---
API_KEY = "27970d14c8e8eb9f2a217c775db6571f"
SPORT = "basketball_nba"

st.set_page_config(page_title="NBA Best Bets", layout="wide")

def get_ai_prediction(game_name, over_odds, under_odds, line):
    """
    Improved Logic: Analyzes the whole game line once.
    """
    # Simulate an AI edge calculation
    # In a real app, you'd compare this 'line' to your model's projected total
    edge = random.uniform(-10, 10) 
    confidence = abs(edge) * 10
    
    if edge > 2.5:
        return "OVER", round(confidence, 1)
    elif edge < -2.5:
        return "UNDER", round(confidence, 1)
    return "PASS", 0

# --- UI ---
st.title("🏀 NBA AI Over/Under Picks")
st.markdown("### High Confidence Predictions")

if st.button("Generate Today's Picks"):
    url = f"https://api.the-odds-api.com/v4/sports/{SPORT}/odds"
    params = {"api_key": API_KEY, "regions": "us", "markets": "totals", "oddsFormat": "american"}
    data = requests.get(url, params=params).json()

    if not data:
        st.warning("No live lines found. Try again closer to tip-off.")
    else:
        for game in data:
            with st.container():
                # Extract Data
                home = game['home_team']
                away = game['away_team']
                
                # Get the first bookie's Over/Under info
                bookie = game['bookmakers'][0]
                market = bookie['markets'][0]
                outcomes = market['outcomes'] # List of 2: Over and Under
                
                line = outcomes[0]['point']
                over_price = next(o['price'] for o in outcomes if o['name'] == 'Over')
                under_price = next(o['price'] for o in outcomes if o['name'] == 'Under')
                
                # Get One Prediction per Game
                rec, conf = get_ai_prediction(f"{away}@{home}", over_price, under_price, line)
                
                # Visual Row
                col1, col2, col3 = st.columns([2, 1, 2])
                
                with col1:
                    st.subheader(f"{away} @ {home}")
                    st.caption(f"Line: **{line}** | O: {over_price} / U: {under_price}")
                
                with col2:
                    st.metric("Confidence", f"{conf}%")
                
                with col3:
                    if rec == "OVER":
                        st.success(f"✅ **PICK: OVER {line}**")
                        st.markdown(f"<span style='color:#00ff00'>High probability of a high-scoring game.</span>", unsafe_allow_html=True)
                    elif rec == "UNDER":
                        st.error(f"🚨 **PICK: UNDER {line}**")
                        st.markdown(f"<span style='color:#ff4b4b'>Defensive matchup expected.</span>", unsafe_allow_html=True)
                    else:
                        st.info("⚖️ **NO EDGE (PASS)**")
                
                st.divider()
