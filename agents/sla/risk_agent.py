from typing import Dict


class RiskAgent:
    """
    Predicts SLA breach risk and financial exposure.
    Pure Python math — no AI needed here.
    """

    def assess_risk(self, tracking_data: Dict, penalty_per_day: float) -> Dict:
        current_rate    = tracking_data["current_rate"]
        tasks_remaining = tracking_data["tasks_remaining"]
        days_remaining  = tracking_data["days_remaining"]
        required_rate   = tracking_data["required_rate"]

        days_needed = (
            (tasks_remaining / current_rate) if current_rate > 0
            else days_remaining + 10
        )

        predicted_miss_days = round(max(0.0, days_needed - days_remaining), 1)
        financial_risk      = round(predicted_miss_days * penalty_per_day, 0)
        rate_gap            = round(required_rate - current_rate, 2)

        if predicted_miss_days > 3:
            risk_level = "HIGH"
        elif predicted_miss_days > 0:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        return {
            **tracking_data,
            "risk_level":                  risk_level,
            "predicted_miss_days":         predicted_miss_days,
            "financial_risk":              financial_risk,
            "rate_gap":                    rate_gap,
            "penalty_per_day":             penalty_per_day,
            "days_needed_at_current_rate": round(float(days_needed), 1),
        }