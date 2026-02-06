import streamlit as st
import requests
import random

# --- CONFIG ---
API_KEY = "27970d14c8e8eb9f2a217c775db6571f"
SPORT = "basketball_nba"

# 1. Initialize the "Save Slot" (Session State)
if 'predictions' not in st.session_state:
    st.session_state.predictions = {}

def get_consistent_prediction(game_id):
    """
    Checks if we already made a prediction for this game today.
    If not, it makes one and saves it.
    """
    if game_id not in st.session_state.predictions:
        # Simulate logic (In real life, this would be your ML model)
        edge = random.uniform(-10, 10)
        confidence = round(abs(edge) * 10, 1)
        
        if edge > 3.0:
            pick = "OVER"
        elif edge < -3.0:
            pick = "UNDER"
        else:
            pick = "PASS"
            
        # Save it so it never changes for this session
        st.session_state.predictions[game_id] = (pick, confidence)
    
    return st.session_state.predictions[game_id]

st.title("🏀 NBA AI: Locked-In Picks")

if st.button("Generate Today's Best Bets"):
    data = requests.get(f"https://api.the-odds-api.com/v4/sports/{SPORT}/odds", 
                        params={"api_key": API_KEY, "regions": "us", "markets": "totals"}).json()

    if data:
        for game in data:
            game_id = game['id'] # Unique ID for each game
            home = game['home_team']
            away = game['away_team']
            
            # Get the line and odds
            outcomes = game['bookmakers'][0]['markets'][0]['outcomes']
            line = outcomes[0]['point']
            
            # Get the PERMANENT prediction for this game
            rec, conf = get_consistent_prediction(game_id)
            
            with st.container():
                col1, col2 = st.columns([2, 1])
                col1.subheader(f"{away} @ {home}")
                col1.write(f"**Current Line:** {line}")
                
                # Visual logic for Green/Red
                if rec == "OVER":
                    col2.success(f"✅ TAKE OVER {line} ({conf}%)")
                elif rec == "UNDER":
                    col2.error(f"🚨 TAKE UNDER {line} ({conf}%)")
                else:
                    col2.info(f"⚖️ PASS (No Edge)")
                st.divider()
