import streamlit as st
import requests
from datetime import datetime

# --- 1. DESIGN ---
st.set_page_config(page_title="NBA Sharp AI", page_icon="🏀", layout="wide")
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Aref+Ruqaa:wght@700&family=Permanent+Marker&display=swap');
    .stApp { background: #05070a !important; color: #ffffff; }
    .header-container { display: flex; justify-content: center; align-items: center; gap: 25px; padding-bottom: 20px; border-bottom: 1px solid #1c2128; margin-bottom: 30px; }
    .graffiti-title-english { font-family: 'Permanent Marker', cursive; font-size: 38px; color: #ffffff; text-shadow: 3px 3px 0px #ff4b4b, -1px -1px 0px #58a6ff; }
    .graffiti-title-arabic { font-family: 'Aref Ruqaa', serif; font-size: 38px; color: #ffffff; text-shadow: 3px 3px 0px #58a6ff, -1px -1px 0px #ff4b4b; direction: rtl; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. THE RECALIBRATED STATS (2026 REAL-TIME) ---
# Efficiency is now expressed as Net PPP (Points Per Possession)
NBA_STATS = {
    "Atlanta Hawks": {"ppp": 1.14, "opp_ppp": 1.15, "pace": 105.9, "stars": ["Jalen Johnson", "Zaccharie Risacher"]},
    "Boston Celtics": {"ppp": 1.21, "opp_ppp": 1.11, "pace": 99.2, "stars": ["Jayson Tatum", "Jaylen Brown", "Kristaps Porzingis"]},
    "Brooklyn Nets": {"ppp": 1.07, "opp_ppp": 1.15, "pace": 100.1, "stars": ["Cam Thomas", "Nicolas Claxton"]},
    "Charlotte Hornets": {"ppp": 1.15, "opp_ppp": 1.14, "pace": 102.2, "stars": ["LaMelo Ball", "Brandon Miller"]},
    "Chicago Bulls": {"ppp": 1.13, "opp_ppp": 1.17, "pace": 105.1, "stars": ["Josh Giddey", "Coby White"]},
    "Cleveland Cavaliers": {"ppp": 1.18, "opp_ppp": 1.14, "pace": 104.9, "stars": ["Donovan Mitchell", "Evan Mobley"]},
    "Dallas Mavericks": {"ppp": 1.12, "opp_ppp": 1.13, "pace": 103.9, "stars": ["Luka Doncic", "Kyrie Irving"]},
    "Denver Nuggets": {"ppp": 1.21, "opp_ppp": 1.18, "pace": 101.8, "stars": ["Nikola Jokic", "Jamal Murray"]},
    "Detroit Pistons": {"ppp": 1.16, "opp_ppp": 1.10, "pace": 104.4, "stars": ["Cade Cunningham", "Jaden Ivey"]},
    "Golden State Warriors": {"ppp": 1.15, "opp_ppp": 1.13, "pace": 103.9, "stars": ["Stephen Curry", "Buddy Hield"]},
    "Houston Rockets": {"ppp": 1.18, "opp_ppp": 1.13, "pace": 101.1, "stars": ["Alperen Sengun", "Jalen Green"]},
    "Indiana Pacers": {"ppp": 1.10, "opp_ppp": 1.16, "pace": 104.6, "stars": ["Tyrese Haliburton", "Pascal Siakam"]},
    "Los Angeles Clippers": {"ppp": 1.16, "opp_ppp": 1.17, "pace": 99.9, "stars": ["James Harden", "Kawhi Leonard"]},
    "Los Angeles Lakers": {"ppp": 1.17, "opp_ppp": 1.18, "pace": 101.8, "stars": ["LeBron James", "Anthony Davis"]},
    "Memphis Grizzlies": {"ppp": 1.13, "opp_ppp": 1.15, "pace": 105.1, "stars": ["Ja Morant", "Desmond Bane"]},
    "Miami Heat": {"ppp": 1.16, "opp_ppp": 1.12, "pace": 108.0, "stars": ["Jimmy Butler", "Bam Adebayo"]},
    "Milwaukee Bucks": {"ppp": 1.13, "opp_ppp": 1.17, "pace": 101.7, "stars": ["Giannis Antetokounmpo", "Damian Lillard"]},
    "Minnesota Timberwolves": {"ppp": 1.18, "opp_ppp": 1.13, "pace": 104.9, "stars": ["Anthony Edwards", "Rudy Gobert"]},
    "New Orleans Pelicans": {"ppp": 1.14, "opp_ppp": 1.19, "pace": 104.6, "stars": ["Zion Williamson", "Brandon Ingram"]},
    "New York Knicks": {"ppp": 1.20, "opp_ppp": 1.14, "pace": 101.6, "stars": ["Jalen Brunson", "Karl-Anthony Towns"]},
    "Oklahoma City Thunder": {"ppp": 1.19, "opp_ppp": 1.07, "pace": 103.9, "stars": ["Shai Gilgeous-Alexander", "Chet Holmgren"]},
    "Orlando Magic": {"ppp": 1.14, "opp_ppp": 1.14, "pace": 103.9, "stars": ["Paolo Banchero", "Franz Wagner"]},
    "Philadelphia 76ers": {"ppp": 1.16, "opp_ppp": 1.15, "pace": 104.0, "stars": ["Joel Embiid", "Tyrese Maxey"]},
    "Phoenix Suns": {"ppp": 1.15, "opp_ppp": 1.13, "pace": 102.0, "stars": ["Kevin Durant", "Devin Booker"]},
    "Portland Trail Blazers": {"ppp": 1.14, "opp_ppp": 1.16, "pace": 105.3, "stars": ["Anfernee Simons", "Shaedon Sharpe"]},
    "Sacramento Kings": {"ppp": 1.10, "opp_ppp": 1.20, "pace": 103.4, "stars": ["De'Aaron Fox", "Domantas Sabonis"]},
    "San Antonio Spurs": {"ppp": 1.17, "opp_ppp": 1.11, "pace": 103.2, "stars": ["Victor Wembanyama", "Devin Vassell"]},
    "Toronto Raptors": {"ppp": 1.14, "opp_ppp": 1.13, "pace": 102.8, "stars": ["Scottie Barnes", "RJ Barrett"]},
    "Utah Jazz": {"ppp": 1.15, "opp_ppp": 1.23, "pace": 106.5, "stars": ["Lauri Markkanen", "Keyonte George"]},
    "Washington Wizards": {"ppp": 1.12, "opp_ppp": 1.21, "pace": 104.8, "stars": ["Kyle Kuzma", "Alex Sarr"]}
}

# --- 3. LIVE SYNC ---
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

# --- 4. THE RE-TUNED ENGINE ---
def analyze_game(away, home, vegas_line):
    # Default stats if team not found
    a = NBA_STATS.get(away, {"ppp": 1.12, "opp_ppp": 1.12, "pace": 102.0, "stars": []})
    h = NBA_STATS.get(home, {"ppp": 1.12, "opp_ppp": 1.12, "pace": 102.0, "stars": []})
    
    a_ppp, h_ppp = a["ppp"], h["ppp"]
    live_report = st.session_state.get('live_report', {})
    shaky = []

    # Apply Injury Penalties to PPP
    for team_data, side in [(a, "Away"), (h, "Home")]:
        for star in team_data["stars"]:
            status = live_report.get(star, "Available")
            if status in ["Out", "Doubtful"]:
                if side == "Away": a_ppp -= 0.08  # ~8 point drop per game
                else: h_ppp -= 0.08
                shaky.append(f"{star} ({status})")
            elif status == "Questionable":
                if side == "Away": a_ppp -= 0.04  # ~4 point drop per game
                else: h_ppp -= 0.04
                shaky.append(f"{star} ({status})")

    if len(shaky) >= 2:
        return ("🚫 STAY AWAY", 0, 0, f"⚠️ ROSTER COLLAPSE: {', '.join(shaky)}")

    # THE NEW PPP FORMULA
    # Projected Score = ((Team A Offense + Team B Defense Allowed) / 2) * Pace
    avg_pace = (a["pace"] + h["pace"]) / 2
    proj_a = ((a_ppp + h["opp_ppp"]) / 2) * avg_pace
    proj_h = (((h_ppp + 0.02) + a["opp_ppp"]) / 2) * avg_pace # +0.02 for Home Court Advantage
    
    final_proj = proj_a + proj_h
    diff = final_proj - vegas_line
    
    # Value calculation is now much tighter
    value = 50 + (min(abs(diff), 15) * 3) 
    
    if diff > 4.5: return ("🔥 TAKE THE OVER", final_proj, value, None)
    elif diff < -4.5: return ("❄️ TAKE THE UNDER", final_proj, value, None)
    return ("🚫 STAY AWAY", final_proj, 0, None)

# --- 5. MAIN UI ---
st.markdown('<div class="header-container"><div class="graffiti-title-english">NBA SHARP AI</div><div class="graffiti-title-arabic">الرهان الذكي</div></div>', unsafe_allow_html=True)

if st.button("RUN LIVE ANALYSIS"):
    with st.spinner("Checking Hospital Reports & Odds..."):
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
                st.caption(f"Vegas Line: {line}")
                if alert: st.warning(alert)
            with c2:
                st.metric("AI Projection", f"{proj:.1f}")
            with c3:
                if "OVER" in call: st.success(call)
                elif "UNDER" in call: st.error(call)
                else: st.info(call)
                if value > 0: st.write(f"Confidence: {value:.1f}%")
