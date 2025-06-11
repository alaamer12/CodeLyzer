from __future__ import annotations

import math
import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Set, Protocol, Union

from codelyzer.config import DEFAULT_EXCLUDED_FILES, FileMetrics, ProjectMetrics, ComplexityLevel, FILE_SIZE_LIMIT, \
    TIMEOUT_SECONDS
from codelyzer.console import console
from codelyzer.utils import FunctionWithTimeout


class FileDiscovery(Protocol):
    """Interface for file discovery components"""

    def discover_files(self, root_path: str) -> List[str]:
        """Discover files to analyze in the given path"""
        ...

    def should_include_file(self, file_path: str) -> bool:
        """Determine if a file should be included in analysis"""
        ...

    def detect_language(self, file_path: str) -> Optional[str]:
        """Detect the programming language of a file"""
        ...


class CodeQualityAnalyzer(Protocol):
    """Interface for code quality analysis components"""

    def analyze(self, file_path: str, content: str, metrics: FileMetrics) -> None:
        """Analyze code quality aspects and update metrics"""
        ...


class MetricsProcessor(Protocol):
    """Interface for metrics processing components"""

    def process_metrics(self, project_metrics: ProjectMetrics) -> None:
        """Process and calculate derived metrics"""
        ...


# ===== Component Implementations =====

class StandardFileDiscovery:
    """Standard implementation of file discovery"""

    def __init__(self, exclude_dirs: Set[str], language_configs: Dict):
        self.exclude_dirs = exclude_dirs
        self.language_detectors = self._build_language_detectors(language_configs)

    @staticmethod
    def _build_language_detectors(language_configs: Dict) -> Dict[str, List[str]]:
        """Build file extension to language mapping"""
        detectors = {}
        for lang, config in language_configs.items():
            for ext in config['extensions']:
                if ext not in detectors:
                    detectors[ext] = []
                detectors[ext].append(lang)
        return detectors

    def discover_files(self, root_path: str) -> List[str]:
        """Discover all analyzable files in the given path"""
        all_files = []
        for root, dirs, files in os.walk(root_path):
            # Filter directories
            dirs[:] = [d for d in dirs if d not in self.exclude_dirs]

            for file in files:
                file_path = os.path.join(root, file)
                if self.detect_language(file_path) and self.should_include_file(file_path):
                    all_files.append(file_path)

        return all_files

    def should_include_file(self, file_path: str) -> bool:
        """Determine if a file should be included in analysis"""
        path = Path(file_path)

        # Check if any part of the path contains excluded directories
        for part in path.parts:
            if part in self.exclude_dirs:
                return False

        # Check excluded file patterns
        for pattern in DEFAULT_EXCLUDED_FILES:
            if path.match(pattern):
                return False

        return True

    def detect_language(self, file_path: str) -> Optional[str]:
        """Detect programming language from file extension"""
        ext = Path(file_path).suffix.lower()
        languages = self.language_detectors.get(ext, [])
        return languages[0] if languages else None


class SecurityAnalyzer:
    """Analyzes code for security vulnerabilities"""

    def __init__(self):
        self.security_patterns = self._build_security_patterns()

    @staticmethod
    def _build_security_patterns() -> Dict[str, List[str]]:
        """Build security vulnerability patterns"""
        return {
            'sql_injection': [
                r'(?i)execute\s*\(\s*["\'].*%.*["\']',
                r'(?i)query\s*\(\s*["\'].*\+.*["\']',
                r'(?i)cursor\.execute\s*\([^,)]*%',
            ],
            'xss': [
                r'(?i)innerHTML\s*=\s*.*\+',
                r'(?i)document\.write\s*\(',
                r'(?i)eval\s*\(',
            ],
            'hardcoded_secrets': [
                r'(?i)(password|pwd|secret|key)\s*=\s*["\'][^"\']{8,}["\']',
                r'(?i)(api_key|apikey|access_key)\s*=\s*["\'][^"\']{20,}["\']',
                r'(?i)(token|auth)\s*=\s*["\'][^"\']{30,}["\']',
            ],
            'unsafe_deserialization': [
                r'(?i)pickle\.load',
                r'(?i)yaml\.load\(',
                r'(?i)json\.loads.*input',
            ]
        }

    def analyze(self, file_path: str, content: str, metrics: FileMetrics) -> None:
        """Analyze code for security issues"""
        if not content:
            return

        security_issues = []

        # Check security patterns
        for category, patterns in self.security_patterns.items():
            for pattern in patterns:
                if re.search(pattern, content, re.MULTILINE | re.IGNORECASE):
                    security_issues.append(category)
                    break

        metrics.security_issues = security_issues


