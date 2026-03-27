from typing import List, Dict


class FinanceAgent:
    """
    Calculates consolidation savings for each duplicate vendor group.
    Pure Python math — no AI needed here.

    Logic:
      - Keep the largest vendor (primary spend)
      - Everything paid to smaller duplicates = waste
      - Realistically recover 70% of that waste
    """

    RECOVERY_RATE = 0.70

    def calculate_savings(self, groups: List[Dict]) -> List[Dict]:
        for group in groups:
            vendors = group["vendors"]
            total_spend   = sum(v.get("annual_spend", 0) for v in vendors)
            primary_spend = max(v.get("annual_spend", 0) for v in vendors)
            duplicate_spend      = total_spend - primary_spend
            estimated_savings    = duplicate_spend * self.RECOVERY_RATE

            group["total_group_spend"] = total_spend
            group["primary_spend"]     = primary_spend
            group["duplicate_spend"]   = duplicate_spend
            group["savings"]           = estimated_savings

        groups.sort(key=lambda x: x["savings"], reverse=True)
        return groups