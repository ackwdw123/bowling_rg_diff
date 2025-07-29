import matplotlib.pyplot as plt

# Updated dictionary of bowling balls and their specs
bowling_balls = {
    "Track Criterion": {"RG": 2.49, "Diff": 0.047},
    "Hammer Hazmat Solid": {"RG": 2.47, "Diff": 0.056},
    "Track Theorem": {"RG": 2.50, "Diff": 0.053},
    "Hammer Black Widow Mania": {"RG": 2.51, "Diff": 0.054},
    "Brunswick Vaporize": {"RG": 2.51, "Diff": 0.047},
    "Hammer Hazmat Pearl": {"RG": 2.47, "Diff": 0.056},
    "Hammer Scorpion Strike": {"RG": 2.47, "Diff": 0.048},
}

def plot_ball_on_grid(ball_name):
    if ball_name not in bowling_balls:
        print(f"Ball '{ball_name}' not found in the database.")
        return

    ball = bowling_balls[ball_name]
    rg = ball["RG"]
    diff = ball["Diff"]

    # Plot settings
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.set_title("Bowling Ball RG vs. Differential Chart")
    ax.set_xlabel("Differential")
    ax.set_ylabel("RG")
    ax.grid(True)

    # Set axis limits and reverse Y to make RG increase from top to bottom
    ax.set_xlim(0.040, 0.060)
    ax.set_ylim(2.60, 2.40)  # RG increases top to bottom

    # Plot all balls for context
    for name, specs in bowling_balls.items():
        ax.scatter(specs["Diff"], specs["RG"], color='gray', alpha=0.6)
        ax.text(specs["Diff"], specs["RG"], name, fontsize=8, ha='right', va='bottom', color='gray')

    # Highlight the selected ball
    ax.scatter(diff, rg, color='red', s=100, edgecolor='black', zorder=5)
    ax.text(diff, rg, f"{ball_name}", fontsize=10, ha='left', va='top', color='red')

    plt.show()

# Example usage
ball_input = "Track Criterion"
plot_ball_on_grid(ball_input)

