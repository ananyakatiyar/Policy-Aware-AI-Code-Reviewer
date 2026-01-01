from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class ReviewRequest(BaseModel):
    code: str
    policies: Optional[List[str]] = []

class DiffReviewRequest(BaseModel):
    original_code: str
    modified_code: str
    policies: Optional[List[str]] = []

class Violation(BaseModel):
    id: str
    line: int
    severity: str
    message: str
    rule_id: str
    status: str = "OPEN" # "OPEN", "FALSE_POSITIVE"
    risk_explanation: Optional[str] = None
    exploit_scenario: Optional[str] = None
    fix_recommendation: Optional[str] = None
    secure_code_example: Optional[str] = None

class FeedbackCreate(BaseModel):
    violation_id: str
    policy_rule_id: str
    feedback_type: str  # "VALID" | "FALSE_POSITIVE"
    optional_comment: Optional[str] = None

class FeedbackStats(BaseModel):
    total_feedback: int
    false_positives: int
    valid_reports: int

class AuditSummary(BaseModel):
    timestamp: str
    file: str
    diff_metadata: Optional[dict] = None # For Diff Review

class ReviewResponse(BaseModel):
    risk_score: int
    risk_level: str
    violations: List[Violation]
    audit: AuditSummary

class DiffMetadata(BaseModel):
    lines_added: int
    lines_modified: int
    lines_removed: int

class DiffReviewResponse(ReviewResponse):
    diff_metadata: DiffMetadata
    risk_delta: int = 0
    original_risk_score: int = 0
    new_risk_score: int = 0
