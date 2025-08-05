import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os

# --- Page Layout ---
st.set_page_config(layout="wide")
st.title("🎳 Bowling Ball Analyzer & Recommendation System")

# --- CSV Upload Section ---
st.markdown("""
**Instructions:**
1. You may upload a new CSV file containing your bowling ball data.  
2. Ensure the file is named **`bowling_balls.csv`**.  
3. Images of balls may not be available since this app does not include a ball image library.  
4. A template CSV is available for download below.
""")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE_DIR, "bowling_balls.csv")

# Download Template
if os.path.exists(CSV_PATH):
    with open(CSV_PATH, "rb") as f:
        st.download_button("📥 Download Template CSV", f, file_name="bowling_balls_template.csv")

# File Uploader
uploaded_file = st.file_uploader("Upload a CSV file", type=["csv"])
if uploaded_file:
    df = pd.read_csv(uploaded_file)
elif os.path.exists(CSV_PATH):
    df = pd.read_csv(CSV_PATH)
else:
    st.error("No CSV file found. Please upload a file or provide bowling_balls.csv in the app folder.")
    st.stop()

# Normalize IntDiff for symmetrical balls
if "IntDiff" in df.columns:
    df["IntDiff"] = df["IntDiff"].fillna("Symmetrical Ball")

# --- Lane Surface Data (with friction) ---
LANE_SURFACES = {
    "Wood (New)": {"SR": 2.0, "Ra": 0.85, "Desc": "High friction, strong early hook."},
    "Wood (Old)": {"SR": 1.8, "Ra": 0.75, "Desc": "Medium friction, smoother reaction."},
    "Guardian Overlay": {"SR": 1.7, "Ra": 0.65, "Desc": "Lower friction overlay, skid in heads."},
    "Murray": {"SR": 1.6, "Ra": 0.55, "Desc": "Medium-low friction synthetic."},
    "AMF SPL": {"SR": 1.35, "Ra": 0.3, "Desc": "Lower friction, sharper backend."},
    "AMF HPL": {"SR": 1.5, "Ra": 0.45, "Desc": "Moderate friction synthetic."},
    "Anvilane 1": {"SR": 1.4, "Ra": 0.35, "Desc": "Medium-low friction, consistent wear."},
    "Anvilane 2": {"SR": 1.35, "Ra": 0.32, "Desc": "Slightly lower friction than Anvilane 1."},
    "Pro Anvilane": {"SR": 1.3, "Ra": 0.25, "Desc": "Lowest friction, long skid, strong backend."}
}

# --- Quadrant Plot Function ---
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
        image_path = os.path.join(BASE_DIR, "images", image_filename)

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
st.subheader("Bowler & Lane Inputs")

# Lane type first to avoid dropdown clipping
lane_type = st.selectbox("Lane Surface Type", list(LANE_SURFACES.keys()))

oil_length = st.slider("Oil Pattern Length (ft)", 20, 55, 40, 1)
oil_volume = st.slider("Oil Volume (mL)", 18.0, 27.0, 22.0, 0.5)
speed = st.slider("Ball Speed (mph)", 10.0, 20.0, 16.0, 0.5)
rev_rate = st.slider("Rev Rate (RPM)", 100, 600, 300, 50)
pin_to_pap = st.slider("Pin-to-PAP (inches)", 3.0, 6.0, 4.5, 0.5)

# Lane friction calculation
lane_props = LANE_SURFACES[lane_type]
lane_friction_index = (lane_props["SR"] - lane_props["Ra"]) * 1.5

# Friction Indicator
if lane_friction_index >= 1.5:
    friction_color = "🟥 High Friction"
elif lane_friction_index >= 1.2:
    friction_color = "🟧 Medium-High Friction"
elif lane_friction_index >= 1.0:
    friction_color = "🟨 Medium Friction"
else:
    friction_color = "🟩 Low Friction"

st.markdown(f"**Lane Friction Index:** {lane_friction_index:.2f} {friction_color}")
st.markdown(f"**Description:** {lane_props['Desc']}")

# Determine lane condition
if oil_length >= 45 or oil_volume >= 24:
    lane_condition = "heavy"
elif oil_length <= 35 or oil_volume <= 20:
    lane_condition = "light"
else:
    lane_condition = "medium"

# --- Scoring Function ---
def score_ball(row, oil_length, oil_volume, speed, rev_rate, pin_to_pap, lane_friction_index, role):
    rg = row['RG']
    diff = row['Diff']
    intdiff = row['IntDiff']
    cover_type = str(row.get('CoverstockType', 'Unknown')).lower()

    score = 0
    friction_adjustment = 1 - (lane_friction_index - 1.0) * 0.2

    if role == "fresh":
        score += (2.60 - rg) * 50 * friction_adjustment
        score += diff * 300
        if intdiff != "Symmetrical Ball":
            score += 30
        if lane_condition == "heavy" and "solid" in cover_type:
            score += 50
        if lane_condition == "light" and ("pearl" in cover_type or "urethane" in cover_type):
            score -= 50

    elif role == "transition":
        score += (2.55 - abs(2.50 - rg)) * 40 * friction_adjustment
        score += diff * 150
        if lane_condition == "medium":
            if "hybrid" in cover_type or "pearl" in cover_type:
                score += 40

    elif role == "burned":
        score += rg * 40
        score += (0.08 - diff) * 300
        if lane_condition == "light":
            if "pearl" in cover_type or "urethane" in cover_type:
                score += 80
            if "solid" in cover_type or intdiff != "Symmetrical Ball":
                score -= 50

    if speed >= 17 and "solid" in cover_type:
        score += 10
    elif speed <= 13 and ("pearl" in cover_type or "urethane" in cover_type):
        score += 10

    rev_score = (rev_rate / 100) * diff * 5
    score += rev_score

    if pin_to_pap <= 4:
        score += diff * 50
    else:
        score += (0.08 - diff) * 50

    return score

# --- Recommend 3 Balls ---
roles = ["fresh", "transition", "burned"]
recommendations = {}

for role in roles:
    df[role + "_score"] = df.apply(
        lambda row: score_ball(row, oil_length, oil_volume, speed, rev_rate, pin_to_pap, lane_friction_index, role),
        axis=1
    )
    recommendations[role] = df.sort_values(role + "_score", ascending=False).iloc[0]

# --- Display Recommendations ---
st.markdown("## 🎳 Recommended Arsenal")
for i, role in enumerate(roles):
    ball = recommendations[role]
    role_label = {
        "fresh": "Fresh Oil (First Ball)", 
        "transition": "Transition (Second Ball)",
        "burned": "Burned Lanes (Third Ball)"
    }
    
    st.subheader(role_label[role])
    st.write(f"**{ball['Name']}**")
    st.write(f"RG: {ball['RG']}, Diff: {ball['Diff']}, IntDiff: {ball['IntDiff']}")
    st.write(f"Coverstock: {ball.get('Coverstock', 'Unknown')} ({ball.get('CoverstockType', 'Unknown')})")
    
    image_filename = ball['Name'].lower().replace(" ", "_") + ".png"
    image_path = os.path.join(BASE_DIR, "images", image_filename)
    if os.path.exists(image_path):
        st.image(image_path, caption=ball['Name'], width=250)
    else:
        st.warning("Ball image not found.")
    
    # Purple horizontal line between recommendations
    if i < len(roles) - 1:
        st.markdown("<hr style='border: 2px solid purple;'>", unsafe_allow_html=True)