class CodeSmellAnalyzer:
    """Analyzes code for code smells"""

    def __init__(self):
        self.code_smell_patterns = self._build_code_smell_patterns()

    @staticmethod
    def _build_code_smell_patterns() -> dict[str, str]:
        """Build code smell patterns"""
        return {
            'long_methods': r'def\s+\w+.*:\s*\n(?:\s+.*\n){50,}',
            'duplicate_code': r'(.{50,})\n(?:.*\n)*?\1',
            'magic_numbers': r'\b(?<![\w.])\d{3,}\b(?![\w.])',
            'god_class': r'class\s+\w+.*:\s*\n(?:\s+.*\n){200,}',
            'feature_envy': r'(\w+)\.(\w+)\.(\w+)\.(\w+)',
        }

    def analyze(self, file_path: str, content: str, metrics: FileMetrics) -> None:
        """Analyze code for code smells"""
        if not content:
            return

        code_smells = []

        # Check code smell patterns
        for smell, pattern in self.code_smell_patterns.items():
            if re.search(pattern, content, re.MULTILINE):
                code_smells.append(smell)

        metrics.code_smells = code_smells


class ComplexityAnalyzer:
    """Analyzes code complexity"""

    def __init__(self, language_configs: Dict):
        self.language_configs = language_configs

    def analyze(self, file_path: str, content: str, metrics: FileMetrics) -> None:
        """Calculate complexity metrics"""
        if metrics.sloc == 0:
            return

        # Get complexity weights for the language
        config = self.language_configs.get(metrics.language, self.language_configs['python'])
        weights = config['complexity_weights']

        # Calculate complexity score
        metrics.complexity_score = (
                metrics.sloc * weights['loc'] +
                metrics.classes * weights['classes'] +
                metrics.functions * weights['functions'] +
                metrics.methods * weights['methods']
        )

        # Maintainability index (simplified)
        if metrics.sloc > 0:
            metrics.maintainability_index = max(0.0, 171 - 5.2 * math.log(metrics.sloc) -
                                                0.23 * (metrics.cyclomatic_complexity or 1) -
                                                16.2 * math.log(max(1, len(metrics.imports or []))))


