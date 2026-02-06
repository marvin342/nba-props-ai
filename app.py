import streamlit as st
import requests

# --- 1. THE "NO-WHITE" URBAN OVERRIDE ---
st.set_page_config(page_title="NBA Sharp AI", page_icon="🏀", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Aref+Ruqaa:wght@700&family=Permanent+Marker&display=swap');

    /* Kill all white space */
    .stApp {
        background: #05070a !important;
        color: #ffffff;
    }

    [data-testid="stSidebar"] {
        background-color: #0c0f16 !important;
        border-right: 4px solid #ff4b4b;
    }

    /* THE UPDATED NBA SHARP AI HEADER */
    .header-container {
        display: flex;
        justify-content: center;
        align-items: center;
        gap: 20px;
        padding: 40px 0;
        flex-wrap: wrap;
    }

    .graffiti-title-english {
        font-family: 'Permanent Marker', cursive;
        font-size: clamp(30px, 6vw, 70px);
        color: #ffffff;
        text-shadow: 4px 4px 0px #ff4b4b, -2px -2px 0px #58a6ff;
    }

    .graffiti-title-arabic {
        font-family: 'Aref Ruqaa', serif;
        font-size: clamp(30px, 6vw, 70px);
        color: #ffffff;
        text-shadow: 4px 4px 0px #58a6ff, -2px -2px 0px #ff4b4b;
        direction: rtl; /* Ensures proper Arabic flow */
    }

    /* Card Styling */
    [data-testid="stVerticalBlock"] > div:has(div.stMetric) {
        background-color: #11151c !important;
        border-radius: 15px;
        border-left: 10px solid #ff4b4b;
        border-right: 10px solid #58a6ff;
        padding: 25px;
        box-shadow: 0px 15px 35px rgba(0,0,0,0.9);
        margin-bottom: 25px;
    }

    .stButton>button {
        background: linear-gradient(90deg, #ff4b4b 0%, #58a6ff 100%) !important;
        color: white !important;
        font-family: 'Permanent Marker', cursive !important;
        font-size: 28px !important;
        border: 3px solid #ffffff !important;
        border-radius: 12px !important;
        height: 5rem !important;
        width: 100% !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. NBA 2026 SHARP DATA ---
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
}

# --- 3. SESSION LOGIC ---
if 'game_data' not in st.session_state:
    st.session_state.game_data = []
if 'locked_picks' not in st.session_state:
    st.session_state.locked_picks = {}

def calculate_sharp_pick(game_id, away, home, line):
    if game_id in st.session_state.locked_picks:
        return st.session_state.locked_picks[game_id]
    a_stats = NBA_STATS.get(away, {"off": 115, "def": 115})
    h_stats = NBA_STATS.get(home, {"off": 115, "def": 115})
    projection = ((a_stats["off"] + h_stats["def"]) / 2) + ((h_stats["off"] + a_stats["def"]) / 2)
    edge = projection - line
    conf = min(abs(edge) * 15, 99.9)
    if edge > 2.0: res = ("✅ SHARP OVER", conf, projection)
    elif edge < -2.0: res = ("🚨 SHARP UNDER", conf, projection)
    else: res = ("⚖️ PASS", 0, projection)
    st.session_state.locked_picks[game_id] = res
    return res

# --- 4. THE UI ---
# UPDATED TITLE: English on Left, Arabic on Right
st.markdown("""
    <div class="header-container">
        <div class="graffiti-title-english">NBA SHARP AI</div>
        <div class="graffiti-title-arabic">الرهان الذكي</div>
    </div>
    """, unsafe_allow_html=True)

if st.button("RUN ANALYSIS - ابدأ التحليل"):
    url = "https://api.the-odds-api.com/v4/sports/basketball_nba/odds"
    params = {"api_key": "27970d14c8e8eb9f2a217c775db6571f", "regions": "us", "markets": "totals"}
    res = requests.get(url, params=params)
    if res.status_code == 200:
        st.session_state.game_data = res.json()

if st.session_state.game_data:
    for game in st.session_state.game_data:
        game_id, h, a = game['id'], game['home_team'], game['away_team']
        try: line = game['bookmakers'][0]['markets'][0]['outcomes'][0]['point']
        except: continue
        
        label, conf, proj = calculate_sharp_pick(game_id, a, h, line)
        
        with st.container():
            col1, col2, col3 = st.columns([3, 2, 2])
            with col1:
                st.markdown(f"## {a} vs {h}")
                st.markdown(f"<span style='color:#58a6ff;'>Vegas Market:</span> **{line}**", unsafe_allow_html=True)
            with col2:
                st.metric("AI Projection", f"{proj:.1f}")
            with col3:
                if "OVER" in label: st.success(label)
                elif "UNDER" in label: st.error(label)
                else: st.info(label)
                st.caption(f"Sharp Level: {conf:.1f}%")

st.sidebar.markdown("<h1 style='color:#ff4b4b; font-family:\"Aref Ruqaa\"; text-align:center;'>الإعدادات</h1>", unsafe_allow_html=True)
if st.sidebar.button("WIPE MEMORY"):
    st.session_state.locked_picks = {}
    st.rerun()
