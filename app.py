import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# --- 1. PRIVATE ACCESS ---
PASSWORD = "benja123"
st.sidebar.title("🏀 NBA PRIVATE ACCESS")
password = st.sidebar.text_input("Password", type="password")

if password != PASSWORD:
    st.warning("Locked. Enter password to view NBA data.")
    st.stop()

# Auto-refresh every 20 mins to save credits (500 limit friendly)
st_autorefresh(interval=1200000, key="nba_master_sync") 

# --- 2. CONFIG ---
st.set_page_config(page_title="NBA COMMAND CENTER", layout="wide", page_icon="🏀")
NEW_API_KEY = "27970d14c8e8eb9f2a217c775db6571f" 

# --- 3. DATA FETCHING (GAME TOTALS + PROPS) ---
@st.cache_data(ttl=1200)
def get_nba_data(api_key):
    # Pulls all live and upcoming games for the next ~7 days
    url = f"https://api.the-odds-api.com/v4/sports/basketball_nba/odds/?apiKey={api_key}&regions=us&markets=totals&oddsFormat=decimal"
    try:
        r = requests.get(url)
        if r.status_code == 200:
            return r.json(), r.headers.get('x-requests-remaining', 'N/A')
        return None, "Error"
    except:
        return None, "Offline"

@st.cache_data(ttl=1200)
def get_full_props(api_key, event_id):
    # Markets: Points, Rebounds, Assists (Supports Over/Under)
    markets = "player_points,player_rebounds,player_assists"
    url = f"https://api.the-odds-api.com/v4/sports/basketball_nba/events/{event_id}/odds?apiKey={api_key}&regions=us&markets={markets}&oddsFormat=decimal"
    try:
        r = requests.get(url)
        return r.json() if r.status_code == 200 else None
    except:
        return None

# --- 4. MAIN INTERFACE ---
st.title("🏀 NBA MASTER COMMAND")
st.markdown(f"**Live Feed:** {pd.Timestamp.now().strftime('%B %d, %Y')}")

nba_data, credits_left = get_nba_data(NEW_API_KEY)
st.sidebar.metric("API Credits Left", credits_left)

if nba_data:
    # Sort games by date automatically
    nba_data = sorted(nba_data, key=lambda x: x['commence_time'])
    
    st.write(f"📡 **Scanner Status:** Connected. Monitoring {len(nba_data)} games (Next 7 Days).")
    
    for game in nba_data:
        home, away = game['home_team'], game['away_team']
        event_id = game['id']
        commence_dt = pd.to_datetime(game['commence_time'])
        display_time = commence_dt.strftime('%m/%d | %I:%M %p')
        
        try:
            # --- GAME TOTALS ANALYSIS ---
            bookie = game['bookmakers'][0]
            market = next(m for m in bookie['markets'] if m['key'] == 'totals')
            over_out = next(o for o in market['outcomes'] if o['name'] == 'Over')
            under_out = next(o for o in market['outcomes'] if o['name'] == 'Under')
            
            line = over_out['point']
            o_price, u_price = over_out['price'], under_out['price']
            
            # --- TRUSTED LOGIC ---
            # TRUSTED OVER: High total (235+) or heavily juiced Over (< 1.85)
            # TRUSTED UNDER: Low total (< 215) or heavily juiced Under (< 1.85)
            is_over = line > 235 or o_price < 1.88
            is_under = line < 218 or u_price < 1.88
            
            status_icon = "🔥" if (is_over or is_under) else "📅"
            title = f"{status_icon} {away} @ {home} ({display_time})"
            
            with st.expander(title, expanded=is_over or is_under):
                c1, c2, c3 = st.columns(3)
                c1.metric("Game Total", f"{line}")
                c2.metric("Over Price", f"{o_price}", delta="TRUSTED" if is_over else None)
                c3.metric("Under Price", f"{u_price}", delta="TRUSTED" if is_under else None, delta_color="inverse")
                
                if is_over: st.success(f"✅ **ACTION:** Take the OVER {line}")
                elif is_under: st.warning(f"📉 **ACTION:** Take the UNDER {line}")

                # --- PLAYER PROPS SECTION ---
                st.markdown("---")
                if st.button(f"Scan All Props for {away} @ {home}", key=f"props_{event_id}"):
                    with st.spinner("Analyzing player markets..."):
                        props = get_full_props(NEW_API_KEY, event_id)
                        if props and 'bookmakers' in props:
                            for b in props['bookmakers']:
                                for mkt in b['markets']:
                                    m_name = mkt['key'].replace('player_', '').replace('_', ' ').title()
                                    st.write(f"📍 **{m_name}**")
                                    # Create columns for clean Over/Under player views
                                    for out in mkt['outcomes']:
                                        color = "🟢" if out['name'] == 'Over' else "🔴"
                                        st.write(f"{color} {out['description']}: {out['name']} {out['point']} @ {out['price']}")
                        else:
                            st.info("Props typically release 2-4 hours before tip-off.")
        except Exception:
            continue
