import streamlit as st
import requests

# --- 1. THE "GRAFFITI" STYLING ---
st.set_page_config(page_title="NBA Sharp AI", page_icon="🏀", layout="wide")

# This CSS injects the Arabic urban street style
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Aref+Ruqaa:wght@400;700&family=Reem+Kufi:wght@400;700&display=swap');

    .stApp {
        background: radial-gradient(circle at top left, #0e1117, #1c1c2b);
        color: #ffffff;
    }

    /* Graffiti Card Style */
    [data-testid="stVerticalBlock"] > div:has(div.stMetric) {
        background-color: rgba(30, 33, 48, 0.8);
        border-radius: 20px;
        padding: 25px;
        border-left: 5px solid #ff4b4b; /* Red Accent */
        border-right: 5px solid #58a6ff; /* Blue Accent */
        box-shadow: 0px 4px 15px rgba(0,0,0,0.5);
        margin-bottom: 20px;
    }

    /* Heading Arabic Style */
    h1, h2, h3 {
        font-family: 'Aref Ruqaa', serif !important;
        text-shadow: 2px 2px #ff4b4b, -1px -1px #58a6ff;
        letter-spacing: 1px;
    }

    /* Blue and Red Writing for labels */
    .blue-tag { color: #58a6ff; font-weight: bold; font-family: 'Reem Kufi'; }
    .red-tag { color: #ff4b4b; font-weight: bold; font-family: 'Reem Kufi'; }

    /* Button: Urban Style */
    .stButton>button {
        background: linear-gradient(45deg, #ff4b4b, #58a6ff);
        border: 2px solid #ffffff;
        color: white;
        font-family: 'Aref Ruqaa';
        font-size: 20px;
        border-radius: 50px;
        box-shadow: 0px 0px 15px rgba(88, 166, 255, 0.4);
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATA (NO CHANGES) ---
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
st.title("🏀 NBA SHARP AI - الرهان الذكي")
st.markdown("<p style='text-align: right; font-family:\"Reem Kufi\"; color:#58a6ff;'>تحليل البيانات الحقيقية لعام ٢٠٢٦</p>", unsafe_allow_html=True)

if st.button("GENERATE PICKS - ابدأ المراهنة"):
    with st.spinner("Calculating..."):
        API_KEY = "27970d14c8e8eb9f2a217c775db6571f"
        url = "https://api.the-odds-api.com/v4/sports/basketball_nba/odds"
        params = {"api_key": API_KEY, "regions": "us", "markets": "totals"}
        response = requests.get(url, params=params)
        if response.status_code == 200:
            st.session_state.game_data = response.json()

if st.session_state.game_data:
    for game in st.session_state.game_data:
        game_id, home, away = game['id'], game['home_team'], game['away_team']
        try:
            line = game['bookmakers'][0]['markets'][0]['outcomes'][0]['point']
        except: continue

        label, conf, proj = calculate_sharp_pick(game_id, away, home, line)

        with st.container():
            c1, c2, c3 = st.columns([3, 2, 2])
            with c1:
                st.markdown(f"### {away} vs {home}")
                st.markdown(f"<span class='blue-tag'>Vegas Total:</span> **{line}**", unsafe_allow_html=True)
            with c2:
                st.metric("PROJECTION - التحليل", f"{proj:.1f}")
            with c3:
                if "OVER" in label:
                    st.success(f"**{label}**\n\n{conf:.1f}% SHARP")
                elif "UNDER" in label:
                    st.error(f"**{label}**\n\n{conf:.1f}% SHARP")
                else:
                    st.info(label)
else:
    st.info("No games loaded. Hit the graffiti button above! 🚀")

st.sidebar.markdown("<h2 style='color:#ff4b4b;'>Settings - الإعدادات</h2>", unsafe_allow_html=True)
if st.sidebar.button("RESET MEMORY - مسح"):
    st.session_state.locked_picks = {}
    st.rerun()
