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

# --- Title / Intro ---
st.title("🎳 Bowling Ball Analyzer & Recommendation System")
st.markdown("""
**Instructions:**
1. Upload a custom `bowling_balls.csv` file to analyze your arsenal.
2. If a ball image is missing, upload a `.png` below. The filename **must** match the ball name (lowercase, spaces → underscores).
3. You can also download your current `bowling_balls.csv` as a template.
""")

# Template download (optional)
if os.path.exists(CSV_PATH):
    with open(CSV_PATH, "rb") as f:
        st.download_button(
            label="📥 Download CSV Template",
            data=f,
            file_name="bowling_balls_template.csv",
            mime="text/csv"
        )

# CSV upload
uploaded_file = st.file_uploader("Upload a CSV file", type=["csv"])
if uploaded_file:
    df = pd.read_csv(uploaded_file)
elif os.path.exists(CSV_PATH):
    df = pd.read_csv(CSV_PATH)
else:
    st.error("No CSV file found. Please upload one to continue.")
    st.stop()

# Ball image upload (right under CSV upload)
uploaded_images = st.file_uploader("Upload Ball Images (.png)", type=["png"], accept_multiple_files=True)
if uploaded_images:
    os.makedirs(IMAGES_DIR, exist_ok=True)
    for img in uploaded_images:
        with open(os.path.join(IMAGES_DIR, img.name), "wb") as f:
            f.write(img.read())
    st.success(f"Uploaded {len(uploaded_images)} image(s).")

# Normalize IntDiff
if "IntDiff" in df.columns:
    df["IntDiff"] = df["IntDiff"].fillna("Symmetrical Ball")

# --- Quadrant plot ---
def plot_all_quadrants(df):
    fig, ax = plt.subplots(figsize=(5, 5))
    rg_mid = (df["RG"].min() + df["RG"].max()) / 2
    diff_mid = (df["Diff"].min() + df["Diff"].max()) / 2

    ax.axhline(diff_mid, color='gray', linestyle='--')
    ax.axvline(rg_mid, color='gray', linestyle='--')

    for _, row in df.iterrows():
        rg, diff, name = row["RG"], row["Diff"], row["Name"]
        fname = name.lower().replace(" ", "_") + ".png"
        img_path = os.path.join(IMAGES_DIR, fname)
        if os.path.exists(img_path):
            img = plt.imread(img_path)
            ax.imshow(img, extent=(rg-0.002, rg+0.002, diff-0.0008, diff+0.0008), aspect='auto')
        else:
            ax.text(rg, diff, name, fontsize=6, ha='center', va='center', color='blue')

    ax.set_xlim(df["RG"].min() - 0.005, df["RG"].max() + 0.005)
    ax.set_ylim(df["Diff"].min() - 0.002, df["Diff"].max() + 0.002)
    ax.set_xlabel("RG", fontsize=10)
    ax.set_ylabel("Differential", fontsize=10)
    ax.set_title("RG/Diff Quadrant", fontsize=11)
    ax.tick_params(labelsize=8)
    st.pyplot(fig)

st.subheader("RG/Diff Quadrant Classification")
plot_all_quadrants(df)

# --- Lane surfaces ---
LANE_SURFACES = {
    "Wood (New)": {"SR": 1.9, "Ra": 0.8, "desc": "High friction, early hook potential."},
    "Wood (Old)": {"SR": 1.8, "Ra": 0.7, "desc": "Medium-high friction, smoother reaction."},
    "Guardian Overlay": {"SR": 1.7, "Ra": 0.65, "desc": "Protective overlay, slightly reduced friction."},
    "Murray": {"SR": 1.6, "Ra": 0.55, "desc": "Medium friction synthetic lane."},
    "AMF SPL": {"SR": 1.35, "Ra": 0.3, "desc": "Medium-low friction, later ball motion."},
    "AMF HPL": {"SR": 1.5, "Ra": 0.45, "desc": "Medium friction, smooth backend."},
    "Anvilane 1": {"SR": 1.4, "Ra": 0.35, "desc": "Durable surface, controlled motion."},
    "Anvilane 2": {"SR": 1.35, "Ra": 0.3, "desc": "Lower friction, delayed hook."},
    "Pro Anvilane": {"SR": 1.3, "Ra": 0.25, "desc": "Very low friction, long skid and sharp backend."}
}

