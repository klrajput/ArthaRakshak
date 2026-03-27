from openai import OpenAI
from typing import Dict

NVIDIA_MODEL = "meta/llama-3.1-70b-instruct"


class RecoveryAgent:
    """
    Calls NVIDIA's LLM API to write a recovery plan and escalation email
    for projects at risk of missing their SLA deadline.
    """

    def __init__(self, client: OpenAI):
        self.client = client

    def generate_recovery_plan(self, risk_data: Dict) -> str:
        blocker_text = ""
        for b in risk_data.get("bottlenecks", [])[:4]:
            blocker_text += (
                f"\n  - Task: '{b.get('task_name', 'Unknown')}'"
                f" (assigned to {b.get('assigned_to', 'Unknown')},"
                f" priority: {b.get('priority', '?')})"
                f"\n    Blocker: {b.get('blocker', 'Unknown')}"
            )

        prompt = (
            "You are a senior project recovery specialist.\n\n"
            "A software delivery project is at risk of missing its SLA deadline.\n\n"
            "Current Status:\n"
            f"- Risk Level: {risk_data['risk_level']}\n"
            f"- Tasks completed: {risk_data['tasks_completed']} of {risk_data['contract_tasks']}\n"
            f"- Tasks remaining: {risk_data['tasks_remaining']}\n"
            f"- Days remaining: {risk_data['days_remaining']}\n"
            f"- Current completion rate: {risk_data['current_rate']} tasks/day\n"
            f"- Required rate to meet SLA: {risk_data['required_rate']} tasks/day\n"
            f"- Predicted SLA miss by: {risk_data['predicted_miss_days']} days\n"
            f"- Financial penalty at risk: Rs {risk_data['financial_risk']:,.0f}\n\n"
            f"Key Bottlenecks:{blocker_text if blocker_text else ' None recorded'}\n\n"
            f"Team members: {', '.join(risk_data.get('assignees', ['Unknown']))}\n\n"
            "Generate a SPECIFIC recovery plan with these sections:\n"
            "1. Immediate Actions (Next 24 Hours)\n"
            "2. Resource Reallocation (be specific about names if given)\n"
            f"3. Daily Milestones for the next {min(risk_data['days_remaining'], 5)} days\n"
            "4. Contingency Plan if the recovery fails\n\n"
            "Keep it practical and brief. Use bullet points."
        )

        response = self.client.chat.completions.create(
            model=NVIDIA_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=900,
            temperature=0.4,
        )
        return response.choices[0].message.content

    def generate_escalation_email(self, risk_data: Dict) -> str:
        blockers_text = "; ".join(
            b.get("blocker", "") for b in risk_data.get("bottlenecks", [])[:3]
        ) or "Resource constraints"

        prompt = (
            "Write a professional escalation email from a project manager "
            "to senior management about an SLA breach risk.\n\n"
            "Situation:\n"
            f"- Project will miss SLA by {risk_data['predicted_miss_days']} days\n"
            f"- Current pace: {risk_data['current_rate']} tasks/day, "
            f"needs {risk_data['required_rate']} tasks/day\n"
            f"- Financial penalty exposure: Rs {risk_data['financial_risk']:,.0f}\n"
            f"- Risk level: {risk_data['risk_level']}\n"
            f"- Key blockers: {blockers_text}\n\n"
            "Write the email with:\n"
            "- Subject line\n"
            "- Professional but urgent tone\n"
            "- Clear problem statement in 2 sentences\n"
            "- Specific ask (approve resource reassignment / authorize overtime)\n"
            "- Brief proposed solution\n"
            "- Professional sign-off\n\n"
            "Keep it under 200 words. Output only the email text."
        )

        response = self.client.chat.completions.create(
            model=NVIDIA_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
            temperature=0.3,
        )
        return response.choices[0].message.content