from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models.schemas import FeedbackCreate, FeedbackStats
from backend.models.feedback import Feedback
from backend.routers.auth import get_current_user

router = APIRouter(
    prefix="/feedback",
    tags=["feedback"]
)

@router.post("", response_model=dict)
def submit_feedback(
    feedback: FeedbackCreate, 
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    # Check if feedback already exists
    existing = db.query(Feedback).filter(
        Feedback.violation_id == feedback.violation_id,
        Feedback.user_id == current_user.id
    ).first()
    
    if existing:
        existing.feedback_type = feedback.feedback_type
        existing.optional_comment = feedback.optional_comment
        existing.policy_rule_id = feedback.policy_rule_id
    else:
        new_feedback = Feedback(
            violation_id=feedback.violation_id,
            policy_rule_id=feedback.policy_rule_id,
            user_id=current_user.id,
            feedback_type=feedback.feedback_type,
            optional_comment=feedback.optional_comment
        )
        db.add(new_feedback)
    
    db.commit()
    return {"status": "success"}

@router.get("/stats", response_model=FeedbackStats)
def get_feedback_stats(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    total = db.query(Feedback).count()
    fps = db.query(Feedback).filter(Feedback.feedback_type == "FALSE_POSITIVE").count()
    valid = db.query(Feedback).filter(Feedback.feedback_type == "VALID").count()
    
    return FeedbackStats(
        total_feedback=total,
        false_positives=fps,
        valid_reports=valid
    )
