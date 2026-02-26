"""
Advanced Error Detector with AST analysis, AI-powered code review, and security checks
"""
import ast
import json
import re
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
import subprocess
import sys
import os
from pathlib import Path
import yaml
import requests
from audit_logger import AuditLogger, retry_on_transient_error, get_audit_logger

@dataclass
class DetectedError:
    """Represents a detected error with its details."""
    error_type: str
    description: str
    severity: str  # 'low', 'medium', 'high', 'critical'
    line_number: int
    file_path: str
    code_snippet: str
    fix_patch: Optional[str] = None  # Git-style diff patch for fixing the error
    confidence: float = 1.0  # Confidence score between 0 and 1
    category: str = "general"  # 'security', 'logic', 'performance', 'style'


class VariableAnalyzer(ast.NodeVisitor):
    """Analyzes variable usage to detect NameError risks and UnusedVariable warnings."""

    def __init__(self):
        self.defined_vars = set()
        self.used_vars = set()
        self.vars_with_assignments = {}  # var_name -> line_no
        self.vars_used_before_def = []  # list of (var_name, line_no)
        self.unused_vars = set()
        # Track built-ins and imports to avoid false positives
        self.imported_modules = set()
        # Comprehensive list of Python builtins
        self.builtins = {
            '__import__', 'abs', 'all', 'any', 'ascii', 'bin', 'bool', 'bytearray', 'bytes',
            'callable', 'chr', 'classmethod', 'compile', 'complex', 'delattr', 'dict', 'dir',
            'divmod', 'enumerate', 'eval', 'exec', 'filter', 'float', 'format', 'frozenset',
            'getattr', 'globals', 'hasattr', 'hash', 'help', 'hex', 'id', 'input', 'int',
            'isinstance', 'issubclass', 'iter', 'len', 'list', 'locals', 'map', 'max', 'memoryview',
            'min', 'next', 'object', 'oct', 'open', 'ord', 'pow', 'print', 'property', 'range',
            'repr', 'reversed', 'round', 'set', 'setattr', 'slice', 'sorted', 'staticmethod',
            'str', 'sum', 'super', 'tuple', 'type', 'vars', 'zip',
            '__build_class__', '__debug__', '__doc__', '__import__', '__loader__', '__name__',
            '__package__', '__spec__', 'Ellipsis', 'False', 'None', 'True', 'NotImplemented',
            'ArithmeticError', 'AssertionError', 'AttributeError', 'BaseException',
            'BlockingIOError', 'BrokenPipeError', 'BufferError', 'BytesWarning',
            'ChildProcessError', 'ConnectionAbortedError', 'ConnectionError',
            'ConnectionRefusedError', 'ConnectionResetError', 'DeprecationWarning',
            'EOFError', 'EnvironmentError', 'Exception', 'FileExistsError',
            'FileNotFoundError', 'FloatingPointError', 'FutureWarning', 'GeneratorExit',
            'IOError', 'ImportError', 'ImportWarning', 'IndentationError', 'IndexError',
            'InterruptedError', 'IsADirectoryError', 'KeyError', 'KeyboardInterrupt',
            'LookupError', 'MemoryError', 'ModuleNotFoundError', 'NameError', 'NotADirectoryError',
            'NotImplementedError', 'OSError', 'OverflowError', 'PendingDeprecationWarning',
            'PermissionError', 'ProcessLookupError', 'RecursionError', 'ReferenceError',
            'ResourceWarning', 'RuntimeError', 'RuntimeWarning', 'StopAsyncIteration',
            'StopIteration', 'SyntaxError', 'SyntaxWarning', 'SystemError', 'SystemExit',
            'TabError', 'TimeoutError', 'TypeError', 'UnboundLocalError', 'UnicodeDecodeError',
            'UnicodeEncodeError', 'UnicodeError', 'UnicodeTranslateError', 'UnicodeWarning',
            'UserWarning', 'ValueError', 'Warning', 'ZeroDivisionError'
        }

    def visit_Import(self, node):
        """Track imported modules."""
        for alias in node.names:
            module_name = alias.name
            self.imported_modules.add(module_name)
            # Also add as defined if it has an alias
            if alias.asname:
                self.defined_vars.add(alias.asname)
            else:
                # For module names like 'import yaml' -> 'yaml' becomes defined
                self.defined_vars.add(module_name.split('.')[0])
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        """Track imported names from modules."""
        for alias in node.names:
            name = alias.asname if alias.asname else alias.name
            self.defined_vars.add(name)
        self.generic_visit(node)

    def visit_Assign(self, node):
        """Track variable assignments."""
        # Handle assignments like x = y = z = value
        for target in node.targets:
            if isinstance(target, ast.Name):
                self.defined_vars.add(target.id)
                self.vars_with_assignments[target.id] = node.lineno
            elif isinstance(target, ast.Tuple) and isinstance(node.value, ast.Tuple):
                # Handle tuple assignments like a, b = 1, 2
                for elt in target.elts:
                    if isinstance(elt, ast.Name):
                        self.defined_vars.add(elt.id)
                        self.vars_with_assignments[elt.id] = node.lineno
        self.generic_visit(node)

    def visit_AnnAssign(self, node):
        """Track annotated assignments."""
        if isinstance(node.target, ast.Name):
            self.defined_vars.add(node.target.id)
            self.vars_with_assignments[node.target.id] = node.lineno
        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        """Handle function definitions - parameters are defined within the function."""
        # Add function name to defined vars
        self.defined_vars.add(node.name)
        self.vars_with_assignments[node.name] = node.lineno

        # Process function parameters - they're defined within the function
        for arg in node.args.args:
            self.defined_vars.add(arg.arg)
            self.vars_with_assignments[arg.arg] = node.lineno

        # Handle default arguments
        for default in node.args.defaults:
            if default:
                self.visit(default)

        # Process function body
        for item in node.body:
            self.visit(item)

    def visit_AsyncFunctionDef(self, node):
        """Handle async function definitions the same as regular functions."""
        self.visit_FunctionDef(node)

    def visit_Lambda(self, node):
        """Handle lambda functions - parameters are defined within the lambda."""
        for arg in node.args.args:
            self.defined_vars.add(arg.arg)
            self.vars_with_assignments[arg.arg] = node.lineno

        # Process lambda body
        self.visit(node.body)

    def visit_Name(self, node):
        """Visit variable names to track usage and definition."""
        if isinstance(node.ctx, ast.Store):
            # Variable is being assigned/defined
            self.defined_vars.add(node.id)
            self.vars_with_assignments[node.id] = node.lineno
        elif isinstance(node.ctx, ast.Load):
            # Variable is being used/loaded
            self.used_vars.add(node.id)
            # Check if variable is used before it's defined and not a builtin/import
            if (node.id not in self.defined_vars and
                node.id not in self.builtins and
                node.id not in self.imported_modules):
                # Skip if it's a function parameter (since we handle those in visit_FunctionDef)
                # We need to check the context more carefully
                self.vars_used_before_def.append((node.id, node.lineno))
        self.generic_visit(node)


