import streamlit as st
import requests
import math
import csv
import os
import subprocess
import pandas as pd
from datetime import datetime, timedelta

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
# API KEY
# ------------------------
API_KEY = st.secrets["BALLDONTLIE_API_KEY"]

# ------------------------
# Safe API helper
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
    except:
        return None

# ------------------------
# UI
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

TODAY_UTC = datetime.utcnow().date()

offsets = (
    [-1] if window == "Yesterday"
    else [0] if window == "Today"
    else [1, 2]
)

# ------------------------
# LOAD GAMES (UTC SAFE)
# ------------------------
@st.cache_data(ttl=1800)
def load_games(offsets):
    games = []
    seen = set()

    for off in offsets:
        d = TODAY_UTC + timedelta(days=off)
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
    st.info("No games available yet.")
    st.stop()

# ------------------------
# SELECT GAME
# ------------------------
game = st.selectbox(
    "Select Game",
    games,
    format_func=lambda g: (
        f"{g['home_team']['full_name']} vs "
        f"{g['visitor_team']['full_name']} "
        f"({g['date'][:10]})"
    )
)

# ------------------------
# PLAYER LOADER (FIXED FOR ALL WINDOWS)
# ------------------------
@st.cache_data(ttl=900)
def get_players_for_team(team_id, window):
    players = {}

    # 1️⃣ Always load active roster (pregame truth)
    roster_url = (
        "https://api.balldontlie.io/v1/players"
        f"?team_ids[]={team_id}&active=true&per_page=100"
    )
    roster_data = safe_get_json(roster_url)

    if roster_data and roster_data.get("data"):
        for p in roster_data["data"]:
            players[p["id"]] = p

    # 2️⃣ Yesterday → merge stats players (postgame truth)
    if window == "Yesterday":
        stats_url = (
            "https://api.balldontlie.io/v1/stats"
            f"?team_ids[]={team_id}&per_page=100"
        )
        stats_data = safe_get_json(stats_url)

        if stats_data and stats_data.get("data"):
            for row in stats_data["data"]:
                p = row.get("player")
                if p:
                    players[p["id"]] = p

    return sorted(
        players.values(),
        key=lambda p: (p["last_name"], p["first_name"])
    )

home_players = get_players_for_team(game["home_team"]["id"], window)
away_players = get_players_for_team(game["visitor_team"]["id"], window)

# ------------------------
# PLAYER STATS
# ------------------------
@st.cache_data(ttl=1800)
def get_recent_stats(player_id, games=10):
    url = (
        "https://api.balldontlie.io/v1/stats"
        f"?player_ids[]={player_id}&per_page={games}"
    )
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

    mean_pts = sum(points) / len(points)
    variance = sum((p - mean_pts) ** 2 for p in points) / len(points)

    return (
        sum(minutes) / len(minutes),
        sum(shots) / len(shots),
        sum(fta) / len(fta),
        max(variance ** 0.5, 4),
    )

def matchup_modifier(team_choice):
    return (1.03 if team_choice == "Home" else 0.97) * 1.02

# ------------------------
# MANUAL PICK
# ------------------------
st.divider()
st.header("🎯 Manual Player Pick")

team_choice = st.radio("Team", ["Home", "Away"], horizontal=True)
players = home_players if team_choice == "Home" else away_players

if not players:
    st.warning("Roster unavailable — try another game.")
    st.stop()

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
            datetime.utcnow().isoformat(),
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
# RESULTS
# ------------------------
st.divider()
st.header("📊 Results")

if os.path.isfile("results_log.csv"):
    st.dataframe(pd.read_csv("results_log.csv"))

# ------------------------
# ML
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
# PERFORMANCE
# ------------------------
st.divider()
st.header("📈 Performance Dashboard")

if os.path.isfile("results_log.csv"):
    df = pd.read_csv("results_log.csv")
    df = df[df["Result"].isin(["Win", "Loss"])]

    if len(df):
        wins = (df["Result"] == "Win").sum()
        total = len(df)
        units = wins * 0.91 - (total - wins)

        c1, c2, c3 = st.columns(3)
        c1.metric("Bets", total)
        c2.metric("Win Rate", f"{wins/total*100:.1f}%")
        c3.metric("Units", f"{units:.2f}")
