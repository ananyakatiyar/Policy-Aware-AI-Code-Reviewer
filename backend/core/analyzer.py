import ast
import re
import hashlib
from typing import List, Dict
from backend.models.schemas import Violation

def generate_violation_id(rule_id: str, line: int, message: str) -> str:
    unique_str = f"{rule_id}:{line}:{message}"
    return hashlib.md5(unique_str.encode()).hexdigest()

class StaticAnalyzer:
    def analyze(self, code: str, policies: List[Dict]) -> List[Violation]:
        violations = []
        lines = code.split('\n')
        
        # 1. Regex Checks
        for policy in policies:
            if policy.get('type') == 'regex':
                pattern = policy.get('pattern')
                for i, line in enumerate(lines):
                    if re.search(pattern, line):
                        # Skip if it's a comment (simple check)
                        if line.strip().startswith('#'):
                            continue
                        
                        v_message = policy['description'] + " detected"
                        v_rule_id = policy['id']
                        v_line = i + 1
                        
                        violations.append(Violation(
                            id=generate_violation_id(v_rule_id, v_line, v_message),
                            line=v_line,
                            severity=policy['severity'],
                            message=v_message,
                            rule_id=v_rule_id,
                            risk_explanation=policy.get('risk_explanation'),
                            exploit_scenario=policy.get('exploit_scenario'),
                            fix_recommendation=policy.get('fix_recommendation'),
                            secure_code_example=policy.get('secure_code_example')
                        ))

        # 2. AST Checks
        try:
            tree = ast.parse(code)
            ast_analyzer = ASTAnalyzer(policies, violations)
            ast_analyzer.visit(tree)
        except SyntaxError:
            # If code is invalid, we can't run AST checks, but that's okay
            pass
            
        return violations

class ASTAnalyzer(ast.NodeVisitor):
    def __init__(self, policies: List[Dict], violations: List[Violation]):
        self.policies = policies
        self.violations = violations
        self.loop_depth = 0

    def visit_For(self, node):
        self._check_loop(node)
        
    def visit_While(self, node):
        self._check_loop(node)

    def _check_loop(self, node):
        self.loop_depth += 1
        
        # Check nested loops policy
        nested_policy = next((p for p in self.policies if p['id'] == 'nested_loops'), None)
        if nested_policy:
            max_depth = nested_policy.get('max_depth', 3)
            if self.loop_depth > max_depth:
                v_message = "Deeply nested loops detected"
                v_rule_id = 'nested_loops'
                v_line = node.lineno
                
                self.violations.append(Violation(
                    id=generate_violation_id(v_rule_id, v_line, v_message),
                    line=v_line,
                    severity=nested_policy['severity'],
                    message=v_message,
                    rule_id=v_rule_id,
                    risk_explanation=nested_policy.get('risk_explanation'),
                    exploit_scenario=nested_policy.get('exploit_scenario'),
                    fix_recommendation=nested_policy.get('fix_recommendation'),
                    secure_code_example=nested_policy.get('secure_code_example')
                ))
        
        self.generic_visit(node)
        self.loop_depth -= 1

    def visit_ExceptHandler(self, node):
        # Check empty except
        error_policy = next((p for p in self.policies if p['id'] == 'error_handling'), None)
        if error_policy and error_policy.get('check') == 'empty_except':
            # Check if body is just 'pass' or '...'
            if len(node.body) == 1 and isinstance(node.body[0], ast.Pass):
                v_message = "Empty except block detected"
                v_rule_id = 'error_handling'
                v_line = node.lineno
                
                self.violations.append(Violation(
                    id=generate_violation_id(v_rule_id, v_line, v_message),
                    line=v_line,
                    severity=error_policy['severity'],
                    message=v_message,
                    rule_id=v_rule_id,
                    risk_explanation=error_policy.get('risk_explanation'),
                    exploit_scenario=error_policy.get('exploit_scenario'),
                    fix_recommendation=error_policy.get('fix_recommendation'),
                    secure_code_example=error_policy.get('secure_code_example')
                ))
        self.generic_visit(node)
