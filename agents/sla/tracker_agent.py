import pandas as pd
from typing import Dict, List


class TrackerAgent:
    """
    Measures current task completion pace vs the pace needed to meet the SLA.
    Pure Python math — no AI needed here.
    """

    def calculate_progress(
        self,
        df: pd.DataFrame,
        contract_tasks: int,
        days_remaining: int,
    ) -> Dict:
        tasks_completed  = int(len(df[df["status"] == "Completed"]))
        tasks_in_progress = int(len(df[df["status"] == "In Progress"]))
        tasks_pending    = int(len(df[df["status"] == "Pending"]))
        tasks_remaining  = max(0, contract_tasks - tasks_completed)

        # Current completion rate (tasks/day)
        completed_df = df[df["status"] == "Completed"]
        if len(completed_df) > 0 and "days_elapsed" in df.columns:
            total_days_used = completed_df["days_elapsed"].sum()
            current_rate = (tasks_completed / total_days_used) if total_days_used > 0 else 0.5
        else:
            current_rate = tasks_completed / max(days_remaining, 1)

        required_rate = tasks_remaining / max(days_remaining, 1)

        # Find blocked tasks
        bottlenecks: List[Dict] = []
        if "blocker" in df.columns:
            blocked = df[
                df["blocker"].notna()
                & (df["blocker"].astype(str).str.strip().str.lower() != "none")
                & (df["blocker"].astype(str).str.strip() != "")
            ]
            keep_cols = [
                c for c in ["task_id", "task_name", "assigned_to", "blocker", "priority"]
                if c in blocked.columns
            ]
            bottlenecks = blocked[keep_cols].to_dict("records")

        assignees = df["assigned_to"].unique().tolist() if "assigned_to" in df.columns else []

        return {
            "tasks_completed":   tasks_completed,
            "tasks_in_progress": tasks_in_progress,
            "tasks_pending":     tasks_pending,
            "tasks_remaining":   tasks_remaining,
            "contract_tasks":    contract_tasks,
            "days_remaining":    days_remaining,
            "current_rate":      round(float(current_rate), 2),
            "required_rate":     round(float(required_rate), 2),
            "bottlenecks":       bottlenecks,
            "assignees":         assignees,
        }