import os
import concurrent.futures
from abc import ABC, abstractmethod
from typing import Any, ClassVar, Dict, List, Optional, Type
from tree_sitter import Language, Parser

from codelyzer.config import PARSE_TIMEOUT, FILE_SIZE_LIMIT
from codelyzer.console import console
from codelyzer.metrics import FileMetrics, BaseFileMetrics, MetricProvider

# Import tree-sitter and language packages
try:
    import tree_sitter_python
    import tree_sitter_javascript
    TREE_SITTER_AVAILABLE = True
except ImportError:
    TREE_SITTER_AVAILABLE = False


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
                    provider.analyze_file(metrics, content, ast_data)

            except Exception as e:
                self._handle_metrics_calculation_error(metrics, content, e)

            # Calculate common metrics like lines of code if not already set
            if metrics.base.loc == 0:
                self._calculate_line_counts(content, metrics)

            return metrics

        except Exception as e:
            # Return minimal metrics object rather than None
            return self._handle_analysis_error(file_path, e)

    @staticmethod
    def _is_file_too_large(file_path: str) -> bool:
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

    @staticmethod
    def _read_file_content(file_path: str) -> Optional[str]:
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

    @staticmethod
    def _handle_metrics_calculation_error(metrics: FileMetrics, content: str, error: Exception) -> None:
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


class TreeSitterASTAnalyzer(ASTAnalyzer, ABC):
    """Base class for analyzers that use tree-sitter"""

    # Will be set by subclasses
    language_parser: Optional[Parser] = None
    language_name: str = ""
    language_module = None  # Reference to the language module (tree_sitter_python, etc.)

    # Comment node types specific to the language
    comment_types: List[str] = []

    @classmethod
    def initialize_parser(cls):
        """Initialize the tree-sitter parser for this language"""
        if cls.language_parser is not None:
            return  # Already initialized

        if not TREE_SITTER_AVAILABLE:
            console.print(f"[red]Error: tree-sitter or language modules not available[/red]")
            cls.language_parser = None
            return

        try:
            # Get language function from the module
            if cls.language_module is None:
                console.print(f"[red]Error: No language module specified for {cls.language_name}[/red]")
                cls.language_parser = None
                return
                
            # Create Language object using the module's language function
            language = Language(cls.language_module.language())
            parser = Parser()
            parser.language = language
            cls.language_parser = parser
            console.print(f"[green]Successfully initialized {cls.language_name} parser[/green]")
        except Exception as e:
            console.print(f"[red]Error initializing {cls.language_name} parser: {str(e)}[/red]")
            cls.language_parser = None

    def _parse_with_timeout(self, content: str, file_path: str) -> Any:
        """Parse the file content into an AST with timeout handling"""
        if self.language_parser is None:
            self.__class__.initialize_parser()
            if self.language_parser is None:
                return Exception(f"Parser for {self.language_name} could not be initialized")

        # Define a function to do the parsing
        def parse_content():
            try:
                tree = self.language_parser.parse(bytes(content, 'utf8'))
                return tree
            except Exception as e:
                return e

        # Execute with timeout
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(parse_content)
            try:
                return future.result(timeout=PARSE_TIMEOUT)
            except (concurrent.futures.TimeoutError, Exception) as e:
                console.print(f"[yellow]Warning: Parsing {file_path} timed out or failed[/yellow]")
                return e

    def _count_comment_lines(self, content: str) -> int:
        """Count comment lines using tree-sitter"""
        try:
            if self.language_parser is None:
                self.__class__.initialize_parser()
                if self.language_parser is None:
                    return 0

            tree = self.language_parser.parse(bytes(content, 'utf8'))
            root_node = tree.root_node

            comment_lines = set()

            def process_node(node):
                if node.type in self.comment_types:
                    start_line = node.start_point[0]
                    end_line = node.end_point[0]
                    for line in range(start_line, end_line + 1):
                        comment_lines.add(line)

                for child in node.children:
                    process_node(child)

            process_node(root_node)
            return len(comment_lines)

        except Exception as e:
            console.print(f"[yellow]Warning: Error counting comment lines: {str(e)}[/yellow]")
            return 0


