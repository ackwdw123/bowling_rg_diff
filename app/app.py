import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os
import re
import unicodedata
import math

# =========================
# Page + Paths
# =========================
st.set_page_config(layout="wide")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE_DIR, "bowling_balls.csv")
IMAGES_DIR = os.path.join(BASE_DIR, "images")
os.makedirs(IMAGES_DIR, exist_ok=True)

# =========================
# Helpers
# =========================
def normalize_text(s: str) -> str:
    if s is None:
        return ""
    s = unicodedata.normalize("NFKC", str(s)).replace("\u00A0", " ").strip()
    return s

def slugify_name(name: str) -> str:
    s = normalize_text(name).lower()
    s = re.sub(r"\s+", " ", s).strip().replace(" ", "_")
    s = re.sub(r"[^a-z0-9_]", "", s)
    s = re.sub(r"_+", "_", s).strip("_")
    return s

def sanitize_filename(value: str) -> str:
    value = normalize_text(value)
    value = value.replace("\\", "/").split("/")[-1]
    return value

def try_paths_for_image(primary_filename: str, name_fallback: str):
    tried = []
    if primary_filename:
        p = os.path.join(IMAGES_DIR, sanitize_filename(primary_filename))
        tried.append(p)
        if os.path.exists(p):
            return p, tried
    stem = slugify_name(name_fallback)
    for ext in [".png", ".jpg", ".jpeg", ".webp"]:
        p = os.path.join(IMAGES_DIR, stem + ext)
        tried.append(p)
        if os.path.exists(p):
            return p, tried
    return None, tried

def expected_roll(row, lane_friction_index, lane_type, lane_condition):
    parts = []
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

    rg = row.get("RG", None)
    diff = row.get("Diff", None)
    if pd.notna(rg):
        if rg < 2.50:
            parts.append("low RG helps it rev earlier")
        elif rg > 2.55:
            parts.append("high RG delays roll")
    if pd.notna(diff):
        if diff >= 0.050:
            parts.append("high diff increases flare/overall hook")
        elif diff <= 0.035:
            parts.append("low diff keeps shape smoother")

    if str(row.get("IntDiff", "Symmetrical Ball")) != "Symmetrical Ball":
        parts.append("asym core adds a stronger direction change")

    if lane_condition == "heavy":
        parts.append("works best with head oil present")
    elif lane_condition == "light":
        parts.append("better once lanes have transitioned or on friction")

    return "; ".join(parts)

# =========================
# Title + Instructions
# =========================
st.title("🎳 Bowling Ball Analyzer & Recommendation System")
st.markdown(
    """
**Instructions:**
1. You can upload a custom `bowling_balls.csv` file to analyze your own arsenal.  
2. Images may not appear if there is no matching image file; we don’t ship a library of ball images.  
3. **Image file names must match the ball name in lowercase, with spaces replaced by underscores.**  
4. Use the template below to create your own CSV file.  
"""
)

# Template download
if os.path.exists(CSV_PATH):
    with open(CSV_PATH, "rb") as f:
        st.download_button(
            label="📥 Download CSV Template",
            data=f,
            file_name="bowling_balls_template.csv",
            mime="text/csv",
        )

# Upload CSV + Images (multiple)
uploaded_file = st.file_uploader("Upload a CSV file", type=["csv"])
uploaded_images = st.file_uploader(
    "Upload Ball Images (.png/.jpg/.jpeg/.webp)", type=["png", "jpg", "jpeg", "webp"], accept_multiple_files=True
)

# Save uploaded images
if uploaded_images:
    for img in uploaded_images:
        with open(os.path.join(IMAGES_DIR, img.name), "wb") as f:
            f.write(img.read())
    st.success(f"Uploaded {len(uploaded_images)} image(s).")

# Load CSV
if uploaded_file:
    df = pd.read_csv(uploaded_file)
elif os.path.exists(CSV_PATH):
    df = pd.read_csv(CSV_PATH)
else:
    st.error("No CSV file found. Please upload a file to continue.")
    st.stop()

# Clean + normalize required columns
required_cols = ["Name", "RG", "Diff"]
for c in required_cols:
    if c not in df.columns:
        st.error("CSV must contain at least: Name, RG, Diff (optional: IntDiff, Coverstock, CoverstockType, Image, Type).")
        st.stop()

df["Name"] = df["Name"].apply(normalize_text)
df["RG"] = pd.to_numeric(df["RG"], errors="coerce")
df["Diff"] = pd.to_numeric(df["Diff"], errors="coerce")
if "IntDiff" not in df.columns:
    df["IntDiff"] = "Symmetrical Ball"
df["IntDiff"] = df["IntDiff"].fillna("Symmetrical Ball")

