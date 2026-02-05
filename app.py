import streamlit as st
import requests
import pandas as pd
from streamlit_autorefresh import st_autorefresh

# ------------------ SECURITY ------------------
PASSWORD = "benja123"
st.sidebar.title("🔐 NBA PRIVATE ACCESS")
password = st.sidebar.text_input("Password", type="password")
if password != PASSWORD:
    st.warning("Locked.")
    st.stop()

st_autorefresh(interval=1200000, key="nba_master_sync")

# ------------------ CONFIG ------------------
st.set_page_config(page_title="NBA ELITE COMMAND", layout="wide", page_icon="🏀")
API_KEY = "27970d14c8e8eb9f2a217c775db6571f"

st.markdown("""
<style>
.stMetric { background:#1e1e1e; padding:10px; border-radius:10px; border:1px solid #333; }
.stExpander { border:1px solid #444 !important; border-radius:10px !important; }
</style>
""", unsafe_allow_html=True)

# ------------------ HELPERS ------------------
def implied_prob(decimal_odds):
    return 1 / decimal_odds

def market_bias(over_odds, under_odds):
    o = implied_prob(over_odds)
    u = implied_prob(under_odds)
    total = o + u
    return o / total, u / total

# ------------------ DATA ------------------
@st.cache_data(ttl=1200)
def get_all_nba_games(api_key):
    url = f"https://api.the-odds-api.com/v4/sports/basketball_nba/odds"
    params = {
        "apiKey": api_key,
        "regions": "us",
        "markets": "totals",
        "oddsFormat": "decimal"
    }
    r = requests.get(url, params=params)
    return r.json(), r.headers.get("x-requests-remaining", "N/A")

@st.cache_data(ttl=1200)
def get_extended_props(api_key, event_id):
    url = f"https://api.the-odds-api.com/v4/sports/basketball_nba/events/{event_id}/odds"
    params = {
        "apiKey": api_key,
        "regions": "us",
        "markets": "player_points,player_rebounds,player_assists",
        "oddsFormat": "decimal"
    }
    r = requests.get(url, params=params)
    return r.json()

# ------------------ UI ------------------
st.title("🏀 NBA ELITE COMMAND CENTER")
col_search, col_stats = st.columns([2, 1])
search_query = col_search.text_input("🔍 Search Teams").lower()

nba_data, credits_left = get_all_nba_games(API_KEY)
col_stats.metric("📡 Credits Left", credits_left)

# ------------------ MAIN LOOP ------------------
if not nba_data:
    st.error("API Error.")
    st.stop()

nba_data = sorted(nba_data, key=lambda x: x["commence_time"])
filtered = [
    g for g in nba_data
    if search_query in g["home_team"].lower()
    or search_query in g["away_team"].lower()
]

for game in filtered:
    try:
        home, away = game["home_team"], game["away_team"]
        event_id = game["id"]
        time = pd.to_datetime(game["commence_time"]).strftime("%m/%d | %I:%M %p")

        book = next(b for b in game["bookmakers"] if "totals" in [m["key"] for m in b["markets"]])
        market = next(m for m in book["markets"] if m["key"] == "totals")

        over = next(o for o in market["outcomes"] if o["name"] == "Over")
        under = next(u for u in market["outcomes"] if u["name"] == "Under")

        line = over["point"]
        o_price, u_price = over["price"], under["price"]

        o_bias, u_bias = market_bias(o_price, u_price)

        confidence = 0
        if o_bias > 0.56 or u_bias > 0.56:
            confidence += 35
        if line >= 235 or line <= 215:
            confidence += 20
        if o_price <= 1.80 or u_price <= 1.80:
            confidence += 25
        if abs(o_price - u_price) >= 0.15:
            confidence += 10

        if confidence >= 70:
            tag = "💣 ELITE PLAY"
        elif confidence >= 50:
            tag = "✅ STRONG EDGE"
        else:
            lean = "OVER" if o_bias > u_bias else "UNDER"
            tag = f"💡 MARKET LEAN: {lean}"

        with st.expander(f"{tag} | {away} @ {home} ({time})"):
            c1, c2, c3 = st.columns(3)
            c1.metric("Total", line)
            c2.metric("Over", o_price)
            c3.metric("Under", u_price)

            st.progress(confidence / 100)
            st.caption(f"Confidence: {confidence}/100")

            st.markdown("---")

            if st.button(f"🚀 ANALYZE ALL PROPS", key=event_id):
                props = get_extended_props(API_KEY, event_id)
                if not props or "bookmakers" not in props:
                    st.info("Props not available yet.")
                    continue

                for b in props["bookmakers"]:
                    for m in b["markets"]:
                        st.subheader(m["key"].replace("player_", "").title())

                        players = {}
                        for o in m["outcomes"]:
                            players.setdefault(o["description"], {})[o["name"]] = o

                        for name, data in players.items():
                            if "Over" not in data or "Under" not in data:
                                continue

                            o_p = data["Over"]["price"]
                            u_p = data["Under"]["price"]
                            line = data["Over"]["point"]

                            o_b, u_b = market_bias(o_p, u_p)

                            p_conf = 0
                            if o_b > 0.58 or u_b > 0.58:
                                p_conf += 40
                            if o_p <= 1.80 or u_p <= 1.80:
                                p_conf += 30
                            if abs(o_p - u_p) >= 0.20:
                                p_conf += 20

                            if p_conf >= 70:
                                st.success(f"🔥 ELITE: {name} {line}")
                            elif p_conf >= 50:
                                st.warning(f"⚡ STRONG: {name} {line}")
                            else:
                                lean = "OVER" if o_b > u_b else "UNDER"
                                st.write(f"{name} {line} → Lean {lean}")

    except:
        continue
