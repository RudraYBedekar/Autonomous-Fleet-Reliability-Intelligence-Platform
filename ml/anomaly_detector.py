import numpy as np

def detect_anomaly_zscore(temp, voltage, vibration):
    """
    Real-time simple threshold and Z-score based heuristic for fast stream processing.
    """
    is_anomaly = False
    
    if temp > 80 or temp < -10:
        is_anomaly = True
    if voltage < 5.0 or voltage > 450: # Depends on sensor, but broad range
        is_anomaly = True
    if vibration > 1.5:
        is_anomaly = True
        
    return is_anomaly

def predict_rul_heuristic(sensor_id, temp, voltage, vibration):
    """
    Estimates Remaining Useful Life in hours.
    """
    # Base RUL: 1000 hours
    rul = 1000.0
    
    # Penalize for high vibration
    if vibration > 0.3:
        rul -= (vibration - 0.3) * 2000
        
    # Penalize for high temp
    if temp > 60:
        rul -= (temp - 60) * 50
        
    # Penalize for low voltage
    if voltage < 11.5 and sensor_id == 'LiDAR':
        rul -= (11.5 - voltage) * 500
        
    return max(0.0, round(rul, 1))
