# Policy-Aware AI Code Reviewer

A FAANG-level internal developer tool for static analysis, risk scoring, and AI-driven remediation.

## Overview

This project is designed as a real-world internal developer tool similar to
those used in large-scale engineering organizations. It combines deterministic
static analysis with policy-driven rules and AI-assisted remediation to improve
signal quality and reduce false positives.

The system emphasizes explainability, modularity, and secure engineering
practices rather than generic rule-based scanning.


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

## Contributors & Ownership

Ownership is module-based, following industry-standard backend and frontend
separation to reflect real-world engineering collaboration.

### Ananya Katiyar — Backend & Systems Engineering
- Backend architecture and API design
- Static analysis and policy enforcement logic
- Risk scoring engine (0–100)
- False-positive handling mechanisms
- Backend testing and validation

### Kamal Pangariya — Frontend & Platform Engineering
- Frontend UI and user experience
- Authentication and authorization flows
- AI remediation interface
- Dashboard and risk visualization

Each contributor commits from their respective GitHub accounts and owns
independent modules.

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

  ## Engineering Practices

- Clean repository hygiene (no generated artifacts committed)
- Modular backend and frontend separation
- Deterministic policy enforcement with explainable outputs
- Test-driven validation for core analysis logic
- Secure authentication using JWT

## Note

This project was built with clear ownership boundaries to reflect how
engineering teams collaborate in production environments. Each contributor
can independently explain and extend their respective modules.