class PatternBasedAnalyzer:
    """Generic pattern-based analyzer for languages without specialized analyzers"""

    def __init__(self, language_configs: Dict):
        self.language_configs = language_configs

    def analyze_file(self, file_path: str, language: str) -> Union[FileMetrics, tuple[FileMetrics, Optional[str]]]:
        """Analyze a file using pattern matching"""
        try:
            metrics = self._initialize_metrics(file_path, language)
            
            # Check file size first to avoid hanging on massive files
            if self._is_file_too_large(file_path):
                return self._create_metrics_for_large_file(metrics, file_path)
            
            content = self._read_file_content(file_path)
            if content is None:
                return metrics
            
            config = self._get_language_config(language)
            
            # Pattern matching with thread-based timeout
            patterns_result = self._perform_pattern_matching(content, config, metrics)
            
            if isinstance(patterns_result, (TimeoutError, Exception)):
                return self._handle_pattern_matching_failure(metrics, content)
            
            # Count lines and categorize them
            self._calculate_line_counts(content, metrics, config)
            
            return metrics, content
            
        except Exception as e:
            return self._handle_analysis_error(file_path, language, e)
    
    def _initialize_metrics(self, file_path: str, language: str) -> FileMetrics:
        """Initialize metrics object for a file"""
        return FileMetrics(file_path=file_path, language=language)
    
    def _is_file_too_large(self, file_path: str) -> bool:
        """Check if file exceeds the size limit"""
        file_size = os.path.getsize(file_path)
        return file_size > FILE_SIZE_LIMIT
    
    def _create_metrics_for_large_file(self, metrics: FileMetrics, file_path: str) -> FileMetrics:
        """Create metrics for files that are too large to process normally"""
        file_size = os.path.getsize(file_path)
        metrics.loc = metrics.sloc = file_size // 100  # Rough estimate
        return metrics
    
    def _read_file_content(self, file_path: str) -> Optional[str]:
        """Read file content with error handling"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        except Exception:
            return None
    
    def _get_language_config(self, language: str) -> Dict:
        """Get configuration for the specified language"""
        return self.language_configs.get(language, self.language_configs['python'])
    
    def _perform_pattern_matching(self, content: str, config: Dict, metrics: FileMetrics) -> Any:
        """Perform pattern matching with timeout protection"""
        def pattern_matching():
            try:
                patterns_found = 0
                for keyword in config['keywords']:
                    pattern = rf'\b{keyword}\b'
                    matches = re.findall(pattern, content, re.IGNORECASE)
                    patterns_found += len(matches)
                    
                    if keyword in ['def', 'function', 'func', 'fn']:
                        metrics.functions += len(matches)
                    elif keyword in ['class', 'struct', 'interface']:
                        metrics.classes += len(matches)
                return patterns_found
            except Exception:
                return 0
        
        timeout_runner = FunctionWithTimeout(timeout=TIMEOUT_SECONDS)
        return timeout_runner.run_with_timeout(pattern_matching)
    
    def _handle_pattern_matching_failure(self, metrics: FileMetrics, content: str) -> FileMetrics:
        """Handle timeout or exception in pattern matching"""
        try:
            lines = content.count('\n') + 1
            metrics.loc = metrics.sloc = lines
        except Exception:
            metrics.loc = metrics.sloc = 0
        return metrics
    
    def _handle_analysis_error(self, file_path: str, language: str, error: Exception) -> tuple[FileMetrics, Optional[str]]:
        """Handle exceptions during file analysis"""
        console.print(f"[yellow]Warning: Generic analysis failed for {file_path}: {str(error)}[/yellow]")
        metrics = FileMetrics(file_path=file_path, language=language)
        metrics.loc = metrics.sloc = 0
        return metrics, None

    @staticmethod
    def _calculate_line_counts(content: str, metrics: FileMetrics, config: Dict) -> None:
        """Count different types of lines"""
        if not content:
            metrics.loc = metrics.sloc = metrics.blanks = metrics.comments = 0
            return

        lines = content.split('\n')
        metrics.loc = len(lines)
        metrics.blanks = sum(1 for line in lines if not line.strip())

        # Count comment lines based on language patterns
        comment_lines = 0
        comment_patterns = [re.compile(pattern) for pattern in config['comment_patterns']]
        for line in lines:
            stripped = line.strip()
            if any(pattern.match(stripped) for pattern in comment_patterns):
                comment_lines += 1

        metrics.comments = comment_lines
        metrics.sloc = metrics.loc - metrics.blanks - metrics.comments


class ProjectMetricsProcessor:
    """Processes project metrics to calculate derived metrics"""

    def process_metrics(self, metrics: ProjectMetrics) -> None:
        """Calculate derived metrics and rankings"""
        if not metrics.file_metrics:
            return

        # Sort by complexity
        metrics.file_metrics.sort(key=lambda x: x.complexity_score, reverse=True)
        metrics.most_complex_files = metrics.file_metrics[:10]

        # Sort by size
        metrics.largest_files = sorted(metrics.file_metrics,
                                       key=lambda x: x.sloc, reverse=True)[:10]

        # Complexity distribution
        Scoring.calculate_complexity_distribution(metrics)

        # Quality scores
        Scoring.calculate_quality_scores(metrics)


class Scoring:
    """Class for handling code scoring and metrics aggregation"""

    @staticmethod
    def update_aggregate_metrics(project_metrics: ProjectMetrics, metrics: FileMetrics) -> ProjectMetrics:
        """Update aggregate metrics"""
        project_metrics.total_files += 1
        project_metrics.total_loc += metrics.loc or 0
        project_metrics.total_sloc += metrics.sloc or 0
        project_metrics.total_comments += metrics.comments or 0
        project_metrics.total_blanks += metrics.blanks or 0
        project_metrics.total_classes += metrics.classes or 0
        project_metrics.total_functions += metrics.functions or 0
        project_metrics.total_methods += metrics.methods or 0
        project_metrics.project_size += metrics.file_size or 0
        return project_metrics
    
    @staticmethod
    def calculate_complexity_distribution(metrics: ProjectMetrics) -> None:
        """Calculate complexity distribution across files"""
        for file_metrics in metrics.file_metrics:
            level = Scoring.determine_complexity_level(file_metrics.complexity_score)
            metrics.complexity_distribution[level] = metrics.complexity_distribution.get(level, 0) + 1

    @staticmethod
    def determine_complexity_level(score: float) -> ComplexityLevel:
        """Determine complexity level based on score"""
        if score < 50:
            return ComplexityLevel.TRIVIAL
        elif score < 200:
            return ComplexityLevel.LOW
        elif score < 500:
            return ComplexityLevel.MODERATE
        elif score < 1000:
            return ComplexityLevel.HIGH
        elif score < 2000:
            return ComplexityLevel.VERY_HIGH
        else:
            return ComplexityLevel.EXTREME

    @staticmethod
    def calculate_quality_scores(metrics: ProjectMetrics) -> None:
        """Calculate code quality scores"""
        if metrics.total_sloc <= 0:
            return

        # Code quality score
        metrics.code_quality_score = min(100, max(0,
                                                  int(100 - (sum(len(f.security_issues) + len(f.code_smells)
                                                                 for f in
                                                                 metrics.file_metrics) / metrics.total_files * 10))))

        # Maintainability score
        avg_maintainability = sum(f.maintainability_index for f in metrics.file_metrics) / len(metrics.file_metrics)
        metrics.maintainability_score = max(0, min(100, int(avg_maintainability)))
