import streamlit as st
import requests
import pandas as pd
from streamlit_autorefresh import st_autorefresh

# ---------------- SECURITY ----------------
PASSWORD = "benja123"
st.sidebar.title("🔐 NBA PRIVATE ACCESS")
password = st.sidebar.text_input("Password", type="password")
if password != PASSWORD:
    st.stop()

st_autorefresh(interval=1200000, key="refresh")

# ---------------- CONFIG ----------------
st.set_page_config(page_title="NBA BET ENGINE", layout="wide", page_icon="🏀")
API_KEY = "27970d14c8e8eb9f2a217c775db6571f"

st.markdown("""
<style>
.stExpander { border:1px solid #333 !important; border-radius:10px !important; }
</style>
""", unsafe_allow_html=True)

# ---------------- HELPERS ----------------
def pick_total(over_price, under_price):
    # no coin flips
    if abs(over_price - under_price) < 0.08:
        return None

    # avoid extreme chalk
    if over_price < 1.65 or under_price < 1.65:
        return None

    return "OVER" if over_price < under_price else "UNDER"


def pick_prop(over_price, under_price, line):
    # props must be cleaner
    if abs(over_price - under_price) < 0.12:
        return None

    if over_price < 1.70 or under_price < 1.70:
        return None

    # avoid stupid lines
    if line >= 40 or line <= 6:
        return None

    return "OVER" if over_price < under_price else "UNDER"


# ---------------- DATA ----------------
@st.cache_data(ttl=1200)
def get_games():
    url = "https://api.the-odds-api.com/v4/sports/basketball_nba/odds"
    params = {
        "apiKey": API_KEY,
        "regions": "us",
        "markets": "totals",
        "oddsFormat": "decimal"
    }
    r = requests.get(url, params=params)
    return r.json(), r.headers.get("x-requests-remaining", "N/A")


@st.cache_data(ttl=1200)
def get_props(event_id):
    url = f"https://api.the-odds-api.com/v4/sports/basketball_nba/events/{event_id}/odds"
    params = {
        "apiKey": API_KEY,
        "regions": "us",
        "markets": "player_points,player_rebounds,player_assists",
        "oddsFormat": "decimal"
    }
    r = requests.get(url, params=params)
    return r.json()


# ---------------- UI ----------------
st.title("🏀 NBA BET ENGINE")

search = st.text_input("Search Team").lower()
games, credits = get_games()
st.caption(f"API Credits Left: {credits}")

if not games:
    st.stop()

games = sorted(games, key=lambda x: x["commence_time"])

for g in games:
    if search and search not in g["home_team"].lower() and search not in g["away_team"].lower():
        continue

    try:
        home, away = g["home_team"], g["away_team"]
        time = pd.to_datetime(g["commence_time"]).strftime("%m/%d %I:%M %p")

        book = g["bookmakers"][0]
        market = next(m for m in book["markets"] if m["key"] == "totals")

        over = next(o for o in market["outcomes"] if o["name"] == "Over")
        under = next(o for o in market["outcomes"] if o["name"] == "Under")

        line = over["point"]
        o_p, u_p = over["price"], under["price"]

        total_pick = pick_total(o_p, u_p)

        if not total_pick:
            continue  # silent pass

        with st.expander(f"🔥 {total_pick} {line} | {away} @ {home} ({time})"):
            st.write(f"Over {o_p} | Under {u_p}")

            if st.button("ANALYZE PROPS", key=g["id"]):
                props = get_props(g["id"])
                if not props or "bookmakers" not in props:
                    continue

                for b in props["bookmakers"]:
                    for m in b["markets"]:
                        players = {}
                        for o in m["outcomes"]:
                            players.setdefault(o["description"], {})[o["name"]] = o

                        for name, d in players.items():
                            if "Over" not in d or "Under" not in d:
                                continue

                            o_p = d["Over"]["price"]
                            u_p = d["Under"]["price"]
                            line = d["Over"]["point"]

                            prop_pick = pick_prop(o_p, u_p, line)
                            if prop_pick:
                                st.success(f"{prop_pick} {name} {line}")

    except:
        continue
