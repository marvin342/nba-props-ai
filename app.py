import streamlit as st
import requests
import math
import csv
import os
import subprocess
import pandas as pd
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
# API KEY (from Streamlit Secrets)
# ------------------------
API_KEY = st.secrets["BALLDONTLIE_API_KEY"]

# ------------------------
# Safe API helper (FIXED)
# ------------------------
def safe_get_json(url):
    try:
        r = requests.get(
            url,
            headers={"Authorization": API_KEY},
            timeout=10
        )
        if r.status_code != 200:
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
# GAME WINDOW
# ------------------------
window = st.radio(
    "Game Window",
    ["Yesterday", "Today", "Upcoming"],
    horizontal=True
)

if window == "Yesterday":
    offsets = [-1]
elif window == "Today":
    offsets = [0]
else:
    offsets = [1, 2]

# ------------------------
# LOAD GAMES (FIXED DOMAIN)
# ------------------------
@st.cache_data(ttl=1800)
def load_games(offsets):
    games = []
    seen = set()

    for off in offsets:
        d = date.today() + timedelta(days=off)
        url = f"https://api.balldontlie.io/v1/games?dates[]={d.isoformat()}"
        data = safe_get_json(url)

        if not data or "data" not in data:
            continue

        for g in data["data"]:
            if g["id"] not in seen:
                games.append(g)
                seen.add(g["id"])

    return games

games = load_games(offsets)

if not games:
    st.info(
        "No games found yet. This is normal early in the day — "
        "the API updates throughout the morning."
    )

# ------------------------
# GAME + PLAYER SECTION
# ------------------------
if games:
    game = st.selectbox(
        "Select Game",
        games,
        format_func=lambda g: (
            f"{g['home_team']['full_name']} vs {g['visitor_team']['full_name']} "
            f"({g['date'][:10]})"
        )
    )

    @st.cache_data(ttl=1800)
    def get_players(team_id):
        url = f"https://api.balldontlie.io/v1/players?team_ids[]={team_id}&per_page=25"
        data = safe_get_json(url)
        return data["data"] if data and "data" in data else []

    home_players = get_players(game["home_team"]["id"])
    away_players = get_players(game["visitor_team"]["id"])

    @st.cache_data(ttl=1800)
    def get_recent_stats(player_id, games=10):
        url = f"https://api.balldontlie.io/v1/stats?player_ids[]={player_id}&per_page={games}"
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

        avg_min = sum(minutes) / len(minutes)
        avg_shots = sum(shots) / len(shots)
        avg_fta = sum(fta) / len(fta)

        mean_pts = sum(points) / len(points)
        variance = sum((p - mean_pts) ** 2 for p in points) / len(points)
        std_dev = max(variance ** 0.5, 4)

        return avg_min, avg_shots, avg_fta, std_dev

    def matchup_modifier(team_choice):
        pace = 1.02
        defense = 0.98 if team_choice == "Away" else 1.00
        home = 1.03 if team_choice == "Home" else 0.97
        return pace * defense * home

    # ------------------------
    # 🎯 MANUAL PICK
    # ------------------------
    st.divider()
    st.header("🎯 Manual Player Pick")

    team_choice = st.radio("Team", ["Home", "Away"], horizontal=True)
    players = home_players if team_choice == "Home" else away_players

    player = st.selectbox(
        "Select Player",
        players,
        format_func=lambda p: f"{p['first_name']} {p['last_name']}"
    )

    line = st.number_input("Sportsbook Line", step=0.5, value=20.5)
    pick_side = st.radio("Pick", ["Over", "Under"], horizontal=True)

    if st.button("📈 Predict & Log"):
        mins, shots, fta, std = get_recent_stats(player["id"])
        mean = (mins * 0.75 + shots * 1.9 + fta * 0.8) * matchup_modifier(team_choice)
        z = (line - mean) / std
        prob_over = 0.5 * (1 - math.erf(z / math.sqrt(2)))
        edge = (prob_over - 0.524) * 100

        log_file = "results_log.csv"
        exists = os.path.isfile(log_file)

        with open(log_file, "a", newline="") as f:
            writer = csv.writer(f)
            if not exists:
                writer.writerow([
                    "Timestamp","Player","Team","Line","Pick",
                    "ProjPts","ProbOver","Edge","ActualPts","Result"
                ])
            writer.writerow([
                datetime.now().isoformat(),
                f"{player['first_name']} {player['last_name']}",
                team_choice,
                line,
                pick_side,
                round(mean,2),
                round(prob_over,3),
                round(edge,2),
                "",
                ""
            ])

        st.success("Pick logged")

# ------------------------
# 📊 RESULTS & ACTUALS
# ------------------------
st.divider()
st.header("📊 Results & Actuals")

if os.path.isfile("results_log.csv"):
    df = pd.read_csv("results_log.csv")
    st.dataframe(df)

# ------------------------
# 🤖 ML
# ------------------------
st.divider()
st.header("🤖 Machine Learning")

if st.button("🔁 Retrain Model"):
    try:
        subprocess.run(["python", "ml/train_model.py"], check=True)
        st.success("Model retrained")
    except:
        st.error("Training failed (need more data)")

# ------------------------
# 📈 PERFORMANCE
# ------------------------
st.divider()
st.header("📈 Performance Dashboard")

if os.path.isfile("results_log.csv"):
    df_perf = pd.read_csv("results_log.csv")
    df_perf = df_perf[df_perf["Result"].isin(["Win", "Loss"])]

    if len(df_perf):
        wins = (df_perf["Result"] == "Win").sum()
        total = len(df_perf)
        units = wins * 0.91 - (total - wins)

        c1, c2, c3 = st.columns(3)
        c1.metric("Bets", total)
        c2.metric("Win Rate", f"{wins/total*100:.1f}%")
        c3.metric("Units", f"{units:.2f}")