class ASTAnalyzer:
    """AST-based code analyzer for detecting potential issues."""

    def __init__(self):
        self.errors = []
        self.current_file = ""
        self.audit_logger = get_audit_logger()

    def analyze_file(self, file_path: str) -> List[DetectedError]:
        """Analyze a single Python file for potential errors."""
        self.current_file = file_path
        self.errors = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            tree = ast.parse(content)
            self.visit(tree, content.split('\n'))

            # Log the analysis event
            self.audit_logger.log_watcher_event(
                watcher_type="ast_analyzer",
                event_type="file_analysis_completed",
                event_data={
                    "file_path": file_path,
                    "error_count": len(self.errors),
                    "errors": [e.error_type for e in self.errors]
                },
                success=True
            )

            return self.errors
        except Exception as e:
            self.audit_logger.log_error(
                error_type="file_analysis_failed",
                error_message=str(e),
                context={"file_path": file_path}
            )
            return []

    def visit(self, node, lines):
        """Visit AST nodes and perform analysis."""
        # Perform variable analysis
        var_analyzer = VariableAnalyzer()
        var_analyzer.visit(node)

        # Report variables used before definition
        for var_name, line_no in var_analyzer.vars_used_before_def:
            code_snippet = self._get_code_snippet(lines, line_no)
            self.errors.append(DetectedError(
                error_type="name_error_risk",
                description=f"Variable '{var_name}' used before definition, may cause NameError",
                severity="high",
                line_number=line_no,
                file_path=self.current_file,
                code_snippet=code_snippet,
                category="logic"
            ))

        # Report unused variables
        defined_but_unused = var_analyzer.defined_vars - var_analyzer.used_vars
        for var_name in defined_but_unused:
            if var_name in var_analyzer.vars_with_assignments:
                line_no = var_analyzer.vars_with_assignments[var_name]
                code_snippet = self._get_code_snippet(lines, line_no)
                self.errors.append(DetectedError(
                    error_type="unused_variable",
                    description=f"Variable '{var_name}' is defined but never used",
                    severity="low",
                    line_number=line_no,
                    file_path=self.current_file,
                    code_snippet=code_snippet,
                    category="style"
                ))

        # Also perform other node analysis
        for child in ast.walk(node):
            self._analyze_node(child, lines)

    def _analyze_node(self, node, lines):
        """Analyze individual AST node."""
        line_no = getattr(node, 'lineno', 0)
        code_snippet = self._get_code_snippet(lines, line_no)

        # Check for hardcoded secrets
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            self._check_hardcoded_secret(node, code_snippet)

        # Check for insecure YAML loading
        if isinstance(node, ast.Call):
            self._check_insecure_yaml_load(node, code_snippet)
            self._check_sql_injection_vulnerabilities(node, code_snippet)

        # Check for other potential issues
        self._check_dangerous_functions(node, code_snippet)
        self._check_unsafe_eval(node, code_snippet)
        self._check_path_traversal(node, code_snippet)

    def _get_code_snippet(self, lines, line_no, context=2):
        """Get code snippet around the specified line."""
        start = max(0, line_no - 1 - context)
        end = min(len(lines), line_no + context)
        return '\n'.join(lines[start:end])

    def _check_hardcoded_secret(self, node, code_snippet):
        """Check for hardcoded secrets in string literals."""
        secret_patterns = [
            r'(password|secret|key|token|api_key|auth_token|access_token|client_secret)',
            r'(AWS_ACCESS_KEY_ID|AWS_SECRET_ACCESS_KEY|SECRET_KEY|DATABASE_URL)',
        ]

        value = node.value
        if isinstance(value, str):
            for pattern in secret_patterns:
                if re.search(pattern, value, re.IGNORECASE) and len(value) > 5:
                    self.errors.append(DetectedError(
                        error_type="hardcoded_secret",
                        description=f"Hardcoded secret detected: {value}",
                        severity="high",
                        line_number=node.lineno,
                        file_path=self.current_file,
                        code_snippet=code_snippet,
                        category="security"
                    ))

    def _check_insecure_yaml_load(self, node, code_snippet):
        """Check for insecure YAML loading (PyYAML vulnerability)."""
        if isinstance(node.func, ast.Attribute) and node.func.attr == 'load':
            if isinstance(node.func.value, ast.Name) and node.func.value.id == 'yaml':
                self.errors.append(DetectedError(
                    error_type="insecure_yaml_load",
                    description="Insecure YAML loading detected. Use yaml.safe_load() instead of yaml.load()",
                    severity="high",
                    line_number=node.lineno,
                    file_path=self.current_file,
                    code_snippet=code_snippet,
                    fix_patch=f"""# Before:
yaml.load(...)
# After:
yaml.safe_load(...)
""",
                    category="security"
                ))

    def _check_sql_injection_vulnerabilities(self, node, code_snippet):
        """Check for potential SQL injection vulnerabilities."""
        if isinstance(node.func, ast.Name) and 'query' in node.func.id.lower():
            for arg in node.args:
                if isinstance(arg, ast.BinOp) and isinstance(arg.op, ast.Add):
                    self.errors.append(DetectedError(
                        error_type="sql_injection",
                        description="Potential SQL injection detected: concatenating user input in SQL query",
                        severity="critical",
                        line_number=node.lineno,
                        file_path=self.current_file,
                        code_snippet=code_snippet,
                        category="security"
                    ))

    def _check_dangerous_functions(self, node, code_snippet):
        """Check for dangerous functions that could be security risks."""
        dangerous_funcs = {
            'eval': 'critical',
            'exec': 'critical',
            'compile': 'high',
            'open': 'medium',
            'subprocess': 'high',
            'os.system': 'high',
            'os.popen': 'high',
            'input': 'medium'  # For potential injection
        }

        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                func_name = node.func.id
                if func_name in dangerous_funcs:
                    self.errors.append(DetectedError(
                        error_type="dangerous_function_usage",
                        description=f"Dangerous function usage: {func_name}",
                        severity=dangerous_funcs[func_name],
                        line_number=node.lineno,
                        file_path=self.current_file,
                        code_snippet=code_snippet,
                        category="security"
                    ))

    def _check_unsafe_eval(self, node, code_snippet):
        """Specifically check for unsafe eval usage."""
        if (isinstance(node, ast.Call) and
            isinstance(node.func, ast.Name) and
            node.func.id in ['eval', 'exec']):
            self.errors.append(DetectedError(
                error_type="unsafe_eval_usage",
                description="Unsafe eval/exec usage detected. This can be a major security vulnerability.",
                severity="critical",
                line_number=node.lineno,
                file_path=self.current_file,
                code_snippet=code_snippet,
                fix_patch=f"""# Before:
eval(user_input)
exec(user_input)
# After:
# Use ast.literal_eval() for simple literals
import ast
ast.literal_eval(safe_literal)
# Or validate input carefully before evaluation
""",
                category="security"
            ))

    def _check_path_traversal(self, node, code_snippet):
        """Check for potential path traversal vulnerabilities."""
        if (isinstance(node, ast.Call) and
            isinstance(node.func, ast.Name) and
            node.func.id in ['open', 'os.path.join']):
            # Look for cases where user input directly affects file paths
            for arg in node.args:
                if isinstance(arg, ast.BinOp) and isinstance(arg.op, ast.Add):
                    # This is a simplified check for string concatenation in file operations
                    self.errors.append(DetectedError(
                        error_type="path_traversal",
                        description="Potential path traversal vulnerability: user input used in file path construction",
                        severity="high",
                        line_number=node.lineno,
                        file_path=self.current_file,
                        code_snippet=code_snippet,
                        category="security"
                    ))


