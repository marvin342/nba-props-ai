import streamlit as st
import requests
import random

# --- CONFIGURATION ---
API_KEY = "YOUR_API_KEY" # Replace with your actual key
SPORT = "basketball_nba"
REGIONS = "us"

st.set_page_config(page_title="NBA AI Predictor", layout="wide")

# --- UI STYLE ---
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    .stExpander { border: 1px solid #374151; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

def fetch_data(endpoint_suffix="odds", params=None):
    url = f"https://api.the-odds-api.com/v4/sports/{SPORT}/{endpoint_suffix}"
    default_params = {"api_key": API_KEY, "regions": REGIONS, "oddsFormat": "american"}
    if params:
        default_params.update(params)
    
    response = requests.get(url, params=default_params)
    if response.status_code == 200:
        return response.json()
    return None

def get_ai_prediction(name, line):
    # Simulated ML Logic
    score = random.uniform(20, 80)
    if score > 65: return "OVER", round(score, 1)
    if score < 35: return "UNDER", round(score, 1)
    return "PASS", round(score, 1)

st.title("🏀 NBA AI Prop & O/U Detector")

# Toggle between Game Totals and Player Points
market_choice = st.sidebar.radio("Market Category", ["Game Totals", "Player Points"])
market_key = "totals" if market_choice == "Game Totals" else "player_points"

if st.button("Analyze Current Lines"):
    with st.spinner("Fetching live market data..."):
        data = fetch_data(params={"markets": market_key})
        
        if not data:
            st.error("No data returned. The API key might be empty or lines aren't out yet.")
        else:
            for game in data:
                # Header for each game
                game_label = f"{game['away_team']} @ {game['home_team']}"
                with st.expander(game_label, expanded=True):
                    
                    if not game.get('bookmakers'):
                        st.info("No active bookmaker lines for this game yet.")
                        continue

                    # Select first bookie (usually FanDuel or DraftKings in 'us' region)
                    bookie = game['bookmakers'][0]
                    market = next((m for m in bookie['markets'] if m['key'] == market_key), None)

                    if market:
                        # Create a clean header for the list
                        h1, h2, h3, h4 = st.columns([2, 1, 1, 2])
                        h1.caption("ENTITY/PLAYER")
                        h2.caption("LINE")
                        h3.caption("ODDS")
                        h4.caption("AI RECOMMENDATION")
                        st.divider()

                        for outcome in market['outcomes']:
                            # Handle Player Names vs Game Totals labels
                            label = outcome.get('description', outcome['name'])
                            line = outcome.get('point', 'N/A')
                            price = outcome['price']
                            
                            rec, conf = get_ai_prediction(label, line)
                            
                            c1, c2, c3, c4 = st.columns([2, 1, 1, 2])
                            c1.write(f"**{label}** ({outcome['name']})")
                            c2.write(str(line))
                            c3.write(str(price))
                            
                            if rec == "OVER":
                                c4.success(f"🚀 OVER ({conf}% Confidence)")
                            elif rec == "UNDER":
                                c4.warning(f"📉 UNDER ({conf}% Confidence)")
                            else:
                                c4.info("⚖️ PASS / NO EDGE")
