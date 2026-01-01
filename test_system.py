import requests
import time
import sys

BASE_URL = "http://127.0.0.1:8000"

def run_test():
    print("=== STARTING SYSTEM VERIFICATION ===")
    
    # 1. Register & Login
    timestamp = int(time.time())
    email = f"test_{timestamp}@example.com"
    password = "password123"
    name = "Test User"
    
    print(f"\n[1] Authentication: Creating user {email}...")
    try:
        res = requests.post(f"{BASE_URL}/auth/register", json={"email": email, "password": password, "name": name})
        if res.status_code != 200:
            print(f"FAIL: Registration failed ({res.status_code}): {res.text}")
            return
        
        res = requests.post(f"{BASE_URL}/auth/login", json={"email": email, "password": password})
        if res.status_code != 200:
            print(f"FAIL: Login failed ({res.status_code}): {res.text}")
            return
            
        token = res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print("PASS: Authentication successful.")
    except Exception as e:
        print(f"FAIL: Auth connection error: {e}")
        return

    # 2. Standard Review & Feedback Loop
    print("\n[2] Testing Feedback Loop...")
    code_with_issue = """
def connect_db():
    password = "super_secret_password" # Hardcoded secret
    print(password)
"""
    policies = ["no_secrets"] # Assuming this policy exists in rules.json
    
    # Initial Review
    res = requests.post(f"{BASE_URL}/review", json={"code": code_with_issue, "policies": policies}, headers=headers)
    data = res.json()
    initial_score = data["risk_score"]
    violations = data["violations"]
    
    if not violations:
        print("FAIL: Expected violations but found none. Check policy engine.")
        return
        
    print(f"Initial Risk Score: {initial_score}")
    print(f"Violations found: {len(violations)}")
    
    # Submit Feedback
    violation = violations[0]
    print(f"Marking violation {violation['id']} as FALSE_POSITIVE...")
    
    res = requests.post(f"{BASE_URL}/feedback", json={
        "violation_id": violation["id"],
        "policy_rule_id": violation["rule_id"],
        "feedback_type": "FALSE_POSITIVE",
        "optional_comment": "This is a test secret"
    }, headers=headers)
    
    if res.status_code != 200:
        print(f"FAIL: Feedback submission failed: {res.text}")
        return
        
    # Re-run Review
    res = requests.post(f"{BASE_URL}/review", json={"code": code_with_issue, "policies": policies}, headers=headers)
    data = res.json()
    new_score = data["risk_score"]
    new_violations = data["violations"]
    
    print(f"New Risk Score: {new_score}")
    
    # Check if violation status is updated
    fp_violation = next((v for v in new_violations if v["id"] == violation["id"]), None)
    if fp_violation and fp_violation.get("status") == "FALSE_POSITIVE":
        print("PASS: Violation status updated to FALSE_POSITIVE.")
    else:
        print("FAIL: Violation status not updated.")
        
    if new_score > initial_score:
        print("PASS: Risk score improved (higher is better/safer).")
    else:
        print("WARNING: Risk score did not improve. (Check scoring weights)")

    # 3. Diff Review (Scoped Analysis)
    print("\n[3] Testing Diff Review...")
    
    original_code = """
def main():
    print("Hello World")
    # Existing violation (unchanged)
    secret = "A_very_long_secret_string_that_is_bad_123"
"""
    
    modified_code = """
def main():
    print("Hello World")
    # Existing violation (unchanged)
    secret = "A_very_long_secret_string_that_is_bad_123"
    
    # New violation (added)
    new_secret = "Another_very_long_secret_that_is_added_now"
"""
    
    res = requests.post(f"{BASE_URL}/review/diff", json={
        "original_code": original_code,
        "modified_code": modified_code,
        "policies": policies
    }, headers=headers)
    
    if res.status_code != 200:
        print(f"FAIL: Diff review failed: {res.text}")
        return
        
    data = res.json()
    diff_violations = data["violations"]
    
    print(f"Diff Violations Found: {len(diff_violations)}")
    for v in diff_violations:
        print(f" - Line {v['line']}: {v['message']}")
        
    # Logic check: Should only catch 'new_secret' (approx line 8), NOT 'old_secret' (approx line 5)
    # Note: Line numbers depend on how backend counts.
    
    # If we get 1 violation, success. If 2, failed scoping.
    if len(diff_violations) == 1:
        print("PASS: Diff review correctly scoped to changed lines.")
    elif len(diff_violations) == 0:
        print("FAIL: Diff review missed the new violation.")
    else:
        print("FAIL: Diff review included unchanged lines (noise).")

    print("\n=== VERIFICATION COMPLETE ===")

if __name__ == "__main__":
    try:
        run_test()
    except requests.exceptions.ConnectionError:
        print("FAIL: Could not connect to server. Is it running?")
