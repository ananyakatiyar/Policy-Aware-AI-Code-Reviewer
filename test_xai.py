import requests
import time

BASE_URL = "http://127.0.0.1:8000"

def test_xai():
    print("Testing Explainable AI fields...")
    
    # Code with a secret to trigger 'no_secrets' policy
    code = """
def main():
    api_key = "1234567890123456789012345"
    print("Hello")
"""
    
    email = "test_xai@example.com"
    password = "password123"
    name = "Test User"
    
    # 1. Register (ignore if exists)
    try:
        requests.post(f"{BASE_URL}/auth/register", json={
            "email": email, 
            "password": password,
            "name": name
        })
    except:
        pass

    # 2. Login
    print(f"Logging in as {email}...")
    response = requests.post(f"{BASE_URL}/auth/login", json={"email": email, "password": password})
    
    if response.status_code != 200:
        print(f"Login failed: {response.text}")
        return
    
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("Login successful.")
    
    # 3. Call /review
    print("Submitting code for review...")
    payload = {
        "code": code,
        "policies": ["no_secrets"]
    }
    
    response = requests.post(f"{BASE_URL}/review", json=payload, headers=headers)
    if response.status_code != 200:
        print(f"Review failed: {response.text}")
        return
    
    data = response.json()
    violations = data["violations"]
    
    if not violations:
        print("No violations found. Expected 'no_secrets' violation.")
        return
    
    v = violations[0]
    print(f"\nViolation: {v['message']}")
    print(f"Risk Explanation: {v.get('risk_explanation')}")
    print(f"Exploit Scenario: {v.get('exploit_scenario')}")
    print(f"Fix Recommendation: {v.get('fix_recommendation')}")
    print(f"Secure Code Example: {v.get('secure_code_example')}")
    
    if v.get('risk_explanation') and v.get('exploit_scenario'):
        print("\nSUCCESS: XAI fields are present.")
    else:
        print("\nFAIL: XAI fields are missing.")

if __name__ == "__main__":
    try:
        test_xai()
    except requests.exceptions.ConnectionError:
        print("Server is not running.")
