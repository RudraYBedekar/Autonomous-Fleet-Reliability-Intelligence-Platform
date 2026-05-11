import pandas as pd
import numpy as np
from sqlalchemy import create_engine
from scipy.stats import zscore
from sklearn.ensemble import IsolationForest
import pickle
import os

DB_FILE = "telemetry_db.sqlite"

class AnalyticsEngine:
    def __init__(self, db_file=DB_FILE):
        self.engine = create_engine(f"sqlite:///{db_file}")

    def get_vehicle_data(self, vehicle_id):
        """Fetches telemetry data for a specific vehicle."""
        query = f"SELECT * FROM telemetry WHERE vehicle_id = '{vehicle_id}' ORDER BY timestamp"
        df = pd.read_sql(query, self.engine)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        return df

    def compute_rolling_stats(self, df, window=20):
        """Calculates rolling mean and std dev for sensor readings."""
        # Calculate separately for each sensor to avoid mixing data
        # But here input df usually filters by vehicle. 
        # We also need to group by sensor_id since a vehicle has multiple sensors.
        
        df_stats = df.copy()
        
        # We need to pivot or group. Let's group.
        # It's easier to calculate if we sort by sensor too.
        
        metrics = ['temperature_c', 'voltage_v', 'vibration_g']
        
        for metric in metrics:
            df_stats[f'{metric}_rolling_mean'] = df_stats.groupby('sensor_id')[metric].transform(lambda x: x.rolling(window=window).mean())
            df_stats[f'{metric}_rolling_std'] = df_stats.groupby('sensor_id')[metric].transform(lambda x: x.rolling(window=window).std())
            
        return df_stats

    def detect_anomalies_zscore(self, df, threshold=3):
        """Detects anomalies using Z-score."""
        df_anom = df.copy()
        metrics = ['temperature_c', 'voltage_v', 'vibration_g']
        
        for metric in metrics:
            # Calculate Z-score per sensor group
            df_anom[f'{metric}_zscore'] = df_anom.groupby('sensor_id')[metric].transform(lambda x: zscore(x, nan_policy='omit'))
            
            # Identify anomaly
            df_anom[f'{metric}_anomaly'] = df_anom[f'{metric}_zscore'].abs() > threshold
            
        return df_anom

    def train_anomaly_model(self, df):
        """Trains an Isolation Forest model for each sensor type."""
        models = {}
        metrics = ['temperature_c', 'voltage_v', 'vibration_g']
        
        # Train a model for each sensor type effectively
        for sensor_type in df['sensor_id'].unique():
            sensor_df = df[df['sensor_id'] == sensor_type][metrics]
            
            # Handle NaN
            sensor_df = sensor_df.fillna(0)
            
            if len(sensor_df) < 10:
                continue # Not enough data
                
            model = IsolationForest(contamination=0.01, random_state=42)
            model.fit(sensor_df)
            models[sensor_type] = model
            
        return models

    def detect_anomalies_ml(self, df, models=None):
        """Detects anomalies using trained ML models."""
        df_ml = df.copy()
        df_ml['ml_anomaly'] = False
        metrics = ['temperature_c', 'voltage_v', 'vibration_g']
        
        if models is None:
            # On-the-fly training if no model provided (expensive but works for demo)
            models = self.train_anomaly_model(df)
            
        for sensor_type in df_ml['sensor_id'].unique():
            if sensor_type in models:
                model = models[sensor_type]
                mask = df_ml['sensor_id'] == sensor_type
                data_to_predict = df_ml.loc[mask, metrics].fillna(0)
                
                # Predict: -1 for outliers, 1 for inliers
                preds = model.predict(data_to_predict)
                
                # Mark anomalies
                df_ml.loc[mask, 'ml_anomaly'] = (preds == -1)
                
        return df_ml

    def get_fleet_reliability_metrics(self):
        """Computes MTBF and Failure Rates for the entire fleet."""
        # This is expensive on large info, but for 600k rows it's manageable
        query = "SELECT vehicle_id, sensor_id, timestamp, status FROM telemetry WHERE status = 'Critical'"
        failures_df = pd.read_sql(query, self.engine)
        failures_df['timestamp'] = pd.to_datetime(failures_df['timestamp'])
        
        if failures_df.empty:
            return pd.DataFrame()

        # MTBF Calculation
        # MTBF = (Total Uptime) / (Number of Failures)
        # OR simple approx: (End Time - Start Time) / Count(Failures) 
        # Better: Average time diff between failures for each vehicle/sensor
        
        failures_df = failures_df.sort_values(['vehicle_id', 'sensor_id', 'timestamp'])
        failures_df['prev_failure'] = failures_df.groupby(['vehicle_id', 'sensor_id'])['timestamp'].shift(1)
        failures_df['time_between_failures'] = (failures_df['timestamp'] - failures_df['prev_failure']).dt.total_seconds() / 3600.0 # Hours
        
        mtbf_stats = failures_df.groupby(['sensor_id'])['time_between_failures'].mean().reset_index()
        mtbf_stats.columns = ['sensor_id', 'mtbf_hours']
        
        # Failure Rate (Failures per hour assuming continuous op for simplicity or just count)
        # failure_counts = failures_df.groupby(['vehicle_id', 'sensor_id']).size().reset_index(name='failure_count')
        
        return mtbf_stats

    def predict_rul(self, df):
        """
        Predicts Remaining Useful Life (RUL) for sensors.
        In a real scenario, this would use a regression model (e.g., Random Forest, LSTM)
        trained on historical failure cycles.
        
        For this demo, we'll estimate RUL based on 'health score' derived from
        distance to anomaly thresholds.
        """
        df_pred = df.copy()
        
        # Simple RUL Heuristic for Demo:
        # RUL (Hours) = (Threshold - Current_Value) * Factor
        # This assumes degradation is linear and positive, which is a simplification.
        
        # We'll assign a random RUL for now to demonstrate the UI, 
        # but modulated by how "bad" the current readings are.
        
        def calculate_rul(row):
            # Base RUL: 1000 hours
            rul = 1000
            
            # Penalize for high vibration
            if row['vibration_g'] > 0.3:
                rul -= (row['vibration_g'] - 0.3) * 2000
                
            # Penalize for high temp
            if row['temperature_c'] > 60:
                rul -= (row['temperature_c'] - 60) * 50
                
            # Penalize for low voltage
            if row['voltage_v'] < 11.5 and row['sensor_id'] == 'LiDAR':
                rul -= (11.5 - row['voltage_v']) * 500
                
            return max(0, round(rul, 1))

        df_pred['predicted_rul_hours'] = df_pred.apply(calculate_rul, axis=1)
        return df_pred

if __name__ == "__main__":
    ae = AnalyticsEngine()
    print("Testing Analytics Engine...")
    
    # Test for one vehicle
    v_id = "AV-001"
    print(f"Fetching data for {v_id}...")
    df = ae.get_vehicle_data(v_id)
    print(f"Rows: {len(df)}")
    
    print("Computing Rolling Stats...")
    df = ae.compute_rolling_stats(df)
    print(df[['timestamp', 'sensor_id', 'temperature_c', 'temperature_c_rolling_mean']].head())
    
    print("Detecting Anomalies (Z-Score)...")
    df = ae.detect_anomalies_zscore(df)
    anomalies = df[df['temperature_c_anomaly'] == True]
    print(f"Found {len(anomalies)} temperature anomalies (Z-Score).")

    print("Detecting Anomalies (ML - Isolation Forest)...")
    df = ae.detect_anomalies_ml(df)
    ml_anomalies = df[df['ml_anomaly'] == True]
    print(f"Found {len(ml_anomalies)} anomalies (ML).")
    
    print("Computing Fleet Reliability...")
    mtbf = ae.get_fleet_reliability_metrics()
    print(mtbf)
