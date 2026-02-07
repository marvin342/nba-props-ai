import subprocess
import sys

# --- 0. THE FAIL-SAFE: FORCING NBA_API INSTALLATION ---
# This block runs before anything else to ensure the cloud server has the library.
try:
    from nba_api.stats.endpoints import leaguedashteamstats, teamplayerstats
    from nba_api.stats.static import teams
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "nba_api"])
    from nba_api.stats.endpoints import leaguedashteamstats, teamplayerstats
    from nba_api.stats.static import teams

import streamlit as st
import requests
from datetime import datetime
import pandas as pd

# --- 1. CONFIG & PRO VISUALS (YOUR CUSTOM CSS) ---
st.set_page_config(page_title="NBA Sharp AI", page_icon="🏀", layout="wide")

st.markdown("""
    <style>
    [data-testid="stAppViewContainer"] {
        background: linear-gradient(rgba(0, 0, 0, 0.85), rgba(0, 0, 0, 0.95)), 
                    url("https://images.unsplash.com/photo-1504450758481-7338eba7524a?q=80&w=2069&auto=format&fit=crop");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }
    [data-testid="stHeader"] { background: rgba(0,0,0,0); }
    .game-card {
        background: rgba(255, 255, 255, 0.04);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 20px;
        padding: 30px;
        margin-bottom: 25px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.8);
    }
    .team-name { font-size: 26px; font-weight: 800; color: #ffffff; letter-spacing: -0.5px; }
    .vs-text { color: #555; font-size: 18px; margin: 0 10px; }
    .metric-box { text-align: center; background: rgba(0,0,0,0.3); padding: 10px; border-radius: 12px; min-width: 100px; }
    .metric-label { font-size: 10px; color: #888; text-transform: uppercase; margin-bottom: 2px; letter-spacing: 1px; }
    .metric-value { font-size: 20px; font-weight: 700; color: #fff; }
    .stButton>button {
        background: linear-gradient(45deg, #1e88e5, #1565c0);
        color: white;
        border: none;
        padding: 15px 40px;
        border-radius: 50px;
        font-weight: bold;
        transition: 0.3s;
        box-shadow: 0 4px 15px rgba(30, 136, 229, 0.4);
    }
    .stButton>button:hover {
        transform: scale(1.05);
        box-shadow: 0 6px 20px rgba(30, 136, 229, 0.6);
    }
    .prop-row { 
        background: rgba(255, 255, 255, 0.02); 
        margin-bottom: 8px; 
        padding: 12px; 
        border-radius: 10px; 
        border-left: 3px solid #1e88e5;
    }
    </style>
    """, unsafe_allow_html=True)

# Initialize session state
if 'results' not in st.session_state: st.session_state.results = None
if 'injuries' not in st.session_state: st.session_state.injuries = {}
if 'live_stats' not in st.session_state: st.session_state.live_stats = {}

# --- 2. DATA (NBA_STATS FALLBACKS) ---
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

def get_team_id(name):
    try:
        team_dict = teams.find_teams_by_full_name(name)
        return team_dict[0]['id'] if team_dict else None
    except: return None

# --- 3. LIVE DATA FETCH ---
def fetch_live_metrics():
    try:
        data = leaguedashteamstats.LeagueDashTeamStats(per_mode_detailed='PerGame').get_data_frames()[0]
        live_map = {}
        for _, row in data.iterrows():
            poss = row['FGA'] + (0.44 * row['FTA']) + row['TOV']
            live_map[row['TEAM_NAME']] = {
                "ppp": row['PTS'] / poss,
                "opp_ppp": row['OPP_PTS'] / poss,
                "pace": row['PACE']
            }
        return live_map
    except: return {}

# --- 4. ANALYTIC ENGINE (GAME TOTALS) ---
def run_sharp_analysis(away, home, line):
    a_base = st.session_state.live_stats.get(away, NBA_STATS.get(away))
    h_base = st.session_state.live_stats.get(home, NBA_STATS.get(home))
    a_ppp, h_ppp = a_base["ppp"], h_base["ppp"]
    
    for star in NBA_STATS.get(away, {}).get("stars", []):
        if st.session_state.injuries.get(star) in ["Out", "Doubtful"]: a_ppp -= 0.08
    for star in NBA_STATS.get(home, {}).get("stars", []):
        if st.session_state.injuries.get(star) in ["Out", "Doubtful"]: h_ppp -= 0.08

    avg_pace = (a_base["pace"] + h_base["pace"]) / 2
    proj = (((a_ppp + h_base["opp_ppp"])/2) * avg_pace) + (((h_ppp + 0.015 + a_base["opp_ppp"])/2) * avg_pace)
    diff = proj - line
    
    if abs(diff) > 12: return ("🚫 STAY AWAY", proj, "Trap Line", "#808080")
    if diff > 6.0: return ("🔥 OVER", proj, f"Edge: +{min(15.0, diff):.1f}%", "#2ecc71")
    if diff < -6.0: return ("❄️ UNDER", proj, f"Edge: +{min(15.0, abs(diff)):.1f}%", "#e74c3c")
    return ("⚖️ NEUTRAL", proj, "Efficient", "#3498db")

