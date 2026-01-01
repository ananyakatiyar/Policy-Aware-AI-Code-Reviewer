from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from datetime import datetime
import uvicorn
import os

from backend.models.schemas import ReviewRequest, ReviewResponse, AuditSummary
from backend.core.policy_engine import PolicyEngine
from backend.core.analyzer import StaticAnalyzer
from backend.core.risk_engine import RiskEngine
from backend.routers import auth, remediation, feedback, review, export
from backend.database import engine, Base, get_db
from backend.routers.auth import get_current_user
from backend.models.feedback import Feedback
from sqlalchemy.orm import Session
from fastapi import Depends

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Policy-Aware AI Code Reviewer")

# Include Routers
app.include_router(auth.router)
app.include_router(remediation.router)
app.include_router(feedback.router)
app.include_router(review.router)
app.include_router(export.router)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, specify domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize engines
policy_engine = PolicyEngine()
static_analyzer = StaticAnalyzer()
risk_engine = RiskEngine()

@app.post("/review", response_model=ReviewResponse)
async def review_code(
    request: ReviewRequest, 
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    try:
        # 1. Get active policies
        active_policies = policy_engine.get_policies(request.policies)
        
        # 2. Run Analysis
        violations = static_analyzer.analyze(request.code, active_policies)
        
        # 3. Apply Feedback
        feedbacks = db.query(Feedback).filter(Feedback.user_id == current_user.id).all()
        fp_map = {f.violation_id: f.feedback_type for f in feedbacks}
        
        for v in violations:
            if fp_map.get(v.id) == "FALSE_POSITIVE":
                v.status = "FALSE_POSITIVE"
        
        # 4. Calculate Risk
        score, level = risk_engine.calculate_score(violations)
        
        # 5. Construct Response
        return ReviewResponse(
            risk_score=score,
            risk_level=level,
            violations=violations,
            audit=AuditSummary(
                timestamp=datetime.now().strftime("%b %d, %Y, %I:%M:%S %p"),
                file="untitled.py" # In real app, this would come from request
            )
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/@vite/client")
async def vite_client_placeholder():
    """
    Dummy endpoint to silence 404 errors from IDEs/tools that expect a Vite dev server.
    """
    return ""

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return Response(status_code=204)

# Mount static files (Frontend)
# Ensure we map the correct absolute path or relative path
frontend_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")
if os.path.exists(frontend_path):
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")
else:
    print(f"Warning: Frontend directory not found at {frontend_path}")

if __name__ == "__main__":
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
