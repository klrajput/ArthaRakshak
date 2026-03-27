from openai import OpenAI
import pandas as pd
from datetime import datetime
from typing import Dict, List

from agents.vendor.scanner_agent import ScannerAgent
from agents.vendor.finance_agent import FinanceAgent
from agents.vendor.advisor_agent import AdvisorAgent
from agents.sla.tracker_agent import TrackerAgent
from agents.sla.risk_agent import RiskAgent
from agents.sla.recovery_agent import RecoveryAgent

NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"


class Orchestrator:
    """
    Master coordinator for ArthaRakshak.

    Creates ONE shared NVIDIA API client and passes it to all AI agents.
    Logs every agent decision with a timestamp for the audit trail.
    """

    def __init__(self, api_key: str):
        # Single OpenAI-compatible client pointed at NVIDIA's endpoint
        self.client = OpenAI(
            base_url=NVIDIA_BASE_URL,
            api_key=api_key,
        )
        self.audit_log: List[Dict] = []

    def _log(self, agent: str, action: str, detail: str) -> None:
        self.audit_log.append(
            {
                "timestamp": datetime.now().strftime("%H:%M:%S"),
                "agent":     agent,
                "action":    action,
                "detail":    detail,
            }
        )

    # ─── Vendor pipeline ──────────────────────────────────────────────────────
    def run_vendor_analysis(self, df: pd.DataFrame) -> Dict:
        self._log("Orchestrator", "start", f"Received {len(df)} vendor records")

        # Step 1 — Scanner (no AI)
        self._log("ScannerAgent", "begin", "Running fuzzy name matching")
        scanner = ScannerAgent()
        groups  = scanner.find_duplicates(df)
        self._log("ScannerAgent", "done", f"Found {len(groups)} duplicate groups")

        if not groups:
            self._log("Orchestrator", "no_duplicates", "No duplicates above threshold")
            return {
                "duplicate_groups": [],
                "total_savings":    0,
                "action_plan":      "No duplicate vendors found. Data looks clean!",
                "audit_log":        self.audit_log,
            }

        # Step 2 — Finance (no AI)
        self._log("FinanceAgent", "begin", f"Calculating savings for {len(groups)} groups")
        finance = FinanceAgent()
        groups  = finance.calculate_savings(groups)
        total_savings = sum(g["savings"] for g in groups)
        self._log("FinanceAgent", "done", f"Total savings: Rs {total_savings:,.0f}")

        # Step 3 — Advisor (NVIDIA LLM)
        self._log("AdvisorAgent", "calling_nvidia", "Sending findings to NVIDIA LLM API")
        advisor     = AdvisorAgent(self.client)
        action_plan = advisor.generate_action_plan(groups, total_savings)
        self._log("AdvisorAgent", "done", "Action plan generated")

        self._log("Orchestrator", "complete", "Vendor pipeline finished")
        return {
            "duplicate_groups": groups,
            "total_savings":    total_savings,
            "action_plan":      action_plan,
            "audit_log":        self.audit_log,
        }

    # ─── SLA pipeline ─────────────────────────────────────────────────────────
    def run_sla_analysis(
        self,
        df: pd.DataFrame,
        contract_tasks: int,
        days_remaining: int,
        penalty_per_day: float,
    ) -> Dict:
        self._log("Orchestrator", "start", f"Received {len(df)} task records")

        # Step 1 — Tracker (no AI)
        self._log("TrackerAgent", "begin", "Measuring completion rate")
        tracker      = TrackerAgent()
        tracking     = tracker.calculate_progress(df, contract_tasks, days_remaining)
        self._log(
            "TrackerAgent", "done",
            f"Rate {tracking['current_rate']}/day, need {tracking['required_rate']}/day, "
            f"bottlenecks: {len(tracking['bottlenecks'])}",
        )

        # Step 2 — Risk (no AI)
        self._log("RiskAgent", "begin", "Predicting SLA breach")
        risk_agent = RiskAgent()
        risk_data  = risk_agent.assess_risk(tracking, penalty_per_day)
        self._log(
            "RiskAgent", "done",
            f"Risk: {risk_data['risk_level']}, miss by {risk_data['predicted_miss_days']} days, "
            f"penalty exposure: Rs {risk_data['financial_risk']:,.0f}",
        )

        # Step 3 — Recovery plan (NVIDIA LLM)
        self._log("RecoveryAgent", "calling_nvidia_plan", "Generating recovery plan via NVIDIA API")
        recovery      = RecoveryAgent(self.client)
        recovery_plan = recovery.generate_recovery_plan(risk_data)
        self._log("RecoveryAgent", "plan_done", "Recovery plan generated")

        # Step 4 — Escalation email (NVIDIA LLM)
        self._log("RecoveryAgent", "calling_nvidia_email", "Generating escalation email via NVIDIA API")
        escalation_email = recovery.generate_escalation_email(risk_data)
        self._log("RecoveryAgent", "email_done", "Escalation email generated")

        self._log("Orchestrator", "complete", "SLA pipeline finished")
        return {
            **risk_data,
            "recovery_plan":     recovery_plan,
            "escalation_email":  escalation_email,
            "audit_log":         self.audit_log,
        }