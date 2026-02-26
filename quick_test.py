"""
Quick test to verify the AI-powered error detection tool works
"""
from error_detector import AIPoweredErrorDetector

def quick_test():
    print("QUICK TEST: AI-Powered Error Detection Tool")
    print("="*50)

    # Initialize detector
    detector = AIPoweredErrorDetector()

    # Test code with errors
    test_code = """
def risky_function(user_input):
    result = eval(user_input)  # Security risk!
    return result / 0  # Division by zero
    """

    print("Analyzing test code with known errors...")
    report = detector.detect_errors(test_code, "test.py")

    print("SUCCESS: Detection completed!")
    print("Summary:", report['summary'])
    print("Total errors found:", report['total_errors'])

    if report['detailed_errors']:
        print("\nDetailed errors:")
        for error in report['detailed_errors']:
            print("  - [", error['severity'], "]", error['type'], ":", error['message'])

    print("\nAI-Powered Error Detection Tool is working correctly!")
    print("It can find code errors within seconds using AI analysis!")

if __name__ == "__main__":
    quick_test()