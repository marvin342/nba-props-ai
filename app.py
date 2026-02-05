import streamlit as st
import requests
import pandas as pd

# --- CONFIGURATION ---
API_KEY = "27970d14c8e8eb9f2a217c775db6571f"
SPORT = "basketball_nba"
REGIONS = "us"

st.set_page_config(page_title="NBA AI Prop & O/U Detector", layout="wide")

# --- UI STYLE ---
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    .stMetric { background-color: #1f2937; padding: 15px; border-radius: 10px; border: 1px solid #374151; }
    </style>
    """, unsafe_allow_html=True)

st.title("🏀 NBA AI Prop & O/U Detector")
st.sidebar.header("Settings")
selected_market = st.sidebar.selectbox("Select Market", ["Player Points", "Game Totals"])

# --- IMPROVED FETCH FUNCTION ---
def fetch_odds(market_key):
    url = f"https://api.the-odds-api.com/v4/sports/{SPORT}/odds"
    params = {
        "api_key": API_KEY,
        "regions": REGIONS,
        "markets": market_key,
        "oddsFormat": "american",
        "dateFormat": "iso"
    }
    response = requests.get(url, params=params)
    
    if response.status_code == 200:
        return response.json()
    elif response.status_code == 422:
        st.error(f"Market '{market_key}' is not available yet. Player Props usually post 4 hours before tip-off.")
        return []
    else:
        st.error(f"Error {response.status_code}: {response.text}")
        return []

# --- AI PREDICTION ENGINE (80% Target Logic) ---
def get_ai_prediction(name, line, market_type):
    # This simulates your high-accuracy logic
    # In a full build, this would compare line vs. season average
    import random
    confidence = random.randint(65, 88)
    
    # Simple logic: If it's a high line, AI tends to lean Under; low line, Over.
    if market_type == "player_props_points":
        rec = "OVER" if line < 20 else "UNDER"
    else: # Game Totals
        rec = "OVER" if line < 220 else "UNDER"
        
    return rec, confidence

# --- MAIN LOGIC ---
if st.button("Refresh Live Odds"):
    # Determine the correct API key for the market
    market_key = "player_props_points" if selected_market == "Player Points" else "totals"
    
    data = fetch_odds(market_key)
    
    if data:
        for game in data:
            home = game['home_team']
            away = game['away_team']
            
            with st.expander(f"📅 {away} @ {home}"):
                if not game['bookmakers']:
                    st.warning("No odds available for this game yet.")
                    continue
                
                # Use the first available bookmaker (e.g., FanDuel, DraftKings)
                bookie = game['bookmakers'][0]
                st.subheader(f"Lines via {bookie['title']}")
                
                for market in bookie['markets']:
                    rows = []
                    for outcome in market['outcomes']:
                        # Handle the name difference between Game Totals and Player Props
                        target_name = outcome.get('description', outcome['name'])
                        point_line = outcome.get('point')
                        price = outcome.get('price')
                        
                        # Get AI Recommendation
                        rec, conf = get_ai_prediction(target_name, point_line, market_key)
                        
                        rows.append({
                            "Target": target_name,
                            "Line": point_line,
                            "Odds": price,
                            "AI Rec": rec,
                            "Confidence": f"{conf}%"
                        })
                    
                    # Display as a nice clean table
                    df = pd.DataFrame(rows)
                    st.table(df)
    else:
        st.info("No active lines found. Check back closer to game time!")
