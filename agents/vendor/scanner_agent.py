import pandas as pd
import re
from rapidfuzz import fuzz
from typing import List, Dict

# Generic business entity words that cause false-positive matches.
# e.g. "Infosys Technologies" vs "HCL Technologies" — both share "Technologies"
# but are completely different companies.
NOISE_WORDS = {
    "technologies", "technology", "corporation", "corp",
    "incorporated", "inc", "limited", "ltd", "pvt", "private",
    "india", "solutions", "services", "consulting", "group",
    "global", "international", "enterprises", "enterprise",
    "company", "co", "llp", "llc", "and", "the", "of", "&",
    "systems", "software", "digital", "tech", "it",
}


def _clean_name(name: str) -> str:
    """
    Strip noise words and punctuation so only the core brand name remains.
    Example:
      "TCS India Pvt Ltd"   → "tcs"
      "Adobe India Pvt Ltd" → "adobe"
      "Salesforce Inc"      → "salesforce"
      "Salesforce India"    → "salesforce"   ← these two should still match!
    """
    name = name.lower()
    name = re.sub(r"[^a-z0-9 ]", "", name)          # remove punctuation
    tokens = [t for t in name.split() if t not in NOISE_WORDS]
    return " ".join(tokens)


class ScannerAgent:
    """
    Finds duplicate or similar vendors using fuzzy name matching on
    *cleaned* core brand names — not raw names with shared suffixes.

    Threshold raised to 85 because cleaned names are short and precise;
    a match now means the actual brand names are nearly identical.
    """

    SIMILARITY_THRESHOLD = 85

    def find_duplicates(self, df: pd.DataFrame) -> List[Dict]:
        vendor_names  = df["vendor_name"].tolist()
        cleaned_names = [_clean_name(n) for n in vendor_names]

        visited: set   = set()
        groups: List[Dict] = []

        for i, name in enumerate(vendor_names):
            if i in visited:
                continue
            if not cleaned_names[i]:          # skip if nothing left after cleaning
                continue

            group_indices = [i]
            best_score    = 0

            for j, other in enumerate(vendor_names):
                if j == i or j in visited:
                    continue
                if not cleaned_names[j]:
                    continue

                # Compare CLEANED names so shared suffixes don't drive the score
                score = fuzz.token_sort_ratio(cleaned_names[i], cleaned_names[j])
                if score >= self.SIMILARITY_THRESHOLD:
                    group_indices.append(j)
                    best_score = max(best_score, score)

            if len(group_indices) > 1:
                group_df = df.iloc[group_indices].copy()
                groups.append(
                    {
                        "canonical_name":   name,
                        "vendors":          group_df.to_dict("records"),
                        "similarity_score": best_score,
                        "count":            len(group_indices),
                    }
                )
                for idx in group_indices:
                    visited.add(idx)

        return groups