"""
Pydantic models for the AI-powered error detection system
"""
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from enum import Enum


class ErrorSeverity(str, Enum):
    """Error severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class ErrorLocation(BaseModel):
    """Represents the location of an error in code"""
    line: Optional[int] = None
    column: Optional[int] = None
    end_line: Optional[int] = None
    end_column: Optional[int] = None


class DetectedErrorModel(BaseModel):
    """Model for a detected error"""
    type: str
    message: str
    severity: ErrorSeverity
    location: Optional[ErrorLocation] = None
    code_snippet: Optional[str] = None
    suggestion: Optional[str] = None
    category: str = "general"


class CodeInput(BaseModel):
    """Input model for code to be analyzed"""
    code: str
    filename: Optional[str] = "unknown"
    language: Optional[str] = "python"


class ErrorDetectionResponse(BaseModel):
    """Response model for error detection"""
    filename: str
    total_errors: int
    errors_by_severity: Dict[str, int]
    errors_by_category: Dict[str, int]
    detailed_errors: List[DetectedErrorModel]
    summary: str


class ErrorExplanationRequest(BaseModel):
    """Request model for error explanation"""
    error_type: str
    error_message: str
    code_context: Optional[str] = None


class ErrorExplanationResponse(BaseModel):
    """Response model for error explanation"""
    explanation: str
    suggested_fix: str
    related_info: List[str]


class ErrorFixSuggestionRequest(BaseModel):
    """Request model for error fix suggestion"""
    error_type: str
    error_message: str
    problematic_code: str
    line_number: Optional[int] = None


class ErrorFixSuggestionResponse(BaseModel):
    """Response model for error fix suggestion"""
    suggested_fix: str
    explanation: str
    alternative_approaches: List[str]


class ErrorAnalysisReport(BaseModel):
    """Comprehensive error analysis report"""
    filename: str
    total_errors: int
    errors_by_severity: Dict[str, int]
    errors_by_category: Dict[str, int]
    detailed_errors: List[DetectedErrorModel]
    summary: str
    timestamp: str
    execution_time_ms: float


class BatchErrorDetectionRequest(BaseModel):
    """Request model for batch error detection"""
    files: List[CodeInput]
    include_explanations: Optional[bool] = False


class BatchErrorDetectionResponse(BaseModel):
    """Response model for batch error detection"""
    results: List[ErrorDetectionResponse]
    total_files: int
    total_errors: int
    processing_time_ms: float


class ErrorPattern(BaseModel):
    """Model for error patterns to match against"""
    id: str
    pattern: str
    type: str
    message: str
    severity: ErrorSeverity
    category: str
    description: Optional[str] = None


class ErrorPatternList(BaseModel):
    """List of error patterns"""
    patterns: List[ErrorPattern]
    total_count: int