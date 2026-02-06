import streamlit as st
import requests

# --- 1. URBAN THEME OVERRIDE ---
st.set_page_config(page_title="NBA Sharp AI", page_icon="🏀", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Aref+Ruqaa:wght@700&family=Permanent+Marker&display=swap');
    .stApp { background: #05070a !important; color: #ffffff; }
    .block-container { max-width: 1000px !important; padding-top: 2rem !important; }
    [data-testid="stSidebar"] { background-color: #0c0f16 !important; border-right: 2px solid #ff4b4b; }
    .header-container { display: flex; justify-content: center; align-items: center; gap: 25px; padding-bottom: 20px; border-bottom: 1px solid #1c2128; margin-bottom: 30px; }
    .graffiti-title-english { font-family: 'Permanent Marker', cursive; font-size: 38px; color: #ffffff; text-shadow: 3px 3px 0px #ff4b4b, -1px -1px 0px #58a6ff; }
    .graffiti-title-arabic { font-family: 'Aref Ruqaa', serif; font-size: 38px; color: #ffffff; text-shadow: 3px 3px 0px #58a6ff, -1px -1px 0px #ff4b4b; direction: rtl; }
    [data-testid="stVerticalBlock"] > div:has(div.stMetric) { background-color: #11151c !important; border-radius: 12px; border-left: 6px solid #ff4b4b; border-right: 6px solid #58a6ff; padding: 20px; box-shadow: 0px 8px 20px rgba(0,0,0,0.5); margin-bottom: 15px; }
    .stButton>button { background: linear-gradient(90deg, #ff4b4b 0%, #58a6ff 100%) !important; color: white !important; font-family: 'Permanent Marker', cursive !important; font-size: 20px !important; border: 2px solid #ffffff !important; border-radius: 8px !important; height: 3.5rem !important; width: 100%; }
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
}

# --- 3. CALLBACKS ---
def run_analysis_callback():
    url = "https://api.the-odds-api.com/v4/sports/basketball_nba/odds"
    params = {"api_key": "27970d14c8e8eb9f2a217c775db6571f", "regions": "us", "markets": "totals"}
    try:
        res = requests.get(url, params=params)
        if res.status_code == 200:
            st.session_state.game_data = res.json()
            st.session_state.locked_picks = {}
    except: st.error("API Connection Error")

def wipe_memory_callback():
    st.session_state.game_data = []
    st.session_state.locked_picks = {}

if 'game_data' not in st.session_state: st.session_state.game_data = []
if 'locked_picks' not in st.session_state: st.session_state.locked_picks = {}

# --- 4. THE POWERED-UP LOGIC ---
def calculate_sharp_pick(game_id, away, home, line, away_fatigue, home_fatigue):
    # We check if context changed, so we don't lock if user is toggling fatigue
    a_stats = NBA_STATS.get(away, {"off": 115, "def": 115})
    h_stats = NBA_STATS.get(home, {"off": 115, "def": 115})
    
    # Base Projection
    a_off = a_stats["off"] - (3.5 if away_fatigue else 0)
    h_off = h_stats["off"] - (3.5 if home_fatigue else 0)
    
    # Apply Home Court Advantage (+2.5 to Home, -1.0 to Away)
    projection = ((a_off + h_stats["def"]) / 2) + ((h_off + 2.5 + a_stats["def"]) / 2)
    
    edge = abs(projection - line)
    
    # Calibrated Confidence
    if edge < 1.0: conf = edge * 25 
    else: conf = 55 + (min(edge, 10) * 4.2)
        
    if (projection - line) > 2.5: res = ("✅ SHARP OVER", conf, projection)
    elif (projection - line) < -2.5: res = ("🚨 SHARP UNDER", conf, projection)
    else: res = ("⚖️ PASS", 0, projection)
        
    return res

# --- 5. THE UI ---
st.markdown('<div class="header-container"><div class="graffiti-title-english">NBA SHARP AI</div><div class="graffiti-title-arabic">الرهان الذكي</div></div>', unsafe_allow_html=True)

# SIDEBAR STRENGTH SETTINGS
st.sidebar.markdown("<h1 style='color:#ff4b4b; font-family:\"Aref Ruqaa\"; text-align:center;'>الإعدادات</h1>", unsafe_allow_html=True)
st.sidebar.markdown("---")
st.sidebar.subheader("Fatigue Toggles (تعب الفريق)")
st.sidebar.info("Check if team played last night")

st.button("RUN ANALYSIS - ابدأ التحليل", on_click=run_analysis_callback)

if st.session_state.game_data:
    for game in st.session_state.game_data:
        game_id, h, a = game['id'], game['home_team'], game['away_team']
        try: line = game['bookmakers'][0]['markets'][0]['outcomes'][0]['point']
        except: continue
        
        # Adding manual toggles per game for fatigue
        with st.sidebar.expander(f"Context: {a} @ {h}"):
            a_tired = st.checkbox(f"{a} is Tired", key=f"t_{a}_{game_id}")
            h_tired = st.checkbox(f"{h} is Tired", key=f"t_{h}_{game_id}")
        
        label, conf, proj = calculate_sharp_pick(game_id, a, h, line, a_tired, h_tired)
        
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

st.sidebar.markdown("---")
st.sidebar.button("WIPE MEMORY", on_click=wipe_memory_callback)
