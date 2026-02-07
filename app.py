import streamlit as st
import requests
from datetime import datetime

# --- 1. CONFIG & SESSION STATE ---
st.set_page_config(page_title="NBA Sharp AI", page_icon="🏀", layout="wide")

# Initialize session state so results don't vanish on click
if 'results' not in st.session_state: st.session_state.results = None
if 'injuries' not in st.session_state: st.session_state.injuries = {}

# --- 2. UPDATED TEAM STATS (MID-SEASON 2026) ---
# Efficiency adjusted to prevent the "All Overs" bug.
NBA_STATS = {
    "Atlanta Hawks": {"ppp": 1.12, "opp_ppp": 1.13, "pace": 105.9, "stars": ["Jalen Johnson", "Zaccharie Risacher"]},
    "Boston Celtics": {"ppp": 1.21, "opp_ppp": 1.10, "pace": 95.3, "stars": ["Jayson Tatum", "Jaylen Brown"]},
    "Brooklyn Nets": {"ppp": 1.07, "opp_ppp": 1.16, "pace": 97.8, "stars": ["Cam Thomas", "Nicolas Claxton"]},
    "Charlotte Hornets": {"ppp": 1.13, "opp_ppp": 1.13, "pace": 101.5, "stars": ["LaMelo Ball", "Brandon Miller"]},
    "Chicago Bulls": {"ppp": 1.13, "opp_ppp": 1.14, "pace": 103.3, "stars": ["Josh Giddey", "Coby White"]},
    "Cleveland Cavaliers": {"ppp": 1.18, "opp_ppp": 1.11, "pace": 101.0, "stars": ["Donovan Mitchell", "Evan Mobley"]},
    "Dallas Mavericks": {"ppp": 1.14, "opp_ppp": 1.11, "pace": 100.1, "stars": ["Luka Doncic", "Kyrie Irving"]},
    "Denver Nuggets": {"ppp": 1.20, "opp_ppp": 1.15, "pace": 99.0, "stars": ["Nikola Jokic", "Jamal Murray"]},
    "Detroit Pistons": {"ppp": 1.17, "opp_ppp": 1.07, "pace": 100.1, "stars": ["Cade Cunningham", "Jaden Ivey"]},
    "Golden State Warriors": {"ppp": 1.15, "opp_ppp": 1.11, "pace": 100.8, "stars": ["Stephen Curry", "Buddy Hield"]},
    "Houston Rockets": {"ppp": 1.15, "opp_ppp": 1.10, "pace": 101.1, "stars": ["Alperen Sengun", "Jalen Green"]},
    "Indiana Pacers": {"ppp": 1.11, "opp_ppp": 1.14, "pace": 100.1, "stars": ["Tyrese Haliburton", "Pascal Siakam"]},
    "Los Angeles Clippers": {"ppp": 1.12, "opp_ppp": 1.14, "pace": 99.5, "stars": ["James Harden", "Kawhi Leonard"]},
    "Los Angeles Lakers": {"ppp": 1.16, "opp_ppp": 1.15, "pace": 98.8, "stars": ["LeBron James", "Anthony Davis"]},
    "Memphis Grizzlies": {"ppp": 1.14, "opp_ppp": 1.12, "pace": 102.1, "stars": ["Ja Morant", "Desmond Bane"]},
    "Miami Heat": {"ppp": 1.17, "opp_ppp": 1.10, "pace": 100.0, "stars": ["Jimmy Butler", "Bam Adebayo"]},
    "Milwaukee Bucks": {"ppp": 1.12, "opp_ppp": 1.14, "pace": 101.0, "stars": ["Giannis Antetokounmpo", "Damian Lillard"]},
    "Minnesota Timberwolves": {"ppp": 1.19, "opp_ppp": 1.10, "pace": 102.5, "stars": ["Anthony Edwards", "Rudy Gobert"]},
    "New Orleans Pelicans": {"ppp": 1.14, "opp_ppp": 1.21, "pace": 101.8, "stars": ["Zion Williamson", "Brandon Ingram"]},
    "New York Knicks": {"ppp": 1.20, "opp_ppp": 1.11, "pace": 98.2, "stars": ["Jalen Brunson", "Karl-Anthony Towns"]},
    "Oklahoma City Thunder": {"ppp": 1.20, "opp_ppp": 1.04, "pace": 101.5, "stars": ["Shai Gilgeous-Alexander", "Chet Holmgren"]},
    "Orlando Magic": {"ppp": 1.15, "opp_ppp": 1.12, "pace": 101.2, "stars": ["Paolo Banchero", "Franz Wagner"]},
    "Philadelphia 76ers": {"ppp": 1.16, "opp_ppp": 1.11, "pace": 100.3, "stars": ["Joel Embiid", "Tyrese Maxey"]},
    "Phoenix Suns": {"ppp": 1.13, "opp_ppp": 1.10, "pace": 100.2, "stars": ["Kevin Durant", "Devin Booker"]},
    "Portland Trail Blazers": {"ppp": 1.15, "opp_ppp": 1.13, "pace": 102.0, "stars": ["Anfernee Simons", "Shaedon Sharpe"]},
    "Sacramento Kings": {"ppp": 1.10, "opp_ppp": 1.17, "pace": 101.8, "stars": ["De'Aaron Fox", "Domantas Sabonis"]},
    "San Antonio Spurs": {"ppp": 1.17, "opp_ppp": 1.09, "pace": 95.4, "stars": ["Victor Wembanyama", "Devin Vassell"]},
    "Toronto Raptors": {"ppp": 1.14, "opp_ppp": 1.10, "pace": 101.8, "stars": ["Scottie Barnes", "RJ Barrett"]},
    "Utah Jazz": {"ppp": 1.18, "opp_ppp": 1.20, "pace": 104.5, "stars": ["Lauri Markkanen", "Keyonte George"]},
    "Washington Wizards": {"ppp": 1.12, "opp_ppp": 1.18, "pace": 106.8, "stars": ["Kyle Kuzma", "Alex Sarr"]}
}

