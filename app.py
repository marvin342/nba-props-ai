import streamlit as st
import requests

# --- 1. REAL 2026 SEASON DATA (Sharp Stats) ---
# PPG = Points Scored | PAPG = Points Allowed
NBA_STATS_2026 = {
    "Oklahoma City Thunder": {"ppg": 120.2, "papg": 107.9},
    "Boston Celtics": {"ppg": 115.9, "papg": 108.6},
    "Detroit Pistons": {"ppg": 117.5, "papg": 109.9},
    "San Antonio Spurs": {"ppg": 116.9, "papg": 111.8},
    "Denver Nuggets": {"ppg": 120.1, "papg": 116.2},
    "Miami Heat": {"ppg": 119.9, "papg": 118.0},
    "New York Knicks": {"ppg": 118.2, "papg": 112.1},
    "Dallas Mavericks": {"ppg": 113.8, "papg": 116.5},
    "Phoenix Suns": {"ppg": 114.1, "papg": 111.6},
    "Golden State Warriors": {"ppg": 116.2, "papg": 114.0},
    "Philadelphia 76ers": {"ppg": 116.8, "papg": 115.3},
    "Los Angeles Lakers": {"ppg": 116.3, "papg": 116.2},
    "Minnesota Timberwolves": {"ppg": 119.6, "papg": 114.8},
}

# --- 2. LOCKING THE PREDICTIONS (Session State) ---
if 'locked_picks' not in st.session_state:
    st.session_state.locked_picks = {}

def get_sharp_pick(game_id, away, home, line):
    # If we already made this pick, return it immediately (No changes!)
    if game_id in st.session_state.locked_picks:
        return st.session_state.locked_picks[game_id]

    # Get stats (default to league average 115 if team not in list)
    a_stats = NBA_STATS_2026.get(away, {"ppg": 115, "papg": 115})
    h_stats = NBA_STATS_2026.get(home, {"ppg": 115, "papg": 115})

    # SHARP FORMULA: Projected score based on Offense vs Defense
    proj_away = (a_stats["ppg"] + h_stats["papg"]) / 2
    proj_home = (h_stats["ppg"] + a_stats["papg"]) / 2
    total_projection = proj_away + proj_home
    
    # Calculate the "Edge" (Difference from the bookie's line)
    diff = total_projection - line
    confidence = min(abs(diff) * 12, 99.9) # Scale confidence by the edge size

    if diff > 2.5:
        pick = ("✅ SHARP OVER", confidence, total_projection)
    elif diff < -2.5:
        pick = ("🚨 SHARP UNDER", confidence, total_projection)
    else:
        pick = ("⚖️ PASS (No Edge)", 0, total_projection)

    # Save to session so it never changes
    st.session_state.locked_picks[game_id] = pick
    return pick

# --- 3. DISPLAY LOGIC ---
st.title("🏀 NBA Sharp Predictor (2026 Stats)")

if st.button("Generate Locked-In Picks"):
    # (Your existing API call to The Odds API goes here)
    # data = requests.get(...).json()
    
    # Example loop for display:
    for game in data:
        game_id = game['id']
        home = game['home_team']
        away = game['away_team']
        line = game['bookmakers'][0]['markets'][0]['outcomes'][0]['point']
        
        label, conf, proj = get_sharp_pick(game_id, away, home, line)
        
        with st.expander(f"{away} @ {home}", expanded=True):
            c1, c2 = st.columns(2)
            c1.metric("Betting Line", line)
            c1.metric("AI Projection", f"{proj:.1f}")
            
            if "OVER" in label:
                c2.success(f"{label}\n\nConfidence: {conf:.1f}%")
            elif "UNDER" in label:
                c2.error(f"{label}\n\nConfidence: {conf:.1f}%")
            else:
                c2.info(label)
