import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
import matplotlib.patches as patches
import os

# ----------------------------
# Utility Functions
# ----------------------------
def get_image(path, zoom=0.2):
    """Load and return a matplotlib OffsetImage for the ball icon."""
    try:
        return OffsetImage(plt.imread(path), zoom=zoom)
    except:
        return None

def classify_ball_quadrant(rg, diff, int_diff):
    """
    Classifies a ball into a quadrant considering RG, Diff, and IntDiff.
    """
    rg_mid = (2.550 + 2.425) / 2
    diff_mid = (0.0600 + 0.0425) / 2
    intdiff_mid = 0.015  # Threshold for asymmetry

    if rg > rg_mid and diff < diff_mid:
        base = "High RG / Low Diff (Later Roll, Light Oil)"
    elif rg > rg_mid and diff >= diff_mid:
        base = "High RG / High Diff (Later Roll, Heavy Oil)"
    elif rg <= rg_mid and diff < diff_mid:
        base = "Low RG / Low Diff (Early Roll, Light Oil)"
    else:
        base = "Low RG / High Diff (Early Roll, Heavy Oil)"

    if int_diff >= intdiff_mid:
        base += " [Asymmetric]"
    else:
        base += " [Symmetric]"
    
    return base

def plot_ball_images_on_grid(df, highlight_ball=None):
    """Plots the RG vs Differential chart with ball images and quadrant shading."""
    fig, ax = plt.subplots(figsize=(10, 8))
    fig.patch.set_facecolor('white')
    ax.set_title("Bowling Ball RG vs. Differential")
    ax.set_xlabel("Differential")
    ax.set_ylabel("RG")
    ax.grid(True)
    
    # Axis limits
    min_diff, max_diff = 0.0425, 0.0600
    min_rg, max_rg = 2.425, 2.550
    ax.set_xlim(min_diff, max_diff)
    ax.set_ylim(min_rg, max_rg)  # Lower RG at bottom

    # Midpoints
    mid_rg = (max_rg + min_rg) / 2
    mid_diff = (max_diff + min_diff) / 2

    # Shaded Quadrants
    colors = ['#FFFACD', '#ADD8E6', '#90EE90', '#FFB6C1']  # Yellow, Blue, Green, Pink
    ax.add_patch(patches.Rectangle((min_diff, mid_rg), mid_diff-min_diff, max_rg-mid_rg, facecolor=colors[0], alpha=0.35))  # Top Left
    ax.add_patch(patches.Rectangle((mid_diff, mid_rg), max_diff-mid_diff, max_rg-mid_rg, facecolor=colors[1], alpha=0.35))  # Top Right
    ax.add_patch(patches.Rectangle((min_diff, min_rg), mid_diff-min_diff, mid_rg-min_rg, facecolor=colors[2], alpha=0.35))  # Bottom Left
    ax.add_patch(patches.Rectangle((mid_diff, min_rg), max_diff-mid_diff, mid_rg-min_rg, facecolor=colors[3], alpha=0.35))  # Bottom Right

    # ----------------------------
    # Centered Quadrant Descriptors
    # ----------------------------
    label_fontsize = 12
    ax.text((min_diff+mid_diff)/2, (mid_rg+max_rg)/2, "Later Roll", fontsize=label_fontsize, ha='center', va='center', color='blue')
    ax.text((mid_diff+max_diff)/2, (mid_rg+max_rg)/2, "Light Oil", fontsize=label_fontsize, ha='center', va='center', color='green')
    ax.text((min_diff+mid_diff)/2, (min_rg+mid_rg)/2, "Early Roll", fontsize=label_fontsize, ha='center', va='center', color='blue')
    ax.text((mid_diff+max_diff)/2, (min_rg+mid_rg)/2, "Heavy Oil", fontsize=label_fontsize, ha='center', va='center', color='green')

    # Quadrant detail labels
    ax.text(min_diff+0.0007, max_rg-0.006, "High RG / Low Diff", fontsize=8, ha='left', va='top', color='purple')
    ax.text(max_diff-0.0007, max_rg-0.006, "High RG / High Diff", fontsize=8, ha='right', va='top', color='purple')
    ax.text(min_diff+0.0007, min_rg+0.006, "Low RG / Low Diff", fontsize=8, ha='left', va='bottom', color='purple')
    ax.text(max_diff-0.0007, min_rg+0.006, "Low RG / High Diff", fontsize=8, ha='right', va='bottom', color='purple')

    # ----------------------------
    # Plot all bowling balls
    # ----------------------------
    for _, row in df.iterrows():
        x, y = row["Diff"], row["RG"]
        name = row["Name"]
        intdiff = row.get("IntDiff", 0.0)

        # Convert name to image file pattern: lowercase + underscores
        image_filename = name.lower().replace(" ", "_") + ".png"
        image_path = os.path.join("images", image_filename)
        if not os.path.exists(image_path):
            image_path = "images/default.png"

        image = get_image(image_path, zoom=0.2)  # 200x200 images

        # Place image
        if image:
            ab = AnnotationBbox(image, (x, y), frameon=False,
                                box_alignment=(0.5, 0.5),
                                zorder=5 if name == highlight_ball else 3)
            ax.add_artist(ab)
        else:
            ax.scatter(x, y, color='blue', s=80)

        # Visual indicator for IntDiff (red outline for asymmetric balls)
        if intdiff >= 0.015:
            circle = plt.Circle((x, y), 0.0006, color='red', fill=False, lw=2, zorder=6)
            ax.add_artist(circle)

        # Label with name
        ax.text(x + 0.0006, y, name, fontsize=8, ha='left', va='center', color='black')

        # Classify quadrant
        df.loc[df["Name"] == name, "Quadrant"] = classify_ball_quadrant(y, x, intdiff)

    # Highlight selected ball
    if highlight_ball:
        row = df[df["Name"] == highlight_ball].iloc[0]
        ax.scatter(row["Diff"], row["RG"], edgecolor='red', facecolor='none', s=300, linewidths=2, zorder=7)

    return fig, df


# ----------------------------
# Streamlit App
# ----------------------------
st.set_page_config(layout="wide", page_title="Bowling Ball RG vs Diff")
st.title("🎳 Bowling Ball RG vs Differential Visualizer")

# Load CSV
uploaded_file = st.file_uploader("Upload your bowling_balls.csv", type=["csv"])
if uploaded_file is None:
    if os.path.exists("bowling_balls.csv"):
        df = pd.read_csv("bowling_balls.csv")
        st.info("Using local `bowling_balls.csv` from current directory.")
    else:
        st.warning("Please upload a CSV file or place `bowling_balls.csv` in this directory.")
        st.stop()
else:
    df = pd.read_csv(uploaded_file)

if "IntDiff" not in df.columns:
    df["IntDiff"] = 0.0

# Dropdown to highlight a ball
highlight_ball = st.selectbox("Select a Bowling Ball to Highlight", options=list(df["Name"]), index=0)

# Layout: Graph + Specs
col1, col2 = st.columns([2, 1])

with col1:
    fig, df = plot_ball_images_on_grid(df, highlight_ball)
    st.pyplot(fig)

with col2:
    selected = df[df["Name"] == highlight_ball].iloc[0]
    st.markdown(f"### {highlight_ball} Specs")
    st.write(f"**RG:** {selected['RG']}")
    st.write(f"**Diff:** {selected['Diff']}")
    st.write(f"**IntDiff:** {selected['IntDiff']}")
    st.write(f"**Quadrant:** {selected['Quadrant']}")