class AIAnalyzer:
    """AI-powered code analyzer using Anthropic's Claude."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        from audit_logger import get_audit_logger
        self.audit_logger = get_audit_logger()
        if not self.api_key:
            self.audit_logger.log_error(
                "missing_api_key",
                "Anthropic API key not found",
                {"component": "AIAnalyzer"}
            )
            print("Warning: Anthropic API key not found. AI analysis will be simulated.")

    @retry_on_transient_error(max_retries=3, base_delay=1.0)
    def analyze_code_with_ai(self, code: str, file_path: str, errors: List[DetectedError]) -> List[DetectedError]:
        """Analyze code with AI and potential errors to enhance detection."""
        if not self.api_key:
            # Simulate AI analysis when no API key is available
            return self._simulate_ai_analysis(code, file_path, errors)

        try:
            # Gather context: Python version and library dependencies
            python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
            dependencies = self._get_dependencies()

            # Create enhanced prompt with context
            prompt = self._create_enhanced_prompt(code, file_path, python_version, dependencies, errors)

            # Call Anthropic API
            response = self._call_anthropic_api(prompt)

            # Parse JSON response
            ai_errors = self._parse_ai_response(response)

            # Log the AI analysis
            self.audit_logger.log_watcher_event(
                watcher_type="ai_analyzer",
                event_type="ai_analysis_completed",
                event_data={
                    "file_path": file_path,
                    "ai_error_count": len(ai_errors),
                    "python_version": python_version,
                    "dependency_count": len(dependencies)
                },
                success=True
            )

            return ai_errors

        except Exception as e:
            self.audit_logger.log_error(
                error_type="ai_analysis_failed",
                error_message=str(e),
                context={
                    "file_path": file_path,
                    "error": str(e)
                }
            )
            return []

    def _create_enhanced_prompt(self, code: str, file_path: str, python_version: str, dependencies: Dict[str, str], errors: List[DetectedError]) -> str:
        """Create an enhanced prompt for AI analysis including context."""
        errors_str = "\n".join([f"- {e.error_type}: {e.description} at line {e.line_number}" for e in errors])

        dependencies_str = "\n".join([f"- {pkg}: {version}" for pkg, version in dependencies.items()])

        return f"""
