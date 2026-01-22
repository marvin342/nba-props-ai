import streamlit as st
import requests
import math
from datetime import date

# ------------------------
# Password protection
# ------------------------
PASSWORD = "benja123"

st.sidebar.title("🔒 Private Access")
password = st.sidebar.text_input("Password", type="password")

if password != PASSWORD:
    st.warning("Access denied")
    st.stop()

# ------------------------
# Safe API helper (PREVENTS JSON ERRORS)
# ------------------------
def safe_get_json(url):
    try:
        r = requests.get(url, timeout=10)

        if r.status_code != 200:
            return None

        if "application/json" not in r.headers.get("Content-Type", ""):
            return None

        return r.json()

    except Exception:
        return None

# ------------------------
# App UI
# ------------------------
st.set_page_config(page_title="NBA Player Props AI", layout="centered")

st.title("🏀 NBA Player Props AI")
st.subheader("Today’s Games – Points Projection")

st.divider()

# ------------------------
# Load today's NBA games
# ------------------------
@st.cache_data(ttl=1800)
def get_games():
    today = date.today().isoformat()
    url = f"https://www.balldontlie.io/api/v1/games?dates[]={today}"

    data = safe_get_json(url)
    if not data or "data" not in data:
        return []

    return data["data"]

games = get_games()

if not games:
    st.warning("No NBA games today.")
    st.stop()

game = st.selectbox(
    "Select Game",
    games,
    format_func=lambda g: f"{g['home_team']['full_name']} vs {g['visitor_team']['full_name']}"
)

# ------------------------
# Load players
# ------------------------
@st.cache_data(ttl=1800)
def get_players(team_id):
    url = f"https://www.balldontlie.io/api/v1/players?team_ids[]={team_id}&per_page=25"

    data = safe_get_json(url)
    if not data or "data" not in data:
        return []

    return data["data"]

team_choice = st.radio("Team", ["Home", "Away"], horizontal=True)
team_id = game["home_team"]["id"] if team_choice == "Home" else game["visitor_team"]["id"]

players = get_players(team_id)

player = st.selectbox(
    "Select Player",
    players,
    format_func=lambda p: f"{p['first_name']} {p['last_name']}"
)

# ------------------------
# Pull recent player stats
# ------------------------
@st.cache_data(ttl=1800)
def get_recent_stats(player_id, games=10):
    url = f"https://www.balldontlie.io/api/v1/stats?player_ids[]={player_id}&per_page={games}"

    data = safe_get_json(url)
    if not data or "data" not in data or len(data["data"]) < 3:
        return 32, 15, 5, 6  # safe fallback

    minutes, shots, fta, points = [], [], [], []

    for g in data["data"]:
        try:
            min_played = int(g["min"].split(":")[0])
            minutes.append(min_played)
            shots.append(g["fga"])
            fta.append(g["fta"])
            points.append(g["pts"])
        except:
            continue

    if not minutes:
        return 32, 15, 5, 6

    avg_min = sum(minutes) / len(minutes)
    avg_shots = sum(shots) / len(shots)
    avg_fta = sum(fta) / len(fta)

    mean_pts = sum(points) / len(points)
    variance = sum((p - mean_pts) ** 2 for p in points) / len(points)
    std_dev = max(variance ** 0.5, 4)

    return avg_min, avg_shots, avg_fta, std_dev

# ------------------------
# Sportsbook input
# ------------------------
line = st.number_input("Sportsbook Line (Points)", step=0.5, value=20.5)

# ------------------------
# Predict
# ------------------------
if st.button("📈 Predict"):
    minutes, shots, fta, std = get_recent_stats(player["id"])

    mean = minutes * 0.75 + shots * 1.9 + fta * 0.8
    z = (line - mean) / std
    prob_over = 0.5 * (1 - math.erf(z / math.sqrt(2)))

    st.divider()
    st.subheader(f"📊 {player['first_name']} {player['last_name']}")

    st.metric("Projected Points", f"{mean:.2f}")
    st.metric("Over Probability", f"{prob_over*100:.1f}%")

    edge = (prob_over - 0.524) * 100
    st.metric("Model Edge", f"{edge:.2f}%")

    if edge >= 6:
        st.success("✅ BET SIGNAL")
    else:
        st.warning("⚠️ No Bet")
