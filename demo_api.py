"""
Demo script for the AI Error Detection API
"""
import json
from error_detector import AIPoweredErrorDetector


def demo_api_equivalent():
    """Demonstrate the API functionality without actually starting a server"""
    print("AI Error Detection API Demo")
    print("="*40)

    # Create detector instance
    detector = AIPoweredErrorDetector()

    # Sample code to analyze
    sample_code = '''
def calculate_average(numbers):
    # This has a potential division by zero error
    total = sum(numbers)
    count = len(numbers)
    return total / count  # Potential division by zero if numbers is empty

def unsafe_eval(user_input):
    # This is a security risk
    return eval(user_input)

# TODO: Add proper error handling here
    '''

    print("Code to analyze:")
    print(sample_code)
    print()

    # Simulate API call
    print("[DETECTING] Detecting errors...")
    report = detector.detect_errors(sample_code, "sample.py")

    # Format as API response
    response = {
        "filename": report["filename"],
        "total_errors": report["total_errors"],
        "errors_by_severity": report["errors_by_severity"],
        "errors_by_category": report["errors_by_category"],
        "detailed_errors": report["detailed_errors"],
        "summary": report["summary"]
    }

    print("[SUCCESS] API Response:")
    print(json.dumps(response, indent=2))

    print(f"\n[SUMMARY] Summary: {response['summary']}")
    print(f"   Total errors: {response['total_errors']}")
    print(f"   By severity: {response['errors_by_severity']}")
    print(f"   By category: {response['errors_by_category']}")


def demo_api_start():
    """Show how to start the actual API server"""
    print("\nAPI Server Demo")
    print("="*40)
    print("To start the API server, run:")
    print("  uvicorn api.error_detection:app --host 0.0.0.0 --port 8005")
    print()
    print("API endpoints available:")
    print("  POST /detect_errors  - Detect errors in provided code")
    print("  POST /explain_error  - Explain a specific error")
    print("  POST /suggest_fix    - Suggest fixes for errors")
    print("  GET  /health         - Health check")


if __name__ == "__main__":
    demo_api_equivalent()
    demo_api_start()

    print("\nAPI Demo completed!")
    print("The AI Error Detection API is ready to use!")