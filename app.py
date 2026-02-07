import streamlit as st
import requests
from datetime import datetime

# --- 1. CONFIG & SESSION STATE ---
st.set_page_config(page_title="NBA Sharp AI", page_icon="🏀", layout="wide")

if 'results' not in st.session_state: st.session_state.results = None
if 'injuries' not in st.session_state: st.session_state.injuries = {}

# --- 2. THE RE-CALIBRATED DATA (MID-2026 SEASON) ---
# Efficiency is now "Net Neutral" to stop the Over-inflation.
NBA_STATS = {
    "Atlanta Hawks": {"ppp": 1.11, "opp_ppp": 1.12, "pace": 105.9, "stars": ["Jalen Johnson", "Zaccharie Risacher"]},
    "Boston Celtics": {"ppp": 1.17, "opp_ppp": 1.07, "pace": 99.2, "stars": ["Jayson Tatum", "Jaylen Brown"]},
    "Brooklyn Nets": {"ppp": 1.07, "opp_ppp": 1.15, "pace": 100.1, "stars": ["Cam Thomas", "Nicolas Claxton"]},
    "Charlotte Hornets": {"ppp": 1.13, "opp_ppp": 1.13, "pace": 102.2, "stars": ["LaMelo Ball", "Brandon Miller"]},
    "Chicago Bulls": {"ppp": 1.12, "opp_ppp": 1.14, "pace": 105.1, "stars": ["Josh Giddey", "Coby White"]},
    "Cleveland Cavaliers": {"ppp": 1.14, "opp_ppp": 1.13, "pace": 104.9, "stars": ["Donovan Mitchell", "Evan Mobley"]},
    "Dallas Mavericks": {"ppp": 1.08, "opp_ppp": 1.11, "pace": 103.9, "stars": ["Luka Doncic", "Kyrie Irving"]},
    "Denver Nuggets": {"ppp": 1.18, "opp_ppp": 1.16, "pace": 101.8, "stars": ["Nikola Jokic", "Jamal Murray"]},
    "Detroit Pistons": {"ppp": 1.13, "opp_ppp": 1.10, "pace": 104.4, "stars": ["Cade Cunningham", "Jaden Ivey"]},
    "Golden State Warriors": {"ppp": 1.12, "opp_ppp": 1.13, "pace": 103.9, "stars": ["Stephen Curry", "Buddy Hield"]},
    "Houston Rockets": {"ppp": 1.14, "opp_ppp": 1.10, "pace": 101.1, "stars": ["Alperen Sengun", "Jalen Green"]},
    "Indiana Pacers": {"ppp": 1.07, "opp_ppp": 1.16, "pace": 104.6, "stars": ["Tyrese Haliburton", "Pascal Siakam"]},
    "Los Angeles Clippers": {"ppp": 1.13, "opp_ppp": 1.13, "pace": 99.9, "stars": ["James Harden", "Kawhi Leonard"]},
    "Los Angeles Lakers": {"ppp": 1.15, "opp_ppp": 1.15, "pace": 101.8, "stars": ["LeBron James", "Anthony Davis"]},
    "Memphis Grizzlies": {"ppp": 1.10, "opp_ppp": 1.15, "pace": 105.1, "stars": ["Ja Morant", "Desmond Bane"]},
    "Miami Heat": {"ppp": 1.11, "opp_ppp": 1.12, "pace": 108.0, "stars": ["Jimmy Butler", "Bam Adebayo"]},
    "Milwaukee Bucks": {"ppp": 1.11, "opp_ppp": 1.16, "pace": 101.7, "stars": ["Giannis Antetokounmpo", "Damian Lillard"]},
    "Minnesota Timberwolves": {"ppp": 1.15, "opp_ppp": 1.13, "pace": 104.9, "stars": ["Anthony Edwards", "Rudy Gobert"]},
    "New Orleans Pelicans": {"ppp": 1.10, "opp_ppp": 1.19, "pace": 104.6, "stars": ["Zion Williamson", "Brandon Ingram"]},
    "New York Knicks": {"ppp": 1.17, "opp_ppp": 1.12, "pace": 101.6, "stars": ["Jalen Brunson", "Karl-Anthony Towns"]},
    "Oklahoma City Thunder": {"ppp": 1.16, "opp_ppp": 1.07, "pace": 103.9, "stars": ["Shai Gilgeous-Alexander", "Chet Holmgren"]},
    "Orlando Magic": {"ppp": 1.11, "opp_ppp": 1.11, "pace": 103.9, "stars": ["Paolo Banchero", "Franz Wagner"]},
    "Philadelphia 76ers": {"ppp": 1.13, "opp_ppp": 1.15, "pace": 104.0, "stars": ["Joel Embiid", "Tyrese Maxey"]},
    "Phoenix Suns": {"ppp": 1.12, "opp_ppp": 1.11, "pace": 102.0, "stars": ["Kevin Durant", "Devin Booker"]},
    "Portland Trail Blazers": {"ppp": 1.09, "opp_ppp": 1.16, "pace": 105.3, "stars": ["Anfernee Simons", "Shaedon Sharpe"]},
    "Sacramento Kings": {"ppp": 1.08, "opp_ppp": 1.20, "pace": 103.4, "stars": ["De'Aaron Fox", "Domantas Sabonis"]},
    "San Antonio Spurs": {"ppp": 1.14, "opp_ppp": 1.11, "pace": 103.2, "stars": ["Victor Wembanyama", "Devin Vassell"]},
    "Toronto Raptors": {"ppp": 1.11, "opp_ppp": 1.12, "pace": 102.8, "stars": ["Scottie Barnes", "RJ Barrett"]},
    "Utah Jazz": {"ppp": 1.11, "opp_ppp": 1.20, "pace": 106.5, "stars": ["Lauri Markkanen", "Keyonte George"]},
    "Washington Wizards": {"ppp": 1.08, "opp_ppp": 1.21, "pace": 104.8, "stars": ["Kyle Kuzma", "Alex Sarr"]}
}

