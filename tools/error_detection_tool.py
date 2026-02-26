"""
LangChain tool for AI-powered error detection
"""
from typing import Optional
from langchain.tools import BaseTool
from pydantic import Field
import json

from error_detector import AIPoweredErrorDetector
from audit_logger import get_audit_logger, AuditLogEntry, AuditActor, AuditAction


class ErrorDetectionTool(BaseTool):
    """A LangChain tool that uses AI to detect errors in code."""

    name = "ai_error_detector"
    description = "Detects errors in code using AI-powered analysis. Input should be a JSON string with 'code' and optional 'filename' fields."

    # Initialize the error detector
    detector: AIPoweredErrorDetector = Field(default_factory=AIPoweredErrorDetector)

    def _run(self, query: str) -> str:
        """
        Detect errors in the provided code.

        Args:
            query: A JSON string containing 'code' and optional 'filename' fields

        Returns:
            A JSON string with the error detection results
        """
        try:
            # Parse the input query
            if isinstance(query, str):
                try:
                    query_dict = json.loads(query)
                except json.JSONDecodeError:
                    # If it's not JSON, assume it's just the code
                    query_dict = {"code": query, "filename": "unknown"}
            else:
                query_dict = query

            code = query_dict.get("code", "")
            filename = query_dict.get("filename", "unknown")

            if not code:
                return json.dumps({
                    "error": "No code provided for error detection",
                    "success": False
                })

            # Log the tool usage
            audit_logger = get_audit_logger()
            audit_logger.log_error_detection(
                filename=filename,
                total_errors=0,  # We don't know yet
                processing_time=0,  # We don't know yet
                success=True,
                session_id=None
            )

            # Perform error detection
            report = self.detector.detect_errors(code, filename)

            # Log successful detection
            audit_logger.log_error_detection(
                filename=filename,
                total_errors=report.get("total_errors", 0),
                processing_time=0,  # In a real implementation, we'd track this
                success=True,
                session_id=None
            )

            return json.dumps(report, indent=2)

        except Exception as e:
            # Log the error
            audit_logger.log_error_detection(
                filename=filename if 'filename' in locals() else "unknown",
                total_errors=0,
                processing_time=0,
                success=False,
                error=str(e),
                session_id=None
            )

            return json.dumps({
                "error": f"Error in error detection: {str(e)}",
                "success": False
            })

    async def _arun(self, query: str) -> str:
        """Async version of the error detection tool."""
        # For now, just call the sync version
        return self._run(query)


