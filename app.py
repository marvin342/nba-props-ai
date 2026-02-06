import streamlit as st
import requests

# --- 1. DESIGN (STRICTLY UNTOUCHED) ---
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

# --- 2. NBA DATA (2026 PROJECTIONS) ---
NBA_STATS = {
    "Oklahoma City Thunder": {"off": 120.2, "def": 107.9, "pace": 102.5},
    "Boston Celtics": {"off": 115.9, "def": 108.6, "pace": 98.2},
    "Detroit Pistons": {"off": 117.5, "def": 109.9, "pace": 100.1},
    "New York Knicks": {"off": 118.2, "def": 112.1, "pace": 95.8},
    "San Antonio Spurs": {"off": 116.9, "def": 111.8, "pace": 101.9},
    "Minnesota Timberwolves": {"off": 119.6, "def": 114.8, "pace": 97.5},
    "Philadelphia 76ers": {"off": 116.8, "def": 115.3, "pace": 99.0},
    "Los Angeles Lakers": {"off": 116.3, "def": 116.2, "pace": 101.1},
}

# --- 3. CALLBACKS ---
def run_analysis_callback():
    url = "https://api.the-odds-api.com/v4/sports/basketball_nba/odds"
    params = {"api_key": "27970d14c8e8eb9f2a217c775db6571f", "regions": "us", "markets": "totals"}
    try:
        res = requests.get(url, params=params)
        if res.status_code == 200:
            st.session_state.game_data = res.json()
    except: st.error("API Connection Error")

if 'game_data' not in st.session_state: st.session_state.game_data = []

# --- 4. CLEAR INSTRUCTION FORMULA ---
def get_betting_instruction(away, home, vegas_line, away_fatigue, home_fatigue):
    a = NBA_STATS.get(away, {"off": 115, "def": 115, "pace": 100})
    h = NBA_STATS.get(home, {"off": 115, "def": 115, "pace": 100})
    
    # Calculate Projected Score
    a_eff = a["off"] - (3.5 if away_fatigue else 0)
    h_eff = h["off"] - (3.5 if home_fatigue else 0)
    matchup_pace = (a["pace"] + h["pace"]) / 2
    
    # Industry Standard: ((Off1 + Def2)/2 + (Off2 + Def1)/2 + HCA) / 100 * Pace
    proj = ((a_eff + h["def"] + h_eff + 2.5 + a["def"]) / 200) * matchup_pace
    
    diff = proj - vegas_line
    
    # DECISIVE INSTRUCTIONS
    if diff > 3.5: # AI expects at least 4 points more than Vegas
        return ("🔥 TAKE THE OVER", proj, 85 + (min(diff, 10) * 1.2))
    elif diff < -3.5: # AI expects at least 4 points less than Vegas
        return ("❄️ TAKE THE UNDER", proj, 85 + (min(abs(diff), 10) * 1.2))
    else:
        return ("🚫 STAY AWAY", proj, 0)

# --- 5. UI ---
st.markdown('<div class="header-container"><div class="graffiti-title-english">NBA SHARP AI</div><div class="graffiti-title-arabic">الرهان الذكي</div></div>', unsafe_allow_html=True)

st.sidebar.markdown("<h1 style='color:#ff4b4b; font-family:\"Aref Ruqaa\"; text-align:center;'>الإعدادات</h1>", unsafe_allow_html=True)
st.button("RUN ANALYSIS - ابدأ التحليل", on_click=run_analysis_callback)

if st.session_state.game_data:
    for game in st.session_state.game_data:
        h, a = game['home_team'], game['away_team']
        try: line = game['bookmakers'][0]['markets'][0]['outcomes'][0]['point']
        except: continue
        
        with st.sidebar.expander(f"Game Context: {a} @ {h}"):
            af = st.checkbox(f"{a} Tired?", key=f"af_{game['id']}")
            hf = st.checkbox(f"{h} Tired?", key=f"hf_{game['id']}")
        
        call, proj, conf = get_betting_instruction(a, h, line, af, hf)
        
        with st.container():
            col1, col2, col3 = st.columns([3, 2, 2])
            with col1:
                st.markdown(f"## {a} vs {h}")
                st.markdown(f"<span style='color:#58a6ff;'>Vegas Line:</span> **{line}**", unsafe_allow_html=True)
            with col2:
                st.metric("AI Prediction", f"{proj:.1f}")
            with col3:
                if "OVER" in call: st.success(call)
                elif "UNDER" in call: st.error(call)
                else: st.info(call)
                if conf > 0: st.caption(f"Confidence: {conf:.1f}%")

st.sidebar.button("WIPE MEMORY", on_click=lambda: st.session_state.update({"game_data": []}))