# --- 3. THE ANALYTIC ENGINE ---
def run_analysis_vFinal(away, home, line):
    a = NBA_STATS.get(away, {"ppp": 1.1, "opp_ppp": 1.1, "pace": 102.0, "stars": []})
    h = NBA_STATS.get(home, {"ppp": 1.1, "opp_ppp": 1.1, "pace": 102.0, "stars": []})
    
    # Apply Injury Penalties
    a_ppp, h_ppp = a["ppp"], h["ppp"]
    for star in a["stars"]:
        if st.session_state.injuries.get(star) in ["Out", "Doubtful"]: a_ppp -= 0.08
    for star in h["stars"]:
        if st.session_state.injuries.get(star) in ["Out", "Doubtful"]: h_ppp -= 0.08

    # Formula: (Offense + Defense Allowed) / 2 * Pace
    avg_pace = (a["pace"] + h["pace"]) / 2
    proj_a = ((a_ppp + h["opp_ppp"]) / 2) * avg_pace
    proj_h = ((h_ppp + a["opp_ppp"]) / 2) * avg_pace
    
    final_proj = proj_a + proj_h
    diff = final_proj - line
    
    # SHARP FILTER: If the AI and Vegas are too far apart, it's a Trap.
    if abs(diff) > 12: return ("🚫 STAY AWAY", final_proj, "Unreliable Edge (Possible Trap)")
    if diff > 5.5: return ("🔥 TAKE THE OVER", final_proj, f"Confidence: {min(85, 50+(diff*3)):.1f}%")
    if diff < -5.5: return ("❄️ TAKE THE UNDER", final_proj, f"Confidence: {min(85, 50+(abs(diff)*3)):.1f}%")
    
    return ("🚫 STAY AWAY", final_proj, "Line is too Efficient")

# --- 4. CALLBACKS (The Click Fix) ---
def update_data():
    with st.spinner("Fetching Data..."):
        # Odds
        try:
            r = requests.get("https://api.the-odds-api.com/v4/sports/basketball_nba/odds", params={"api_key": "27970d14c8e8eb9f2a217c775db6571f", "regions": "us", "markets": "totals"})
            st.session_state.results = r.json()
        except: st.error("Odds API Error")
        
        # Injuries
        try:
            today = datetime.now().strftime('%Y-%m-%d')
            i = requests.get(f"https://nba-injury-reports.p.rapidapi.com/injuries/{today}", headers={"X-RapidAPI-Key": "55ee678671msh2dd4de4a390207bp10cd2bjsnf77bbbf65916", "X-RapidAPI-Host": "nba-injury-reports.p.rapidapi.com"})
            st.session_state.injuries = {item['player']: item['status'] for item in i.json()}
        except: pass

# --- 5. UI ---
st.title("🏀 NBA SHARP AI")
st.button("RUN ANALYSIS", on_click=update_data)

if st.session_state.results:
    for game in st.session_state.results:
        h, a = game['home_team'], game['away_team']
        try: line = game['bookmakers'][0]['markets'][0]['outcomes'][0]['point']
        except: continue
        
        call, proj, status = run_analysis_vFinal(a, h, line)
        
        with st.expander(f"{a} @ {h}", expanded=True):
            col1, col2 = st.columns(2)
            col1.metric("Vegas Line", line)
            col1.metric("AI Projection", f"{proj:.1f}")
            col2.subheader(call)
            col2.write(status)