# =========================
# Quadrant Graph (smaller fonts + overlap offset)
# =========================
def plot_all_quadrants(df_in):
    valid = df_in.dropna(subset=["RG", "Diff"])
    if valid.empty:
        st.warning("RG or Diff values are missing/invalid in the CSV.")
        return

    valid = valid.copy()
    valid["_rg_key"] = valid["RG"].round(3)
    valid["_diff_key"] = valid["Diff"].round(3)
    groups = valid.groupby(["_rg_key", "_diff_key"], sort=False)

    fig, ax = plt.subplots(figsize=(5, 5))
    rg_min, rg_max = valid["RG"].min(), valid["RG"].max()
    diff_min, diff_max = valid["Diff"].min(), valid["Diff"].max()
    rg_mid = (rg_min + rg_max) / 2
    diff_mid = (diff_min + diff_max) / 2

    ax.axhline(diff_mid, color='gray', linestyle='--', linewidth=0.8)
    ax.axvline(rg_mid, color='gray', linestyle='--', linewidth=0.8)

    rg_radius = 0.0009
    diff_radius = 0.0004

    for (_, _), g in groups:
        rows = list(g.itertuples(index=False))
        n = len(rows)
        for i, row in enumerate(rows):
            rg_c, diff_c, name = row.RG, row.Diff, row.Name
            angle = (2 * math.pi * i) / n
            rg = rg_c + (rg_radius * math.cos(angle) if n > 1 else 0)
            diff = diff_c + (diff_radius * math.sin(angle) if n > 1 else 0)

            image_col = getattr(row, "Image", "") if "Image" in g.columns else ""
            image_col = image_col if isinstance(image_col, str) else ""
            img_path, _ = try_paths_for_image(image_col, name)
            if img_path:
                img = plt.imread(img_path)
                ax.imshow(img, extent=(rg-0.002, rg+0.002, diff-0.0008, diff+0.0008), aspect='auto', zorder=2+i)
            else:
                ax.scatter(rg, diff, color='blue', s=22, zorder=2+i)
                ax.text(rg, diff, name, fontsize=5, ha='center', va='center', color='blue', zorder=3+i)

    ax.set_xlim(rg_min - 0.005, rg_max + 0.005)
    ax.set_ylim(diff_min - 0.002, diff_max + 0.002)
    ax.set_xlabel("RG", fontsize=7)
    ax.set_ylabel("Differential", fontsize=7)
    ax.set_title("RG/Diff Quadrant", fontsize=8)
    ax.tick_params(axis='both', labelsize=6)
    st.pyplot(fig)

    with st.expander("📂 Images directory contents"):
        files = sorted(os.listdir(IMAGES_DIR))
        if not files:
            st.write("(images/ is empty)")
        else:
            for f in files:
                fp = os.path.join(IMAGES_DIR, f)
                try:
                    size = os.path.getsize(fp)
                except OSError:
                    size = "?"
                st.write(f"{f} — {size} bytes")

st.subheader("RG/Diff Quadrant Classification")
plot_all_quadrants(df)

# =========================
# Lane surfaces
# =========================
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

# =========================
# Bowler inputs
# =========================
oil_length = st.slider("Oil Pattern Length (ft)", 20, 55, 40, 1)
oil_volume = st.slider("Oil Volume (mL)", 18.0, 27.0, 22.0, 0.5)
speed = st.slider("Ball Speed (mph)", 10.0, 20.0, 16.0, 0.5)
rev_rate = st.slider("Rev Rate (RPM)", 100, 600, 300, 50)
pin_to_pap = st.slider("Pin-to-PAP (inches)", 2.5, 6.0, 4.5, 0.5)

# Lane condition
if oil_length >= 45 or oil_volume >= 24:
    lane_condition = "heavy"
elif oil_length <= 35 or oil_volume <= 20:
    lane_condition = "light"
else:
    lane_condition = "medium"

# =========================
# Scoring
# =========================
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

    if speed >= 17 and "solid" in cover_type:
        score += 10
    elif speed <= 13 and ("pearl" in cover_type or "urethane" in cover_type):
        score += 10

    score += (rev_rate / 100) * diff * 5

    if pin_to_pap <= 4:
        score += diff * 50
    else:
        score += (0.08 - diff) * 50

    return score

roles = ["fresh", "transition", "burned"]
recommendations = {}
for role in roles:
    df[role + "_score"] = df.apply(lambda row: score_ball(row, oil_length, oil_volume, speed, rev_rate, pin_to_pap, lane_friction_index, role), axis=1)
    recommendations[role] = df.sort_values(role + "_score", ascending=False).iloc[0]

# =========================
# Recommended Arsenal
# =========================
st.markdown("## 🎳 Recommended Arsenal")
for idx, role in enumerate(roles):
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
    st.write(f"Score: {ball[role + '_score']:.2f}")
    st.write(f"Expected ball roll on lane type chosen: {expected_roll(ball, lane_friction_index, lane_type, lane_condition)}")

    image_filename = ball['Name'].lower().replace(" ", "_") + ".png"
    image_path = os.path.join(IMAGES_DIR, image_filename)
    if os.path.exists(image_path):
        st.image(image_path, caption=ball['Name'], width=250)
    else:
        st.warning("Ball image not found.")

    if idx < len(roles) - 1:
        st.markdown("<hr style='border:2px solid purple'>", unsafe_allow_html=True)

# =========================
# Balls Not Chosen
# =========================
st.markdown("<hr style='border:2px solid darkred'>", unsafe_allow_html=True)
st.subheader("Balls Not Chosen")
for _, row in df.iterrows():
    if row['Name'] not in [recommendations[r]['Name'] for r in roles]:
        st.write(f"**{row['Name']}**")
        st.write(f"RG: {row['RG']}, Diff: {row['Diff']}, IntDiff: {row['IntDiff']}")
        st.write(f"Coverstock: {row.get('Coverstock', 'Unknown')} ({row.get('CoverstockType', 'Unknown')})")
        st.write(f"Score: {max(row['fresh_score'], row['transition_score'], row['burned_score']):.2f}")
        st.write(f"Expected ball roll on lane type chosen: {expected_roll(row, lane_friction_index, lane_type, lane_condition)}")

        image_filename = row['Name'].lower().replace(" ", "_") + ".png"
        image_path = os.path.join(IMAGES_DIR, image_filename)
        if os.path.exists(image_path):
            st.image(image_path, caption=row['Name'], width=200)
        else:
            st.warning("Ball image not found.")

