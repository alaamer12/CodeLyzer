import os
from abc import ABC, abstractmethod
from typing import Optional, Type, ClassVar, Dict, List, Any

from codelyzer.config import BaseFileMetrics, FileMetrics, FILE_SIZE_LIMIT, MetricProvider
from codelyzer.console import console


class ASTAnalyzer(ABC):
    """Base class for language-specific AST analyzers"""

    # Class attribute mapping file extension to analyzer class
    ANALYZERS: ClassVar[Dict[str, Type['ASTAnalyzer']]] = {}

    # Class attribute for extensions supported by this analyzer
    extensions: ClassVar[List[str]] = []
    
    # Class attribute for metric providers
    metric_providers: ClassVar[List[MetricProvider]] = []

    def __init_subclass__(cls, **kwargs):
        """Register each analyzer subclass with its supported extensions"""
        super().__init_subclass__(**kwargs)
        for ext in cls.extensions:
            ASTAnalyzer.ANALYZERS[ext] = cls

    @classmethod
    def get_analyzer_for_extension(cls, extension: str) -> Optional[Type['ASTAnalyzer']]:
        """Factory method to get the appropriate analyzer for a file extension"""
        return cls.ANALYZERS.get(extension.lower())
    
    @classmethod
    def register_metric_provider(cls, provider: MetricProvider) -> None:
        """Register a metric provider for all analyzers"""
        if provider not in cls.metric_providers:
            cls.metric_providers.append(provider)

    def analyze_file(self, file_path: str) -> Optional[FileMetrics]:
        """Analyze a file and return its metrics - common implementation with template pattern"""
        try:
            # Check file size first to avoid hanging on massive files
            if self._is_file_too_large(file_path):
                return self._create_metrics_for_large_file(file_path)

            # Read file content with appropriate error handling
            content = self._read_file_content(file_path)
            if content is None:
                return self._create_empty_metrics(file_path)

            # Parse AST with thread-based timeout - language specific
            ast_data = self._parse_with_timeout(content, file_path)

            # Handle parsing errors
            if isinstance(ast_data, Exception):
                return self._create_metrics_from_content(file_path, content)

            # Initialize metrics
            metrics = self._create_metrics_for_file(file_path)

            # Calculate AST-based metrics - language specific
            try:
                # Calculate core metrics first
                self._calculate_metrics(ast_data, metrics, content)
                
                # Run all registered metric providers
                for provider in self.metric_providers:
                    provider.provide_file_metrics(metrics, content, ast_data)
                
            except Exception as e:
                self._handle_metrics_calculation_error(metrics, content, e)

            # Calculate common metrics like lines of code if not already set
            if metrics.base.loc == 0:
                self._calculate_line_counts(content, metrics)

            return metrics

        except Exception as e:
            # Return minimal metrics object rather than None
            return self._handle_analysis_error(file_path, e)
    
    def _is_file_too_large(self, file_path: str) -> bool:
        """Check if file exceeds the size limit"""
        file_size = os.path.getsize(file_path)
        return file_size > FILE_SIZE_LIMIT
    
    def _create_metrics_for_large_file(self, file_path: str) -> FileMetrics:
        """Create metrics for files that are too large to process normally"""
        metrics = self._create_metrics_for_file(file_path)
        file_size = os.path.getsize(file_path)
        metrics.base.loc = metrics.base.sloc = file_size // 100  # Rough estimate
        metrics.base.file_size = file_size
        return metrics
    
    def _read_file_content(self, file_path: str) -> Optional[str]:
        """Read file content with error handling"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        except Exception:
            return None
    
    def _create_empty_metrics(self, file_path: str) -> FileMetrics:
        """Create metrics for files that couldn't be read"""
        metrics = self._create_metrics_for_file(file_path)
        metrics.base.loc = metrics.base.sloc = 0
        return metrics
    
    def _create_metrics_from_content(self, file_path: str, content: str) -> FileMetrics:
        """Create metrics based on content when AST parsing fails"""
        metrics = self._create_metrics_for_file(file_path)
        lines = content.count('\n') + 1
        metrics.base.loc = metrics.base.sloc = lines
        return metrics
    
    def _handle_metrics_calculation_error(self, metrics: FileMetrics, content: str, error: Exception) -> None:
        """Handle errors during metrics calculation"""
        lines = content.count('\n') + 1
        metrics.base.loc = metrics.base.sloc = lines
        console.print(f"[yellow]Warning: Error calculating metrics: {str(error)}[/yellow]")
    
    def _handle_analysis_error(self, file_path: str, error: Exception) -> FileMetrics:
        """Handle general errors during file analysis"""
        console.print(f"[yellow]Warning: Error analyzing {file_path}: {str(error)}[/yellow]")
        metrics = self._create_metrics_for_file(file_path)
        metrics.base.loc = metrics.base.sloc = 0
        return metrics

    def _calculate_line_counts(self, content: str, metrics: FileMetrics) -> None:
        """Count different types of lines in the file content"""
        if not content:
            metrics.base.loc = metrics.base.sloc = metrics.base.blanks = metrics.base.comments = 0
            return

        lines = content.split('\n')
        metrics.base.loc = len(lines)
        metrics.base.blanks = sum(1 for line in lines if not line.strip())

        # Comments need to be counted by language-specific logic
        comment_lines = self._count_comment_lines(content)
        metrics.base.comments = comment_lines
        metrics.base.sloc = metrics.base.loc - metrics.base.blanks - metrics.base.comments

    def _create_metrics_for_file(self, file_path: str) -> FileMetrics:
        """Create a FileMetrics object with the appropriate language"""
        language = self._detect_language(file_path)
        file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
        last_modified = os.path.getmtime(file_path) if os.path.exists(file_path) else 0
        
        base_metrics = BaseFileMetrics(
            file_path=file_path,
            language=language,
            file_size=file_size,
            last_modified=last_modified
        )
        return FileMetrics(base=base_metrics)

    def _detect_language(self, file_path: str) -> str:
        """Detect language from file extension - can be overridden if needed"""
        ext = os.path.splitext(file_path)[1].lower()
        for language_class in ASTAnalyzer.ANALYZERS.values():
            if ext in language_class.extensions:
                return language_class._get_language_name()
        return "unknown"

    @classmethod
    def _get_language_name(cls) -> str:
        """Return the name of the language this analyzer handles"""
        return cls.__name__.replace('ASTAnalyzer', '').lower()

    @abstractmethod
    def _parse_with_timeout(self, content: str, file_path: str) -> Any:
        """Parse the file content into an AST with timeout handling"""
        pass

    @abstractmethod
    def _calculate_metrics(self, ast_data: Any, metrics: FileMetrics, content: str = None) -> None:
        """Calculate language-specific metrics from the AST"""
        pass

    @abstractmethod
    def _count_comment_lines(self, content: str) -> int:
        """Count comment lines in the file content"""
        pass


class PythonASTAnalyzer(ASTAnalyzer):
    """Analyzer for Python files using the Abstract Syntax Tree"""

    extensions = ['.py']

    @classmethod
    def _get_language_name(cls) -> str:
        return "python"

    


class JavaScriptASTAnalyzer(ASTAnalyzer):
    """Analyzer for JavaScript/TypeScript files using Abstract Syntax Tree"""

    extensions = ['.js', '.jsx', '.ts', '.tsx']

    @classmethod
    def _get_language_name(cls) -> str:
        return "javascript"  # Base language name, more specific detection in _detect_language

if __name__ == "__main__":
    analyzer = JavaScriptASTAnalyzer()
    metrics = analyzer.analyze_file("test.js")
    print(metrics)