else:
    st.error("Connection Failed. Check API Credits.")import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# --- 1. PRIVATE ACCESS ---
PASSWORD = "benja123"
st.sidebar.title("🏀 NBA PRIVATE ACCESS")
password = st.sidebar.text_input("Password", type="password")

if password != PASSWORD:
    st.warning("Locked. Enter password to view NBA data.")
    st.stop()

# Auto-refresh every 20 mins to save credits (500 limit friendly)
st_autorefresh(interval=1200000, key="nba_master_sync") 

# --- 2. CONFIG ---
st.set_page_config(page_title="NBA COMMAND CENTER", layout="wide", page_icon="🏀")
NEW_API_KEY = "27970d14c8e8eb9f2a217c775db6571f" 

# --- 3. DATA FETCHING (GAME TOTALS + PROPS) ---
@st.cache_data(ttl=1200)
def get_nba_data(api_key):
    # Pulls all live and upcoming games for the next ~7 days
    url = f"https://api.the-odds-api.com/v4/sports/basketball_nba/odds/?apiKey={api_key}&regions=us&markets=totals&oddsFormat=decimal"
    try:
        r = requests.get(url)
        if r.status_code == 200:
            return r.json(), r.headers.get('x-requests-remaining', 'N/A')
        return None, "Error"
    except:
        return None, "Offline"

@st.cache_data(ttl=1200)
def get_full_props(api_key, event_id):
    # Markets: Points, Rebounds, Assists (Supports Over/Under)
    markets = "player_points,player_rebounds,player_assists"
    url = f"https://api.the-odds-api.com/v4/sports/basketball_nba/events/{event_id}/odds?apiKey={api_key}&regions=us&markets={markets}&oddsFormat=decimal"
    try:
        r = requests.get(url)
        return r.json() if r.status_code == 200 else None
    except:
        return None

# --- 4. MAIN INTERFACE ---
st.title("🏀 NBA MASTER COMMAND")
st.markdown(f"**Live Feed:** {pd.Timestamp.now().strftime('%B %d, %Y')}")

nba_data, credits_left = get_nba_data(NEW_API_KEY)
st.sidebar.metric("API Credits Left", credits_left)

if nba_data:
    # Sort games by date automatically
    nba_data = sorted(nba_data, key=lambda x: x['commence_time'])
    
    st.write(f"📡 **Scanner Status:** Connected. Monitoring {len(nba_data)} games (Next 7 Days).")
    
    for game in nba_data:
        home, away = game['home_team'], game['away_team']
        event_id = game['id']
        commence_dt = pd.to_datetime(game['commence_time'])
        display_time = commence_dt.strftime('%m/%d | %I:%M %p')
        
        try:
            # --- GAME TOTALS ANALYSIS ---
            bookie = game['bookmakers'][0]
            market = next(m for m in bookie['markets'] if m['key'] == 'totals')
            over_out = next(o for o in market['outcomes'] if o['name'] == 'Over')
            under_out = next(o for o in market['outcomes'] if o['name'] == 'Under')
            
            line = over_out['point']
            o_price, u_price = over_out['price'], under_out['price']
            
            # --- TRUSTED LOGIC ---
            # TRUSTED OVER: High total (235+) or heavily juiced Over (< 1.85)
            # TRUSTED UNDER: Low total (< 215) or heavily juiced Under (< 1.85)
            is_over = line > 235 or o_price < 1.88
            is_under = line < 218 or u_price < 1.88
            
            status_icon = "🔥" if (is_over or is_under) else "📅"
            title = f"{status_icon} {away} @ {home} ({display_time})"
            
            with st.expander(title, expanded=is_over or is_under):
                c1, c2, c3 = st.columns(3)
                c1.metric("Game Total", f"{line}")
                c2.metric("Over Price", f"{o_price}", delta="TRUSTED" if is_over else None)
                c3.metric("Under Price", f"{u_price}", delta="TRUSTED" if is_under else None, delta_color="inverse")
                
                if is_over: st.success(f"✅ **ACTION:** Take the OVER {line}")
                elif is_under: st.warning(f"📉 **ACTION:** Take the UNDER {line}")

                # --- PLAYER PROPS SECTION ---
                st.markdown("---")
                if st.button(f"Scan All Props for {away} @ {home}", key=f"props_{event_id}"):
                    with st.spinner("Analyzing player markets..."):
                        props = get_full_props(NEW_API_KEY, event_id)
                        if props and 'bookmakers' in props:
                            for b in props['bookmakers']:
                                for mkt in b['markets']:
                                    m_name = mkt['key'].replace('player_', '').replace('_', ' ').title()
                                    st.write(f"📍 **{m_name}**")
                                    # Create columns for clean Over/Under player views
                                    for out in mkt['outcomes']:
                                        color = "🟢" if out['name'] == 'Over' else "🔴"
                                        st.write(f"{color} {out['description']}: {out['name']} {out['point']} @ {out['price']}")
                        else:
                            st.info("Props typically release 2-4 hours before tip-off.")
        except Exception:
            continue
else:
    st.error("Connection Failed. Check API Credits.")
