import streamlit as st
import requests
from datetime import datetime

# --- 1. DESIGN & STYLE ---
st.set_page_config(page_title="NBA Sharp AI", page_icon="🏀", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Aref+Ruqaa:wght@700&family=Permanent+Marker&display=swap');
    .stApp { background: #05070a !important; color: #ffffff; }
    .header-container { display: flex; justify-content: center; align-items: center; gap: 25px; padding-bottom: 20px; border-bottom: 1px solid #1c2128; margin-bottom: 30px; }
    .graffiti-title-english { font-family: 'Permanent Marker', cursive; font-size: 38px; color: #ffffff; text-shadow: 3px 3px 0px #ff4b4b, -1px -1px 0px #58a6ff; }
    .graffiti-title-arabic { font-family: 'Aref Ruqaa', serif; font-size: 38px; color: #ffffff; text-shadow: 3px 3px 0px #58a6ff, -1px -1px 0px #ff4b4b; direction: rtl; }
    .stButton>button { 
        background: linear-gradient(90deg, #ff4b4b 0%, #58a6ff 100%) !important; 
        color: white !important; font-family: 'Permanent Marker', cursive !important; 
        font-size: 20px !important; border: 2px solid #ffffff !important; border-radius: 8px !important; 
        height: 3.5rem !important; width: 100%; cursor: pointer !important; 
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. THE FULL 30-TEAM DATABASE (2026 UPDATED) ---
NBA_STATS = {
    "Atlanta Hawks": {"off": 114.6, "def": 115.0, "pace": 105.9, "stars": ["Jalen Johnson", "Zaccharie Risacher"]},
    "Boston Celtics": {"off": 121.0, "def": 114.4, "pace": 99.2, "stars": ["Jayson Tatum", "Jaylen Brown", "Kristaps Porzingis"]},
    "Brooklyn Nets": {"off": 110.3, "def": 118.4, "pace": 100.1, "stars": ["Cam Thomas", "Nicolas Claxton"]},
    "Charlotte Hornets": {"off": 117.4, "def": 116.0, "pace": 102.2, "stars": ["LaMelo Ball", "Brandon Miller"]},
    "Chicago Bulls": {"off": 114.6, "def": 118.3, "pace": 105.1, "stars": ["Josh Giddey", "Coby White"]},
    "Cleveland Cavaliers": {"off": 117.9, "def": 114.2, "pace": 104.9, "stars": ["Donovan Mitchell", "Evan Mobley", "Darius Garland"]},
    "Dallas Mavericks": {"off": 110.5, "def": 113.5, "pace": 105.9, "stars": ["Luka Doncic", "Kyrie Irving"]},
    "Denver Nuggets": {"off": 121.9, "def": 118.9, "pace": 101.8, "stars": ["Nikola Jokic", "Jamal Murray"]},
    "Detroit Pistons": {"off": 116.1, "def": 110.1, "pace": 104.4, "stars": ["Cade Cunningham", "Jaden Ivey"]},
    "Golden State Warriors": {"off": 115.9, "def": 113.3, "pace": 103.9, "stars": ["Stephen Curry", "Jonathan Kuminga"]},
    "Houston Rockets": {"off": 118.4, "def": 113.5, "pace": 101.1, "stars": ["Alperen Sengun", "Jalen Green"]},
    "Indiana Pacers": {"off": 110.1, "def": 116.9, "pace": 104.6, "stars": ["Tyrese Haliburton", "Pascal Siakam"]},
    "Los Angeles Clippers": {"off": 116.7, "def": 117.2, "pace": 99.9, "stars": ["James Harden", "Kawhi Leonard"]},
    "Los Angeles Lakers": {"off": 117.7, "def": 118.2, "pace": 101.8, "stars": ["LeBron James", "Anthony Davis"]},
    "Memphis Grizzlies": {"off": 113.5, "def": 115.2, "pace": 105.1, "stars": ["Ja Morant", "Desmond Bane", "Jaren Jackson Jr."]},
    "Miami Heat": {"off": 114.9, "def": 112.7, "pace": 108.0, "stars": ["Jimmy Butler", "Bam Adebayo"]},
    "Milwaukee Bucks": {"off": 113.5, "def": 117.7, "pace": 101.7, "stars": ["Giannis Antetokounmpo", "Damian Lillard"]},
    "Minnesota Timberwolves": {"off": 117.6, "def": 113.6, "pace": 104.9, "stars": ["Anthony Edwards", "Rudy Gobert"]},
    "New Orleans Pelicans": {"off": 114.0, "def": 119.8, "pace": 104.6, "stars": ["Zion Williamson", "Brandon Ingram"]},
    "New York Knicks": {"off": 120.3, "def": 114.8, "pace": 101.6, "stars": ["Jalen Brunson", "Karl-Anthony Towns"]},
    "Oklahoma City Thunder": {"off": 119.3, "def": 107.8, "pace": 103.9, "stars": ["Shai Gilgeous-Alexander", "Chet Holmgren"]},
    "Orlando Magic": {"off": 114.8, "def": 114.9, "pace": 103.9, "stars": ["Paolo Banchero", "Franz Wagner"]},
    "Philadelphia 76ers": {"off": 116.6, "def": 115.3, "pace": 104.0, "stars": ["Joel Embiid", "Tyrese Maxey"]},
    "Phoenix Suns": {"off": 115.9, "def": 113.3, "pace": 102.0, "stars": ["Kevin Durant", "Devin Booker"]},
    "Portland Trail Blazers": {"off": 114.5, "def": 116.1, "pace": 105.3, "stars": ["Anfernee Simons", "Shaedon Sharpe"]},
    "Sacramento Kings": {"off": 110.5, "def": 120.5, "pace": 103.4, "stars": ["De'Aaron Fox", "Domantas Sabonis"]},
    "San Antonio Spurs": {"off": 117.2, "def": 111.8, "pace": 103.2, "stars": ["Victor Wembanyama", "Devin Vassell"]},
    "Toronto Raptors": {"off": 114.6, "def": 113.4, "pace": 102.8, "stars": ["Scottie Barnes", "RJ Barrett"]},
    "Utah Jazz": {"off": 116.0, "def": 123.4, "pace": 106.5, "stars": ["Lauri Markkanen", "Keyonte George"]},
    "Washington Wizards": {"off": 110.1, "def": 116.9, "pace": 104.8, "stars": ["Trae Young", "Anthony Davis"]}
}

# --- 3. LIVE API SYNC ---
RAPID_API_KEY = "55ee678671msh2dd4de4a390207bp10cd2bjsnf77bbbf65916"

def get_live_injury_data():
    today = datetime.now().strftime('%Y-%m-%d')
    url = f"https://nba-injury-reports.p.rapidapi.com/injuries/{today}"
    headers = {"X-RapidAPI-Key": RAPID_API_KEY, "X-RapidAPI-Host": "nba-injury-reports.p.rapidapi.com"}
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return {item['player']: item['status'] for item in response.json()}
    except: return {}
    return {}

# --- 4. ENGINE LOGIC ---
def analyze_game(away, home, vegas_line):
    a = NBA_STATS.get(away, {"off": 114, "def": 115, "pace": 100, "stars": []})
    h = NBA_STATS.get(home, {"off": 114, "def": 115, "pace": 100, "stars": []})
    
    a_eff, h_eff = a["off"], h["off"]
    live_report = st.session_state.get('live_report', {})
    shaky = []

    for team_data, eff, side in [(a, a_eff, "Away"), (h, h_eff, "Home")]:
        for star in team_data["stars"]:
            status = live_report.get(star, "Available")
            if status in ["Out", "Doubtful"]:
                if side == "Away": a_eff -= 8.5
                else: h_eff -= 8.5
                shaky.append(f"{star} ({status})")
            elif status == "Questionable":
                if side == "Away": a_eff -= 4.5
                else: h_eff -= 4.5
                shaky.append(f"{star} ({status})")

    if len(shaky) >= 2:
        return ("🚫 STAY AWAY", 0, 0, f"⚠️ ROSTER COLLAPSE: {', '.join(shaky)}")

    pace = (a["pace"] + h["pace"]) / 2
    proj = ((a_eff + h["def"] + h_eff + 2.5 + a["def"]) / 200) * pace
    diff = proj - vegas_line
    value = 60 + (min(abs(diff), 12) * 2.8)
    
    if diff > 3.5: return ("🔥 TAKE THE OVER", proj, value, None)
    elif diff < -3.5: return ("❄️ TAKE THE UNDER", proj, value, None)
    return ("🚫 STAY AWAY", proj, 0, None)

# --- 5. MAIN UI ---
st.markdown('<div class="header-container"><div class="graffiti-title-english">NBA SHARP AI</div><div class="graffiti-title-arabic">الرهان الذكي</div></div>', unsafe_allow_html=True)

if st.button("RUN ANALYSIS - ابدأ التحليل"):
    st.session_state.live_report = get_live_injury_data()
    odds_url = "https://api.the-odds-api.com/v4/sports/basketball_nba/odds"
    params = {"api_key": "27970d14c8e8eb9f2a217c775db6571f", "regions": "us", "markets": "totals"}
    try:
        res = requests.get(odds_url, params=params)
        if res.status_code == 200: st.session_state.game_data = res.json()
    except: st.error("Odds API Down")

if 'game_data' in st.session_state:
    for game in st.session_state['game_data']:
        h, a = game['home_team'], game['away_team']
        try: line = game['bookmakers'][0]['markets'][0]['outcomes'][0]['point']
        except: continue
        
        call, proj, value, alert = analyze_game(a, h, line)
        
        with st.container():
            c1, c2, c3 = st.columns([3, 2, 2])
            with c1:
                st.markdown(f"### {a} @ {h}")
                st.caption(f"Vegas: {line}")
                if alert: st.warning(alert)
            with c2:
                st.metric("AI Projection", f"{proj:.1f}" if proj > 0 else "N/A")
            with c3:
                if "OVER" in call: st.success(call)
                elif "UNDER" in call: st.error(call)
                else: st.info(call)
                if value > 0: st.write(f"Confidence: {value:.1f}%")
