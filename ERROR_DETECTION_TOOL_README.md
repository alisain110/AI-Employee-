# AI-Powered Error Detection Tool

The AI-Powered Error Detection Tool is a sophisticated system that can find and explain code errors within seconds using AI analysis and pattern matching.

## 🚀 Features

- **Multi-layered Analysis**: Combines static code analysis, pattern matching, and AI-powered semantic analysis
- **Real-time Error Detection**: Finds errors in code within seconds
- **Natural Language Explanations**: Provides human-readable explanations for detected errors
- **Fix Suggestions**: Offers concrete suggestions for fixing errors
- **Severity Classification**: Categorizes errors by severity (critical, high, medium, low, info)
- **Security Vulnerability Detection**: Identifies potential security risks in code
- **FastAPI Integration**: Includes a production-ready API with multiple endpoints
- **LangChain Tools**: Integrates with LangChain for use in AI agents
- **Comprehensive Audit Logging**: Tracks all error detection activities

## 📁 Directory Structure

```
AI_Employee_Vault/
├── error_detector.py          # Core error detection engine
├── api/
│   └── error_detection.py     # FastAPI endpoints for error detection
├── models/
│   └── error_models.py        # Pydantic models for API
├── tools/
│   └── error_detection_tool.py # LangChain tools for error detection
├── config/
│   ├── error_detection_config.py # Configuration settings
│   └── settings.py            # Global settings
├── test_error_detection.py    # Test suite
├── ai_error_detector.py       # Main integration script
└── demo_api.py               # API demonstration
```

## ⚙️ Core Components

### 1. Error Detection Engine (`error_detector.py`)
- **CodeAnalyzer**: Performs static code analysis for syntax errors and common issues
- **AIErrorAnalyzer**: Uses AI to detect semantic and logical errors
- **ErrorPatternMatcher**: Matches code against known error patterns
- **ErrorReporter**: Generates comprehensive reports with natural language explanations

### 2. API Endpoints (`api/error_detection.py`)
- `POST /detect_errors`: Analyze code and find errors
- `POST /explain_error`: Get detailed explanation for specific errors
- `POST /suggest_fix`: Get suggestions to fix specific errors
- `GET /health`: Health check endpoint

### 3. Data Models (`models/error_models.py`)
- Pydantic models for request/response validation
- Error location and classification models
- Batch processing models

### 4. LangChain Integration (`tools/error_detection_tool.py`)
- Error detection tools for AI agents
- Error explanation and fix suggestion tools
- Ready to integrate with Claude/AI systems

## 🛠️ Usage Examples

### 1. Direct Usage
```python
from error_detector import AIPoweredErrorDetector

detector = AIPoweredErrorDetector()

sample_code = """
def unsafe_eval(user_input):
    return eval(user_input)  # Security risk!
"""

report = detector.detect_errors(sample_code, "sample.py")
print(report["summary"])
```

### 2. API Usage
```bash
# Start the API server
uvicorn api.error_detection:app --host 0.0.0.0 --port 8005

# Call the API
curl -X POST http://localhost:8005/detect_errors \
  -H "Content-Type: application/json" \
  -d '{"code": "def f(): return eval(input())"}'
```

### 3. Interactive Mode
```bash
python ai_error_detector.py
```

## 🧪 Testing

Run the test suite to verify functionality:
```bash
python test_error_detection.py
```

## 📊 Error Classification

The tool categorizes errors by:
- **Severity**: Critical, High, Medium, Low, Info
- **Category**: Security, Performance, Development, Syntax, etc.
- **Type**: Specific error types (SecurityWarning, ResourceLeak, etc.)

## 🔧 Configuration

The system includes comprehensive configuration options:
- API settings (host, port, rate limiting)
- AI model settings (temperature, max tokens)
- Performance settings (timeouts, caching)
- Error detection settings (enabled checks)

## 📈 Performance

- Sub-second error detection for typical code files
- Optimized for both development and production use
- Caching support for frequently analyzed patterns
- Scalable architecture supporting concurrent requests

## 🛡️ Security

- Identifies security vulnerabilities (SQL injection, command injection)
- Detects potential resource leaks
- Warns about unsafe function calls (eval, exec, etc.)
- Flags hardcoded credentials and secrets

## 🤖 AI Integration

Built to seamlessly integrate with:
- Anthropic Claude models for advanced analysis
- LangChain for agent-based systems
- FastAPI for web services
- Existing AI Employee Vault infrastructure

## 📋 Supported Languages

Currently supports:
- Python (primary focus)
- JavaScript/TypeScript (with pattern matching)
- Java, Go, Rust, C# (with pattern matching)
- Additional languages easily extendable

## 🚀 Getting Started

1. Install dependencies (if needed)
2. Start the main system
3. Use the error detection tool directly or via API
4. Integrate with your development workflow

The tool is designed to be highly accurate while maintaining fast response times, making it perfect for real-time error detection in development environments.