# --- 3. THE ANALYTIC ENGINE ---
def run_sharp_analysis(away, home, line):
    a = NBA_STATS.get(away, {"ppp": 1.1, "opp_ppp": 1.1, "pace": 100.0, "stars": []})
    h = NBA_STATS.get(home, {"ppp": 1.1, "opp_ppp": 1.1, "pace": 100.0, "stars": []})
    
    a_ppp, h_ppp = a["ppp"], h["ppp"]
    
    # 🩹 LIVE INJURY TAX
    for star in a["stars"]:
        status = st.session_state.injuries.get(star, "Available")
        if status in ["Out", "Doubtful"]: a_ppp -= 0.08
        elif status == "Questionable": a_ppp -= 0.04
    for star in h["stars"]:
        status = st.session_state.injuries.get(star, "Available")
        if status in ["Out", "Doubtful"]: h_ppp -= 0.08
        elif status == "Questionable": h_ppp -= 0.04

    # 🧮 FORMULA (PPP * PACE)
    avg_pace = (a["pace"] + h["pace"]) / 2
    proj_a = ((a_ppp + h["opp_ppp"]) / 2) * avg_pace
    proj_h = (((h_ppp + 0.015) + a["opp_ppp"]) / 2) * avg_pace # Home Court Advantage
    
    final_proj = proj_a + proj_h
    diff = final_proj - line
    
    # 🚨 SKEPTICAL FILTER (No Edge, Trap, or Bet)
    if abs(diff) > 12: 
        return ("🚫 STAY AWAY", final_proj, "Unreliable Edge (Trap Line)", "#808080")
    if diff > 6.0: 
        edge = min(15.0, diff)
        return ("🔥 OVER", final_proj, f"Projected Edge: +{edge:.1f}%", "#2ecc71")
    if diff < -6.0: 
        edge = min(15.0, abs(diff))
        return ("❄️ UNDER", final_proj, f"Projected Edge: +{edge:.1f}%", "#e74c3c")
    
    return ("🚫 STAY AWAY", final_proj, "Line is too Efficient", "#3498db")

# --- 4. CALLBACK FOR DATA SYNC ---
def sync_live_data():
    with st.spinner("Fetching Live Hospital & Vegas Feeds..."):
        # 🏥 Injury Feed
        today = datetime.now().strftime('%Y-%m-%d')
        inj_url = f"https://nba-injury-reports.p.rapidapi.com/injuries/{today}"
        headers = {"X-RapidAPI-Key": "55ee678671msh2dd4de4a390207bp10cd2bjsnf77bbbf65916", "X-RapidAPI-Host": "nba-injury-reports.p.rapidapi.com"}
        try:
            i_res = requests.get(inj_url, headers=headers)
            if i_res.status_code == 200:
                st.session_state.injuries = {item['player']: item['status'] for item in i_res.json()}
        except: pass

        # 🎰 Odds Feed
        try:
            o_res = requests.get("https://api.the-odds-api.com/v4/sports/basketball_nba/odds", 
                               params={"api_key": "27970d14c8e8eb9f2a217c775db6571f", "regions": "us", "markets": "totals"})
            if o_res.status_code == 200:
                st.session_state.results = o_res.json()
        except: st.error("Vegas API Down")

# --- 5. UI DISPLAY ---
st.title("🏀 NBA SHARP AI")
st.button("REFRESH ANALYSIS", on_click=sync_live_data)

if st.session_state.results:
    for game in st.session_state.results:
        h, a = game['home_team'], game['away_team']
        try: line = game['bookmakers'][0]['markets'][0]['outcomes'][0]['point']
        except: continue
        
        call, proj, status, color = run_sharp_analysis(a, h, line)
        
        st.markdown(f"""
            <div style="border: 1px solid #1c2128; padding: 20px; border-radius: 10px; margin-bottom: 15px; border-left: 10px solid {color}; background: #0d1117;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <h3 style="margin: 0; color: white;">{a} @ {h}</h3>
                        <p style="margin: 5px 0; color: #8b949e;">Vegas: {line} | AI Projection: <b>{proj:.1f}</b></p>
                    </div>
                    <div style="text-align: right;">
                        <h2 style="margin: 0; color: {color};">{call}</h2>
                        <p style="margin: 0; color: #8b949e; font-weight: bold;">{status}</p>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)
