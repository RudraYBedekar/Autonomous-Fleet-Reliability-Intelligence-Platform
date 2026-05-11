class RootCauseAnalyzer:
    """
    Simulates an expert system for Root Cause Analysis (RCA).
    Correlates multiple sensor states to deduce the likely root cause.
    """

    @staticmethod
    def analyze(sensor_id: str, temp: float, voltage: float, vibration: float) -> dict:
        cause = "Unknown Anomaly"
        action = "Inspect component immediately."
        confidence = 50

        if sensor_id == "LiDAR":
            if vibration > 1.0 and temp > 60:
                cause = "Mounting Bracket Failure leading to overheating friction."
                action = "Replace LiDAR mounting bracket and recalibrate."
                confidence = 85
            elif voltage < 10.0:
                cause = "Power Delivery Fluctuation (Wiring harness degradation)."
                action = "Check wiring harness for shorts or corrosion."
                confidence = 90
            elif temp > 70:
                cause = "Cooling fan failure inside LiDAR unit."
                action = "Replace internal cooling fan."
                confidence = 80
                
        elif sensor_id == "Battery":
            if temp > 60 and voltage < 350:
                cause = "Thermal Runaway Pre-condition / Cell Degradation."
                action = "Isolate vehicle. Schedule immediate pack replacement."
                confidence = 95
            elif temp < 0:
                cause = "Battery Heater Failure."
                action = "Inspect battery thermal management system."
                confidence = 85
                
        elif sensor_id == "EngineRPM":
            if vibration > 1.5:
                cause = "Drivetrain Imbalance / Motor Bearing Wear."
                action = "Inspect motor bearings and drivetrain alignment."
                confidence = 88
                
        # Default generic checks
        if cause == "Unknown Anomaly":
            if vibration > 1.2:
                cause = "Excessive mechanical stress detected."
                confidence = 60
            elif temp > 80:
                cause = "Critical overheating."
                confidence = 70
            elif voltage == 0:
                cause = "Complete power loss."
                action = "Check main fuse and power distribution module."
                confidence = 99

        return {
            "root_cause": cause,
            "recommended_action": action,
            "confidence_score": confidence
        }

if __name__ == "__main__":
    rca = RootCauseAnalyzer()
    print(rca.analyze("LiDAR", 85, 12, 1.5))
    print(rca.analyze("Battery", 70, 300, 0.2))
