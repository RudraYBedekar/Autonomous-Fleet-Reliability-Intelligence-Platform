import pandas as pd
import numpy as np

class Forecaster:
    """
    In a real-world scenario, this class would use ARIMA, Prophet, or LSTM 
    to forecast sensor degradation over time.
    For this simulation, we'll use a linear degradation model to estimate 
    Failure Probability and RUL based on historical trends.
    """
    
    def __init__(self):
        pass

    def calculate_failure_probability(self, current_rul_hours: float) -> dict:
        """
        Given the current RUL, calculate the probability of failure 
        within 24, 48, and 72 hours using an exponential decay curve.
        """
        # If RUL is high (> 500), probability is basically 0
        # As RUL approaches 0, probability approaches 100%
        
        def prob(time_window):
            if current_rul_hours <= 0:
                return 99.9
            
            # Simple inverse relationship smoothed by exponential
            # P(fail in T hours) = e^(-RUL / (T * factor))
            # Just a heuristic for the dashboard
            raw_prob = np.exp(-current_rul_hours / (time_window * 2))
            return min(99.9, round(raw_prob * 100, 1))

        return {
            "24h": prob(24),
            "48h": prob(48),
            "72h": prob(72)
        }

if __name__ == "__main__":
    f = Forecaster()
    print("Test RUL=100 hours:", f.calculate_failure_probability(100))
    print("Test RUL=500 hours:", f.calculate_failure_probability(500))
    print("Test RUL=10 hours:", f.calculate_failure_probability(10))