# Lane surface selector (under graph)
lane_type = st.selectbox("Lane Surface Type", list(LANE_SURFACES.keys()))
lane_props = LANE_SURFACES[lane_type]
lane_friction_index = (lane_props["SR"] - lane_props["Ra"]) * 1.5
st.markdown(f"**Lane Description:** {lane_props['desc']}")
st.markdown(f"**Lane Friction Index:** {lane_friction_index:.2f}")

# --- Bowler inputs ---
oil_length = st.slider("Oil Pattern Length (ft)", 20, 55, 40, 1)
oil_volume = st.slider("Oil Volume (mL)", 18.0, 27.0, 22.0, 0.5)
speed = st.slider("Ball Speed (mph)", 10.0, 20.0, 16.0, 0.5)
rev_rate = st.slider("Rev Rate (RPM)", 100, 600, 300, 50)
pin_to_pap = st.slider("Pin-to-PAP (inches)", 2.5, 6.0, 4.5, 0.5)

# Lane condition label (used in reasoning)
if oil_length >= 45 or oil_volume >= 24:
    lane_condition = "heavy"
elif oil_length <= 35 or oil_volume <= 20:
    lane_condition = "light"
else:
    lane_condition = "medium"

# --- Expected roll string builder ---
def expected_roll(row, lane_friction_index, lane_type, lane_condition):
    parts = []
    # Base by friction
    if lane_friction_index >= 1.5:
        parts.append("earlier read with smoother overall motion")
    elif lane_friction_index >= 1.2:
        parts.append("controlled midlane read with moderate backend")
    else:
        parts.append("longer skid with potential for sharper backend")

    cover = str(row.get("CoverstockType", "")).lower()
    if "solid" in cover:
        parts.append("solid cover adds traction in oil")
    elif "hybrid" in cover:
        parts.append("hybrid balances length and control")
    elif "pearl" in cover:
        parts.append("pearl adds length and backend pop")
    elif "urethane" in cover:
        parts.append("urethane smooths the breakpoint")

    rg = row["RG"]
    diff = row["Diff"]
    if rg < 2.50:
        parts.append("low RG helps it rev earlier")
    elif rg > 2.55:
        parts.append("high RG delays roll")

    if diff >= 0.050:
        parts.append("high diff increases flare/overall hook")
    elif diff <= 0.035:
        parts.append("low diff keeps shape smoother")

    if row["IntDiff"] != "Symmetrical Ball":
        parts.append("asym core adds a stronger direction change")

    # Lane condition hint
    if lane_condition == "heavy":
        parts.append("works best with head oil present")
    elif lane_condition == "light":
        parts.append("better once lanes have transitioned or on friction")

    return "; ".join(parts)

# --- Scoring function (includes PAP) ---
def score_ball(row, role):
    rg = row['RG']
    diff = row['Diff']
    intdiff = row['IntDiff']
    cover_type = str(row.get('CoverstockType', 'Unknown')).lower()
    score = 0
    friction_adjust = 1 - (lane_friction_index - 1.0) * 0.2

    if role == "fresh":
        score += (2.60 - rg) * 50 * friction_adjust
        score += diff * 300
        if intdiff != "Symmetrical Ball":
            score += 30
        if lane_condition == "heavy" and "solid" in cover_type:
            score += 50
        if lane_condition == "light" and ("pearl" in cover_type or "urethane" in cover_type):
            score -= 50

    elif role == "transition":
        score += (2.55 - abs(2.50 - rg)) * 40 * friction_adjust
        score += diff * 150
        if lane_condition == "medium" and ("hybrid" in cover_type or "pearl" in cover_type):
            score += 40

    elif role == "burned":
        score += rg * 40
        score += (0.08 - diff) * 300
        if lane_condition == "light":
            if "pearl" in cover_type or "urethane" in cover_type:
                score += 80
            if "solid" in cover_type or intdiff != "Symmetrical Ball":
                score -= 50

    # Speed + rev rate
    if speed >= 17 and "solid" in cover_type:
        score += 10
    elif speed <= 13 and ("pearl" in cover_type or "urethane" in cover_type):
        score += 10

    score += (rev_rate / 100) * diff * 5

    # Pin-to-PAP: ≤4" favors higher diff; >4" favors lower diff
    if pin_to_pap <= 4.0:
        score += diff * 50
    else:
        score += (0.08 - diff) * 50

    return score