You are a security-focused code analysis expert. Analyze the following Python code for potential bugs, vulnerabilities, and code quality issues.

CONTEXT:
- Python Version: {python_version}
- Dependencies: {dependencies_str}
- Previously detected errors: {errors_str if errors else "None"}

CODE TO ANALYZE:
```python
{code}
```

Please respond in the following JSON format:
{{
  "analysis": {{
    "file_path": "{file_path}",
    "detected_issues": [
      {{
        "type": "issue_type",
        "description": "detailed_description",
        "severity": "low|medium|high|critical",
        "category": "security|logic|performance|style",
        "line_number": 123,
        "code_snippet": "relevant_code_line(s)",
        "fix_suggestion": "git_diff_style_patch_or_explanation",
        "confidence": 0.9
      }}
    ]
  }}
}}

Focus especially on:
1. Security vulnerabilities (injection attacks, hardcoded secrets, path traversal, etc.)
2. Logic errors that could cause runtime issues
3. Performance anti-patterns
4. Code that doesn't follow Python best practices
5. Potential crashes or exceptions
"""

    def _call_anthropic_api(self, prompt: str):
        """Call Anthropic API to analyze code."""
        if not self.api_key:
            # Return simulated response if no API key is available
            return self._simulate_anthropic_response()

        try:
            import anthropic

            client = anthropic.Anthropic(api_key=self.api_key)

            # Create a message using the new API format
            message = client.messages.create(
                model="claude-3-haiku-20240307",  # Using a more cost-effective model for analysis
                max_tokens=1000,
                temperature=0.1,  # Low temperature for consistent, analytical responses
                system="You are a security-focused code analysis expert. Respond in valid JSON format only.",
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            # Return the response content
            response_text = message.content[0].text if message.content else "{}"

            # Parse response as JSON to ensure it's valid
            try:
                import json
                parsed_response = json.loads(response_text)
                return parsed_response
            except json.JSONDecodeError:
                # If response isn't valid JSON, return a structured error response
                return {
                    "analysis": {
                        "file_path": "unknown",
                        "detected_issues": [
                            {
                                "type": "parsing_error",
                                "description": "AI response was not in valid JSON format",
                                "severity": "medium",
                                "category": "parsing",
                                "line_number": 0,
                                "code_snippet": response_text[:200],
                                "fix_suggestion": "Retry analysis or check prompt format",
                                "confidence": 0.5
                            }
                        ]
                    }
                }

        except ImportError:
            # Anthropic library not available, return simulated response
            return self._simulate_anthropic_response()
        except Exception as e:
            self.audit_logger.log_error(
                error_type="anthropic_api_error",
                error_message=str(e),
                context={"prompt_length": len(prompt)}
            )
            # Return simulated response as fallback
            return self._simulate_anthropic_response()

    def _simulate_anthropic_response(self):
        """Simulate Anthropic API response for demonstration purposes."""
        # This is a simulated response that would normally come from Claude
        return {
            "analysis": {
                "file_path": "mock_file.py",
                "detected_issues": [
                    {
                        "type": "security_concern",
                        "description": "Potential vulnerability found",
                        "severity": "medium",
                        "category": "security",
                        "line_number": 1,
                        "code_snippet": "import some_module",
                        "fix_suggestion": "# Add security check here",
                        "confidence": 0.8
                    }
                ]
            }
        }

    def _parse_ai_response(self, response) -> List[DetectedError]:
        """Parse the AI response into DetectedError objects."""
        try:
            if isinstance(response, str):
                response = json.loads(response)

            issues = response.get("analysis", {}).get("detected_issues", [])
            ai_errors = []

            for issue in issues:
                ai_errors.append(DetectedError(
                    error_type=issue.get("type", "unknown"),
                    description=issue.get("description", ""),
                    severity=issue.get("severity", "medium"),
                    category=issue.get("category", "general"),
                    line_number=issue.get("line_number", 0),
                    file_path=issue.get("file_path", ""),
                    code_snippet=issue.get("code_snippet", ""),
                    fix_patch=issue.get("fix_suggestion"),
                    confidence=issue.get("confidence", 0.5)
                ))

            return ai_errors
        except Exception as e:
            self.audit_logger.log_error(
                error_type="ai_response_parse_failed",
                error_message=str(e),
                context={"response": str(response)}
            )
            return []

    def _get_dependencies(self) -> Dict[str, str]:
        """Get the project dependencies."""
        dependencies = {}

        # Look for requirements.txt
        req_paths = ["requirements.txt", "requirements-dev.txt", "setup.py", "pyproject.toml"]

        for req_path in req_paths:
            if os.path.exists(req_path):
                try:
                    with open(req_path, 'r') as f:
                        content = f.read()

                    if req_path.endswith('.txt'):
                        # Parse requirements.txt format
                        for line in content.split('\n'):
                            line = line.strip()
                            if line and not line.startswith('#') and '==' in line:
                                pkg_ver = line.split('==', 1)
                                if len(pkg_ver) == 2:
                                    dependencies[pkg_ver[0]] = pkg_ver[1]
                    elif req_path == 'setup.py':
                        # Basic parsing of setup.py (simplified)
                        if 'install_requires' in content:
                            # This is a simplified parsing - in reality would need more sophisticated parsing
                            pass
                    elif req_path.endswith('.toml'):
                        # Try to parse pyproject.toml if it contains dependencies
                        try:
                            pyproject = yaml.safe_load(content)
                            deps = pyproject.get('project', {}).get('dependencies', [])
                            for dep in deps:
                                if '==' in dep:
                                    pkg_ver = dep.split('==', 1)
                                    dependencies[pkg_ver[0]] = pkg_ver[1]
                        except:
                            pass
                except Exception as e:
                    self.audit_logger.log_error(
                        error_type="dependency_parsing_failed",
                        error_message=str(e),
                        context={"file": req_path}
                    )

        # Use pip list to get currently installed packages
        try:
            result = subprocess.run([sys.executable, '-m', 'pip', 'list', '--format', 'json'],
                                    capture_output=True, text=True)
            if result.returncode == 0:
                installed_packages = json.loads(result.stdout)
                for pkg in installed_packages:
                    pkg_name = pkg['name']
                    if pkg_name not in dependencies:
                        dependencies[pkg_name] = pkg['version']
        except Exception as e:
            self.audit_logger.log_error(
                error_type="pip_list_failed",
                error_message=str(e),
                context={"operation": "get_installed_packages"}
            )

        return dependencies

    def _simulate_ai_analysis(self, code: str, file_path: str, errors: List[DetectedError]) -> List[DetectedError]:
        """Simulate AI analysis when API is not available."""
        # For demonstration, return a mock analysis
        # In a real implementation, this would be replaced with actual AI analysis
        simulated_errors = []

        # Add existing errors with enhanced confidence from AI perspective
        for error in errors:
            simulated_errors.append(DetectedError(
                error_type=error.error_type,
                description=error.description,
                severity=error.severity,
                line_number=error.line_number,
                file_path=error.file_path,
                code_snippet=error.code_snippet,
                fix_patch=error.fix_patch,
                confidence=error.confidence,
                category=error.category
            ))

        # Potentially add more errors based on simple heuristics
        # In a real AI implementation, this would be handled by the LLM
        if 'pickle' in code:
            # Simulate detection of pickle usage (potential security risk)
            simulated_errors.append(DetectedError(
                error_type="insecure_pickle_usage",
                description="Pickle usage detected. Consider using safer serialization methods for untrusted data",
                severity="high",
                line_number=1,
                file_path=file_path,
                code_snippet="import pickle # Consider using JSON for safer serialization",
                category="security",
                confidence=0.7
            ))

        return simulated_errors


class ErrorDetector:
    """Main Error Detector class that orchestrates AST and AI analysis."""

    def __init__(self, api_key: Optional[str] = None):
        self.ast_analyzer = ASTAnalyzer()
        self.ai_analyzer = AIAnalyzer(api_key)
        from audit_logger import get_audit_logger
        self.audit_logger = get_audit_logger()

    def analyze_directory(self, directory_path: str, include_subdirs: bool = True) -> List[DetectedError]:
        """Analyze all Python files in a directory."""
        errors = []

        # Find all Python files
        py_files = []
        dir_path = Path(directory_path)

        if include_subdirs:
            py_files = list(dir_path.rglob("*.py"))
        else:
            py_files = list(dir_path.glob("*.py"))

        self.audit_logger.log_watcher_event(
            watcher_type="error_detector",
            event_type="directory_analysis_started",
            event_data={
                "directory": directory_path,
                "file_count": len(py_files),
                "include_subdirs": include_subdirs
            },
            success=True
        )

        for py_file in py_files:
            file_errors = self.analyze_file(str(py_file))
            errors.extend(file_errors)

        self.audit_logger.log_watcher_event(
            watcher_type="error_detector",
            event_type="directory_analysis_completed",
            event_data={
                "directory": directory_path,
                "total_errors": len(errors),
                "unique_error_types": list(set(e.error_type for e in errors))
            },
            success=True
        )

        return errors

    def analyze_file(self, file_path: str) -> List[DetectedError]:
        """Analyze a single file combining AST and AI analysis."""
        # AST Analysis
        ast_errors = self.ast_analyzer.analyze_file(file_path)

        # Read file content for AI analysis
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            self.audit_logger.log_error(
                error_type="file_read_failed",
                error_message=str(e),
                context={"file_path": file_path}
            )
            return ast_errors

        # AI Analysis
        ai_errors = self.ai_analyzer.analyze_code_with_ai(content, file_path, ast_errors)

        # Combine and deduplicate errors
        combined_errors = self._combine_errors(ast_errors, ai_errors)

        # Log the file analysis
        self.audit_logger.log_watcher_event(
            watcher_type="error_detector",
            event_type="file_analysis_completed_all",
            event_data={
                "file_path": file_path,
                "ast_error_count": len(ast_errors),
                "ai_error_count": len(ai_errors),
                "combined_error_count": len(combined_errors)
            },
            success=True
        )

        return combined_errors

    def _combine_errors(self, ast_errors: List[DetectedError], ai_errors: List[DetectedError]) -> List[DetectedError]:
        """Combine and deduplicate errors from AST and AI analysis."""
        combined = list(ast_errors)  # Start with AST errors

        # Add AI errors that aren't already detected by AST
        for ai_error in ai_errors:
            is_duplicate = False
            for ast_error in ast_errors:
                # Simple deduplication based on line number and error type
                if (ai_error.line_number == ast_error.line_number and
                    ai_error.error_type == ast_error.error_type):
                    is_duplicate = True
                    # Update with AI's confidence if higher
                    if ai_error.confidence > ast_error.confidence:
                        ast_error.confidence = ai_error.confidence
                    break

            if not is_duplicate:
                combined.append(ai_error)

        return combined

    def get_error_report(self, errors: List[DetectedError]) -> Dict[str, Any]:
        """Generate a comprehensive error report."""
        report = {
            "summary": {
                "total_errors": len(errors),
                "by_severity": {},
                "by_category": {},
                "by_file": {}
            },
            "detailed_errors": [self._error_to_dict(error) for error in errors]
        }

        # Aggregate by severity
        for error in errors:
            # Count by severity
            severity = error.severity
            report["summary"]["by_severity"][severity] = report["summary"]["by_severity"].get(severity, 0) + 1

            # Count by category
            category = error.category
            report["summary"]["by_category"][category] = report["summary"]["by_category"].get(category, 0) + 1

            # Count by file
            file_path = error.file_path
            if file_path not in report["summary"]["by_file"]:
                report["summary"]["by_file"][file_path] = {
                    "count": 0,
                    "errors": []
                }
            report["summary"]["by_file"][file_path]["count"] += 1
            report["summary"]["by_file"][file_path]["errors"].append({
                "type": error.error_type,
                "severity": error.severity,
                "line": error.line_number,
                "description": error.description
            })

        return report

    def _error_to_dict(self, error: DetectedError) -> Dict[str, Any]:
        """Convert DetectedError to dictionary for JSON serialization."""
        return {
            "error_type": error.error_type,
            "description": error.description,
            "severity": error.severity,
            "category": error.category,
            "line_number": error.line_number,
            "file_path": error.file_path,
            "code_snippet": error.code_snippet,
            "fix_patch": error.fix_patch,
            "confidence": error.confidence
        }


def main():
    """Command line interface for the Error Detector."""
    import argparse

    parser = argparse.ArgumentParser(description="Advanced Python Error Detector")
    parser.add_argument("path", help="Path to file or directory to analyze")
    parser.add_argument("--output", "-o", help="Output file for results (JSON format)")
    parser.add_argument("--api-key", help="Anthropic API key (alternatively use ANTHROPIC_API_KEY env var)")

    args = parser.parse_args()

    detector = ErrorDetector(api_key=args.api_key)

    path = Path(args.path)
    if path.is_file() and path.suffix == '.py':
        errors = detector.analyze_file(str(path))
    elif path.is_dir():
        errors = detector.analyze_directory(str(path))
    else:
        print(f"Error: {args.path} is not a Python file or directory")
        return

    report = detector.get_error_report(errors)

    if args.output:
        with open(args.output, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"Report saved to {args.output}")
    else:
        print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()