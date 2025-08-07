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

# --- Instructions and CSV Template ---
st.title("🎳 Bowling Ball Analyzer & Recommendation System")

st.markdown("""
**Instructions:**
1. You can upload a custom `bowling_balls.csv` file to analyze your own arsenal.
2. Images may not appear if there is no matching `.png` image in the `images` folder.
3. Use the template below to create your own CSV file.
""")

if os.path.exists(CSV_PATH):
    with open(CSV_PATH, "rb") as f:
        st.download_button(
            label="📥 Download CSV Template",
            data=f,
            file_name="bowling_balls_template.csv",
            mime="text/csv"
        )

# --- CSV Upload ---
uploaded_file = st.file_uploader("Upload a CSV file", type=["csv"])
if uploaded_file:
    df = pd.read_csv(uploaded_file)
elif os.path.exists(CSV_PATH):
    df = pd.read_csv(CSV_PATH)
else:
    st.error("No CSV file found. Please upload a file to continue.")
    st.stop()

# --- Image Upload ---
st.markdown("### Optional: Upload image for new ball")
ball_image = st.file_uploader("Upload a PNG image (match the name of the ball)", type=["png"])
if ball_image:
    image_path = os.path.join(IMAGES_DIR, ball_image.name)
    with open(image_path, "wb") as f:
        f.write(ball_image.read())
    st.success(f"Saved: {ball_image.name}")

# --- Quadrant Plot ---
def plot_all_quadrants(df):
    fig, ax = plt.subplots(figsize=(5, 5))
    rg_mid = (df["RG"].min() + df["RG"].max()) / 2
    diff_mid = (df["Diff"].min() + df["Diff"].max()) / 2

    ax.axhline(diff_mid, color='gray', linestyle='--')
    ax.axvline(rg_mid, color='gray', linestyle='--')

    for _, row in df.iterrows():
        rg = row['RG']
        diff = row['Diff']
        name = row['Name']
        image_filename = name.lower().replace(" ", "_") + ".png"
        image_path = os.path.join(IMAGES_DIR, image_filename)

        if os.path.exists(image_path):
            img = plt.imread(image_path)
            ax.imshow(img, extent=(rg-0.002, rg+0.002, diff-0.0008, diff+0.0008), aspect='auto')
        else:
            ax.scatter(rg, diff, color='blue', s=20)

    ax.set_xlim(df["RG"].min()-0.005, df["RG"].max()+0.005)
    ax.set_ylim(df["Diff"].min()-0.002, df["Diff"].max()+0.002)
    ax.set_xlabel("RG", fontsize=8)
    ax.set_ylabel("Differential", fontsize=8)
    ax.set_title("RG/Diff Quadrant", fontsize=10)
    ax.tick_params(axis='both', labelsize=6)
    st.pyplot(fig)

st.subheader("RG/Diff Quadrant Classification")
plot_all_quadrants(df)

# --- Lane Surface Type ---
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

lane_type = st.selectbox("Lane Surface Type", list(LANE_SURFACES.keys()))
lane_props = LANE_SURFACES[lane_type]
lane_friction_index = (lane_props["SR"] - lane_props["Ra"]) * 1.5

st.markdown(f"**Lane Description:** {lane_props['desc']}")
st.markdown(f"**Lane Friction Index:** {lane_friction_index:.2f}")

# --- Bowler Inputs ---
oil_length = st.slider("Oil Pattern Length (ft)", 20, 55, 40, 1)
oil_volume = st.slider("Oil Volume (mL)", 18.0, 27.0, 22.0, 0.5)
speed = st.slider("Ball Speed (mph)", 10.0, 20.0, 16.0, 0.5)
rev_rate = st.slider("Rev Rate (RPM)", 100, 600, 300, 50)
pin_to_pap = st.slider("Pin-to-PAP (inches)", 2.5, 6.0, 4.5, 0.5)

# Determine lane condition
if oil_length >= 45 or oil_volume >= 24:
    lane_condition = "heavy"
elif oil_length <= 35 or oil_volume <= 20:
    lane_condition = "light"
else:
    lane_condition = "medium"

# Normalize IntDiff
if "IntDiff" in df.columns:
    df["IntDiff"] = df["IntDiff"].fillna("Symmetrical Ball")

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

    # Speed & Rev adjustments
    if speed >= 17 and "solid" in cover_type:
        score += 10
    elif speed <= 13 and ("pearl" in cover_type or "urethane" in cover_type):
        score += 10

    # Rev rate contribution
    score += (rev_rate / 100) * diff * 5

    # Pin-to-PAP effect
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
    st.subheader(f"{role.title()} Oil Ball")
    st.write(f"**{ball['Name']}**")
    st.write(f"RG: {ball['RG']}, Diff: {ball['Diff']}, IntDiff: {ball['IntDiff']}")
    st.write(f"Coverstock: {ball.get('Coverstock', 'Unknown')} ({ball.get('CoverstockType', 'Unknown')})")
    st.write(f"Score: {ball[role + '_score']:.2f}")

    image_filename = ball['Name'].lower().replace(" ", "_") + ".png"
    image_path = os.path.join(IMAGES_DIR, image_filename)
    if os.path.exists(image_path):
        st.image(image_path, caption=ball['Name'], width=250)
    else:
        st.warning("Ball image not found.")

# --- Full Ball List ---
st.markdown("""
<hr style='border:2px solid maroon'>
<h4>Balls Not Chosen</h4>
""", unsafe_allow_html=True)

chosen_ids = [b['Name'] for b in recommendations.values()]

for idx, row in df.iterrows():
    if row['Name'] not in chosen_ids:
        st.write(f"**{row['Name']}**")
        st.write(f"RG: {row['RG']}, Diff: {row['Diff']}, IntDiff: {row['IntDiff']}")
        st.write(f"Coverstock: {row.get('Coverstock', 'Unknown')} ({row.get('CoverstockType', 'Unknown')})")
        scores = [row[role + '_score'] for role in roles]
        st.write(f"Scores - Fresh: {scores[0]:.2f}, Transition: {scores[1]:.2f}, Burned: {scores[2]:.2f}")
        st.write("Not selected due to lower combined scoring compared to chosen options.")
        image_filename = row['Name'].lower().replace(" ", "_") + ".png"
        image_path = os.path.join(IMAGES_DIR, image_filename)
        if os.path.exists(image_path):
            st.image(image_path, caption=row['Name'], width=250)

