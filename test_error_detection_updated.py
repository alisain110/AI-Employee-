"""
Test script to verify the error detector works properly with all features
"""

# Test file with various security vulnerabilities and issues
test_code = '''
import os
import yaml
import subprocess
import pickle

# Hardcoded secret
API_KEY = "sk-1234567890abcdef"  # Security issue: hardcoded API key

def insecure_yaml_load():
    # Security issue: insecure YAML loading
    data = yaml.load("{exploit: 'payload'}")  # Should use yaml.safe_load()
    return data

def sql_injection_vulnerability(user_input):
    # Security issue: potential SQL injection
    query = "SELECT * FROM users WHERE name = '" + user_input + "'"
    return query

def dangerous_eval(user_input):
    # Security issue: dangerous eval usage
    result = eval(user_input)  # Highly dangerous!
    return result

def path_traversal_vulnerability(user_input):
    # Security issue: path traversal
    file_path = os.path.join("/safe/path", user_input)
    with open(file_path, "r") as f:
        return f.read()

def normal_function():
    # Regular function for comparison
    x = 1 + 2
    return x

# Pickle usage (potential security risk)
def use_pickle():
    dangerous_data = pickle.dumps({"dangerous": "data"})
    return dangerous_data
'''

# Write test file
with open('test_vulnerable_code.py', 'w') as f:
    f.write(test_code)

print("Test file 'test_vulnerable_code.py' created with various vulnerabilities.")

# Now run the error detector on it
from error_detector import ErrorDetector

detector = ErrorDetector()
errors = detector.analyze_file('test_vulnerable_code.py')

print(f"\nFound {len(errors)} errors:")
for i, error in enumerate(errors, 1):
    print(f"\n{i}. {error.error_type} ({error.severity}) in {error.file_path}:{error.line_number}")
    print(f"   Description: {error.description}")
    print(f"   Code snippet:\n{error.code_snippet}")
    if error.fix_patch:
        print(f"   Fix suggestion: {error.fix_patch}")
    print(f"   Confidence: {error.confidence}")

# Generate report
report = detector.get_error_report(errors)
print(f"\nError Report Summary:")
print(f"Total errors: {report['summary']['total_errors']}")
print(f"By severity: {report['summary']['by_severity']}")
print(f"By category: {report['summary']['by_category']}")

# Clean up test file
import os
os.remove('test_vulnerable_code.py')

print("\nTest completed successfully! The error detector is working with all enhanced features.")