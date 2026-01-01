from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.database import Base

class Feedback(Base):
    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True, index=True)
    violation_id = Column(String, index=True)
    policy_rule_id = Column(String, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    feedback_type = Column(String)  # "VALID" | "FALSE_POSITIVE"
    optional_comment = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")

