import streamlit as st
import matplotlib.pyplot as plt
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
import os

# Bowling ball data with RG, Differential, Image, and optional override for ideal conditions
bowling_balls = {
    "Track Criterion": {
        "RG": 2.49, "Diff": 0.047, "Image": "images/track_criterion.png"
    },
    "Hammer Hazmat Solid": {
        "RG": 2.47, "Diff": 0.056, "Image": "images/hazmat_solid.png"
    },
    "Track Theorem": {
        "RG": 2.50, "Diff": 0.053, "Image": "images/track_theorem.png"
    },
    "Hammer Black Widow Mania": {
        "RG": 2.51, "Diff": 0.054, "Image": "images/black_widow_mania.png"
    },
    "Brunswick Vaporize": {
        "RG": 2.51, "Diff": 0.047, "Image": "images/brunswick_vaporize.png"
    },
    "Hammer Hazmat Pearl": {
        "RG": 2.47, "Diff": 0.056, "Image": "images/hazmat_pearl.png"
    },
    "Hammer Scorpion Strike": {
        "RG": 2.47, "Diff": 0.048, "Image": "images/scorpion_strike.png"
    },
}

def get_image(path, zoom=0.15):
    if not os.path.exists(path):
        return None
    return OffsetImage(plt.imread(path), zoom=zoom)

def determine_ideal_conditions(rg, diff):
    # Basic logic for ideal conditions (can be customized)
    if rg < 2.48 and diff > 0.053:
        return "Ideal for heavy oil conditions with early roll and strong backend."
    elif rg < 2.48 and diff <= 0.053:
        return "Medium-heavy oil; smooth early rolling ball."
    elif rg >= 2.50 and diff > 0.053:
        return "Medium to heavy oil with length and backend pop."
    elif rg >= 2.50 and diff <= 0.050:
        return "Best for light to medium oil with a controllable backend."
    else:
        return "Versatile ball for medium oil and blended patterns."

def plot_ball_images_on_grid(highlight_ball=None):
    fig, ax = plt.subplots(figsize=(10, 8))
    ax.set_title("Bowling Ball RG vs. Differential")
    ax.set_xlabel("Differential (↑ = More Flare / Heavy Oil)")
    ax.set_ylabel("RG (↓ = Earlier Roll)")
    ax.grid(True)

    ax.set_xlim(0.0425, 0.0575)
    ax.set_ylim(2.550, 2.425)  # RG increases from top to bottom

    # Add descriptive labels (adjusted positions to avoid overlap)
    ax.text(0.0427, 2.428, "Later Roll", fontsize=10, ha='left', va='bottom', color='blue')
    ax.text(0.0427, 2.547, "Earlier Roll", fontsize=10, ha='left', va='top', color='blue')
    ax.text(0.0573, 2.547, "Heavy Oil", fontsize=10, ha='right', va='top', color='green')
    ax.text(0.0427, 2.535, "Light Oil", fontsize=10, ha='left', va='top', color='green')

    for name, specs in bowling_balls.items():
        x, y = specs["Diff"], specs["RG"]
        image = get_image(specs["Image"])

        if image:
            ab = AnnotationBbox(
                image, (x, y),
                frameon=False,
                box_alignment=(0.5, 0.5),
                zorder=5 if name == highlight_ball else 3
            )
            ax.add_artist(ab)
        else:
            ax.scatter(x, y, color='blue', s=80)

        # Add ball name
        ax.text(x + 0.0006, y, name, fontsize=9, ha='left', va='center', color='black')

    if highlight_ball and highlight_ball in bowling_balls:
        specs = bowling_balls[highlight_ball]
        ax.scatter(
            specs["Diff"], specs["RG"],
            edgecolor='red', facecolor='none',
            s=300, linewidths=2, zorder=6
        )

    return fig

# Streamlit UI
st.set_page_config(layout="wide")
st.title("🎳 Bowling Ball RG vs. Differential Visualizer")

# Two-column layout
col1, col2 = st.columns([3, 1])  # left 75%, right 25%

with col1:
    selected_ball = st.selectbox("Choose a bowling ball to highlight:", list(bowling_balls.keys()))
    fig = plot_ball_images_on_grid(highlight_ball=selected_ball)
    st.pyplot(fig)

with col2:
    st.subheader("🧾 Ball Details")
    specs = bowling_balls[selected_ball]
    st.markdown(f"**Name:** {selected_ball}")
    st.markdown(f"**RG:** {specs['RG']}")
    st.markdown(f"**Differential:** {specs['Diff']}")

    ideal_conditions = determine_ideal_conditions(specs["RG"], specs["Diff"])
    st.markdown("**Ideal Conditions:**")
    st.info(ideal_conditions)

