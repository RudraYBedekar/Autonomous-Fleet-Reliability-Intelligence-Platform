import time
import datetime
import random
import pandas as pd
import numpy as np
from sqlalchemy import create_engine
from db_manager import DB_FILE

# Configuration
NUM_VEHICLES = 50
SENSORS = ['LiDAR', 'Camera', 'Radar', 'IMU', 'Battery', 'Speed', 'EngineRPM']
REFRESH_RATE_SECONDS = 2

def get_engine():
    return create_engine(f"sqlite:///{DB_FILE}")

def simulate_live_feed():
    engine = get_engine()
    print("🚀 Starting Live Telemetry Simulation...")
    print(f"Streaming data for {NUM_VEHICLES} vehicles to {DB_FILE} every {REFRESH_RATE_SECONDS}s.")
    print("Press Ctrl+C to stop.")

    # Specific Route: Fremont, CA (Mowry Ave - Straight section)
    # This ensures the vehicle looks like it's exactly on the street on the map.
    ROUTES = [
        # Mowry Ave from I-880 to roughly Mission Blvd
        {"start": (37.525048, -122.004070), "end": (37.540443, -121.969795), "name": "Fremont-MowryAve"},
    ]
    
    # Initialize vehicle positions and routes
    vehicle_states = {}
    for i in range(1, NUM_VEHICLES + 1):
        # All vehicles on the same street for now to guarantee they are "on street"
        route = ROUTES[0] 
        vehicle_states[f"AV-{i:03d}"] = {
            "route": route,
            "progress": random.random(),
            "direction": 1 if random.random() > 0.5 else -1
        }
    
    step_increment = 0.002 # Slower speed to look realistic on map

    try:
        while True:
            current_time = datetime.datetime.now()
            new_data = []

            for vehicle_id in range(1, NUM_VEHICLES + 1):
                vehicle_name = f"AV-{vehicle_id:03d}"
                state = vehicle_states[vehicle_name]
                route = state["route"]
                
                # Update Location
                state["progress"] += step_increment * state["direction"]
                
                if state["progress"] > 1.0:
                    state["progress"] = 1.0
                    state["direction"] = -1
                elif state["progress"] < 0.0:
                    state["progress"] = 0.0
                    state["direction"] = 1
                
                start_lat, start_lon = route["start"]
                end_lat, end_lon = route["end"]
                d_lat = end_lat - start_lat
                d_lon = end_lon - start_lon
                
                current_lat = start_lat + d_lat * state["progress"]
                current_lon = start_lon + d_lon * state["progress"]
                
                # Add tiny noise
                current_lat += random.uniform(-0.0001, 0.0001)
                current_lon += random.uniform(-0.0001, 0.0001)

                for sensor in SENSORS:
                    # Generate somewhat realistic fluctuating data
                    if sensor == 'LiDAR':
                        temp = np.random.normal(45, 5) 
                        voltage = np.random.normal(12.0, 0.5)
                        vibration = np.random.normal(0.5, 0.1)
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
                        voltage = np.random.normal(400, 20)
                        vibration = np.random.normal(0.2, 0.1)
                    elif sensor == 'Speed':
                        temp = np.random.normal(60, 5) # Tire temp maybe?
                        voltage = np.random.normal(12.0, 0.1)
                        vibration = np.random.normal(0.5, 0.2)
                        # We'll re-purpose 'voltage' or 'temp' or add a new field? 
                        # simpler to reuse fields or add a generic 'value' field but for now reusing fields with context
                        # Actually, let's just stick to the schema: temp, voltage, vibration.
                        # Ideally we should add a 'value' column, but let's map Speed -> voltage_v (just as a placeholder for main value)
                        # Speed usually doesn't map to voltage. 
                        # Let's map Speed -> voltage_v for now as "Primary Value"
                        voltage = np.random.normal(60, 20) # Speed km/h
                    elif sensor == 'EngineRPM':
                        temp = np.random.normal(90, 10) # Engine temp
                        voltage = np.random.normal(3000, 1000) # RPM
                        vibration = np.random.normal(0.8, 0.3)
                    
                    # Random Anomaly Injection
                    is_anomaly = False
                    if random.random() < 0.01: # 1% chance per tick
                        is_anomaly = True
                        if random.choice([True, False]):
                            temp += 30 # Heater spike
                        else:
                            voltage = 0 # Power loss
                    
                    status = "Critical" if is_anomaly else "Operational"
                    
                    new_data.append({
                        "timestamp": current_time,
                        "vehicle_id": vehicle_name,
                        "sensor_id": sensor,
                        "temperature_c": round(temp, 2),
                        "voltage_v": round(voltage, 2),
                        "vibration_g": round(vibration, 3),
                        "latitude": round(current_lat, 6),
                        "longitude": round(current_lon, 6),
                        "status": status
                    })
            
            # Batch Insert
            df = pd.DataFrame(new_data)
            df.to_sql('telemetry', engine, if_exists='append', index=False)
            
            print(f"[{current_time.strftime('%H:%M:%S')}] 📡 Sent {len(df)} records. Fleet Status: {len(df[df['status']=='Critical'])} Critical Alerts.")
            
            time.sleep(REFRESH_RATE_SECONDS)

    except KeyboardInterrupt:
        print("\n🛑 Simulation Stopped.")

if __name__ == "__main__":
    simulate_live_feed()
