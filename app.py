import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os

# 🖼️ Page layout
st.set_page_config(layout="wide")
st.title("🎳 Bowling Ball Analyzer & Recommendation System")

# 📤 CSV Upload or fallback
uploaded_file = st.file_uploader(
    "Upload a CSV file with columns: Name, RG, Diff, IntDiff, Coverstock, CoverstockType, Image, Speed, RevRate, PinToPAP",
    type=["csv"]
)
if uploaded_file:
    df = pd.read_csv(uploaded_file)
elif os.path.exists("bowling_balls.csv"):
    df = pd.read_csv("bowling_balls.csv")
else:
    st.error("No file uploaded and bowling_balls.csv not found.")
    st.stop()

# Normalize IntDiff for symmetrical balls
df["IntDiff"] = df["IntDiff"].apply(lambda x: "Symmetrical Ball" if pd.isna(x) else x)

# --- Quadrant Plot with Thumbnails ---
def plot_all_quadrants(df):
    fig, ax = plt.subplots(figsize=(6, 6))
    x_min, x_max = df["RG"].min(), df["RG"].max()
    y_min, y_max = df["Diff"].min(), df["Diff"].max()
    ax.axhline((y_min + y_max) / 2, color='gray', linestyle='--')
    ax.axvline((x_min + x_max) / 2, color='gray', linestyle='--')

    for idx, row in df.iterrows():
        rg, diff, name = row['RG'], row['Diff'], row['Name']
        image_filename = name.lower().replace(" ", "_") + ".png"
        image_path = os.path.join("images", image_filename)
        if os.path.exists(image_path):
            img = plt.imread(image_path)
            ax.imshow(img, extent=[rg-0.0025, rg+0.0025, diff-0.001, diff+0.001], aspect='auto', zorder=2)
        else:
            ax.scatter(rg, diff, color='red', s=80, label=name if idx == 0 else "", zorder=2)

    ax.set_xlim(x_min - 0.005, x_max + 0.005)
    ax.set_ylim(y_min - 0.002, y_max + 0.002)
    ax.set_xlabel("RG")
    ax.set_ylabel("Differential")
    ax.set_title("RG/Diff Quadrant")
    st.pyplot(fig)

# Show Quadrant Plot
st.subheader("RG/Diff Quadrant Classification")
plot_all_quadrants(df)

# Ball selector below graph
ball_names = df["Name"].tolist()
selected_ball = st.selectbox("Select a Ball", ball_names)
ball_row = df[df["Name"] == selected_ball].iloc[0]

# --- Bowler Info ---
st.subheader("🏹 Bowler Information")
col1, col2, col3 = st.columns(3)
with col1:
    speed = st.number_input("Ball Speed (mph)", min_value=10.0, max_value=25.0, value=float(ball_row.get("Speed", 16.5)))
with col2:
    rev_rate = st.number_input("Rev Rate (RPM)", min_value=150, max_value=650, value=int(ball_row.get("RevRate", 350)))
with col3:
    pin_to_pap = st.number_input("Pin-to-PAP (inches)", min_value=3.0, max_value=7.0, value=float(ball_row.get("PinToPAP", 4.5)))

# --- Ball Specs ---
st.subheader("📋 Ball Specs")
st.write(f"**RG:** {ball_row['RG']}")
st.write(f"**Differential:** {ball_row['Diff']}")
st.write(f"**Intermediate Diff:** {ball_row['IntDiff']}")
st.write(f"**Coverstock:** {ball_row['Coverstock']}")
st.write(f"**Coverstock Type:** {ball_row['CoverstockType']}")

# Display selected ball image
image_filename = selected_ball.lower().replace(" ", "_") + ".png"
image_path = os.path.join("images", image_filename)
if os.path.exists(image_path):
    st.image(image_path, caption=selected_ball, width=250)
else:
    st.warning("Ball image not found.")

# --- Oil Pattern Slider ---
oil_length = st.slider("Oil Pattern Length (ft)", 20, 55, 40)

