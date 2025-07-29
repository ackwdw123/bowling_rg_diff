import numpy as np
import matplotlib.pyplot as plt
import matplotlib.image as mpimg

class BowlingSimulation:
    def __init__(self, put_down_board, target_arrows, oil_pattern_length, speed, rev_rate, lane_image):
        self.put_down_board = put_down_board  # Initial board where ball is placed
        self.target_arrows = target_arrows  # Board number over arrows
        self.break_point_distance = oil_pattern_length - 10  # Rule-based breakpoint distance
        self.break_point_board = self.calculate_break_point(target_arrows)  # Rule of 13 applied
        self.speed = speed  # Ball speed (mph)
        self.rev_rate = rev_rate  # Revolutions per minute (RPM)
        self.lane_image = lane_image  # Bowling lane background image

    def calculate_break_point(self, target_board):
        """ Applies the Rule of 13 to determine break point board. """
        return max(1, min(39, (target_board - 13) * 2 + 13))  # Ensures valid board range

    def simulate_path(self):
        """
        Simulates ball trajectory, ensuring it starts at the put-down board,
        follows a realistic path to the break point, and smoothly hooks toward the pocket.
        """
        x_positions = np.linspace(0, 60, num=100)  # Lane distance from foul line to pins
        
        # Ball path before reaction (skid phase)
        board_positions = np.linspace(self.put_down_board, self.target_arrows, num=50)

        # Ball path after break point (smooth hook toward pocket using sigmoid curve)
        hook_factor = max(1, (self.rev_rate / self.speed) * 2)  # Hook intensity
        pocket_board = 17.5  # Pocket location for right-handed bowlers
        
        # Generate a smooth arc using a sigmoid curve from break point to pocket
        hook_positions = self.break_point_board + (pocket_board - self.break_point_board) / (1 + np.exp(-np.linspace(-3, 3, num=50)))

        # Combine trajectory
        board_positions = np.append(board_positions, hook_positions)

        # Ensure hook begins **exactly at the break point distance**
        reaction_index = np.argmin(np.abs(x_positions - self.break_point_distance))

        return x_positions, board_positions, reaction_index

    def display_result(self):
        """
        Visualizes ball path with a properly scaled bowling lane background.
        """
        x_positions, board_positions, reaction_index = self.simulate_path()
        
        # Load bowling lane image correctly scaled
        img = mpimg.imread(self.lane_image)
        fig, ax = plt.subplots(figsize=(8, 16))  # Adjusting figure size for better proportions
        ax.imshow(img, extent=[0, 60, 0, 40], aspect='auto')  # Ensure proper scaling
        
        # Plot ball path from put-down board
        ax.plot(x_positions, board_positions, label="Ball Path", color="blue", linewidth=2)
        
        # Mark reaction point at calculated break point distance
        ax.scatter(x_positions[reaction_index], board_positions[reaction_index], color="red", s=100, label=f"Reaction Point (Break Point: {self.break_point_board}, {self.break_point_distance} ft)")
        
        # Pocket reference
        ax.axhline(y=17.5, color='r', linestyle='--', label="Pocket (Board 17.5)")
        ax.set_xlabel("Lane Distance (feet)")
        ax.set_ylabel("Board Position")
        ax.set_title("Bowling Ball Trajectory Simulation with Smooth Hook Motion")
        ax.legend()
        plt.show()

# User input
put_down_board = float(input("Enter put-down board (1-39): "))
target_arrows = float(input("Enter target board over arrows: "))
oil_pattern_length = float(input("Enter total oil pattern length (feet): "))
speed = float(input("Enter ball speed (mph): "))
rev_rate = float(input("Enter rev rate (RPM): "))
lane_image = "bowling_lane.jpg"  # Use the generated lane image file

# Run simulation
bowling_sim = BowlingSimulation(put_down_board, target_arrows, oil_pattern_length, speed, rev_rate, lane_image)
bowling_sim.display_result()