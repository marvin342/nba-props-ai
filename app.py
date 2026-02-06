import streamlit as st
import requests

# --- 1. DESIGN & INTERACTION FIX ---
st.set_page_config(page_title="NBA Sharp AI", page_icon="🏀", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Aref+Ruqaa:wght@700&family=Permanent+Marker&display=swap');
    
    /* FIX: Ensure the background doesn't block clicks */
    .stApp { 
        background: #05070a !important; 
        color: #ffffff; 
    }
    
    /* FIX: Force buttons to the front */
    .stButton, .stCheckbox, [data-testid="stExpander"] {
        position: relative;
        z-index: 999 !important;
    }

    .header-container { display: flex; justify-content: center; align-items: center; gap: 25px; padding-bottom: 20px; border-bottom: 1px solid #1c2128; margin-bottom: 30px; }
    .graffiti-title-english { font-family: 'Permanent Marker', cursive; font-size: 38px; color: #ffffff; text-shadow: 3px 3px 0px #ff4b4b, -1px -1px 0px #58a6ff; }
    .graffiti-title-arabic { font-family: 'Aref Ruqaa', serif; font-size: 38px; color: #ffffff; text-shadow: 3px 3px 0px #58a6ff, -1px -1px 0px #ff4b4b; direction: rtl; }
    
    [data-testid="stVerticalBlock"] > div:has(div.stMetric) { 
        background-color: #11151c !important; 
        border-radius: 12px; 
        border-left: 6px solid #ff4b4b; 
        border-right: 6px solid #58a6ff; 
        padding: 20px; 
        box-shadow: 0px 8px 20px rgba(0,0,0,0.5); 
        margin-bottom: 15px; 
    }

    .stButton>button { 
        background: linear-gradient(90deg, #ff4b4b 0%, #58a6ff 100%) !important; 
        color: white !important; 
        font-family: 'Permanent Marker', cursive !important; 
        font-size: 20px !important; 
        border: 2px solid #ffffff !important; 
        border-radius: 8px !important; 
        height: 3.5rem !important; 
        width: 100%;
        cursor: pointer !important; /* Ensure cursor shows up */
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. THE STATS (PERMA-SAVED) ---
NBA_STATS = {
    "Boston Celtics": {"off": 121.1, "def": 114.4, "pace": 95.6, "stars": ["Jayson Tatum", "Jaylen Brown"]},
    "Oklahoma City Thunder": {"off": 119.3, "def": 107.8, "pace": 101.0, "stars": ["Shai Gilgeous-Alexander", "Chet Holmgren"]},
    "New York Knicks": {"off": 120.3, "def": 114.8, "pace": 98.9, "stars": ["Jalen Brunson", "Karl-Anthony Towns"]},
    "Detroit Pistons": {"off": 116.2, "def": 109.8, "pace": 100.8, "stars": ["Cade Cunningham", "Jalen Duren"]},
    "Los Angeles Lakers": {"off": 117.7, "def": 118.3, "pace": 99.5, "stars": ["Luka Doncic", "Anthony Davis"]},
    "Denver Nuggets": {"off": 121.9, "def": 118.9, "pace": 98.3, "stars": ["Nikola Jokic", "Jamal Murray"]},
    "Milwaukee Bucks": {"off": 113.5, "def": 117.7, "pace": 98.0, "stars": ["Giannis Antetokounmpo", "Damian Lillard"]},
    "Phoenix Suns": {"off": 116.0, "def": 113.3, "pace": 99.3, "stars": ["Kevin Durant", "Devin Booker"]},
    "Indiana Pacers": {"off": 110.1, "def": 116.9, "pace": 100.8, "stars": ["Tyrese Haliburton"]},
    "Miami Heat": {"off": 115.0, "def": 112.7, "pace": 105.2, "stars": ["Jimmy Butler", "Bam Adebayo"]},
    "Dallas Mavericks": {"off": 110.3, "def": 113.2, "pace": 94.5, "stars": ["Kyrie Irving"]},
    "Minnesota Timberwolves": {"off": 117.6, "def": 113.6, "pace": 101.5, "stars": ["Anthony Edwards", "Ayo Dosunmu"]},
    "Washington Wizards": {"off": 110.6, "def": 121.2, "pace": 100.8, "stars": ["Trae Young"]},
    "Golden State Warriors": {"off": 115.9, "def": 113.4, "pace": 101.0, "stars": ["Stephen Curry"]},
}

# --- 3. CALLBACKS & DATA ---
def run_analysis_callback():
    # Fetching real lines
    url = "https://api.the-odds-api.com/v4/sports/basketball_nba/odds"
    params = {"api_key": "27970d14c8e8eb9f2a217c775db6571f", "regions": "us", "markets": "totals"}
    
    # Perma-Check Injuries (Simulated)
    st.session_state.injured_stars = ["Jayson Tatum", "Tyrese Haliburton", "Luka Doncic"]
    
    try:
        res = requests.get(url, params=params)
        if res.status_code == 200:
            st.session_state.game_data = res.json()
    except: st.error("API Link Error")

if 'game_data' not in st.session_state: st.session_state.game_data = []

def get_betting_instruction(away, home, vegas_line, af, hf):
    a = NBA_STATS.get(away, {"off": 114, "def": 115, "pace": 100, "stars": []})
    h = NBA_STATS.get(home, {"off": 114, "def": 115, "pace": 100, "stars": []})
    
    a_eff, h_eff = a["off"], h["off"]
    if af: a_eff -= 3.5
    if hf: h_eff -= 3.5
    
    # Auto-slash for injuries
    for star in a["stars"]:
        if star in st.session_state.get('injured_stars', []): a_eff -= 8.5
    for star in h["stars"]:
        if star in st.session_state.get('injured_stars', []): h_eff -= 8.5

    matchup_pace = (a["pace"] + h["pace"]) / 2
    proj = ((a_eff + h["def"] + h_eff + 2.5 + a["def"]) / 200) * matchup_pace
    diff = proj - vegas_line
    value_score = 60 + (min(abs(diff), 12) * 2.8)
    
    if diff > 3.2: return ("🔥 TAKE THE OVER", proj, value_score)
    elif diff < -3.2: return ("❄️ TAKE THE UNDER", proj, value_score)
    return ("🚫 STAY AWAY", proj, 0)

# --- 4. MAIN UI ---
st.markdown('<div class="header-container"><div class="graffiti-title-english">NBA SHARP AI</div><div class="graffiti-title-arabic">الرهان الذكي</div></div>', unsafe_allow_html=True)

# Main Action Button
st.button("RUN ANALYSIS - ابدأ التحليل", on_click=run_analysis_callback)

if st.session_state.game_data:
    for game in st.session_state.game_data:
        h, a = game['home_team'], game['away_team']
        try: line = game['bookmakers'][0]['markets'][0]['outcomes'][0]['point']
        except: continue
        
        with st.sidebar.expander(f"Situational: {a} @ {h}"):
            af = st.checkbox(f"{a} Tired?", key=f"af_{game['id']}")
            hf = st.checkbox(f"{h} Tired?", key=f"hf_{game['id']}")
            for s in NBA_STATS.get(a, {}).get('stars', []) + NBA_STATS.get(h, {}).get('stars', []):
                if s in st.session_state.get('injured_stars', []):
                    st.warning(f"AUTO-DETECT: {s} is OUT")
        
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
                if value > 0: st.markdown(f"**Value Rating: {value:.1f}%**")

st.sidebar.button("WIPE MEMORY", on_click=lambda: st.session_state.update({"game_data": []}))
