# Policy-Aware AI Code Reviewer

A FAANG-level internal developer tool for static analysis, risk scoring, and AI-driven remediation.

## Project Structure

```
/
├── frontend/           # Frontend Application (Served by Backend)
│   ├── index.html      # Dashboard
│   ├── login.html      # Authentication
│   ├── styles.css      # Enterprise Dark Theme
│   └── script.js       # Client Logic
│
├── backend/            # FastAPI Backend
│   ├── core/           # Core Logic Engines (Analysis, Risk, Security)
│   ├── routers/        # API Endpoints (Auth, Remediation)
│   ├── models/         # Pydantic & SQLAlchemy Models
│   ├── policies/       # Policy Definitions
│   ├── main.py         # App Entry Point
│   └── requirements.txt
```

## Quick Start (VS Code)

1.  **Install Extensions**: Ensure you have the Python extension installed.
2.  **Install Dependencies**:
    ```bash
    pip install -r backend/requirements.txt
    ```
3.  **Run**:
    *   Press `F5` or go to the **Run and Debug** tab and click "Run AI Code Reviewer".
    *   **OR** run in terminal: `uvicorn backend.main:app --reload`

4.  **Access**:
    *   Open [http://localhost:8000](http://localhost:8000)
    *   Register a new account and log in.

## Features

*   **Full Authentication**: JWT-based Login/Register flow.
*   **Static Analysis**: Detects secrets, nested loops, blocking calls.
*   **AI Remediation**: Deterministic "How to Fix" suggestions with code examples.
*   **Risk Scoring**: 0-100 score with visual indicators.
*   **Enterprise UI**: Dark mode, neon accents, responsive design.
