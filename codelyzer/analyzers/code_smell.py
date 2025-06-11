from typing import Any, Dict
from codelyzer.config import FileMetrics, ProjectMetrics, MetricProvider, CodeSmellSeverity


class CodeSmellAnalyzer(MetricProvider):
    """Analyzer for identifying code smells in projects"""
    
    def provide_file_metrics(self, file_metrics: FileMetrics, file_content: str, ast_data: Any) -> None:
        """Analyze file for code smells"""
        language = file_metrics.language
        
        # Skip if content is empty
        if not file_content:
            return
            
        # Run common code smell detections
        self._check_file_length(file_metrics, file_content)
        self._check_function_length(file_metrics, file_content, language)
        self._check_commented_code(file_metrics, file_content, language)
        self._check_duplicate_code(file_metrics, file_content)
        
        # Language-specific smells
        if language == "python":
            self._check_python_smells(file_metrics, file_content, ast_data)
        elif language in ("javascript", "typescript", "jsx"):
            self._check_js_smells(file_metrics, file_content, ast_data)
        
        # Calculate technical debt ratio based on code smells
        self._calculate_technical_debt(file_metrics)
    
    def provide_project_metrics(self, project_metrics: ProjectMetrics) -> None:
        """Analyze project-level code smell metrics"""
        # Aggregate duplicate code blocks across the project
        self._detect_project_duplications(project_metrics)
        
        # Calculate project-level metrics
        smell_counts = {}
        for file_metrics in project_metrics.file_metrics:
            for smell in file_metrics.code_smells_list:
                smell_type = smell.get('type', 'unknown')
                if smell_type not in smell_counts:
                    smell_counts[smell_type] = 0
                smell_counts[smell_type] += 1
        
        # Add to project metrics
        project_metrics.code_quality.smell_counts = smell_counts
        
        # Calculate duplicated lines ratio
        total_duplicated = sum(f.duplicated_lines for f in project_metrics.file_metrics)
        if project_metrics.total_sloc > 0:
            project_metrics.code_quality.duplicated_lines_ratio = total_duplicated / project_metrics.total_sloc
    
    def _check_file_length(self, file_metrics: FileMetrics, file_content: str) -> None:
        """Check if file is too long"""
        lines = file_content.split('\n')
        line_count = len(lines)
        
        if line_count > 1000:
            self._add_code_smell(
                file_metrics,
                "file_too_long",
                f"File has {line_count} lines (recommended max: 1000)",
                {'line': 1, 'column': 1},
                CodeSmellSeverity.MAJOR
            )
        elif line_count > 500:
            self._add_code_smell(
                file_metrics,
                "file_long",
                f"File has {line_count} lines (recommended max: 500)",
                {'line': 1, 'column': 1},
                CodeSmellSeverity.MINOR
            )
    
    def _check_function_length(self, file_metrics: FileMetrics, file_content: str, language: str) -> None:
        """Check for overly long functions/methods"""
        import re
        
        # Language-specific function detection
        if language == "python":
            # Find Python function definitions
            func_pattern = r"def\s+(\w+)\s*\("
            functions = re.finditer(func_pattern, file_content)
            
            for match in functions:
                # Get function name and position
                func_name = match.group(1)
                func_start = match.start()
                
                # Find function body by indentation
                lines = file_content[func_start:].split('\n')
                line_count = 0
                in_function = False
                
                for i, line in enumerate(lines):
                    if i == 0:  # Function definition line
                        in_function = True
                        continue
                        
                    if in_function:
                        stripped = line.strip()
                        if stripped:  # Non-empty line
                            # Check if line is still in function (by indentation)
                            indent = len(line) - len(line.lstrip())
                            if indent == 0:  # No indentation means out of function
                                break
                            line_count += 1
                
                # Check function length
                if line_count > 50:
                    location = self._get_line_number(file_content, func_start)
                    self._add_code_smell(
                        file_metrics,
                        "function_too_long",
                        f"Function '{func_name}' has {line_count} lines (recommended max: 50)",
                        location,
                        CodeSmellSeverity.MAJOR
                    )
                elif line_count > 30:
                    location = self._get_line_number(file_content, func_start)
                    self._add_code_smell(
                        file_metrics,
                        "function_long",
                        f"Function '{func_name}' has {line_count} lines (recommended max: 30)",
                        location,
                        CodeSmellSeverity.MINOR
                    )
        
        elif language in ("javascript", "typescript", "jsx"):
            # Find JS function definitions (multiple formats)
            func_patterns = [
                r"function\s+(\w+)\s*\([^)]*\)\s*{",  # function name() {}
                r"(?:const|let|var)\s+(\w+)\s*=\s*function\s*\([^)]*\)\s*{",  # const name = function() {}
                r"(?:const|let|var)\s+(\w+)\s*=\s*\([^)]*\)\s*=>\s*{",  # const name = () => {}
                r"(\w+)\s*:\s*function\s*\([^)]*\)\s*{",  # name: function() {}
            ]
            
            for pattern in func_patterns:
                functions = re.finditer(pattern, file_content)
                
                for match in functions:
                    # Get function name and position
                    func_name = match.group(1)
                    func_start = match.start()
                    
                    # Find function body by counting braces
                    lines = file_content[func_start:].split('\n')
                    brace_count = 0
                    line_count = 0
                    
                    for i, line in enumerate(lines):
                        if i == 0:  # Function definition line
                            brace_count += line.count('{')
                            continue
                            
                        brace_count += line.count('{') - line.count('}')
                        line_count += 1
                        
                        if brace_count <= 0:
                            break
                    
                    # Check function length
                    if line_count > 50:
                        location = self._get_line_number(file_content, func_start)
                        self._add_code_smell(
                            file_metrics,
                            "function_too_long",
                            f"Function '{func_name}' has {line_count} lines (recommended max: 50)",
                            location,
                            CodeSmellSeverity.MAJOR
                        )
                    elif line_count > 30:
                        location = self._get_line_number(file_content, func_start)
                        self._add_code_smell(
                            file_metrics,
                            "function_long",
                            f"Function '{func_name}' has {line_count} lines (recommended max: 30)",
                            location,
                            CodeSmellSeverity.MINOR
                        )
    
    def _check_commented_code(self, file_metrics: FileMetrics, file_content: str, language: str) -> None:
        """Detect commented-out code blocks"""
        lines = file_content.split('\n')
        comment_markers = {
            "python": "#",
            "javascript": "//",
            "typescript": "//",
            "jsx": "//"
        }
        
        marker = comment_markers.get(language, "#")
        code_indicators = [
            "if ", "for ", "while ", "def ", "class ", "function", "return ", "var ", "let ", "const "
        ]
        
        # Track consecutive commented lines
        comment_block = []
        for i, line in enumerate(lines):
            stripped = line.strip()
            
            # Check for comment line
            if stripped.startswith(marker):
                comment_content = stripped[len(marker):].strip()
                
                # Check if comment looks like code
                if any(indicator in comment_content for indicator in code_indicators):
                    comment_block.append((i+1, comment_content))
                else:
                    # Not code-like, reset block if only one line
                    if len(comment_block) <= 1:
                        comment_block = []
            else:
                # Not a comment, check if we had a comment block
                if len(comment_block) >= 3:  # 3+ lines of commented code
                    start_line = comment_block[0][0]
                    self._add_code_smell(
                        file_metrics,
                        "commented_code",
                        f"Found block of {len(comment_block)} lines of commented-out code",
                        {'line': start_line, 'column': 1},
                        CodeSmellSeverity.MINOR
                    )
                comment_block = []
        
        # Check remaining block at end of file
        if len(comment_block) >= 3:
            start_line = comment_block[0][0]
            self._add_code_smell(
                file_metrics,
                "commented_code",
                f"Found block of {len(comment_block)} lines of commented-out code",
                {'line': start_line, 'column': 1},
                CodeSmellSeverity.MINOR
            )
    
    def _check_duplicate_code(self, file_metrics: FileMetrics, file_content: str) -> None:
        """Check for duplicate code within a file (simplified)"""
        lines = file_content.split('\n')
        duplicate_count = 0
        chunk_size = 6  # Minimum size of duplicate chunks to detect
        
        # Simplistic duplicate detection (can be replaced with more robust algorithm)
        chunks = {}
        
        for i in range(len(lines) - chunk_size + 1):
            chunk = "\n".join(lines[i:i+chunk_size])
            if len(chunk.strip()) < 30:  # Skip small chunks
                continue
                
            if chunk in chunks:
                # Found duplicate
                if chunks[chunk] != -1:  # Not already counted
                    duplicate_count += chunk_size
                    file_metrics.code_smells.duplicated_lines += chunk_size
                    
                    # Report first occurrence
                    first_line = chunks[chunk] + 1
                    self._add_code_smell(
                        file_metrics,
                        "duplicate_code",
                        f"Duplicate code block (also at line {i+1})",
                        {'line': first_line, 'column': 1},
                        CodeSmellSeverity.MINOR
                    )
                    
                    # Report second occurrence
                    self._add_code_smell(
                        file_metrics,
                        "duplicate_code",
                        f"Duplicate code block (also at line {first_line})",
                        {'line': i+1, 'column': 1},
                        CodeSmellSeverity.MINOR
                    )
                    
                    chunks[chunk] = -1  # Mark as counted
            else:
                chunks[chunk] = i
                
        file_metrics.code_smells.duplicated_lines = duplicate_count
    
    def _check_python_smells(self, file_metrics: FileMetrics, file_content: str, ast_data: Any) -> None:
        """Check for Python-specific code smells"""
        import re
        
        # Check for wildcard imports
        wildcard_pattern = r"from\s+\w+\s+import\s+\*"
        matches = re.finditer(wildcard_pattern, file_content)
        for match in matches:
            location = self._get_line_number(file_content, match.start())
            self._add_code_smell(
                file_metrics,
                "wildcard_import",
                "Wildcard import should be avoided",
                location,
                CodeSmellSeverity.MINOR
            )
        
        # Check for excessive exception catching
        broad_except_pattern = r"except\s*:"
        matches = re.finditer(broad_except_pattern, file_content)
        for match in matches:
            location = self._get_line_number(file_content, match.start())
            self._add_code_smell(
                file_metrics,
                "broad_except",
                "Broad exception clause should be avoided",
                location,
                CodeSmellSeverity.MAJOR
            )
            
        # Check for mutable default arguments
        mutable_defaults_pattern = r"def\s+\w+\s*\([^)]*=\s*(\[\]|\{\}|\(\)|\{\s*:\s*\}|\[\s*\]|\(\s*\))[^)]*\)"
        matches = re.finditer(mutable_defaults_pattern, file_content)
        for match in matches:
            location = self._get_line_number(file_content, match.start())
            self._add_code_smell(
                file_metrics,
                "mutable_default",
                "Mutable default argument can cause unexpected behavior",
                location,
                CodeSmellSeverity.MAJOR
            )
    
    def _check_js_smells(self, file_metrics: FileMetrics, file_content: str, ast_data: Any) -> None:
        """Check for JavaScript-specific code smells"""
        import re
        
        # Check for console.log statements
        console_pattern = r"console\.(log|warn|error|info|debug)\("
        matches = re.finditer(console_pattern, file_content)
        for match in matches:
            location = self._get_line_number(file_content, match.start())
            self._add_code_smell(
                file_metrics,
                "console_statement",
                "Console statement should be removed in production code",
                location,
                CodeSmellSeverity.MINOR
            )
        
        # Check for alert/prompt usage
        alert_pattern = r"\b(alert|prompt|confirm)\("
        matches = re.finditer(alert_pattern, file_content)
        for match in matches:
            location = self._get_line_number(file_content, match.start())
            self._add_code_smell(
                file_metrics,
                "alert_usage",
                f"Usage of {match.group(1)} should be avoided in modern web applications",
                location,
                CodeSmellSeverity.MINOR
            )
        
        # Check for == instead of ===
        equality_pattern = r"[^=!]=(?!=)[^=]"
        matches = re.finditer(equality_pattern, file_content)
        for match in matches:
            location = self._get_line_number(file_content, match.start())
            self._add_code_smell(
                file_metrics,
                "loose_equality",
                "Use === instead of == for equality checks",
                location,
                CodeSmellSeverity.MINOR
            )
    
    def _detect_project_duplications(self, project_metrics: ProjectMetrics) -> None:
        """Detect duplicated code across project files (simplified)"""
        # This would typically use a more sophisticated algorithm
        # For now, just aggregate file-level duplications
        duplicate_blocks = []
        
        # In a real implementation, we'd compare chunks across files
        # For now, just collect the duplicates already found
        for file_metrics in project_metrics.file_metrics:
            if file_metrics.duplicated_lines > 0:
                duplicate_blocks.append({
                    'file': file_metrics.file_path,
                    'lines': file_metrics.duplicated_lines
                })
        
        project_metrics.code_quality.duplicate_blocks = duplicate_blocks
    
    def _calculate_technical_debt(self, file_metrics: FileMetrics) -> None:
        """Calculate technical debt ratio based on code smells"""
        # Simple calculation: each code smell contributes to debt
        total_smells = len(file_metrics.code_smells_list)
        if total_smells == 0:
            file_metrics.code_smells.technical_debt_ratio = 0.0
            return
            
        # Weight smells by severity
        debt_score = 0
        for smell in file_metrics.code_smells_list:
            severity = smell.get('severity', 'minor')
            if severity == 'critical':
                debt_score += 10
            elif severity == 'major':
                debt_score += 5
            else:  # minor
                debt_score += 1
        
        # Calculate debt ratio (0.0 to 1.0, where higher is worse)
        file_metrics.code_smells.technical_debt_ratio = min(1.0, debt_score / (file_metrics.sloc or 1) * 0.02)
    
    def _get_line_number(self, content: str, position: int) -> Dict:
        """Get line number from position in the content"""
        lines = content[:position].split('\n')
        line = len(lines)
        column = len(lines[-1]) + 1
        return {
            'line': line,
            'column': column,
            'position': position
        }
    
    def _add_code_smell(
        self, 
        file_metrics: FileMetrics, 
        smell_type: str, 
        message: str, 
        location: Dict,
        severity: CodeSmellSeverity = CodeSmellSeverity.MINOR
    ) -> None:
        """Add a code smell to the file metrics"""
        smell = {
            'type': smell_type,
            'message': message,
            'location': location,
            'severity': self._severity_to_string(severity)
        }
        
        file_metrics.code_smells.smells.append(smell)
    
    def _severity_to_string(self, severity: CodeSmellSeverity) -> str:
        """Convert code smell severity to string"""
        if severity == CodeSmellSeverity.CRITICAL:
            return "critical"
        elif severity == CodeSmellSeverity.MAJOR:
            return "major"
        elif severity == CodeSmellSeverity.MINOR:
            return "minor"
        else:
            return "none" 