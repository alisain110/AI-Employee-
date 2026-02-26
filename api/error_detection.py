"""
API endpoints for AI-powered error detection
"""
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import asyncio

from error_detector import AIPoweredErrorDetector, DetectedError, ErrorSeverity
from audit_logger import get_audit_logger, AuditLogEntry, AuditActor, AuditAction


# Pydantic models for API requests and responses
class CodeInput(BaseModel):
    code: str
    filename: Optional[str] = "unknown"
    language: Optional[str] = "python"


class ErrorLocation(BaseModel):
    line: Optional[int] = None
    column: Optional[int] = None
    end_line: Optional[int] = None
    end_column: Optional[int] = None


class DetectedErrorModel(BaseModel):
    type: str
    message: str
    severity: str
    location: Optional[ErrorLocation] = None
    code_snippet: Optional[str] = None
    suggestion: Optional[str] = None
    category: str


class ErrorDetectionResponse(BaseModel):
    filename: str
    total_errors: int
    errors_by_severity: Dict[str, int]
    errors_by_category: Dict[str, int]
    detailed_errors: List[DetectedErrorModel]
    summary: str


class ErrorExplanationRequest(BaseModel):
    error_type: str
    error_message: str
    code_context: Optional[str] = None


class ErrorExplanationResponse(BaseModel):
    explanation: str
    suggested_fix: str
    related_info: List[str]


class ErrorFixSuggestionRequest(BaseModel):
    error_type: str
    error_message: str
    problematic_code: str
    line_number: Optional[int] = None


class ErrorFixSuggestionResponse(BaseModel):
    suggested_fix: str
    explanation: str
    alternative_approaches: List[str]


# Initialize the error detector
detector = AIPoweredErrorDetector()


# FastAPI app
app = FastAPI(title="AI-Powered Error Detection API", version="1.0.0")


@app.post("/detect_errors", response_model=ErrorDetectionResponse)
async def detect_errors(input_data: CodeInput):
    """
    Detect errors in provided code using AI-powered analysis
    """
    try:
        # Log the API call
        audit_logger = get_audit_logger()
        audit_logger.log_error_detection(
            filename=input_data.filename,
            total_errors=0,  # We don't know this yet
            processing_time=0,  # We don't know this yet
            success=True,
            session_id=None
        )

        # Perform error detection
        report = detector.detect_errors(input_data.code, input_data.filename)

        # Convert the internal error objects to API response models
        detailed_errors = []
        for error in report.get("detailed_errors", []):
            location = ErrorLocation(
                line=error.get("location", {}).get("line"),
                column=error.get("location", {}).get("column"),
                end_line=error.get("location", {}).get("end_line"),
                end_column=error.get("location", {}).get("end_column")
            ) if error.get("location") else None

            detailed_errors.append(DetectedErrorModel(
                type=error.get("type", ""),
                message=error.get("message", ""),
                severity=error.get("severity", "info"),
                location=location,
                code_snippet=error.get("code_snippet"),
                suggestion=error.get("suggestion"),
                category=error.get("category", "general")
            ))

        response = ErrorDetectionResponse(
            filename=report.get("filename", input_data.filename),
            total_errors=report.get("total_errors", 0),
            errors_by_severity=report.get("errors_by_severity", {}),
            errors_by_category=report.get("errors_by_category", {}),
            detailed_errors=detailed_errors,
            summary=report.get("summary", "")
        )

        # Log successful detection with actual results
        processing_time = 0  # In a real implementation, we would track this
        audit_logger.log_error_detection(
            filename=input_data.filename,
            total_errors=response.total_errors,
            processing_time=processing_time,
            success=True,
            session_id=None
        )

        return response

    except Exception as e:
        # Log the error
        audit_logger.log_error_detection(
            filename=input_data.filename,
            total_errors=0,
            processing_time=0,
            success=False,
            error=str(e),
            session_id=None
        )

        raise HTTPException(status_code=500, detail=f"Error detecting code issues: {str(e)}")


@app.post("/explain_error", response_model=ErrorExplanationResponse)
async def explain_error(explanation_request: ErrorExplanationRequest):
    """
    Provide detailed explanation for a specific error
    """
    try:
        # Log the API call
        audit_logger = get_audit_logger()
        audit_logger.log_error_explanation(
            error_type=explanation_request.error_type,
            error_message=explanation_request.error_message,
            explanation_provided=False,  # Not provided yet
            success=True,
            session_id=None
        )

        # In a real implementation, this would use AI to generate detailed explanations
        # For now, we'll provide basic explanations for common error types
        explanation = generate_error_explanation(
            explanation_request.error_type,
            explanation_request.error_message,
            explanation_request.code_context
        )

        response = ErrorExplanationResponse(
            explanation=explanation["explanation"],
            suggested_fix=explanation["suggested_fix"],
            related_info=explanation["related_info"]
        )

        # Log successful explanation
        audit_logger.log_error_explanation(
            error_type=explanation_request.error_type,
            error_message=explanation_request.error_message,
            explanation_provided=True,
            success=True,
            session_id=None
        )

        return response

    except Exception as e:
        # Log the error
        audit_logger.log_error_explanation(
            error_type=explanation_request.error_type,
            error_message=explanation_request.error_message,
            explanation_provided=False,
            success=False,
            error=str(e),
            session_id=None
        )

        raise HTTPException(status_code=500, detail=f"Error explaining error: {str(e)}")


@app.post("/suggest_fix", response_model=ErrorFixSuggestionResponse)
async def suggest_fix(fix_request: ErrorFixSuggestionRequest):
    """
    Suggest a fix for a specific error in the code
    """
    try:
        # Log the API call
        audit_logger = get_audit_logger()
        audit_logger.log_error_fix_suggestion(
            error_type=fix_request.error_type,
            error_message=fix_request.error_message,
            fix_suggested=False,  # Not suggested yet
            success=True,
            session_id=None
        )

        # In a real implementation, this would use AI to generate fix suggestions
        # For now, we'll provide basic fix suggestions for common error types
        fix_suggestion = generate_fix_suggestion(
            fix_request.error_type,
            fix_request.error_message,
            fix_request.problematic_code,
            fix_request.line_number
        )

        response = ErrorFixSuggestionResponse(
            suggested_fix=fix_suggestion["suggested_fix"],
            explanation=fix_suggestion["explanation"],
            alternative_approaches=fix_suggestion["alternative_approaches"]
        )

        # Log successful fix suggestion
        audit_logger.log_error_fix_suggestion(
            error_type=fix_request.error_type,
            error_message=fix_request.error_message,
            fix_suggested=True,
            success=True,
            session_id=None
        )

        return response

    except Exception as e:
        # Log the error
        audit_logger.log_error_fix_suggestion(
            error_type=fix_request.error_type,
            error_message=fix_request.error_message,
            fix_suggested=False,
            success=False,
            error=str(e),
            session_id=None
        )

        raise HTTPException(status_code=500, detail=f"Error suggesting fix: {str(e)}")


def generate_error_explanation(error_type: str, error_message: str, code_context: Optional[str] = None) -> Dict[str, Any]:
    """
    Generate an explanation for a specific error
    This is a simplified function - in a real system, this would use AI
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


def generate_fix_suggestion(
    error_type: str,
    error_message: str,
    problematic_code: str,
    line_number: Optional[int] = None
) -> Dict[str, Any]:
    """
    Generate a fix suggestion for a specific error
    This is a simplified function - in a real system, this would use AI
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


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check for the error detection API"""
    return {"status": "healthy", "service": "AI-Powered Error Detection"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)