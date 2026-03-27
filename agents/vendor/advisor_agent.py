from openai import OpenAI
from typing import List, Dict

NVIDIA_MODEL = "meta/llama-3.1-70b-instruct"


class AdvisorAgent:
    """
    Calls NVIDIA's LLM API to write a professional vendor consolidation
    action plan based on the findings from ScannerAgent + FinanceAgent.

    Uses openai SDK pointed at NVIDIA's OpenAI-compatible endpoint.
    """

    def __init__(self, client: OpenAI):
        self.client = client

    def generate_action_plan(self, groups: List[Dict], total_savings: float) -> str:
        findings = ""
        for i, g in enumerate(groups[:6], 1):
            names = ", ".join(v["vendor_name"] for v in g["vendors"])
            service = g["vendors"][0].get("service_category", "Unknown")
            findings += (
                f"\n{i}. Duplicate group: {names}\n"
                f"   Service category: {service}\n"
                f"   Total annual spend: Rs {g['total_group_spend']:,.0f}\n"
                f"   Estimated savings if consolidated: Rs {g['savings']:,.0f}\n"
            )

        prompt = (
            "You are a senior enterprise cost optimization advisor.\n\n"
            "A vendor audit has identified these duplicate vendor groups:\n"
            f"{findings}\n"
            f"Total estimated annual savings: Rs {total_savings:,.0f}\n\n"
            "Generate a clear, practical action plan with three sections:\n"
            "1. Immediate Actions (This Week) - quick wins doable in days\n"
            "2. 30-Day Actions - consolidations needing vendor negotiation\n"
            "3. Process Improvements - how to prevent new duplicates\n\n"
            "Use bullet points. Keep each point to 1-2 sentences. "
            "Be specific. Do not repeat the numbers I gave you."
        )

        response = self.client.chat.completions.create(
            model=NVIDIA_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=900,
            temperature=0.4,
        )
        return response.choices[0].message.content