class ErrorExplanationTool(BaseTool):
    """A LangChain tool that explains detected errors."""

    name = "error_explanation_tool"
    description = "Provides detailed explanations for specific errors. Input should be a JSON string with 'error_type' and 'error_message' fields."

    def _run(self, query: str) -> str:
        """
        Provide an explanation for a specific error.

        Args:
            query: A JSON string containing 'error_type' and 'error_message' fields

        Returns:
            A JSON string with the error explanation
        """
        try:
            if isinstance(query, str):
                query_dict = json.loads(query)
            else:
                query_dict = query

            error_type = query_dict.get("error_type", "unknown")
            error_message = query_dict.get("error_message", "")
            code_context = query_dict.get("code_context", "")

            # Log the tool usage
            audit_logger = get_audit_logger()
            audit_logger.log_error_explanation(
                error_type=error_type,
                error_message=error_message,
                explanation_provided=False,  # We haven't provided it yet
                success=True,
                session_id=None
            )

            # Generate explanation based on error type
            explanation = self._generate_error_explanation(error_type, error_message, code_context)

            # Log successful explanation
            audit_logger.log_error_explanation(
                error_type=error_type,
                error_message=error_message,
                explanation_provided=True,
                success=True,
                session_id=None
            )

            return json.dumps(explanation, indent=2)

        except Exception as e:
            # Log the error
            audit_logger.log_error_explanation(
                error_type="unknown",
                error_message="",
                explanation_provided=False,
                success=False,
                error=str(e),
                session_id=None
            )

            return json.dumps({
                "error": f"Error in error explanation: {str(e)}",
                "success": False
            })

    def _generate_error_explanation(self, error_type: str, error_message: str, code_context: str = "") -> dict:
        """
        Generate an explanation for a specific error.
        This is a simplified function - in a real system, this would use AI.
        """
        explanations = {
            "SyntaxError": {
                "explanation": "A syntax error occurs when the code violates the rules of the programming language. This could be due to missing parentheses, incorrect indentation, or other structural issues.",
                "suggested_fix": "Carefully check the syntax around the error location. Verify that all parentheses, brackets, and braces are properly matched.",
                "related_info": ["Check indentation", "Verify proper use of colons", "Ensure proper statement termination"]
            },
            "NameError": {
                "explanation": "A NameError occurs when Python encounters a variable or function name that hasn't been defined yet in the current scope.",
                "suggested_fix": "Verify that the variable or function is defined before it's used. Check for typos in the variable name.",
                "related_info": ["Check variable scope", "Verify variable is defined", "Look for typos"]
            },
            "TypeError": {
                "explanation": "A TypeError occurs when an operation or function is applied to an object of inappropriate type.",
                "suggested_fix": "Convert the object to the correct type before performing the operation, or check that the correct types are being used.",
                "related_info": ["Check data types", "Use type conversion", "Verify function arguments"]
            },
            "AttributeError": {
                "explanation": "An AttributeError occurs when trying to access an attribute or method that doesn't exist on an object.",
                "suggested_fix": "Check if the attribute or method name is correct, or verify that the object is of the expected type.",
                "related_info": ["Verify attribute name", "Check object type", "Inspect available methods"]
            },
            "ImportError": {
                "explanation": "An ImportError occurs when Python cannot find or import a module.",
                "suggested_fix": "Make sure the module is installed and in the Python path, or check if the import statement is correct.",
                "related_info": ["Check module installation", "Verify import path", "Check module availability"]
            },
            "IndentationError": {
                "explanation": "An IndentationError occurs when Python's indentation rules are violated. Python uses indentation to define code blocks.",
                "suggested_fix": "Review the indentation of the code. Make sure to use consistent indentation (preferably 4 spaces) throughout.",
                "related_info": ["Use consistent indentation", "Avoid mixing spaces and tabs", "Check code block structure"]
            },
            "IndexError": {
                "explanation": "An IndexError occurs when trying to access an index that is outside the bounds of a sequence.",
                "suggested_fix": "Check the length of the sequence before accessing an index, or use proper bounds checking.",
                "related_info": ["Verify sequence length", "Use bounds checking", "Check loop conditions"]
            },
            "KeyError": {
                "explanation": "A KeyError occurs when trying to access a dictionary key that doesn't exist.",
                "suggested_fix": "Check if the key exists in the dictionary before accessing it, or use the get() method with a default value.",
                "related_info": ["Use dict.get() method", "Check key existence", "Handle missing keys gracefully"]
            },
            "ValueError": {
                "explanation": "A ValueError occurs when a function receives an argument of the correct type but with an inappropriate value.",
                "suggested_fix": "Verify the values being passed to the function, and ensure they are within the expected range.",
                "related_info": ["Check function arguments", "Validate input values", "Review function documentation"]
            }
        }

        # Default explanation if specific error type not found
        default_explanation = {
            "explanation": f"The error '{error_type}' with message '{error_message}' indicates an issue in your code.",
            "suggested_fix": "Review the error message and the code at the specified location to identify the problem.",
            "related_info": ["Check error message", "Review code context", "Verify input values"]
        }

        # Return explanation for the specific error type or default
        return explanations.get(error_type, default_explanation)

    async def _arun(self, query: str) -> str:
        """Async version of the error explanation tool."""
        # For now, just call the sync version
        return self._run(query)


