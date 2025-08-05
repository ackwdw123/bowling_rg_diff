import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os

# Page layout
st.set_page_config(layout="wide")

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE_DIR, "bowling_balls.csv")
IMAGES_DIR = os.path.join(BASE_DIR, "images")

# --- Notes and Template Download ---
st.title("🎳 Bowling Ball Analyzer & Recommendation System")

st.markdown("""
**Instructions:**
1. You may upload a new CSV file to analyze bowling balls.  
2. Ensure the file is named **`bowling_balls.csv`**.  
3. Images may not be available unless you have a local `images` folder with ball images.  
4. You can download a **template CSV** here to create your own file:
""")

# Template download
if os.path.exists(CSV_PATH):
    with open(CSV_PATH, "rb") as f:
        st.download_button(
            label="📥 Download Current bowling_balls.csv as Template",
            data=f,
            file_name="bowling_balls_template.csv",
            mime="text/csv"
        )
else:
    st.warning("No default bowling_balls.csv found for download.")

# --- File Upload ---
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

# Lane surfaces with SR and Ra from USBC studies
LANE_SURFACES = {
    "Wood (New)": {
        "Description": "High friction, softer surface, hooks early",
        "Friction": "High",
        "Effect": "Strong early hook and less backend",
        "SR": 1.9, "Ra": 0.8
    },
    "Wood (Old)": {
        "Description": "Worn wood, more track wear, slightly smoother",
        "Friction": "Medium-High",
        "Effect": "Earlier hook, less consistent backend",
        "SR": 1.8, "Ra": 0.7
    },
    "Guardian Overlay": {
        "Description": "Thin plastic overlay on wood, reduces wear",
        "Friction": "Medium",
        "Effect": "Smoother front part, moderate backend",
        "SR": 1.7, "Ra": 0.65
    },
    "Murray": {
        "Description": "Medium-friction synthetic lane",
        "Friction": "Medium",
        "Effect": "Predictable motion, moderate backend",
        "SR": 1.55, "Ra": 0.5
    },
    "AMF SPL": {
        "Description": "Medium-low friction synthetic",
        "Friction": "Medium-Low",
        "Effect": "Longer skid, later hook",
        "SR": 1.35, "Ra": 0.3
    },
    "AMF HPL": {
        "Description": "Lower friction synthetic, smooth surface",
        "Friction": "Medium-Low",
        "Effect": "Skid through fronts, sharper backend",
        "SR": 1.5, "Ra": 0.45
    },
    "Anvilane 1": {
        "Description": "Early generation Brunswick synthetic",
        "Friction": "Low",
        "Effect": "Long skid, sharp backend",
        "SR": 1.4, "Ra": 0.35
    },
    "Anvilane 2": {
        "Description": "Improved synthetic with smoother front",
        "Friction": "Low",
        "Effect": "Very long skid, clean backend reaction",
        "SR": 1.35, "Ra": 0.3
    },
    "Pro Anvilane": {
        "Description": "Modern low-friction synthetic",
        "Friction": "Low",
        "Effect": "Maximum skid, strongest backend",
        "SR": 1.3, "Ra": 0.25
    }
}

# --- Lane Type Dropdown (fixed indexing) ---
lane_keys = list(LANE_SURFACES.keys())
lane_display = [f"{k} – {LANE_SURFACES[k]['Description']}" for k in lane_keys]

lane_index = st.selectbox("Select Lane Surface Type", range(len(lane_keys)),
                          format_func=lambda x: lane_display[x])
selected_lane_key = lane_keys[lane_index]
lane_props = LANE_SURFACES[selected_lane_key]
lane_friction_index = (lane_props["SR"] - lane_props["Ra"]) * 1.5

# --- Sliders ---
oil_length = st.slider("Oil Pattern Length (ft)", 20, 55, 40, 1)
oil_volume = st.slider("Oil Volume (mL)", 18.0, 27.0, 22.0, 0.5)
speed = st.slider("Ball Speed (mph)", 10.0, 20.0, 16.0, 0.5)
rev_rate = st.slider("Rev Rate (RPM)", 100, 600, 300, 50)
pin_to_pap = st.slider("Pin-to-PAP (inches)", 3.0, 6.0, 4.5, 0.5)

# Display lane friction indicator
if lane_friction_index >= 1.5:
    friction_color = "🟥 High Friction"
elif lane_friction_index >= 1.2:
    friction_color = "🟧 Medium-High Friction"
elif lane_friction_index >= 1.0:
    friction_color = "🟨 Medium Friction"
else:
    friction_color = "🟩 Low Friction"

st.markdown(f"**Lane Friction Index:** {lane_friction_index:.2f} {friction_color}")

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
        score += (diff * 150)
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
for role in roles:
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
    image_path = os.path.join(IMAGES_DIR, image_filename)
    if os.path.exists(image_path):
        st.image(image_path, caption=ball['Name'], width=250)
    else:
        st.warning("Ball image not found.")

    # Purple horizontal line
    st.markdown("<hr style='border:3px solid purple'>", unsafe_allow_html=True)

