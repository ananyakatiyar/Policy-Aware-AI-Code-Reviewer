from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import List
from backend.routers.auth import get_current_user

router = APIRouter(tags=["Remediation"])

class RemediationItem(BaseModel):
    rule_id: str

class RemediationRequest(BaseModel):
    violations: List[RemediationItem]

class RemediationSuggestion(BaseModel):
    violation_rule_id: str
    suggestion: str
    example_fix: str
    reason: str

REMEDIATION_KNOWLEDGE_BASE = {
    "no_secrets": {
        "suggestion": "Move secrets to environment variables or a secret management service.",
        "example_fix": "import os\napi_key = os.getenv('API_KEY')",
        "reason": "Hardcoding secrets poses a severe security risk. If the code is committed to version control, the secret is compromised."
    },
    "nested_loops": {
        "suggestion": "Refactor nested loops into separate functions or use efficient data structures (e.g., hash maps).",
        "example_fix": "# Use dictionary for O(1) lookups\nlookup = {x.id: x for x in items}\nfor y in other_items: ...",
        "reason": "Deeply nested loops increase time complexity (often O(N^3) or worse), causing performance bottlenecks."
    },
    "blocking_calls": {
        "suggestion": "Offload blocking calls to a background thread or use asynchronous alternatives.",
        "example_fix": "await asyncio.sleep(5)  # Instead of time.sleep(5)",
        "reason": "Blocking calls in the main thread (especially in async contexts) freeze the application, making it unresponsive."
    },
    "enforce_logging": {
        "suggestion": "Integrate the `logging` module to track application state and errors.",
        "example_fix": "import logging\nlogging.info('Operation started')",
        "reason": "Without logs, debugging production issues is nearly impossible. `print` statements are insufficient for enterprise apps."
    },
    "error_handling": {
        "suggestion": "Catch specific exceptions and log the error; never use bare `except:` pass.",
        "example_fix": "except ValueError as e:\n    logging.error(f'Invalid input: {e}')",
        "reason": "Empty except blocks silence legitimate errors, leading to unpredictable behavior and difficult debugging."
    }
}

@router.post("/remediation", response_model=List[RemediationSuggestion])
async def get_remediation(request: RemediationRequest, current_user = Depends(get_current_user)):
    """
    AI-powered (Deterministic Heuristic) remediation assistant.
    Returns actionable advice for each violation.
    """
    suggestions = []
    
    # De-duplicate violations by rule_id to avoid repetitive advice
    seen_rules = set()
    
    for v in request.violations:
        if v.rule_id in seen_rules:
            continue
            
        if v.rule_id in REMEDIATION_KNOWLEDGE_BASE:
            kb = REMEDIATION_KNOWLEDGE_BASE[v.rule_id]
            suggestions.append(RemediationSuggestion(
                violation_rule_id=v.rule_id,
                suggestion=kb["suggestion"],
                example_fix=kb["example_fix"],
                reason=kb["reason"]
            ))
            seen_rules.add(v.rule_id)
            
    return suggestions
