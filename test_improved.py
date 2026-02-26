"""
Test script to verify all components of the updated error detection tool
"""
from error_detector import AIPoweredErrorDetector

def test_improved_functionality():
    print("Testing Improved Error Detection Tool")
    print("="*50)

    # Initialize detector
    detector = AIPoweredErrorDetector()

    # Test code with multiple types of errors
    test_code = """
def risky_function(user_input):
    # Undefined variable usage
    result = eval(user_input)  # Security risk

    # Another undefined variable
    another_var = undefined_var + 10

    # Proper variable definition
    safe_var = 42

    # None comparison issue
    if safe_var == None:  # Should use 'is' instead of '=='
        print("Checking None incorrectly")

    # Hardcoded password
    password = "secret123"  # Security issue

    return result / 0  # Division by zero
    """

    print("Analyzing complex test code...")
    report = detector.detect_errors(test_code, "complex_test.py")

    print(f"Detection completed!")
    print(f"Summary: {report['summary']}")
    print(f"Total errors found: {report['total_errors']}")

    print("\nDetailed errors:")
    for error in report['detailed_errors']:
        print(f"  - [{error['severity']}] {error['type']}: {error['message']}")
        if error['location'] and error['location']['line'] > 0:
            print(f"    Line: {error['location']['line']}")
        if error['code_snippet']:
            print(f"    Code: {error['code_snippet']}")
        print()

    print(f"Error types detected: {len(set(e['type'] for e in report['detailed_errors']))}")
    print(f"Error categories: {list(report['errors_by_category'].keys())}")

if __name__ == "__main__":
    test_improved_functionality()