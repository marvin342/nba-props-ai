import streamlit as st
import requests

# --- 1. DESIGN & URBAN THEME (UNTOUCHED) ---
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

# --- 2. UPDATED NBA 2026 STATS (FULL 30 TEAMS) ---
# Data based on February 2026 League Efficiency and Pace
NBA_STATS = {
    "Atlanta Hawks": {"off": 114.4, "def": 115.2, "pace": 100.2},
    "Boston Celtics": {"off": 121.1, "def": 114.4, "pace": 95.6},
    "Brooklyn Nets": {"off": 110.6, "def": 118.4, "pace": 96.2},
    "Charlotte Hornets": {"off": 117.5, "def": 116.3, "pace": 98.4},
    "Chicago Bulls": {"off": 114.6, "def": 118.0, "pace": 101.6},
    "Cleveland Cavaliers": {"off": 117.9, "def": 114.2, "pace": 101.8},
    "Dallas Mavericks": {"off": 110.3, "def": 113.2, "pace": 94.5},
    "Denver Nuggets": {"off": 121.9, "def": 118.9, "pace": 98.3},
    "Detroit Pistons": {"off": 116.2, "def": 109.8, "pace": 100.8},
    "Golden State Warriors": {"off": 115.9, "def": 113.4, "pace": 101.0},
    "Houston Rockets": {"off": 118.7, "def": 113.6, "pace": 96.9},
    "Indiana Pacers": {"off": 110.1, "def": 116.9, "pace": 100.8},
    "Los Angeles Clippers": {"off": 116.7, "def": 117.2, "pace": 96.6},
    "Los Angeles Lakers": {"off": 117.7, "def": 118.3, "pace": 99.5},
    "Memphis Grizzlies": {"off": 113.5, "def": 115.2, "pace": 101.2},
    "Miami Heat": {"off": 115.0, "def": 112.7, "pace": 105.2},
    "Milwaukee Bucks": {"off": 113.5, "def": 117.7, "pace": 98.0},
    "Minnesota Timberwolves": {"off": 117.6, "def": 113.6, "pace": 101.5},
    "New Orleans Pelicans": {"off": 114.0, "def": 119.8, "pace": 100.0},
    "New York Knicks": {"off": 120.3, "def": 114.8, "pace": 98.9},
    "Oklahoma City Thunder": {"off": 119.3, "def": 107.8, "pace": 101.0},
    "Orlando Magic": {"off": 114.8, "def": 115.1, "pace": 100.6},
    "Philadelphia 76ers": {"off": 116.7, "def": 115.3, "pace": 99.4},
    "Phoenix Suns": {"off": 116.0, "def": 113.3, "pace": 99.3},
    "Portland Trail Blazers": {"off": 114.5, "def": 116.1, "pace": 100.9},
    "Sacramento Kings": {"off": 110.5, "def": 120.6, "pace": 99.4},
    "San Antonio Spurs": {"off": 116.9, "def": 111.6, "pace": 100.4},
    "Toronto Raptors": {"off": 114.3, "def": 113.3, "pace": 99.2},
    "Utah Jazz": {"off": 115.9, "def": 123.4, "pace": 101.7},
    "Washington Wizards": {"off": 110.6, "def": 121.2, "pace": 100.8},
}

# --- 3. CORE LOGIC & CALLBACKS ---
def run_analysis_callback():
    # Fetching real lines from Odds API
    url = "https://api.the-odds-api.com/v4/sports/basketball_nba/odds"
    params = {"api_key": "27970d14c8e8eb9f2a217c775db6571f", "regions": "us", "markets": "totals"}
    try:
        res = requests.get(url, params=params)
        if res.status_code == 200:
            st.session_state.game_data = res.json()
    except: st.error("API Link Error")

if 'game_data' not in st.session_state: st.session_state.game_data = []

def get_betting_instruction(away, home, vegas_line, away_fatigue, home_fatigue):
    a = NBA_STATS.get(away, {"off": 114, "def": 115, "pace": 100})
    h = NBA_STATS.get(home, {"off": 114, "def": 115, "pace": 100})
    
    # Situational Fatigue Adjustments
    a_eff = a["off"] - (3.5 if away_fatigue else 0)
    h_eff = h["off"] - (3.5 if home_fatigue else 0)
    matchup_pace = (a["pace"] + h["pace"]) / 2
    
    # Advanced Projection: ((OffEff + DefEff) / 200) * Pace
    # Includes small home court bump (+2.5)
    proj = ((a_eff + h["def"] + h_eff + 2.5 + a["def"]) / 200) * matchup_pace
    diff = proj - vegas_line
    
    # Value Rating Logic (Scaled 60% to 95%)
    value_score = 60 + (min(abs(diff), 12) * 2.8)
    
    if diff > 3.2: return ("🔥 TAKE THE OVER", proj, value_score)
    elif diff < -3.2: return ("❄️ TAKE THE UNDER", proj, value_score)
    else: return ("🚫 STAY AWAY", proj, 0)

# --- 4. MAIN UI ---
st.markdown('<div class="header-container"><div class="graffiti-title-english">NBA SHARP AI</div><div class="graffiti-title-arabic">الرهان الذكي</div></div>', unsafe_allow_html=True)

st.sidebar.markdown("<h1 style='color:#ff4b4b; font-family:\"Aref Ruqaa\"; text-align:center;'>الإعدادات</h1>", unsafe_allow_html=True)
st.button("RUN ANALYSIS - ابدأ التحليل", on_click=run_analysis_callback)

if st.session_state.game_data:
    for game in st.session_state.game_data:
        h, a = game['home_team'], game['away_team']
        try: line = game['bookmakers'][0]['markets'][0]['outcomes'][0]['point']
        except: continue
        
        # Side context for fatigue
        with st.sidebar.expander(f"Context: {a} @ {h}"):
            af = st.checkbox(f"{a} Tired?", key=f"af_{game['id']}")
            hf = st.checkbox(f"{h} Tired?", key=f"hf_{game['id']}")
        
        call, proj, value = get_betting_instruction(a, h, line, af, hf)
        
        with st.container():
            col1, col2, col3 = st.columns([3, 2, 2])
            with col1:
                st.markdown(f"## {a} vs {h}")
                st.caption(f"Vegas Set: {line}")
            with col2:
                st.metric("AI Projection", f"{proj:.1f}")
            with col3:
                if "OVER" in call: st.success(call)
                elif "UNDER" in call: st.error(call)
                else: st.info(call)
                
                if value > 0:
                    st.markdown(f"**Value Rating: {value:.1f}%**")
                    if value > 90: st.markdown("⚠️ *High Value Detected*")

st.sidebar.button("WIPE MEMORY", on_click=lambda: st.session_state.update({"game_data": []}))