# --- Recommend three balls ---
roles = ["fresh", "transition", "burned"]
recommendations = {}

for role in roles:
    df[f"{role}_score"] = df.apply(lambda r: score_ball(r, role), axis=1)
    recommendations[role] = df.sort_values(f"{role}_score", ascending=False).iloc[0]

# --- Recommended Arsenal ---
st.markdown("## 🎯 Recommended Arsenal")
st.caption(f"Lane type chosen: **{lane_type}**")

for idx, role in enumerate(roles):
    ball = recommendations[role]
    role_label = {
        "fresh": "Fresh Oil (First Ball)",
        "transition": "Transition (Second Ball)",
        "burned": "Burned Lanes (Third Ball)",
    }[role]

    st.subheader(role_label)
    st.write(f"**{ball['Name']}**")
    st.write(f"RG: {ball['RG']}, Diff: {ball['Diff']}, IntDiff: {ball['IntDiff']}")
    st.write(f"Coverstock: {ball.get('Coverstock', 'Unknown')} ({ball.get('CoverstockType', 'Unknown')})")
    st.write(f"**Score:** {ball[f'{role}_score']:.2f}")
    st.write(
        f"**Expected ball roll on lane type chosen:** "
        f"{expected_roll(ball, lane_friction_index, lane_type, lane_condition)}"
    )

    image_path = os.path.join(IMAGES_DIR, ball['Name'].lower().replace(" ", "_") + ".png")
    if os.path.exists(image_path):
        st.image(image_path, caption=ball['Name'], width=250)

    if idx < len(roles) - 1:
        st.markdown("<hr style='border:2px solid purple'>", unsafe_allow_html=True)

# --- Balls Not Chosen (single condensed list) ---
st.markdown("<hr style='border:2px solid maroon'>", unsafe_allow_html=True)
st.markdown("## 🧾 Balls Not Chosen")
st.caption(f"Lane type chosen: **{lane_type}**")

chosen_names = {recommendations[r]["Name"] for r in roles}
not_chosen_df = df[~df["Name"].isin(chosen_names)].copy()

for _, row in not_chosen_df.iterrows():
    st.write(f"**{row['Name']}**")
    st.write(f"RG: {row['RG']}, Diff: {row['Diff']}, IntDiff: {row['IntDiff']}")
    st.write(f"Coverstock: {row.get('Coverstock', 'Unknown')} ({row.get('CoverstockType', 'Unknown')})")
    # Show all role scores so the user sees context
    scores_line = " | ".join([f"{r.title()} Score: {row[f'{r}_score']:.2f}" for r in roles if f'{r}_score' in row])
    if scores_line:
        st.write(scores_line)
    # Replace old 'not selected' message with expected roll line
    st.write(
        f"**Expected ball roll on lane type chosen:** "
        f"{expected_roll(row, lane_friction_index, lane_type, lane_condition)}"
    )

    img_path = os.path.join(IMAGES_DIR, row['Name'].lower().replace(" ", "_") + ".png")
    if os.path.exists(img_path):
        st.image(img_path, caption=row['Name'], width=200)
    st.markdown("---")
