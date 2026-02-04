import pandas as pd
import plotly.express as px
import matplotlib.pyplot as plt
import os

INPUT_FILE = "exported_telemetry.csv"

def visualize_data():
    if not os.path.exists(INPUT_FILE):
        print(f"Error: {INPUT_FILE} not found. Run export_data.py first.")
        return

    print(f"Reading {INPUT_FILE}...")
    df = pd.read_csv(INPUT_FILE)
    
    # Ensure timestamp is datetime
    df['timestamp'] = pd.to_datetime(df['timestamp'])

    print("Generating Visualizations...")
    
    # --- 1. Plotly: Interactive Time Series for a Random Vehicle ---
    vehicle_id = df['vehicle_id'].unique()[0] # Pick first vehicle
    print(f"Creating interactive time series for {vehicle_id}...")
    
    vehicle_df = df[df['vehicle_id'] == vehicle_id]
    
    fig = px.line(vehicle_df, x='timestamp', y='voltage_v', color='sensor_id', 
                  title=f"Sensor Values Over Time for {vehicle_id}")
    
    fig.write_html("plot_vehicle_timeseries.html")
    print("✅ Saved plot_vehicle_timeseries.html")

    # --- 2. Matplotlib: Distribution of Vibration ---
    print("Creating static distribution plot...")
    plt.figure(figsize=(10, 6))
    plt.hist(df['vibration_g'], bins=50, color='skyblue', edgecolor='black')
    plt.title("Distribution of Vibration Generation (g)")
    plt.xlabel("Vibration (g)")
    plt.ylabel("Frequency")
    plt.grid(True)
    plt.savefig("plot_vibration_dist.png")
    print("✅ Saved plot_vibration_dist.png")

    # --- 3. Plotly: Anomaly Scatter Plot ---
    print("Creating anomaly scatter plot...")
    # Highlight anomalies
    anomalies = df[df['status'] == 'Critical']
    
    if not anomalies.empty:
        fig2 = px.scatter(anomalies, x='timestamp', y='sensor_id', color='sensor_id',
                          title="Detected Anomalies Timeline")
        fig2.write_html("plot_anomalies.html")
        print("✅ Saved plot_anomalies.html")
    else:
        print("No anomalies found to plot.")

if __name__ == "__main__":
    visualize_data()
