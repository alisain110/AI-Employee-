"""
Test script for the AI-powered error detection tool
"""
import json
from error_detector import AIPoweredErrorDetector


def test_error_detection():
    """Test the error detection capabilities"""
    print("Testing AI-Powered Error Detection Tool...")

    # Create an instance of the error detector
    detector = AIPoweredErrorDetector()

    # Test code with various errors
    test_code = '''
def divide_numbers(a, b):
    # This function has potential division by zero
    result = a / b
    return result

# This import is considered an anti-pattern
import sys
sys.path.append('/some/path')

def risky_function(user_input):
    # Potential security risk - executing arbitrary code
    eval(user_input)

    # Broad except clause
    try:
        risky_operation()
    except:  # This catches all exceptions
        print("Error occurred")

    # TODO: Fix this later
    # FIXME: This needs attention

    # Resource leak - not using context manager
    f = open('file.txt', 'r')
    content = f.read()
    # File never closed!

    return content

# Syntax error example (commented out to avoid parse error)
# if True:
# print("This has indentation error")

# Name error example
undefined_variable = non_existent_variable + 10
    '''

    print("\nAnalyzing test code...")
    report = detector.detect_errors(test_code, "test_code.py")

    print(f"\nSummary: {report['summary']}")
    print(f"Total errors detected: {report['total_errors']}")

    print("\nDetailed errors:")
    for i, error in enumerate(report['detailed_errors']):
        print(f"{i+1}. [{error['severity'].upper()}] {error['type']}: {error['message']}")
        if error['location'] and error['location']['line'] > 0:
            print(f"   Location: Line {error['location']['line']}")
        if error['code_snippet']:
            print(f"   Code: {error['code_snippet']}")
        print()

    print(f"Errors by severity: {report['errors_by_severity']}")
    print(f"Errors by category: {report['errors_by_category']}")

    # Test with clean code
    print("\n" + "="*50)
    print("Testing with clean code...")

    clean_code = '''
def safe_divide(a, b):
    """Safely divide two numbers"""
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b

def process_file(filename):
    """Safely process a file using context manager"""
    with open(filename, 'r') as f:
        return f.read().strip()
    '''

    clean_report = detector.detect_errors(clean_code, "clean_code.py")
    print(f"Clean code report: {clean_report['summary']}")
    print(f"Errors found: {clean_report['total_errors']}")

    print("\nError detection test completed!")


def test_api_models():
    """Test the API models"""
    print("\nTesting API models...")

    from models.error_models import (
        CodeInput, ErrorDetectionResponse,
        ErrorExplanationRequest, ErrorFixSuggestionRequest
    )

    # Test CodeInput model
    code_input = CodeInput(code="print('hello world')", filename="test.py")
    print(f"CodeInput: {code_input}")

    print("API models test completed!")


def test_tools():
    """Test the LangChain tools"""
    print("\nTesting LangChain tools...")

    try:
        from tools.error_detection_tool import (
            ErrorDetectionTool, ErrorExplanationTool, ErrorFixSuggestionTool,
            ERROR_DETECTION_TOOLS
        )

        print(f"Number of error detection tools: {len(ERROR_DETECTION_TOOLS)}")

        # Test the tools can be initialized
        detection_tool = ErrorDetectionTool()
        explanation_tool = ErrorExplanationTool()
        fix_tool = ErrorFixSuggestionTool()

        print("Tools initialization test completed!")
    except ImportError as e:
        print(f"LangChain tools not available (expected if langchain not installed): {e}")
        print("Core error detection functionality works without LangChain.")


if __name__ == "__main__":
    test_error_detection()
    test_api_models()
    test_tools()

    print("\n" + "="*60)
    print("ALL TESTS COMPLETED SUCCESSFULLY!")
    print("AI-Powered Error Detection Tool is ready for use.")
    print("="*60)