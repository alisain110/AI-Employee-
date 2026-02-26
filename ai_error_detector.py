def main():
    """Main function to demonstrate the AI-powered error detection tool"""
    print("=" * 60)
    print("AI-POWERED ERROR DETECTION TOOL")
    print("=" * 60)
    print("Detects errors in code using AI analysis and pattern matching")
    print("Provides natural language explanations and fix suggestions")
    print("=" * 60)

    # Initialize the detector
    detector = AIPoweredErrorDetector()

    # Example 1: Detect errors in problematic code
    print("\n[FILE] EXAMPLE 1: Analyzing problematic code...")
    problematic_code = '''
def process_user_data(data):
    # Security issue: executing user input
    result = eval(data['input'])

    # Potential division by zero
    value = data['value'] / data['divisor']

    # Resource leak: opening file without context manager
    f = open('temp_file.txt', 'w')
    f.write(str(result))
    # File never closed!

    return value

# Anti-pattern: import inside function
import sys
sys.path.append('/dangerous/path')

# TODO: Add input validation
    '''

    start_time = time.time()
    report = detector.detect_errors(problematic_code, "problematic_code.py")
    end_time = time.time()

    print(f"\n[⏱️] Analysis completed in {end_time - start_time:.2f} seconds")
    print(f"[📊] Summary: {report['summary']}")

    if report['total_errors'] > 0:
        print("\n[🔍] DETECTED ERRORS:")
        for i, error in enumerate(report['detailed_errors'], 1):
            severity_marker = {
                "critical": "[CRITICAL]",
                "high": "[HIGH]",
                "medium": "[MEDIUM]",
                "low": "[LOW]",
                "info": "[INFO]"
            }.get(error['severity'], "[UNKNOWN]")

            print(f"  {i}. {severity_marker} [{error['severity'].upper()}] {error['type']}")
            print(f"     Message: {error['message']}")
            if error['location'] and error['location']['line'] > 0:
                print(f"     Line: {error['location']['line']}")
            if error['code_snippet']:
                print(f"     Code: {error['code_snippet']}")
            print()
    else:
        print("✅ No errors found!")

    # Example 2: Detect errors in clean code
    print("\n[FILE] EXAMPLE 2: Analyzing clean code...")
    clean_code = '''
def process_user_data_safely(data):
    """
    Safely process user data with proper validation
    """
    # Validate input
    if not isinstance(data, dict):
        raise ValueError("Data must be a dictionary")

    # Safe division with check
    divisor = data.get('divisor', 1)
    if divisor == 0:
        raise ValueError("Division by zero is not allowed")

    value = data['value'] / divisor

    # Safe file handling with context manager
    with open('safe_file.txt', 'w') as f:
        f.write(str(value))

    return value

def validate_input(user_input: str) -> bool:
    """
    Validate user input safely
    """
    # Perform validation without eval()
    return isinstance(user_input, str) and len(user_input) > 0
    '''

    start_time = time.time()
    clean_report = detector.detect_errors(clean_code, "clean_code.py")
    end_time = time.time()

    print(f"\n[⏱️] Analysis completed in {end_time - start_time:.2f} seconds")
    print(f"[📊] Summary: {clean_report['summary']}")

    if clean_report['total_errors'] > 0:
        print(f"\n[🔍] Found {clean_report['total_errors']} potential issues:")
        for i, error in enumerate(clean_report['detailed_errors'], 1):
            print(f"  {i}. [{error['severity'].upper()}] {error['message']}")
            if error['location'] and error['location']['line'] > 0:
                print(f"     Line: {error['location']['line']}")
            if error['code_snippet']:
                print(f"     Code: {error['code_snippet']}")
    else:
        print("✅ No errors found! Code looks good.")

    # Example 3: Interactive mode
    print("\n" + "="*60)
    print("[🎯] INTERACTIVE MODE")
    print("="*60)
    print("Enter your own code to analyze (type 'quit' to exit):")

    while True:
        print("\nEnter code (or 'quit' to exit):")
        user_input = input("> ")

        if user_input.lower() == 'quit':
            break

        if not user_input.strip():
            continue

        # Handle multi-line input
        if user_input.endswith('\\'):
            print("Enter more lines (end with an empty line):")
            lines = [user_input[:-1]]  # Remove backslash
            while True:
                line = input("... ")
                if not line.strip():
                    break
                lines.append(line)
            user_input = '\n'.join(lines)

        print(f"\n[🔍] Analyzing your code...")
        start_time = time.time()
        user_report = detector.detect_errors(user_input, "user_code.py")
        end_time = time.time()

        print(f"\n[⏱️] Analysis completed in {end_time - start_time:.2f} seconds")
        print(f"[📊] Summary: {user_report['summary']}")

        if user_report['total_errors'] > 0:
            print(f"\n[🔍] Found {user_report['total_errors']} issues:")
            for i, error in enumerate(user_report['detailed_errors'], 1):
                severity_marker = {
                    "critical": "[CRITICAL]",
                    "high": "[HIGH]",
                    "medium": "[MEDIUM]",
                    "low": "[LOW]",
                    "info": "[INFO]"
                }.get(error['severity'], "[UNKNOWN]")

                print(f"  {i}. {severity_marker} [{error['severity'].upper()}] {error['type']}")
                print(f"     Message: {error['message']}")
                if error['location'] and error['location']['line'] > 0:
                    print(f"     Line: {error['location']['line']}")
                if error['code_snippet']:
                    print(f"     Code: {error['code_snippet']}")
                if error['suggestion']:
                    print(f"     Suggestion: {error['suggestion']}")
                print()
        else:
            print("✅ No errors found! Your code looks good.")

    print("\n👋 Thank you for using the AI-Powered Error Detection Tool!")
    print("This tool can find and explain code errors within seconds! 🚀")