class PythonASTAnalyzer(TreeSitterASTAnalyzer):
    """Analyzer for Python files using tree-sitter"""

    extensions = ['.py']
    language_name = "python"
    language_module = tree_sitter_python if TREE_SITTER_AVAILABLE else None
    comment_types = ["comment", "string"]  # Python docstrings are string nodes

    def __init__(self):
        """Initialize the Python analyzer"""
        self.__class__.initialize_parser()

    @classmethod
    def _get_language_name(cls) -> str:
        return "python"

    def _calculate_metrics(self, ast_data: Any, metrics: FileMetrics, content: str = None) -> None:
        """Calculate Python-specific metrics from the tree-sitter AST"""
        if ast_data is None or isinstance(ast_data, Exception):
            return

        root_node = ast_data.root_node

        # Initialize counters
        class_count = 0
        function_count = 0
        method_count = 0
        import_count = 0

        # Process the AST
        def process_node(node):
            nonlocal class_count, function_count, method_count, import_count

            if node.type == "class_definition":
                class_count += 1
            elif node.type == "function_definition":
                # Check if this is a method (child of a class)
                is_method = False
                parent = node.parent
                while parent:
                    if parent.type == "class_definition":
                        is_method = True
                        break
                    parent = parent.parent

                if is_method:
                    method_count += 1
                else:
                    function_count += 1
            elif node.type in ["import_statement", "import_from_statement"]:
                import_count += 1

            # Process children
            for child in node.children:
                process_node(child)

        # Start processing from root
        process_node(root_node)

        # Update metrics
        metrics.base.classes = class_count
        metrics.base.functions = function_count + method_count
        metrics.base.imports = import_count

        # Calculate cyclomatic complexity - count branches
        complexity = self._calculate_cyclomatic_complexity(root_node)
        metrics.base.complexity_score = complexity

    @staticmethod
    def _calculate_cyclomatic_complexity(root_node: Any) -> int:
        """Calculate cyclomatic complexity for Python code"""
        complexity = 1  # Start with 1

        # Branch keywords and operators
        branch_types = [
            "if_statement", "elif_clause", "else_clause",
            "for_statement", "while_statement",
            "try_statement", "except_clause", "finally_clause",
            "and", "or", "conditional_expression"
        ]

        def traverse(node):
            nonlocal complexity

            if node.type in branch_types:
                complexity += 1

            for child in node.children:
                traverse(child)

        traverse(root_node)
        return complexity


class JavaScriptASTAnalyzer(TreeSitterASTAnalyzer):
    """Analyzer for JavaScript/TypeScript files using tree-sitter"""

    extensions = ['.js', '.jsx', '.ts', '.tsx']
    language_name = "javascript"
    language_module = tree_sitter_javascript if TREE_SITTER_AVAILABLE else None
    comment_types = ["comment", "comment_block", "jsx_comment", "multiline_comment"]

    def __init__(self):
        """Initialize the JavaScript analyzer"""
        self.__class__.initialize_parser()

    @classmethod
    def _get_language_name(cls) -> str:
        """Return specific language name based on file extension"""
        return "javascript"  # Base language name, more specific detection in _detect_language

    def _detect_language(self, file_path: str) -> str:
        """Detect specific JS variant from file extension"""
        ext = os.path.splitext(file_path)[1].lower()
        if ext == '.jsx':
            return "jsx"
        elif ext == '.ts':
            return "typescript"
        elif ext == '.tsx':
            return "tsx"
        return "javascript"

    def _calculate_metrics(self, ast_data: Any, metrics: FileMetrics, content: str = None) -> None:
        """Calculate JavaScript-specific metrics from the tree-sitter AST"""
        if ast_data is None or isinstance(ast_data, Exception):
            return

        root_node = ast_data.root_node

        # Initialize counters
        class_count = 0
        function_count = 0
        import_count = 0

        # Process the AST
        def process_node(node):
            nonlocal class_count, function_count, import_count

            if node.type == "class_declaration":
                class_count += 1
            elif node.type in ["function_declaration", "arrow_function", "method_definition",
                               "generator_function_declaration", "function"]:
                function_count += 1
            elif node.type in ["import_statement", "import_declaration"]:
                import_count += 1

            # Process children
            for child in node.children:
                process_node(child)

        # Start processing from root
        process_node(root_node)

        # Update metrics
        metrics.base.classes = class_count
        metrics.base.functions = function_count
        metrics.base.imports = import_count

        # Calculate cyclomatic complexity
        complexity = self._calculate_cyclomatic_complexity(root_node)
        metrics.base.complexity_score = complexity

    @staticmethod
    def _calculate_cyclomatic_complexity(root_node: Any) -> int:
        """Calculate cyclomatic complexity for JavaScript/TypeScript code"""
        complexity = 1  # Start with 1

        # Branch keywords and operators
        branch_types = [
            "if_statement", "else_clause",
            "for_statement", "for_in_statement", "for_of_statement",
            "while_statement", "do_statement",
            "try_statement", "catch_clause", "finally_clause",
            "case_statement", "switch_statement",
            "&&", "||", "?", "ternary_expression"
        ]

        def traverse(node):
            nonlocal complexity

            if node.type in branch_types:
                complexity += 1

            for child in node.children:
                traverse(child)

        traverse(root_node)
        return complexity


# Initialize the analyzers
def initialize_analyzers():
    """Initialize all tree-sitter analyzers"""
    if not TREE_SITTER_AVAILABLE:
        console.print("[yellow]Warning: tree-sitter or language modules not available.[/yellow]")
        console.print("[yellow]Install them with: pip install tree-sitter tree-sitter-python tree-sitter-javascript[/yellow]")
        return
    
    PythonASTAnalyzer.initialize_parser()
    JavaScriptASTAnalyzer.initialize_parser()
    console.print("[green]Initialized tree-sitter parsers for: Python, JavaScript[/green]")


if __name__ == "__main__":
    analyzer = JavaScriptASTAnalyzer()
    metrics = analyzer.analyze_file("test.js")
    print(metrics)
