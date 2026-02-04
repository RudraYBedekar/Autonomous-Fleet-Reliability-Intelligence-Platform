import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import pydeck as pdk
from analytics_engine import AnalyticsEngine

# Page Config
st.set_page_config(layout="wide", page_title="Hardware Reliability Analytics")

# Initialize Analytics Engine
# Caching the engine init to avoid reconnecting on every rerun
@st.cache_resource
def get_analytics_engine():
    return AnalyticsEngine()

ae = get_analytics_engine()

# Title and Auto-Refresh
col_title, col_refresh = st.columns([3, 1])
with col_title:
    st.title("🚜 Hardware Reliability Analytics Dashboard")

with col_refresh:
    live_mode = st.toggle("🔴 Live Mode (Auto-Refresh)")
    if live_mode:
        time_sleep = st.slider("Refresh Rate (s)", 1, 10, 2)
        import time
        time.sleep(time_sleep)
        st.rerun()
st.markdown("Monitor fleet health, detect anomalies, and track reliability metrics in real-time.")

# Sidebar - Filter
st.sidebar.header("Filter Settings")
# Get list of vehicles (optimize this query in real prod)
vehicles = pd.read_sql("SELECT DISTINCT vehicle_id FROM telemetry", ae.engine)['vehicle_id'].tolist()
selected_vehicle = st.sidebar.selectbox("Select Vehicle", vehicles)

# Main Content
col1, col2, col3 = st.columns(3)

# Fleet Wide Metrics
mtbf_df = ae.get_fleet_reliability_metrics()
avg_mtbf = mtbf_df['mtbf_hours'].mean() if not mtbf_df.empty else 0

with col1:
    st.metric("Total Vehicles", len(vehicles))
with col2:
    st.metric("Avg Fleet MTBF", f"{avg_mtbf:.2f} Hours")
with col3:
    # Count total critical alerts
    alert_count = pd.read_sql("SELECT count(*) FROM telemetry WHERE status='Critical'", ae.engine).iloc[0,0]
    st.metric("Total Critical Alerts", alert_count)

st.divider()

# Vehicle Specific Analysis
st.subheader(f"📊 Analysis for {selected_vehicle}")

# Fetch Data
with st.spinner("Loading Vehicle Data..."):
    df = ae.get_vehicle_data(selected_vehicle)
    df = ae.compute_rolling_stats(df)

    df = ae.detect_anomalies_zscore(df)
    df = ae.detect_anomalies_ml(df) # Add ML detection

# Tabs
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["Telemetry Overview", "Geospatial View", "Predictive Maintenance", "Z-Score Anomalies", "ML Anomalies", "Raw Data"])

with tab1:
    st.markdown("### Sensor Telemetry")
    sensor_type = st.selectbox("Select Sensor Type", df['sensor_id'].unique())
    
    sensor_df = df[df['sensor_id'] == sensor_type]
    
    fig = go.Figure()
    
    # Temperature
    fig.add_trace(go.Scatter(x=sensor_df['timestamp'], y=sensor_df['temperature_c'],
                        mode='lines', name='Temperature (C)'))
    
    # Rolling Mean
    fig.add_trace(go.Scatter(x=sensor_df['timestamp'], y=sensor_df['temperature_c_rolling_mean'],
                        mode='lines', name='Rolling Mean (Temp)', line=dict(dash='dash')))
    
    # Annotate Anomalies
    anomalies = sensor_df[sensor_df['temperature_c_anomaly']]
    if not anomalies.empty:
        fig.add_trace(go.Scatter(x=anomalies['timestamp'], y=anomalies['temperature_c'],
                            mode='markers', name='Anomaly', marker=dict(color='red', size=10, symbol='x')))

    fig.update_layout(title=f"{sensor_type} - Temperature Over Time", xaxis_title="Time", yaxis_title="Temperature (C)")
    st.plotly_chart(fig, use_container_width=True)

    # Voltage/Value Plot
    y_label = "Voltage (V)"
    if sensor_type == 'Speed': y_label = "Speed (km/h)"
    elif sensor_type == 'EngineRPM': y_label = "RPM"
    
    fig2 = px.line(sensor_df, x='timestamp', y='voltage_v', title=f"{sensor_type} - {y_label} Over Time")
    fig2.update_yaxes(title=y_label)
    st.plotly_chart(fig2, use_container_width=True)