# --- Scoring Algorithm ---
def calculate_score(row, oil_length, speed, rev_rate, pin_to_pap):
    rg = row["RG"]
    diff = row["Diff"]
    int_diff = row["IntDiff"]
    cover = row["CoverstockType"]
    is_asym = isinstance(int_diff, (float, int))

    score = 0

    # Oil length scoring
    if oil_length <= 35:  # short oil
        score += 20 if not is_asym else 5
        if "pearl" in cover.lower():
            score += 10
    elif oil_length >= 43:  # long oil
        score += 20 if is_asym else 5
        if "solid" in cover.lower() or "hybrid" in cover.lower():
            score += 10
    else:
        score += 10

    # Ball speed & rev rate influence
    if speed < 15 and is_asym:
        score += 5
    if rev_rate > 450 and not is_asym:
        score += 5

    # Pin-to-PAP influence
    if pin_to_pap <= 4.0 and is_asym:
        score += 5
    elif pin_to_pap >= 6.0 and not is_asym:
        score += 5

    # RG/Diff weighting
    score += (2.55 - rg) * 10  # lower RG = earlier motion
    score += diff * 200        # higher diff = more hook potential

    return score

# --- Dynamic Recommendation Explanation ---
def explain_ball_choice(row, oil_length, speed, rev_rate, pin_to_pap):
    rg, diff, int_diff = row["RG"], row["Diff"], row["IntDiff"]
    cover, name = row["CoverstockType"], row["Name"]
    is_asym = isinstance(int_diff, (float, int))

    conditions = []
    if oil_length <= 35:
        conditions.append("short oil → favors quicker response and pearls")
    elif oil_length >= 43:
        conditions.append("long oil → favors stronger asymmetrics and solids")
    else:
        conditions.append("medium oil → versatile options work best")

    if is_asym:
        conditions.append("asymmetrical core for strong mid-lane read")
    else:
        conditions.append("symmetrical core for controllable motion")

    if speed < 15:
        conditions.append("slower speed → needs earlier rolling ball")
    if rev_rate > 450:
        conditions.append("high rev rate → can benefit from controllable or weaker layouts")

    return f"**{name}** is recommended because it has RG {rg}, Diff {diff}, " \
           f"{'Asymmetrical' if is_asym else 'Symmetrical'} core, " \
           f"{cover} cover, and matches your bowler profile: {', '.join(conditions)}."

# --- Scoring and Sorting ---
df["Score"] = df.apply(lambda row: calculate_score(row, oil_length, speed, rev_rate, pin_to_pap), axis=1)
df_sorted = df.sort_values(by="Score", ascending=False)

best_ball = df_sorted.iloc[0]
transition_ball = df_sorted.iloc[1] if len(df_sorted) > 1 else best_ball
late_transition_ball = df_sorted.iloc[2] if len(df_sorted) > 2 else transition_ball

# --- Recommended Arsenal ---
st.subheader("🏆 Recommended Arsenal")
for label, ball in zip(["Start With", "Transition To", "Finish With"], [best_ball, transition_ball, late_transition_ball]):
    st.write(f"### {label}: {ball['Name']}")
    st.write(
        f"- RG: {ball['RG']} | Diff: {ball['Diff']} | IntDiff: {ball['IntDiff']}  \n"
        f"- Coverstock: {ball['Coverstock']} ({ball['CoverstockType']})  \n"
        f"- Recommended Oil: {oil_length} ft"
    )
    st.write(explain_ball_choice(ball, oil_length, speed, rev_rate, pin_to_pap))
    image_filename = ball['Name'].lower().replace(" ", "_") + ".png"
    if os.path.exists(os.path.join("images", image_filename)):
        st.image(os.path.join("images", image_filename), caption=f"{label}: {ball['Name']}", width=250)

st.markdown("### 📝 Ball Change Guidance")
st.write(
    "- **Ball hooks too early / crosses over** → Switch to weaker or pearl ball (Transition Ball).  \n"
    "- **Skids too far / leaves corner pins** → Switch to stronger or earlier rolling ball.  \n"
    "- **Flat 10s or weak hits** → Move to a ball with earlier roll or stronger core.  \n"
    "- **As lanes fully break down** → Use late transition ball with higher RG or pearl cover."
)

