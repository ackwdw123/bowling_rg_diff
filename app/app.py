import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os

# 🖼️ Page layout
st.set_page_config(layout="wide")

# Determine the current directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE_DIR, "bowling_balls.csv")
IMAGES_DIR = os.path.join(BASE_DIR, "images")

# Load CSV
st.title("🎳 Bowling Ball Analyzer")
uploaded_file = st.file_uploader("Upload a CSV file", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)
elif os.path.exists(CSV_PATH):
    df = pd.read_csv(CSV_PATH)
else:
    st.error("No CSV file found.")
    st.stop()

# Normalize IntDiff for symmetrical balls
if "IntDiff" in df.columns:
    df["IntDiff"] = df["IntDiff"].fillna("Symmetrical Ball")

# --- Quadrant Plot ---
def plot_all_quadrants(df):
    fig, ax = plt.subplots(figsize=(5, 5))
    rg_mid = (df["RG"].min() + df["RG"].max()) / 2
    diff_mid = (df["Diff"].min() + df["Diff"].max()) / 2

    ax.axhline(diff_mid, color='gray', linestyle='--')
    ax.axvline(rg_mid, color='gray', linestyle='--')

    for idx, row in df.iterrows():
        rg = row['RG']
        diff = row['Diff']
        name = row['Name']

        image_filename = name.lower().replace(" ", "_") + ".png"
        image_path = os.path.join(IMAGES_DIR, image_filename)

        if os.path.exists(image_path):
            img = plt.imread(image_path)
            ax.imshow(img, extent=(rg-0.002, rg+0.002, diff-0.0008, diff+0.0008), aspect='auto')
        else:
            ax.scatter(rg, diff, color='blue', s=40)

    ax.set_xlim(df["RG"].min()-0.005, df["RG"].max()+0.005)
    ax.set_ylim(df["Diff"].min()-0.002, df["Diff"].max()+0.002)
    ax.set_xlabel("RG")
    ax.set_ylabel("Differential")
    ax.set_title("RG/Diff Quadrant")
    st.pyplot(fig)

st.subheader("RG/Diff Quadrant Classification")
plot_all_quadrants(df)

# --- Bowler Inputs ---
oil_length = st.slider("Oil Pattern Length (ft)", 20, 55, 40)
speed = st.selectbox("Ball Speed (mph)", [14, 15, 16, 17, 18])
rev_rate = st.selectbox("Rev Rate (RPM)", [200, 300, 400, 500])
pin_to_pap = st.selectbox("Pin-to-PAP (inches)", [3, 4, 5, 6])
coverstock_input = st.selectbox(
    "Preferred Coverstock Type",
    ["Any", "Solid", "Hybrid", "Pearl", "Urethane"]
)

# --- Scoring Function ---
def score_ball(row, oil_length, speed, rev_rate, pin_to_pap, coverstock_input):
    rg = row['RG']
    diff = row['Diff']
    intdiff = row['IntDiff']
    cover_type = str(row.get('CoverstockType', 'Unknown')).lower()

    score = 0

    # --- Oil Pattern Matching ---
    if oil_length <= 35:  # short
        score += rg * 20                   # high RG for skid
        score += (0.08 - diff) * 200       # lower diff = smoother
        if intdiff == "Symmetrical Ball":
            score += 20
        if "pearl" in cover_type or "urethane" in cover_type:
            score += 40
    elif oil_length >= 45:  # long
        score += (2 - rg) * 20             # low RG starts earlier
        score += diff * 200                # high diff = flare
        if intdiff != "Symmetrical Ball":
            score += 20
        if "solid" in cover_type or "hybrid" in cover_type:
            score += 40
    else:  # medium
        score += 10
        score += diff * 100
        if "hybrid" in cover_type:
            score += 20

    # --- Speed Matching ---
    if speed >= 17:  # fast speed needs stronger balls
        if "solid" in cover_type or intdiff != "Symmetrical Ball":
            score += 20
    else:  # slower speed needs length
        if "pearl" in cover_type or intdiff == "Symmetrical Ball":
            score += 20

    # --- Rev Rate Matching ---
    score += (rev_rate / 100) * diff * 5

    # --- Pin-to-PAP Matching ---
    if pin_to_pap <= 4:
        score += diff * 50  # more flare
    else:
        score += (0.08 - diff) * 50  # smoother backend

    # --- Coverstock Preference Weighting ---
    if coverstock_input != "Any" and coverstock_input.lower() in cover_type:
        score += 50  # strong preference match

    return score

# --- Recommend Ball ---
df["Score"] = df.apply(
    lambda row: score_ball(row, oil_length, speed, rev_rate, pin_to_pap, coverstock_input),
    axis=1
)
recommended_ball = df.sort_values("Score", ascending=False).iloc[0]

st.markdown("## 🎯 Recommended Ball")
st.write(f"**{recommended_ball['Name']}**")
st.write(f"RG: {recommended_ball['RG']}, Diff: {recommended_ball['Diff']}, IntDiff: {recommended_ball['IntDiff']}")
st.write(f"Coverstock: {recommended_ball.get('Coverstock', 'Unknown')} ({recommended_ball.get('CoverstockType', 'Unknown')})")

# Display image
image_filename = recommended_ball['Name'].lower().replace(" ", "_") + ".png"
image_path = os.path.join(IMAGES_DIR, image_filename)
if os.path.exists(image_path):
    st.image(image_path, caption=recommended_ball['Name'], width=250)
else:
    st.warning("Recommended ball image not found.")

