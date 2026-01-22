import streamlit as st
import requests
import math
import csv
import os
from datetime import date, timedelta, datetime

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
# Safe API helper
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
st.subheader("NBA Points Props – Smart Projections")

st.divider()

# ------------------------
# Load games with fallback
# ------------------------
@st.cache_data(ttl=1800)
def get_games_with_fallback():
    dates = [
        date.today(),
        date.today() + timedelta(days=1),
        date.today() - timedelta(days=1),
    ]

    for d in dates:
        url = f"https://www.balldontlie.io/api/v1/games?dates[]={d.isoformat()}"
        data = safe_get_json(url)
        if data and "data" in data and data["data"]:
            return data["data"], d

    return [], None

games, used_date = get_games_with_fallback()

if not games:
    st.warning("NBA schedule unavailable.")
    st.stop()

st.caption(f"Games for: {used_date.isoformat()}")

game = st.selectbox(
    "Select Game",
    games,
    format_func=lambda g: f"{g['home_team']['full_name']} vs {g['visitor_team']['full_name']}"
)

# ------------------------
# Players
# ------------------------
@st.cache_data(ttl=1800)
def get_players(team_id):
    url = f"https://www.balldontlie.io/api/v1/players?team_ids[]={team_id}&per_page=25"
    data = safe_get_json(url)
    if not data or "data" not in data:
        return []
    return data["data"]

home_players = get_players(game["home_team"]["id"])
away_players = get_players(game["visitor_team"]["id"])

# ------------------------
# Player recent stats
# ------------------------
@st.cache_data(ttl=1800)
def get_recent_stats(player_id, games=10):
    url = f"https://www.balldontlie.io/api/v1/stats?player_ids[]={player_id}&per_page={games}"
    data = safe_get_json(url)

    if not data or "data" not in data or len(data["data"]) < 3:
        return 32, 15, 5, 6

    minutes, shots, fta, points = [], [], [], []

    for g in data["data"]:
        try:
            minutes.append(int(g["min"].split(":")[0]))
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
# Matchup adjustments
# ------------------------
def matchup_modifier(team_choice):
    pace = 1.02
    defense = 0.98 if team_choice == "Away" else 1.00
    home = 1.03 if team_choice == "Home" else 0.97
    return pace * defense * home

# ------------------------
# 🔥 TOP EDGES TODAY
# ------------------------
st.divider()
st.header("🔥 Top Edges Today")

edges = []

for team, players in [("Home", home_players), ("Away", away_players)]:
    for p in players:
        mins, shots, fta, std = get_recent_stats(p["id"])
        base_mean = mins * 0.75 + shots * 1.9 + fta * 0.8
        mean = base_mean * matchup_modifier(team)

        synthetic_line = mean - 1.5
        z = (synthetic_line - mean) / std
        prob_over = 0.5 * (1 - math.erf(z / math.sqrt(2)))
        edge = (prob_over - 0.524) * 100

        edges.append({
            "Player": f"{p['first_name']} {p['last_name']}",
            "Team": team,
            "Proj Pts": round(mean, 1),
            "Edge %": round(edge, 2)
        })

edges = sorted(edges, key=lambda x: x["Edge %"], reverse=True)[:5]
st.table(edges)

# ------------------------
# 🎯 MANUAL PLAYER CHECK + RESULTS LOGGING
# ------------------------
st.divider()
st.header("🎯 Manual Player Check")

team_choice = st.radio("Team", ["Home", "Away"], horizontal=True)
players = home_players if team_choice == "Home" else away_players

player = st.selectbox(
    "Select Player",
    players,
    format_func=lambda p: f"{p['first_name']} {p['last_name']}"
)

line = st.number_input("Sportsbook Line (Points)", step=0.5, value=20.5)
pick_side = st.radio("Pick", ["Over", "Under"], horizontal=True)

if st.button("📈 Predict & Log Pick"):
    mins, shots, fta, std = get_recent_stats(player["id"])
    mean = (mins * 0.75 + shots * 1.9 + fta * 0.8) * matchup_modifier(team_choice)

    z = (line - mean) / std
    prob_over = 0.5 * (1 - math.erf(z / math.sqrt(2)))
    edge = (prob_over - 0.524) * 100

    st.metric("Projected Points", f"{mean:.2f}")
    st.metric("Over Probability", f"{prob_over*100:.1f}%")
    st.metric("Model Edge", f"{edge:.2f}%")

    log_file = "results_log.csv"
    file_exists = os.path.isfile(log_file)

    with open(log_file, "a", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow([
                "Timestamp",
                "Player",
                "Team",
                "Line",
                "Pick",
                "ProjPts",
                "ProbOver",
                "Edge",
                "Result"
            ])

        writer.writerow([
            datetime.now().isoformat(),
            f"{player['first_name']} {player['last_name']}",
            team_choice,
            line,
            pick_side,
            round(mean, 2),
            round(prob_over, 3),
            round(edge, 2),
            ""
        ])

    st.success("✅ Pick logged successfully")

# ------------------------
# 📊 RESULTS TABLE
# ------------------------
st.divider()
st.header("📊 Results Log")

if os.path.isfile("results_log.csv"):
    with open("results_log.csv", "r") as f:
        st.dataframe(list(csv.DictReader(f)))
else:
    st.info("No picks logged yet.")



