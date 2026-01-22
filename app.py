import streamlit as st

# ------------------------
# Password protection
# ------------------------
PASSWORD = "changethispassword"

st.sidebar.title("🔒 Private Access")
password = st.sidebar.text_input("Password", type="password")

if password != PASSWORD:
    st.warning("Access denied")
    st.stop()

# ------------------------
# App UI
# ------------------------
st.set_page_config(page_title="NBA Player Props AI", layout="centered")

st.title("🏀 NBA Player Props AI")
st.subheader("Points Projection Dashboard")

st.divider()

player = st.text_input("Player Name", "Example Player")
line = st.number_input("Sportsbook Line (Points)", step=0.5, value=22.5)

minutes = st.slider("Projected Minutes", 10, 42, 34)
shots = st.slider("Shot Attempts", 5, 30, 18)
fta = st.slider("Free Throw Attempts", 0, 15, 5)
std = st.slider("Player Volatility (Std Dev)", 3.0, 10.0, 6.0)

if st.button("📈 Predict"):
    mean = minutes * 0.7 + shots * 1.8 + fta * 0.8
    prob_over = 1 - norm.cdf(line, mean, std)

    st.divider()
    st.subheader(f"📊 Projection for {player}")

    st.metric("Projected Points", f"{mean:.2f}")
    st.metric("Over Probability", f"{prob_over*100:.1f}%")

    implied_prob = 0.524  # ~ -110
    edge = (prob_over - implied_prob) * 100

    st.metric("Model Edge", f"{edge:.2f}%")

    if edge >= 6:
        st.success("✅ BET SIGNAL (Edge ≥ 6%)")
    else:
        st.warning("⚠️ No Bet — Edge Too Small")
