import streamlit as st
import matplotlib.pyplot as plt
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
import pandas as pd
import os

# Load CSV
@st.cache_data
def load_ball_data(csv_path):
    return pd.read_csv(csv_path)

# Image loader
def get_image(path, zoom=0.15):
    if not os.path.exists(path):
        return None
    return OffsetImage(plt.imread(path), zoom=zoom)

# Ideal condition logic
def determine_ideal_conditions(rg, diff):
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

# Plotter
def plot_ball_images_on_grid(df, highlight_ball=None):
    fig, ax = plt.subplots(figsize=(10, 8))
    ax.set_title("Bowling Ball RG vs. Differential")
    ax.set_xlabel("Differential (↑ = More Flare / Heavy Oil)")
    ax.set_ylabel("RG (↓ = Earlier Roll)")
    ax.grid(True)
    ax.set_xlim(0.0425, 0.0575)
    ax.set_ylim(2.550, 2.425)

    # Corner guidance text
    ax.text(0.0427, 2.428, "Later Roll", fontsize=10, ha='left', va='bottom', color='blue')
    ax.text(0.0427, 2.547, "Earlier Roll", fontsize=10, ha='left', va='top', color='blue')
    ax.text(0.0573, 2.547, "Heavy Oil", fontsize=10, ha='right', va='top', color='green')
    ax.text(0.0427, 2.535, "Light Oil", fontsize=10, ha='left', va='top', color='green')

    for _, row in df.iterrows():
        x, y = row["Diff"], row["RG"]
        name = row["Name"]
        image_path = row["Image"]
        image = get_image(image_path)

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

        ax.text(x + 0.0006, y, name, fontsize=9, ha='left', va='center', color='black')

    if highlight_ball:
        row = df[df["Name"] == highlight_ball].iloc[0]
        ax.scatter(row["Diff"], row["RG"], edgecolor='red', facecolor='none', s=300, linewidths=2, zorder=6)

    return fig

# Streamlit App
st.set_page_config(layout="wide")
st.title("🎳 Bowling Ball RG vs. Differential Visualizer")

# File input
csv_file = st.file_uploader("Upload a CSV file with bowling ball data", type=["csv"])
if csv_file is not None:
    df = pd.read_csv(csv_file)
else:
    #df = load_ball_data("bowling_balls.csv")
    csv_path = os.path.join(os.path.dirname(__file__), "bowling_balls.csv")
    df = load_ball_data(csv_path)

# Two-column layout
col1, col2 = st.columns([3, 1])

with col1:
    selected_ball = st.selectbox("Choose a bowling ball to highlight:", df["Name"].tolist())
    fig = plot_ball_images_on_grid(df, highlight_ball=selected_ball)
    st.pyplot(fig)

with col2:
    st.subheader("🧾 Ball Details")
    selected = df[df["Name"] == selected_ball].iloc[0]
    st.markdown(f"**Name:** {selected['Name']}")
    st.markdown(f"**RG:** {selected['RG']}")
    st.markdown(f"**Differential:** {selected['Diff']}")
    st.markdown("**Ideal Conditions:**")
    st.info(determine_ideal_conditions(selected["RG"], selected["Diff"]))