class ErrorFixSuggestionTool(BaseTool):
    """A LangChain tool that suggests fixes for detected errors."""

    name = "error_fix_suggestion_tool"
    description = "Suggests fixes for specific code errors. Input should be a JSON string with 'error_type', 'error_message', and 'problematic_code' fields."

    def _run(self, query: str) -> str:
        """
        Suggest a fix for a specific error.

        Args:
            query: A JSON string containing 'error_type', 'error_message', and 'problematic_code' fields

        Returns:
            A JSON string with the fix suggestion
        """
        try:
            if isinstance(query, str):
                query_dict = json.loads(query)
            else:
                query_dict = query

            error_type = query_dict.get("error_type", "unknown")
            error_message = query_dict.get("error_message", "")
            problematic_code = query_dict.get("problematic_code", "")
            line_number = query_dict.get("line_number", None)

            # Log the tool usage
            audit_logger = get_audit_logger()
            audit_logger.log_error_fix_suggestion(
                error_type=error_type,
                error_message=error_message,
                fix_suggested=False,  # We haven't provided it yet
                success=True,
                session_id=None
            )

            # Generate fix suggestion based on error type
            suggestion = self._generate_fix_suggestion(error_type, error_message, problematic_code, line_number)

            # Log successful suggestion
            audit_logger.log_error_fix_suggestion(
                error_type=error_type,
                error_message=error_message,
                fix_suggested=True,
                success=True,
                session_id=None
            )

            return json.dumps(suggestion, indent=2)

        except Exception as e:
            # Log the error
            audit_logger.log_error_fix_suggestion(
                error_type="unknown",
                error_message="",
                fix_suggested=False,
                success=False,
                error=str(e),
                session_id=None
            )

            return json.dumps({
                "error": f"Error in fix suggestion: {str(e)}",
                "success": False
            })

    def _generate_fix_suggestion(
        self,
        error_type: str,
        error_message: str,
        problematic_code: str,
        line_number: Optional[int] = None
    ) -> dict:
        """
        Generate a fix suggestion for a specific error.
        This is a simplified function - in a real system, this would use AI.
        """
        suggestions = {
            "SyntaxError": {
                "suggested_fix": "Check the syntax around the error location. Ensure all parentheses, brackets, and braces are properly matched. Verify proper indentation and statement termination.",
                "explanation": "Syntax errors prevent the code from being parsed correctly and must be fixed before the code can run.",
                "alternative_approaches": [
                    "Use a code editor with syntax highlighting",
                    "Run the code through a linter",
                    "Compare with working code examples"
                ]
            },
            "NameError": {
                "suggested_fix": "Define the variable or function before using it. Check for typos in the variable name. If in a function, ensure it's in the correct scope.",
                "explanation": "Python cannot find the variable or function name used in the code.",
                "alternative_approaches": [
                    "Define the variable before using it",
                    "Import the required module or function",
                    "Check variable scope and spelling"
                ]
            },
            "TypeError": {
                "suggested_fix": "Convert the value to the expected type before using it, or change the operation to work with the current type.",
                "explanation": "The operation is not supported for the given data types.",
                "alternative_approaches": [
                    "Use type conversion (int(), str(), etc.)",
                    "Check function parameter types",
                    "Use isinstance() for type checking"
                ]
            },
            "AttributeError": {
                "suggested_fix": "Verify that the object has the attribute or method you're trying to access. Check the documentation for the correct method name.",
                "explanation": "The object doesn't have the requested attribute or method.",
                "alternative_approaches": [
                    "Use dir() to see available attributes",
                    "Check object documentation",
                    "Verify object type before calling methods"
                ]
            },
            "ImportError": {
                "suggested_fix": "Install the required package using pip, or verify the module path is correct. Check if the package name is spelled correctly.",
                "explanation": "Python cannot find the module you're trying to import.",
                "alternative_approaches": [
                    "Install the package with pip install",
                    "Check PYTHONPATH",
                    "Verify module location and name"
                ]
            }
        }

        # Default suggestion if specific error type not found
        default_suggestion = {
            "suggested_fix": f"Review the error message: '{error_message}' and the problematic code to identify the issue. Consider reviewing documentation or examples of correct usage.",
            "explanation": "The error indicates a problem with the code that needs to be addressed before it can run properly.",
            "alternative_approaches": [
                "Check the official documentation",
                "Review similar working examples",
                "Use debugging tools to inspect variables",
                "Consult community resources"
            ]
        }

        # Return suggestion for the specific error type or default
        return suggestions.get(error_type, default_suggestion)

    async def _arun(self, query: str) -> str:
        """Async version of the error fix suggestion tool."""
        # For now, just call the sync version
        return self._run(query)


# Initialize the tools
error_detection_tool = ErrorDetectionTool()
error_explanation_tool = ErrorExplanationTool()
error_fix_suggestion_tool = ErrorFixSuggestionTool()

# List of all error detection tools for easy access
ERROR_DETECTION_TOOLS = [
    error_detection_tool,
    error_explanation_tool,
    error_fix_suggestion_tool
]