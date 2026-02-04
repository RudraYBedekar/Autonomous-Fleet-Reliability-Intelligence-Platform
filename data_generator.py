import pandas as pd
import numpy as np
import datetime
import random
import os

# Configuration
NUM_VEHICLES = 50
NUM_RECORDS_PER_VEHICLE = 2500  # Total ~125,000 records
START_TIME = datetime.datetime.now() - datetime.timedelta(days=7)
SENSORS = ['LiDAR', 'Camera', 'Radar', 'IMU', 'Battery']

# Anomaly Injection Config
FAILURE_RATE = 0.05  # 5% chance of anomaly per batch

def generate_telemetry():
    """Generates synthetic telemetry data."""
    print(f"Generating data for {NUM_VEHICLES} vehicles...")
    
    all_data = []

    # Specific Routes (Start -> End) to ensure they stay on land/streets
    # Fremont, CA (Mowry Ave)
    ROUTES = [
        {"start": (37.525048, -122.004070), "end": (37.540443, -121.969795), "name": "Fremont-MowryAve"},
    ]

    for vehicle_id in range(1, NUM_VEHICLES + 1):
        vehicle_name = f"AV-{vehicle_id:03d}"
        
        # Base state for the vehicle
        current_time = START_TIME
        
        # Assign vehicle to a random route
        route = random.choice(ROUTES)
        
        # Interpolate position along the route
        # We start at a random progress along the line to distribute them
        progress = random.random() # 0.0 to 1.0
        
        start_lat, start_lon = route["start"]
        end_lat, end_lon = route["end"]
        
        # Direction vector
        d_lat = end_lat - start_lat
        d_lon = end_lon - start_lon
        
        # Current Position
        current_lat = start_lat + d_lat * progress
        current_lon = start_lon + d_lon * progress
        
        # Speed factor (how fast they move along the line per step)
        # Avg step is 1-5 mins. 
        # Lat/Lon distance? 
        # Total route length ~5km. Speed ~30-60km/h.
        # Just use a small fixed increment for simulation
        step_increment = 0.0005 # Lat/Lon degrees per step (approx 50m)
        
        # Direction needs to be normalized? Nah, just simple linear interpolation
        # Actually, let's just bounce back and forth or loop
        direction = 1 if random.random() > 0.5 else -1

        for _ in range(NUM_RECORDS_PER_VEHICLE):
            # Advance time by random intervals (1-5 minutes)
            current_time += datetime.timedelta(minutes=random.randint(1, 5))
            
            # Move vehicle
            progress += step_increment * direction * random.uniform(0.5, 1.5)
            
            # Boundary check - reverse direction if end of route
            if progress > 1.0:
                progress = 1.0
                direction = -1
            elif progress < 0.0:
                progress = 0.0
                direction = 1
                
            current_lat = start_lat + d_lat * progress
            current_lon = start_lon + d_lon * progress
            
            # Add tiny noise so they aren't on a perfect line
            sim_lat = current_lat + random.uniform(-0.0001, 0.0001)
            sim_lon = current_lon + random.uniform(-0.0001, 0.0001)
            
            for sensor in SENSORS:
                # Normal operating ranges
                if sensor == 'LiDAR':
                    temp = np.random.normal(45, 5) # degrees C
                    voltage = np.random.normal(12.0, 0.5)
                    vibration = np.random.normal(0.5, 0.1) # G-force
                elif sensor == 'Camera':
                    temp = np.random.normal(50, 8)
                    voltage = np.random.normal(5.0, 0.1)
                    vibration = np.random.normal(0.3, 0.05)
                elif sensor == 'Radar':
                    temp = np.random.normal(40, 4)
                    voltage = np.random.normal(24.0, 1.0)
                    vibration = np.random.normal(0.4, 0.1)
                elif sensor == 'IMU':
                    temp = np.random.normal(35, 3)
                    voltage = np.random.normal(5.0, 0.1)
                    vibration = np.random.normal(0.1, 0.01)
                elif sensor == 'Battery':
                    temp = np.random.normal(30, 10)
                    voltage = np.random.normal(400, 20) # EV Battery
                    vibration = np.random.normal(0.2, 0.1)
                
                # Inject Anomalies (Random Spikes / Drifts)
                is_anomaly = False
                if random.random() < 0.005: # 0.5% individual sensor glitch chance
                    is_anomaly = True
                    anomaly_type = random.choice(['spike', 'drop', 'noise'])
                    if anomaly_type == 'spike':
                        temp += random.uniform(20, 50)
                        vibration += random.uniform(1.0, 3.0)
                    elif anomaly_type == 'drop':
                         voltage *= 0.1
                    elif anomaly_type == 'noise':
                        temp += np.random.normal(0, 20)
                
                status = "Critical" if is_anomaly else "Operational"
                
                record = {
                    "timestamp": current_time,
                    "vehicle_id": vehicle_name,
                    "sensor_id": sensor,
                    "temperature_c": round(temp, 2),
                    "voltage_v": round(voltage, 2),
                    "vibration_g": round(vibration, 3),
                    "latitude": round(sim_lat, 6),
                    "longitude": round(sim_lon, 6),
                    "status": status
                }
                all_data.append(record)
    
    df = pd.DataFrame(all_data)
    return df

if __name__ == "__main__":
    df = generate_telemetry()
    output_file = "telemetry_data.csv"
    df.to_csv(output_file, index=False)
    print(f"✅ Generated {len(df)} records. Saved to {output_file}")
