import matplotlib.pyplot as plt
import pandas as pd
import os

class Visualizer:
    def __init__(self, session_path):
        self.session_path = session_path
        self.reports_path = os.path.join(session_path, 'REPORTS')
        self.assets_path = os.path.join(session_path, 'ASSETS')
        os.makedirs(self.assets_path, exist_ok=True)

    def plot_lap_times(self, lap_data: pd.DataFrame, output_filename="lap_times_progression.png"):
        """
        Generates a lap time progression chart.

        Args:
            lap_data (pd.DataFrame): DataFrame containing lap times.
                                     Expected columns: 'lap_number', 'total_lap_time'.
            output_filename (str): Name of the output image file.
        """
        if 'lap_number' not in lap_data.columns or 'total_lap_time' not in lap_data.columns:
            print("Error: lap_data must contain 'lap_number' and 'total_lap_time' columns.")
            return

        plt.figure(figsize=(12, 6))
        plt.plot(lap_data['lap_number'], lap_data['total_lap_time'], marker='o', linestyle='-')
        plt.title('Lap Time Progression')
        plt.xlabel('Lap Number')
        plt.ylabel('Lap Time (seconds)')
        plt.grid(True)
        plt.tight_layout()

        output_filepath = os.path.join(self.assets_path, output_filename)
        plt.savefig(output_filepath)
        plt.close()
        print(f"Lap time progression chart saved to {output_filepath}")

    # Add more visualization methods here as needed
    # def plot_telemetry_data(self, telemetry_data, channels, output_filename):
    #     pass
