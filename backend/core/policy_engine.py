import json
import os
from typing import List, Dict

class PolicyEngine:
    def __init__(self, rules_path: str = "backend/policies/rules.json"):
        self.rules_path = rules_path
        self._last_mtime = 0
        self.policies = self._load_policies()

    def _load_policies(self) -> List[Dict]:
        try:
            # Adjust path if running from root
            if not os.path.exists(self.rules_path):
                # Fallback for different CWD
                if os.path.exists("policies/rules.json"):
                    self.rules_path = "policies/rules.json"
                else:
                    return []
            
            # Check modification time
            mtime = os.path.getmtime(self.rules_path)
            self._last_mtime = mtime
            
            with open(self.rules_path, 'r') as f:
                print(f"Loading policies from {self.rules_path}...")
                return json.load(f)
        except Exception as e:
            print(f"Error loading policies: {e}")
            return []

    def _check_reload(self):
        if os.path.exists(self.rules_path):
            current_mtime = os.path.getmtime(self.rules_path)
            if current_mtime > self._last_mtime:
                print("Policy file changed. Reloading...")
                self.policies = self._load_policies()

    def get_policies(self, policy_ids: List[str]) -> List[Dict]:
        """Filter policies by ID"""
        self._check_reload()
        return [p for p in self.policies if p['id'] in policy_ids]
