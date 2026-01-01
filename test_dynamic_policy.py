import requests
import json
import time
import os

BASE_URL = "http://127.0.0.1:8000"
RULES_PATH = "backend/policies/rules.json"

def test_dynamic_policy():
    print("Testing Dynamic Policy Loading...")
    
    # 1. Read original rules
    with open(RULES_PATH, 'r') as f:
        original_rules = json.load(f)
    
    # 2. Modify 'no_secrets' severity to LOW
    print("Modifying 'no_secrets' severity to LOW...")
    modified_rules = json.loads(json.dumps(original_rules)) # Deep copy
    for rule in modified_rules:
        if rule['id'] == 'no_secrets':
            rule['severity'] = "LOW"
            
    with open(RULES_PATH, 'w') as f:
        json.dump(modified_rules, f, indent=4)
        
    # Wait a bit for file system event (though my code checks on request)
    time.sleep(1)
    
    # 3. Trigger Review
    # Need auth
    # Assuming previous test created the user
    email = "test_xai@example.com"
    password = "password123"
    
    try:
        requests.post(f"{BASE_URL}/auth/register", json={"email": email, "password": password, "name": "Test"})
    except:
        pass
        
    resp = requests.post(f"{BASE_URL}/auth/login", json={"email": email, "password": password})
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    code = """
def main():
    api_key = "1234567890123456789012345"
"""
    
    print("Requesting review...")
    resp = requests.post(f"{BASE_URL}/review", json={"code": code, "policies": ["no_secrets"]}, headers=headers)
    data = resp.json()
    
    violation = data["violations"][0]
    print(f"Violation Severity: {violation['severity']}")
    
    if violation['severity'] == "LOW":
        print("SUCCESS: Policy updated dynamically.")
    else:
        print(f"FAIL: Expected LOW, got {violation['severity']}")
        
    # 4. Revert
    print("Reverting rules...")
    with open(RULES_PATH, 'w') as f:
        json.dump(original_rules, f, indent=4)

if __name__ == "__main__":
    try:
        test_dynamic_policy()
    except Exception as e:
        print(f"Error: {e}")
        # Try to revert anyway
        with open(RULES_PATH, 'r') as f:
            # If we failed before writing, original_rules might not be defined
            pass 
