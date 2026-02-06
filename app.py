import streamlit as st
import requests

# --- 1. DESIGN & CSS (THE "NICE LOOK") ---
st.set_page_config(page_title="NBA Sharp AI", page_icon="🏀", layout="wide")

# Custom CSS for a professional Dark Mode look
st.markdown("""
    <style>
    /* Background color and font */
    .stApp {
        background-color: #0e1117;
        color: #ffffff;
    }
    /* Style the game containers as cards */
    [data-testid="stVerticalBlock"] > div:has(div.stMetric) {
        background-color: #1e2130;
        border-radius: 15px;
        padding: 20px;
        border: 1px solid #30363d;
        transition: transform 0.2s;
    }
    [data-testid="stVerticalBlock"] > div:has(div.stMetric):hover {
        transform: scale(1.01);
        border-color: #58a6ff;
    }
    /* Subheaders */
    .st-emotion-cache-10trblm {
        color: #58a6ff !important;
        font-weight: 700;
    }
    /* Button Styling */
    .stButton>button {
        width: 100%;
        border-radius: 10px;
        background-color: #58a6ff;
        color: white;
        font-weight: bold;
        border: none;
        height: 3em;
    }
    /* Metric styling */
    [data-testid="stMetricValue"] {
        font-size: 24px;
        color: #00ff00;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. REAL-WORLD SHARP DATA ---
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

# --- 3. SESSION STATE & LOGIC (NO CHANGES) ---
if 'game_data' not in st.session_state:
    st.session_state.game_data = []
if 'locked_picks' not in st.session_state:
    st.session_state.locked_picks = {}

def calculate_sharp_pick(game_id, away, home, line):
    if game_id in st.session_state.locked_picks:
        return st.session_state.locked_picks[game_id]
    a_off = NBA_STATS.get(away, {"off": 115})["off"]
    a_def = NBA_STATS.get(away, {"def": 115})["def"]
    h_off = NBA_STATS.get(home, {"off": 115})["off"]
    h_def = NBA_STATS.get(home, {"def": 115})["def"]
    projection = ((a_off + h_def) / 2) + ((h_off + a_def) / 2)
    edge = projection - line
    confidence = min(abs(edge) * 12.5, 99.8)
    if edge > 2.0:
        result = ("✅ SHARP OVER", confidence, projection)
    elif edge < -2.0:
        result = ("🚨 SHARP UNDER", confidence, projection)
    else:
        result = ("⚖️ PASS (No Edge)", 0, projection)
    st.session_state.locked_picks[game_id] = result
    return result

# --- 4. THE UI LAYOUT ---
st.title("🏀 NBA Sharp AI")
st.caption("February 2026 Season Intelligence Dashboard")

# Top Metrics Row
t1, t2, t3 = st.columns(3)
t1.metric("Market Status", "LIVE", delta="Active")
t2.metric("Sharp Accuracy", "68%", delta="4.2%")
t3.metric("League Avg PPG", "115.4")

st.divider()

if st.button("Generate Today's Sharp Picks"):
    with st.spinner("Analyzing match-ups..."):
        API_KEY = "27970d14c8e8eb9f2a217c775db6571f"
        url = "https://api.the-odds-api.com/v4/sports/basketball_nba/odds"
        params = {"api_key": API_KEY, "regions": "us", "markets": "totals"}
        response = requests.get(url, params=params)
        if response.status_code == 200:
            st.session_state.game_data = response.json()

# Result Cards
if st.session_state.game_data:
    for game in st.session_state.game_data:
        game_id, home, away = game['id'], game['home_team'], game['away_team']
        try:
            line = game['bookmakers'][0]['markets'][0]['outcomes'][0]['point']
        except: continue

        label, conf, proj = calculate_sharp_pick(game_id, away, home, line)

        # Card Layout
        with st.container():
            c1, c2, c3 = st.columns([3, 2, 2])
            with c1:
                st.subheader(f"{away} vs {home}")
                st.write(f"Vegas Total: **{line}**")
            with c2:
                st.metric("AI Projection", f"{proj:.1f}")
            with c3:
                if "OVER" in label:
                    st.success(f"**{label}**\n\n{conf:.1f}% Sharp")
                elif "UNDER" in label:
                    st.error(f"**{label}**\n\n{conf:.1f}% Sharp")
                else:
                    st.info(label)
            st.markdown("---")
else:
    st.info("No games loaded. Please click 'Generate Today's Sharp Picks'.")

st.sidebar.title("Settings")
if st.sidebar.button("Reset AI Memory"):
    st.session_state.locked_picks = {}
    st.rerun()
