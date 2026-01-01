from typing import List, Tuple
from backend.models.schemas import Violation

class RiskEngine:
    def calculate_score(self, violations: List[Violation]) -> Tuple[int, str]:
        score = 100
        
        weights = {
            "HIGH": 20,
            "MEDIUM": 10,
            "LOW": 5
        }
        
        for v in violations:
            if v.status == "FALSE_POSITIVE":
                continue

            deduction = weights.get(v.severity.upper(), 5)
            score -= deduction
            
        score = max(0, score)
        
        # Determine level
        if score >= 80:
            level = "LOW RISK"
        elif score >= 50:
            level = "MEDIUM RISK"
        else:
            level = "HIGH RISK"
            
        return score, level
