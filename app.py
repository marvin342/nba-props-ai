import streamlit as st
import requests

# --- 1. 2026 REAL-WORLD SHARP DATA ---
# Source: 2025-26 Season Stats as of Feb 5, 2026
NBA_STATS = {
    "Oklahoma City Thunder": {"off": 120.2, "def": 107.9},
    "Boston Celtics": {"off": 115.9, "def": 108.6},
    "Detroit Pistons": {"off": 117.5, "def": 109.9},
    "New York Knicks": {"off": 118.2, "def": 112.1},
    "San Antonio Spurs": {"off": 116.9, "def": 111.8},
    "Minnesota Timberwolves": {"off": 119.6, "def": 114.8},
    "Philadelphia 76ers": {"off": 116.8, "def": 115.3},
    "Los Angeles Lakers": {"off": 116.3, "def": 116.2},
    "Phoenix Suns": {"off": 114.1, "def": 111.6},
    "Golden State Warriors": {"off": 116.2, "def": 114.0},
    "Miami Heat": {"off": 119.9, "def": 118.0},
    "Dallas Mavericks": {"off": 113.8, "def": 116.5},
    "Houston Rockets": {"off": 115.5, "def": 110.1},
    "Denver Nuggets": {"off": 120.1, "def": 116.2},
}

# --- 2. SETUP & INITIALIZATION ---
st.set_page_config(page_title="NBA Sharp AI", page_icon="🏀")
API_KEY = "27970d14c8e8eb9f2a217c775db6571f" # Your Key

# Initialize session state to store data and prevent "randomness"
if 'game_data' not in st.session_state:
    st.session_state.game_data = []
if 'locked_picks' not in st.session_state:
    st.session_state.locked_picks = {}

# --- 3. SHARP LOGIC FUNCTION ---
def calculate_sharp_pick(game_id, away, home, line):
    """Uses a projected score formula to find an edge against Vegas."""
    if game_id in st.session_state.locked_picks:
        return st.session_state.locked_picks[game_id]

    # Get team stats (default to league average 115 if not found)
    a_off = NBA_STATS.get(away, {"off": 115})["off"]
    a_def = NBA_STATS.get(away, {"def": 115})["def"]
    h_off = NBA_STATS.get(home, {"off": 115})["off"]
    h_def = NBA_STATS.get(home, {"def": 115})["def"]

    # SHARP FORMULA: (Away Off vs Home Def + Home Off vs Away Def) / 2
    projection = ((a_off + h_def) / 2) + ((h_off + a_def) / 2)
    edge = projection - line
    confidence = min(abs(edge) * 12.5, 99.8) # Stronger edge = higher %

    if edge > 2.0:
        result = ("✅ SHARP OVER", confidence, projection)
    elif edge < -2.0:
        result = ("🚨 SHARP UNDER", confidence, projection)
    else:
        result = ("⚖️ PASS (No Edge)", 0, projection)

    st.session_state.locked_picks[game_id] = result
    return result

# --- 4. USER INTERFACE ---
st.title("🏀 NBA Sharp AI Predictor")
st.markdown("Uses actual 2026 Offensive/Defensive ratings to find market edges.")

if st.button("Generate Today's Sharp Picks"):
    with st.spinner("Fetching latest lines..."):
        url = f"https://api.the-odds-api.com/v4/sports/basketball_nba/odds"
        params = {"api_key": API_KEY, "regions": "us", "markets": "totals"}
        response = requests.get(url, params=params)
        
        if response.status_code == 200:
            st.session_state.game_data = response.json()
        else:
            st.error(f"API Error: {response.status_code}. Check your API Key!")

# --- 5. DISPLAY RESULTS ---
if st.session_state.game_data:
    for game in st.session_state.game_data:
        game_id = game['id']
        home = game['home_team']
        away = game['away_team']
        
        # Extract the line (point) safely
        try:
            market = game['bookmakers'][0]['markets'][0]
            line = market['outcomes'][0]['point']
        except (IndexError, KeyError):
            continue

        # Get the pick (it stays the same now!)
        label, conf, proj = calculate_sharp_pick(game_id, away, home, line)

        with st.container(border=True):
            col1, col2 = st.columns([2, 1])
            col1.subheader(f"{away} @ {home}")
            col1.write(f"**Vegas Line:** {line} | **AI Projection:** {proj:.1f}")
            
            if "OVER" in label:
                col2.success(f"**{label}**\n\n{conf:.1f}% Sharpness")
            elif "UNDER" in label:
                col2.error(f"**{label}**\n\n{conf:.1f}% Sharpness")
            else:
                col2.info(f"**{label}**")
else:
    st.info("No games loaded yet. Click the button above.")

if st.sidebar.button("Reset AI Memory"):
    st.session_state.locked_picks = {}
    st.rerun()
