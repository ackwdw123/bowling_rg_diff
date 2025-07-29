import os

def load_ball_data():
    csv_path = os.path.join(os.path.dirname(__file__), "bowling_balls.csv")
    st.write("Looking for CSV at:", csv_path)  # Optional debug
    return pd.read_csv(csv_path)

# Use like this
if csv_file is not None:
    df = pd.read_csv(csv_file)
else:
    df = load_ball_data()

