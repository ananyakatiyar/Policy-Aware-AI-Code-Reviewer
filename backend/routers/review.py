from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from backend.models.schemas import DiffReviewRequest, DiffReviewResponse, ReviewResponse, AuditSummary, DiffMetadata
from backend.core.policy_engine import PolicyEngine
from backend.core.analyzer import StaticAnalyzer
from backend.core.risk_engine import RiskEngine
from backend.routers.auth import get_current_user
from backend.database import get_db
from backend.models.feedback import Feedback
from datetime import datetime
import difflib

router = APIRouter(
    prefix="/review",
    tags=["review"]
)

policy_engine = PolicyEngine()
static_analyzer = StaticAnalyzer()
risk_engine = RiskEngine()

@router.post("/diff", response_model=DiffReviewResponse)
async def review_diff(
    request_body: dict = Body(...),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    try:
        # Accept flexible JSON body to avoid 422 on validation differences from clients
        original = request_body.get('original_code')
        modified = request_body.get('modified_code')
        policies = request_body.get('policies', []) or []

        if original is None or modified is None:
            raise HTTPException(status_code=422, detail="Both 'original_code' and 'modified_code' are required")

        # 1. Compute Diff & Changed Lines
        d = difflib.Differ()
        original_lines = str(original).splitlines()
        modified_lines = str(modified).splitlines()
        
        diff = list(d.compare(original_lines, modified_lines))
        
        changed_lines_indices = [] # 1-based indices in modified code
        lines_added = 0
        lines_removed = 0
        
        current_line_idx = 0 # in modified file
        
        for line in diff:
            code = line[0]
            if code == ' ':
                # Unchanged
                current_line_idx += 1
            elif code == '-':
                # Removed from original
                lines_removed += 1
            elif code == '+':
                # Added/Modified in new
                current_line_idx += 1
                changed_lines_indices.append(current_line_idx)
                lines_added += 1
        
        # 2. Analyze Modified Code
        active_policies = policy_engine.get_policies(policies)
        all_violations = static_analyzer.analyze(modified, active_policies)
        
        # Apply Feedback
        feedbacks = db.query(Feedback).filter(Feedback.user_id == current_user.id).all()
        fp_map = {f.violation_id: f.feedback_type for f in feedbacks}
        
        for v in all_violations:
            if fp_map.get(v.id) == "FALSE_POSITIVE":
                v.status = "FALSE_POSITIVE"

        # 3. Filter Violations
        diff_violations = [
            v for v in all_violations 
            if v.line in changed_lines_indices
        ]
        
        # 4. Calculate Risk (Scoped)
        score, level = risk_engine.calculate_score(diff_violations)
        
        # 5. Calculate Global Risk Delta
        original_violations = static_analyzer.analyze(original, active_policies)
        for v in original_violations:
            if fp_map.get(v.id) == "FALSE_POSITIVE":
                v.status = "FALSE_POSITIVE"
        
        score_old, _ = risk_engine.calculate_score(original_violations)
        score_new, _ = risk_engine.calculate_score(all_violations)
        risk_delta = score_new - score_old
        
        # 6. Response
        return DiffReviewResponse(
            risk_score=score,
            risk_level=level,
            violations=diff_violations,
            audit=AuditSummary(
                timestamp=datetime.now().strftime("%b %d, %Y, %I:%M:%S %p"),
                file="diff_review.py",
                diff_metadata={
                    "lines_added": lines_added,
                    "lines_removed": lines_removed,
                    "lines_modified": lines_added 
                }
            ),
            diff_metadata=DiffMetadata(
                lines_added=lines_added,
                lines_modified=lines_added,
                lines_removed=lines_removed
            ),
            risk_delta=risk_delta,
            original_risk_score=score_old,
            new_risk_score=score_new
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