with tab2:
    st.markdown("### 🗺️ Geospatial Fleet Tracking")
    st.markdown("Live location of the vehicle moving along Mowry Ave, Fremont, CA.")
    
    # Map requires lat/lon columns
    map_df = df[['latitude', 'longitude', 'status']].dropna()
    
    if not map_df.empty:
        # Get latest position for centering
        midpoint = (np.average(map_df["latitude"]), np.average(map_df["longitude"]))
        
        # Define Layer
        layer = pdk.Layer(
            "ScatterplotLayer",
            map_df,
            get_position='[longitude, latitude]',
            get_color='[0, 100, 255, 200]', # Blue
            get_radius=15, # Radius in meters
            pickable=True
        )

        # Set the view state (Zoom level 15 is good for streets)
        view_state = pdk.ViewState(
            latitude=midpoint[0],
            longitude=midpoint[1],
            zoom=15,
            pitch=0,
        )

        # Render
        r = pdk.Deck(
            layers=[layer],
            initial_view_state=view_state,
            tooltip={"text": "Lat: {latitude}\nLon: {longitude}\nStatus: {status}"},
            map_style='mapbox://styles/mapbox/streets-v11' # Use street style
        )
        
        st.pydeck_chart(r)
        
        st.markdown(f"**Current Location:** {map_df.iloc[-1]['latitude']:.4f}, {map_df.iloc[-1]['longitude']:.4f}")
    else:
        st.warning("No GPS data available for this vehicle.")

with tab3:
    st.markdown("### 🔮 Predictive Maintenance (RUL)")
    st.info("Estimated Remaining Useful Life (RUL) based on sensor degradation patterns.")
    
    # Calculate RUL
    rul_df = ae.predict_rul(df)
    
    # Get latest RUL for each sensor
    latest_rul = rul_df.groupby('sensor_id').last().reset_index()
    
    # Display metrics
    cols = st.columns(len(latest_rul))
    for idx, row in latest_rul.iterrows():
        with cols[idx % 3]:
            rul_val = row['predicted_rul_hours']
            delta_color = "normal"
            if rul_val < 200: delta_color = "inverse" # Critical
            
            st.metric(f"{row['sensor_id']} RUL", f"{rul_val} Hrs", delta=None, delta_color=delta_color)
            if rul_val < 200:
                st.error(f"⚠️ Maintenance Required soon for {row['sensor_id']}")
    
    # Plot RUL over time for a selected sensor
    st.markdown("#### RUL Forecast Trend")
    rul_sensor = st.selectbox("Select Sensor for RUL Trend", latest_rul['sensor_id'].unique())
    
    sensor_rul_df = rul_df[rul_df['sensor_id'] == rul_sensor]
    fig_rul = px.line(sensor_rul_df, x='timestamp', y='predicted_rul_hours', title=f"Predicted RUL Degradation - {rul_sensor}")
    fig_rul.add_hline(y=200, line_dash="dash", line_color="red", annotation_text="Critical Threshold")
    st.plotly_chart(fig_rul, use_container_width=True)

with tab4:
    st.markdown("### Z-Score Detected Anomalies")
    
    # Filter only anomalies
    anomalies_all = df[(df['temperature_c_anomaly']) | (df['voltage_v_anomaly']) | (df['vibration_g_anomaly'])]
    
    if anomalies_all.empty:
        st.success("No anomalies detected for this vehicle.")
    else:
        st.warning(f"Found {len(anomalies_all)} anomalies.")
        st.dataframe(anomalies_all[['timestamp', 'sensor_id', 'temperature_c', 'voltage_v', 'vibration_g', 'status']])
        
        # Heatmap of anomalies over time/sensor could go here
        fig_scatter = px.scatter(anomalies_all, x='timestamp', y='sensor_id', color='status', 
                                 title="Anomaly Timeline", symbol='sensor_id')
        st.plotly_chart(fig_scatter, use_container_width=True)


with tab5:
    st.markdown("### Machine Learning Detected Anomalies (Isolation Forest)")
    st.info("Isolation Forest is an unsupervised learning algorithm that isolates anomalies by randomly selecting a feature and then randomly selecting a split value between the maximum and minimum values of the selected feature.")
    
    ml_anomalies = df[df['ml_anomaly']]
    
    if ml_anomalies.empty:
        st.success("No anomalies detected by ML model.")
    else:
        st.warning(f"ML Model found {len(ml_anomalies)} anomalies (potentially subtle ones missed by Z-Score).")
        st.dataframe(ml_anomalies[['timestamp', 'sensor_id', 'temperature_c', 'voltage_v', 'vibration_g']])
        
        # Compare with Z-score
        st.markdown("#### Comparison: ML vs Z-Score")
        
        # Plot
        fig_ml = px.scatter(df, x='timestamp', y='voltage_v', color='ml_anomaly', 
                             title="ML Anomaly Detection Results", symbol='ml_anomaly',
                             color_discrete_map={False: 'blue', True: 'red'})
        st.plotly_chart(fig_ml, use_container_width=True)

with tab6:
    st.dataframe(df)

st.markdown("---")
st.caption("Hardware Reliability Analytics | Built by Antigravity")