# --- 5. SYNC LOGIC ---
def sync_live_data():
    with st.spinner("Syncing Live Stats..."):
        st.session_state.live_stats = fetch_live_metrics()
        try:
            o_res = requests.get("https://api.the-odds-api.com/v4/sports/basketball_nba/odds", 
                               params={"api_key": "27970d14c8e8eb9f2a217c775db6571f", "regions": "us", "markets": "totals"})
            if o_res.status_code == 200: st.session_state.results = o_res.json()
        except: st.error("Vegas API Down")

# --- 6. PLAYER PROPS LOGIC (PRA + USAGE) ---
def get_player_props(team_name, opp_team):
    tid = get_team_id(team_name)
    if not tid: return []
    try:
        df = teamplayerstats.TeamPlayerStats(team_id=tid, season='2025-26').get_data_frames()[0]
        opp_data = st.session_state.live_stats.get(opp_team, NBA_STATS.get(opp_team))
        pace_factor = opp_data['pace'] / 100
        
        props = []
        for _, p in df.head(8).iterrows():
            name = p['PLAYER_NAME']
            usage_boost = 1.0
            for star in NBA_STATS.get(team_name, {}).get("stars", []):
                if st.session_state.injuries.get(star) == "Out" and name != star:
                    usage_boost += 0.15
            
            p_pts = round(p['PTS'] * (opp_data['opp_ppp']/1.12) * usage_boost, 1)
            p_reb = round(p['REB'] * pace_factor * (1 + (usage_boost-1)*0.5), 1)
            p_ast = round(p['AST'] * usage_boost * 1.1, 1)
            
            props.append({"name": name, "pts": p_pts, "reb": p_reb, "ast": p_ast, "pra": round(p_pts+p_reb+p_ast, 1)})
        return props
    except: return []

# --- 7. MAIN UI ---
st.title("🏀 NBA SHARP AI")
st.markdown("<p style='color:#888; margin-top:-20px;'>QUANTITATIVE ANALYSIS • TRIPLE-DOUBLE PROPS • 2026 SEASON</p>", unsafe_allow_html=True)

col_l, col_m, col_r = st.columns([1,1,1])
with col_m:
    if st.button("REFRESH ANALYTICS"): sync_live_data()

if st.session_state.results:
    t1, t2 = st.tabs(["🔥 GAME TOTALS", "🏹 PLAYER PROPS"])
    
    with t1:
        for game in st.session_state.results:
            h, a = game['home_team'], game['away_team']
            try: line = game['bookmakers'][0]['markets'][0]['outcomes'][0]['point']
            except: continue
            call, proj, status, color = run_sharp_analysis(a, h, line)
            
            st.markdown(f"""
                <div class="game-card">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div style="flex: 2;">
                            <span class="team-name">{a}</span> <span class="vs-text">at</span> <span class="team-name">{h}</span>
                            <div style="display: flex; gap: 20px; margin-top: 20px;">
                                <div class="metric-box"><p class="metric-label">Vegas Total</p><p class="metric-value" style="color:#aaa;">{line}</p></div>
                                <div class="metric-box" style="border: 1px solid {color}44;"><p class="metric-label" style="color:{color};">AI Project</p><p class="metric-value">{proj:.1f}</p></div>
                            </div>
                        </div>
                        <div style="flex: 1; text-align: right;">
                            <h1 style="margin: 0; color: {color}; font-size: 42px; font-weight: 900;">{call.split(' ')[1]}</h1>
                            <p style="margin: 10px 0 0 0; color: #fff; font-weight: 600;">{status}</p>
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

    with t2:
        game_list = [f"{g['away_team']} @ {g['home_team']}" for g in st.session_state.results]
        selected_game = st.selectbox("Active Matchups", game_list)
        if selected_game:
            a_t, h_t = selected_game.split(" @ ")
            c1, c2 = st.columns(2)
            for team, col, opp in [(a_t, c1, h_t), (h_t, c2, a_t)]:
                with col:
                    st.subheader(f"{team} Targets")
                    for p in get_player_props(team, opp):
                        st.markdown(f"""<div class="prop-row">
                            <b>{p['name']}</b><br>
                            <span style="color:#2ecc71;">PRA: {p['pra']}</span> (P:{p['pts']} R:{p['reb']} A:{p['ast']})
                            </div>""", unsafe_allow_html=True)
