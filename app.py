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
    </style>
    """, unsafe_allow_html=True)

# --- 2. RE-CALIBRATED PPP (FEB 2026 DEFENSIVE UPDATE) ---
# opp_ppp (Opponent Points Per Possession) has been raised to reflect mid-season defensive adjustments.
NBA_STATS = {
    "Atlanta Hawks": {"ppp": 1.14, "opp_ppp": 1.18, "pace": 102.6, "stars": ["Jalen Johnson", "Zaccharie Risacher"]},
    "Boston Celtics": {"ppp": 1.16, "opp_ppp": 1.08, "pace": 96.4, "stars": ["Jayson Tatum", "Jaylen Brown"]},
    "Brooklyn Nets": {"ppp": 1.06, "opp_ppp": 1.15, "pace": 100.3, "stars": ["Cam Thomas", "Nicolas Claxton"]},
    "Charlotte Hornets": {"ppp": 1.13, "opp_ppp": 1.14, "pace": 101.5, "stars": ["LaMelo Ball", "Brandon Miller"]},
    "Chicago Bulls": {"ppp": 1.13, "opp_ppp": 1.19, "pace": 103.3, "stars": ["Josh Giddey", "Coby White"]},
    "Cleveland Cavaliers": {"ppp": 1.18, "opp_ppp": 1.15, "pace": 101.0, "stars": ["Donovan Mitchell", "Evan Mobley"]},
    "Dallas Mavericks": {"ppp": 1.12, "opp_ppp": 1.16, "pace": 100.1, "stars": ["Luka Doncic", "Kyrie Irving"]},
    "Denver Nuggets": {"ppp": 1.21, "opp_ppp": 1.16, "pace": 99.0, "stars": ["Nikola Jokic", "Jamal Murray"]},
    "Detroit Pistons": {"ppp": 1.17, "opp_ppp": 1.10, "pace": 100.1, "stars": ["Cade Cunningham", "Jaden Ivey"]},
    "Golden State Warriors": {"ppp": 1.14, "opp_ppp": 1.13, "pace": 100.8, "stars": ["Stephen Curry", "Buddy Hield"]},
    "Houston Rockets": {"ppp": 1.15, "opp_ppp": 1.10, "pace": 101.1, "stars": ["Alperen Sengun", "Jalen Green"]},
    "Indiana Pacers": {"ppp": 1.10, "opp_ppp": 1.18, "pace": 100.1, "stars": ["Tyrese Haliburton", "Pascal Siakam"]},
    "Los Angeles Clippers": {"ppp": 1.12, "opp_ppp": 1.13, "pace": 99.5, "stars": ["James Harden", "Kawhi Leonard"]},
    "Los Angeles Lakers": {"ppp": 1.16, "opp_ppp": 1.17, "pace": 98.8, "stars": ["LeBron James", "Anthony Davis"]},
    "Memphis Grizzlies": {"ppp": 1.14, "opp_ppp": 1.17, "pace": 102.1, "stars": ["Ja Morant", "Desmond Bane"]},
    "Miami Heat": {"ppp": 1.19, "opp_ppp": 1.18, "pace": 100.0, "stars": ["Jimmy Butler", "Bam Adebayo"]},
    "Milwaukee Bucks": {"ppp": 1.12, "opp_ppp": 1.16, "pace": 101.0, "stars": ["Giannis Antetokounmpo", "Damian Lillard"]},
    "Minnesota Timberwolves": {"ppp": 1.19, "opp_ppp": 1.14, "pace": 102.5, "stars": ["Anthony Edwards", "Rudy Gobert"]},
    "New Orleans Pelicans": {"ppp": 1.14, "opp_ppp": 1.21, "pace": 101.8, "stars": ["Zion Williamson", "Brandon Ingram"]},
    "New York Knicks": {"ppp": 1.18, "opp_ppp": 1.09, "pace": 98.2, "stars": ["Jalen Brunson", "Karl-Anthony Towns"]},
    "Oklahoma City Thunder": {"ppp": 1.20, "opp_ppp": 1.07, "pace": 101.5, "stars": ["Shai Gilgeous-Alexander", "Chet Holmgren"]},
    "Orlando Magic": {"ppp": 1.15, "opp_ppp": 1.15, "pace": 101.2, "stars": ["Paolo Banchero", "Franz Wagner"]},
    "Philadelphia 76ers": {"ppp": 1.16, "opp_ppp": 1.18, "pace": 100.3, "stars": ["Joel Embiid", "Tyrese Maxey"]},
    "Phoenix Suns": {"ppp": 1.13, "opp_ppp": 1.11, "pace": 100.2, "stars": ["Kevin Durant", "Devin Booker"]},
    "Portland Trail Blazers": {"ppp": 1.15, "opp_ppp": 1.18, "pace": 102.0, "stars": ["Anfernee Simons", "Shaedon Sharpe"]},
    "Sacramento Kings": {"ppp": 1.10, "opp_ppp": 1.20, "pace": 101.8, "stars": ["De'Aaron Fox", "Domantas Sabonis"]},
    "San Antonio Spurs": {"ppp": 1.17, "opp_ppp": 1.12, "pace": 95.4, "stars": ["Victor Wembanyama", "Devin Vassell"]},
    "Toronto Raptors": {"ppp": 1.14, "opp_ppp": 1.12, "pace": 101.8, "stars": ["Scottie Barnes", "RJ Barrett"]},
    "Utah Jazz": {"ppp": 1.18, "opp_ppp": 1.26, "pace": 104.5, "stars": ["Lauri Markkanen", "Keyonte George"]},
    "Washington Wizards": {"ppp": 1.12, "opp_ppp": 1.22, "pace": 106.8, "stars": ["Kyle Kuzma", "Alex Sarr"]}
}

# --- 3. THE RE-TUNED SHARP ENGINE ---
def analyze_game_v4(away, home, vegas_line):
    a = NBA_STATS.get(away, {"ppp": 1.12, "opp_ppp": 1.15, "pace": 100.0, "stars": []})
    h = NBA_STATS.get(home, {"ppp": 1.12, "opp_ppp": 1.15, "pace": 100.0, "stars": []})
    
    # 1. Injury Sync (Using live report)
    a_ppp, h_ppp = a["ppp"], h["ppp"]
    live_report = st.session_state.get('live_report', {})
    shaky = []
    for team_data, side in [(a, "Away"), (h, "Home")]:
        for star in team_data["stars"]:
            status = live_report.get(star, "Available")
            if status in ["Out", "Doubtful"]:
                if side == "Away": a_ppp -= 0.09 
                else: h_ppp -= 0.09
                shaky.append(f"{star} ({status})")
            elif status == "Questionable":
                if side == "Away": a_ppp -= 0.05
                else: h_ppp -= 0.05
                shaky.append(f"{star} ({status})")

    if len(shaky) >= 2:
        return ("🚫 STAY AWAY", 0, 0, f"⚠️ ROSTER COLLAPSE: {', '.join(shaky)}")

    # 2. Score Projection using Harmonic Defensive Balancing
    # This prevents the AI from just looking at offense; it forces the defense to 'push back'
    avg_pace = (a["pace"] + h["pace"]) / 2
    proj_a = ((a_ppp + h["opp_ppp"]) / 2.02) * avg_pace # Slightly harder to score on the road
    proj_h = (((h_ppp + 0.015) + a["opp_ppp"]) / 1.98) * avg_pace # Home court multiplier
    
    final_proj = proj_a + proj_h
    diff = final_proj - vegas_line
    
    # 3. Decision Logic (Much more selective)
    # Only bets if the edge is > 6.5 points (Typical Sharp threshold)
    if diff > 6.5: 
        val = 50 + (min(abs(diff), 15) * 2.5)
        return ("🔥 TAKE THE OVER", final_proj, val, None)
    elif diff < -6.5: 
        val = 50 + (min(abs(diff), 15) * 2.5)
        return ("❄️ TAKE THE UNDER", final_proj, val, None)
    
    return ("🚫 STAY AWAY", final_proj, 0, "Consensus Line - No Edge Found")

# --- 4. UI ---
st.markdown('<div class="header-container"><div class="graffiti-title-english">NBA SHARP AI V4</div><div class="graffiti-title-arabic">الرهان الذكي</div></div>', unsafe_allow_html=True)

if st.button("RUN LIVE ANALYSIS"):
    # ... [Same API call logic as before to get live_report and game_data] ...
    pass
