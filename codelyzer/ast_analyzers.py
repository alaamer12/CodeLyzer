import os
import concurrent.futures
from abc import ABC, abstractmethod
from typing import Any, ClassVar, Dict, List, Optional, Type
from tree_sitter import Language, Parser

from codelyzer.config import PARSE_TIMEOUT, FILE_SIZE_LIMIT
from codelyzer.console import console
from codelyzer.metrics import FileMetricCategory, FileMetrics, BaseFileMetrics, MetricProvider

# Import tree-sitter and language packages
try:
    import tree_sitter_python
    import tree_sitter_javascript
    import tree_sitter_typescript
    TREE_SITTER_AVAILABLE = True
except ImportError:
    tree_sitter_python = None
    tree_sitter_javascript = None
    tree_sitter_typescript = None
    tree_sitter_rust = None
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
            # Check if the file is a TypeScript definition file (.d.ts) - these often need special handling
            if file_path.endswith('.d.ts'):
                return self._analyze_definition_file(file_path)
                
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
        
        # Accurately count lines for large files without reading the whole file into memory
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                loc = sum(1 for _ in f)
            metrics.base.loc = loc
            metrics.base.sloc = loc  # Estimate SLOC as LOC for very large files
        except Exception:
            # Fallback to estimation if line counting fails
            metrics.base.loc = metrics.base.sloc = file_size // 100
            
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
        comment_lines = self._count_comment_lines(content, metrics.base.file_path)
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
    def _count_comment_lines(self, content: str, file_path: str) -> int:
        """Count comment lines in the file content"""
        pass

    def _analyze_definition_file(self, file_path: str) -> FileMetrics:
        """Override for TypeScript-specific definition file analysis"""
        metrics = self._create_metrics_for_file(file_path)
        file_size = os.path.getsize(file_path)
        metrics.base.file_size = file_size
        
        try:
            # Count total lines first to ensure accurate LOC reporting
            total_line_count = 0
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                total_line_count = sum(1 for _ in f)
            
            # Special handling for very large definition files
            if total_line_count > 5000:  # Threshold for "large" definition files
                # # Just log the correct count and update metrics
                # console.print(f"[green]Processed TypeScript definition file {file_path} with {total_line_count} lines[/green]")
                
                # Use a conservative estimation for blank and comment lines
                blank_lines = int(total_line_count * 0.1)  # Estimate 10% blank lines
                comment_lines = int(total_line_count * 0.4)  # Estimate 40% comment lines
                
                # Update metrics with accurate counts
                metrics.base.loc = total_line_count
                metrics.base.blanks = blank_lines
                metrics.base.comments = comment_lines
                metrics.base.sloc = total_line_count - blank_lines - comment_lines
                
                # Add some complexity based on total size
                interface_count = int(total_line_count / 100)
                type_count = int(total_line_count / 150)
                function_count = int(total_line_count / 200)
                
                # Structure metrics
                metrics.structure.functions = function_count
                
                # Add TypeScript specific metrics
                ts_metrics = FileMetricCategory()
                ts_metrics.add_metric("interfaces", interface_count)
                ts_metrics.add_metric("types", type_count)
                metrics.add_custom_metric_category("typescript", ts_metrics)
                
                # Complexity metrics - use a formula that makes sense for definition files
                metrics.complexity.cyclomatic_complexity = interface_count + type_count + function_count
                metrics.complexity.complexity_score = float(interface_count * 2 + type_count + function_count)
                
                return metrics
            
            # For regular-sized files, use the standard line-by-line approach
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                # Initialize counters
                loc = total_line_count  # Set to total line count from initial pass
                blank_lines = 0
                comment_lines = 0
                interface_count = 0
                type_count = 0
                function_count = 0
                
                # Simple state tracking
                in_multiline_comment = False
                
                # Process the file line by line
                for line in f:
                    stripped_line = line.strip()
                    
                    # Track blank lines
                    if not stripped_line:
                        blank_lines += 1
                        continue
                        
                    # Track comments
                    if in_multiline_comment:
                        comment_lines += 1
                        if '*/' in stripped_line:
                            in_multiline_comment = False
                        continue
                        
                    if stripped_line.startswith('//'):
                        comment_lines += 1
                        continue
                        
                    if stripped_line.startswith('/*'):
                        comment_lines += 1
                        if '*/' not in stripped_line:
                            in_multiline_comment = True
                        continue
                    
                    # Count TypeScript constructs
                    if 'interface ' in stripped_line:
                        interface_count += 1
                    elif 'type ' in stripped_line and '=' in stripped_line:
                        type_count += 1
                    elif 'function ' in stripped_line or 'method(' in stripped_line:
                        function_count += 1
                
                # Update metrics with accurate counts
                metrics.base.loc = loc
                metrics.base.blanks = blank_lines
                metrics.base.comments = comment_lines
                metrics.base.sloc = loc - blank_lines - comment_lines
                
                # Structure metrics
                metrics.structure.functions = function_count
                
                # Add TypeScript specific metrics
                ts_metrics = FileMetricCategory()
                ts_metrics.add_metric("interfaces", interface_count)
                ts_metrics.add_metric("types", type_count)
                metrics.add_custom_metric_category("typescript", ts_metrics)
                
                # Complexity metrics - use a formula that makes sense for definition files
                metrics.complexity.cyclomatic_complexity = interface_count + type_count + function_count
                metrics.complexity.complexity_score = float(interface_count * 2 + type_count + function_count)
                
            # console.print(f"[green]Processed TypeScript definition file {file_path} with {loc} lines[/green]")
            
        except Exception as e:
            console.print(f"[yellow]Warning: Error analyzing TypeScript definition file {file_path}: {str(e)}[/yellow]")
            # Fall back to basic estimation
            metrics.base.loc = metrics.base.sloc = file_size // 40  # More accurate estimate for .d.ts files
            
        return metrics


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

    def _count_comment_lines(self, content: str, file_path: str) -> int:
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

        # Extract structure metrics (classes, functions, methods, imports)
        structure_metrics = self._extract_structure_metrics(root_node)
        
        # Update structure metrics
        self._update_structure_metrics(metrics, structure_metrics)
        
        # Calculate and update complexity metrics
        self._update_complexity_metrics(metrics, root_node)
    
    def _extract_structure_metrics(self, root_node: Any) -> Dict[str, Any]:
        """Extract structural metrics from the AST"""
        class_count = 0
        function_count = 0
        method_count = 0
        imports_list = []

        def process_node(node):
            nonlocal class_count, function_count, method_count, imports_list

            if node.type == "class_definition":
                class_count += 1
            elif node.type == "function_definition":
                if self._is_method(node):
                    method_count += 1
                else:
                    function_count += 1
            elif node.type in ["import_statement", "import_from_statement"]:
                imports_list.append(node.text.decode('utf8').split('\n')[0])

            # Process children
            for child in node.children:
                process_node(child)

        # Start processing from root
        process_node(root_node)

        return {
            'classes': class_count,
            'functions': function_count,
            'methods': method_count,
            'imports': imports_list
        }
    
    @staticmethod
    def _is_method(node: Any) -> bool:
        """Determine if a function definition is a method (inside a class)"""
        parent = node.parent
        while parent:
            if parent.type == "class_definition":
                return True
            parent = parent.parent
        return False
    
    @staticmethod
    def _update_structure_metrics(metrics: FileMetrics, structure_metrics: Dict[str, Any]) -> None:
        """Update the metrics object with structure metrics"""
        metrics.structure.classes = structure_metrics['classes']
        metrics.structure.functions = structure_metrics['functions']
        metrics.structure.methods = structure_metrics['methods']
        metrics.structure.imports = structure_metrics['imports']
    
    def _update_complexity_metrics(self, metrics: FileMetrics, root_node: Any) -> None:
        """Calculate and update complexity metrics"""
        complexity = self._calculate_cyclomatic_complexity(root_node)
        metrics.complexity.cyclomatic_complexity = complexity
        metrics.complexity.complexity_score = float(complexity)

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
    """Analyzer for JavaScript files using tree-sitter"""

    extensions = ['.js', '.jsx']
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
        return "javascript"

    def _calculate_metrics(self, ast_data: Any, metrics: FileMetrics, content: str = None) -> None:
        """Calculate JavaScript-specific metrics from the tree-sitter AST"""
        if ast_data is None or isinstance(ast_data, Exception):
            return

        root_node = ast_data.root_node

        # Initialize counters
        class_count = 0
        function_count = 0
        imports_list = []

        # Process the AST
        def process_node(node):
            nonlocal class_count, function_count, imports_list

            if node.type == "class_declaration":
                class_count += 1
            elif node.type in ["function_declaration", "arrow_function", "method_definition",
                               "generator_function_declaration", "function"]:
                function_count += 1
            elif node.type in ["import_statement", "import_declaration"]:
                imports_list.append(node.text.decode('utf8').split('\n')[0])

            # Process children
            for child in node.children:
                process_node(child)

        # Start processing from root
        process_node(root_node)

        # Update metrics
        metrics.structure.classes = class_count
        metrics.structure.functions = function_count
        metrics.structure.imports = imports_list

        # Calculate cyclomatic complexity
        complexity = self._calculate_cyclomatic_complexity(root_node)
        metrics.complexity.cyclomatic_complexity = complexity
        metrics.complexity.complexity_score = float(complexity)

    @staticmethod
    def _calculate_cyclomatic_complexity(root_node: Any) -> int:
        """Calculate cyclomatic complexity for JavaScript code"""
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


class TypeScriptASTAnalyzer(TreeSitterASTAnalyzer):
    """Analyzer for TypeScript files using tree-sitter"""

    extensions = ['.ts', '.tsx', '.d.ts']  # Explicitly add .d.ts
    language_name = "typescript"
    # TypeScript module provides separate language objects for ts and tsx
    language_module = None  # Will be set in _parse_with_timeout based on file extension
    comment_types = ["comment", "comment_block", "jsx_comment", "multiline_comment"]

    def __init__(self):
        """Initialize the TypeScript analyzer"""
        self._ts_parser: Optional[Parser] = None
        self._tsx_parser: Optional[Parser] = None

    @classmethod
    def _get_language_name(cls) -> str:
        """Return specific language name based on file extension"""
        return "typescript"  # Base language name, more specific detection in _detect_language

    def _detect_language(self, file_path: str) -> str:
        """Detect specific TS variant from file extension"""
        ext = os.path.splitext(file_path)[1].lower()
        if ext == '.tsx':
            return "tsx"
        elif ext == '.d.ts':
            return "typescript-def"
        return "typescript"

    def _parse_with_timeout(self, content: str, file_path: str) -> Any:
        """Parse the file content into an AST with timeout handling"""
        ext = os.path.splitext(file_path)[1].lower()
        parser: Optional[Parser] = None

        try:
            if ext == '.tsx':
                if self._tsx_parser is None:
                    language = Language(tree_sitter_typescript.language_tsx())
                    self._tsx_parser = Parser()
                    self._tsx_parser.language = language
                parser = self._tsx_parser
            else:
                if self._ts_parser is None:
                    language = Language(tree_sitter_typescript.language_typescript())
                    self._ts_parser = Parser()
                    self._ts_parser.language = language
                parser = self._ts_parser
        except Exception as e:
            lang_name = "TSX" if ext == ".tsx" else "TypeScript"
            console.print(f"[red]Error initializing {lang_name} parser: {str(e)}[/red]")
            return Exception(f"Parser for {lang_name} could not be initialized: {str(e)}")

        if parser is None:
            return Exception(f"Parser for {file_path} could not be obtained.")

        # Define a function to do the parsing
        def parse_content():
            try:
                tree = parser.parse(bytes(content, 'utf8'))
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

    def _calculate_metrics(self, ast_data: Any, metrics: FileMetrics, content: str = None) -> None:
        """Calculate TypeScript-specific metrics from the tree-sitter AST"""
        if ast_data is None or isinstance(ast_data, Exception):
            return

        root_node = ast_data.root_node

        # Initialize counters
        class_count = 0
        function_count = 0
        interface_count = 0
        type_count = 0
        imports_list = []

        # Process the AST
        def process_node(node):
            nonlocal class_count, function_count, interface_count, type_count, imports_list

            if node.type == "class_declaration":
                class_count += 1
            elif node.type in ["function_declaration", "arrow_function", "method_definition",
                               "generator_function_declaration", "function"]:
                function_count += 1
            elif node.type == "interface_declaration":
                interface_count += 1
            elif node.type == "type_alias_declaration":
                type_count += 1
            elif node.type in ["import_statement", "import_declaration"]:
                imports_list.append(node.text.decode('utf8').split('\n')[0])

            # Process children
            for child in node.children:
                process_node(child)

        # Start processing from root
        process_node(root_node)

        # Update metrics
        metrics.structure.classes = class_count
        metrics.structure.functions = function_count
        metrics.structure.imports = imports_list
        
        # Add TypeScript specific metrics as custom metrics
        ts_metrics = FileMetricCategory()
        ts_metrics.add_metric("interfaces", interface_count)
        ts_metrics.add_metric("types", type_count)
        metrics.add_custom_metric_category("typescript", ts_metrics)

        # Calculate cyclomatic complexity
        complexity = self._calculate_cyclomatic_complexity(root_node)
        metrics.complexity.cyclomatic_complexity = complexity
        metrics.complexity.complexity_score = float(complexity)

    @staticmethod
    def _calculate_cyclomatic_complexity(root_node: Any) -> int:
        """Calculate cyclomatic complexity for TypeScript code"""
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

    def _count_comment_lines(self, content: str, file_path: str) -> int:
        """Count comment lines using tree-sitter, choosing the correct parser."""
        ext = os.path.splitext(file_path)[1].lower()
        parser: Optional[Parser] = None

        try:
            if ext == '.tsx':
                if self._tsx_parser is None:
                    language = Language(tree_sitter_typescript.language_tsx())
                    self._tsx_parser = Parser()
                    self._tsx_parser.language = language
                parser = self._tsx_parser
            else:
                if self._ts_parser is None:
                    language = Language(tree_sitter_typescript.language_typescript())
                    self._ts_parser = Parser()
                    self._ts_parser.language = language
                parser = self._ts_parser
        except Exception:
            return 0  # Fail silently, parser init errors are already logged.

        if parser is None:
            return 0

        try:
            tree = parser.parse(bytes(content, 'utf8'))
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
            console.print(f"[yellow]Warning: Error counting comment lines in {file_path}: {str(e)}[/yellow]")
            return 0


class RustStubASTAnalyzer(ASTAnalyzer):
    """Stub analyzer for Rust files when tree-sitter-rust is incompatible"""

    extensions = ['.rs']
    
    def __init__(self):
        """Initialize the Rust stub analyzer"""
        console.print("[yellow]Using stub analyzer for Rust due to compatibility issues[/yellow]")
        console.print("[yellow]This will provide basic metrics without AST analysis[/yellow]")
    
    @classmethod
    def _get_language_name(cls) -> str:
        return "rust"
    
    def _parse_with_timeout(self, content: str, file_path: str) -> Any:
        """Return None since we can't parse the AST"""
        return None
    
    def _calculate_metrics(self, ast_data: Any, metrics: FileMetrics, content: str = None) -> None:
        """Calculate basic metrics without AST analysis"""
        # We can still calculate some basic metrics from the content
        if content:
            # Count functions by looking for 'fn' keyword
            fn_count = content.count("\nfn ")
            metrics.structure.functions = fn_count
            
            # Count structs by looking for 'struct' keyword
            struct_count = content.count("\nstruct ")
            
            # Count impls by looking for 'impl' keyword
            impl_count = content.count("\nimpl ")
            
            # Count traits by looking for 'trait' keyword
            trait_count = content.count("\ntrait ")
            
            # Use structs + traits as a rough estimate for "classes"
            metrics.structure.classes = struct_count + trait_count
            
            # Count imports by looking for 'use' statements
            import_count = content.count("\nuse ")
            metrics.structure.imports = [f"use_statement_{i+1}" for i in range(import_count)]
            
            # Add Rust specific metrics
            rust_metrics = FileMetricCategory()
            rust_metrics.add_metric("structs", struct_count)
            rust_metrics.add_metric("traits", trait_count)
            rust_metrics.add_metric("impls", impl_count)
            metrics.add_custom_metric_category("rust", rust_metrics)
            
            # Very rough complexity estimate based on control flow keywords
            complexity = 1
            complexity += content.count("if ")
            complexity += content.count("else ")
            complexity += content.count("match ")
            complexity += content.count("for ")
            complexity += content.count("while ")
            complexity += content.count("loop ")
            metrics.complexity.cyclomatic_complexity = complexity
            metrics.complexity.complexity_score = float(complexity)
    
    def _count_comment_lines(self, content: str, file_path: str) -> int:
        """Count comment lines by simple text analysis"""
        if not content:
            return 0
        
        lines = content.split('\n')
        comment_count = 0
        
        for line in lines:
            line = line.strip()
            if line.startswith('//') or line.startswith('/*') or line.endswith('*/'):
                comment_count += 1
        
        return comment_count


# Initialize the analyzers
def initialize_analyzers():
    """Initialize all tree-sitter analyzers"""
    if not TREE_SITTER_AVAILABLE:
        console.print("[yellow]Warning: tree-sitter or language modules not available.[/yellow]")
        console.print("[yellow]Install them with: pip install tree-sitter tree-sitter-python tree-sitter-javascript[/yellow]")
        console.print("[yellow]For TypeScript and Rust, consider using tree-sitter-languages for better compatibility:[/yellow]")
        console.print("[yellow]pip install tree-sitter-languages[/yellow]")
        return
    
    try:
        PythonASTAnalyzer.initialize_parser()
        console.print("[green]Initialized tree-sitter parser for Python[/green]")
    except Exception as e:
        console.print(f"[red]Failed to initialize Python parser: {str(e)}[/red]")
    
    try:
        JavaScriptASTAnalyzer.initialize_parser()
        console.print("[green]Initialized tree-sitter parser for JavaScript[/green]")
    except Exception as e:
        console.print(f"[red]Failed to initialize JavaScript parser: {str(e)}[/red]")
    
    # TypeScript parser is initialized when needed
    console.print("[blue]TypeScript parser will be initialized when needed[/blue]")
    
    # Use RustStubASTAnalyzer instead of trying to initialize RustASTAnalyzer
    # Register the stub analyzer for .rs files
    ASTAnalyzer.ANALYZERS['.rs'] = RustStubASTAnalyzer
    console.print("[yellow]Using stub analyzer for Rust due to compatibility issues[/yellow]")
    console.print("[yellow]For better Rust support, fix the version compatibility between tree-sitter and tree-sitter-rust[/yellow]")


def test_rust_parser():
    """Test function to diagnose Rust parser initialization issues"""
    console.print("[bold]Testing Rust parser initialization...[/bold]")
    
    try:
        import tree_sitter
        console.print(f"tree-sitter version: {tree_sitter.__version__}")
    except Exception as e:
        console.print(f"Error importing tree_sitter: {e}")
    
    try:
        import tree_sitter_rust
        console.print("tree_sitter_rust imported successfully")
        
        # Try to access language attribute
        if hasattr(tree_sitter_rust, 'language'):
            console.print("tree_sitter_rust.language exists")
            
            # Check if it's callable
            if callable(tree_sitter_rust.language):
                console.print("tree_sitter_rust.language is callable")
                try:
                    lang_obj = tree_sitter_rust.language()
                    console.print(f"Called tree_sitter_rust.language() successfully: {type(lang_obj)}")
                except Exception as e:
                    console.print(f"Error calling tree_sitter_rust.language(): {e}")
            else:
                console.print("tree_sitter_rust.language is not callable")
                console.print(f"Type of tree_sitter_rust.language: {type(tree_sitter_rust.language)}")
        else:
            console.print("tree_sitter_rust.language does not exist")
            
        # List all attributes
        console.print("All attributes of tree_sitter_rust:")
        for attr in dir(tree_sitter_rust):
            if not attr.startswith('_'):
                console.print(f"- {attr}: {type(getattr(tree_sitter_rust, attr))}")
    except Exception as e:
        console.print(f"Error with tree_sitter_rust: {e}")
    
    try:
        from tree_sitter_languages import get_parser
        console.print("tree_sitter_languages.get_parser is available")
        try:
            parser = get_parser('rust')
            console.print("Successfully created Rust parser using tree_sitter_languages")
            console.print(f"Parser type: {type(parser)}")
        except Exception as e:
            console.print(f"Error creating Rust parser with tree_sitter_languages: {e}")
    except Exception as e:
        console.print(f"Error with tree_sitter_languages: {e}")
        
    # Try direct parser creation without Language constructor
    try:
        parser = tree_sitter.Parser()
        console.print("Created tree_sitter.Parser successfully")
        
        try:
            # Try direct assignment
            parser.language = tree_sitter_rust.language
            console.print("Direct assignment of tree_sitter_rust.language succeeded")
        except Exception as e:
            console.print(f"Direct assignment failed: {e}")
            
            try:
                # Try calling it first
                lang_obj = tree_sitter_rust.language()
                parser.language = lang_obj
                console.print("Assignment after calling tree_sitter_rust.language() succeeded")
            except Exception as e:
                console.print(f"Assignment after calling failed: {e}")
    except Exception as e:
        console.print(f"Error creating parser: {e}")


if __name__ == "__main__":
    
    tests_path = r"E:\Projects\Languages\Python\WorkingOnIt\CodeLyzer\test_examples"

    # Test JavaScript analyzer
    console.print("\n[bold]Testing JavaScript analyzer...[/bold]")
    analyzer = JavaScriptASTAnalyzer()
    metrics = analyzer.analyze_file(os.path.join(tests_path, "test.js"))
    console.print(metrics)
    console.print("--------------------------------")

    # Test Python analyzer
    console.print("\n[bold]Testing Python analyzer...[/bold]")
    analyzer = PythonASTAnalyzer()
    metrics = analyzer.analyze_file(os.path.join(tests_path, "test.py"))
    console.print(metrics)
    console.print("--------------------------------")

    # Test TypeScript analyzer
    console.print("\n[bold]Testing TypeScript analyzer...[/bold]")
    analyzer = TypeScriptASTAnalyzer()
    metrics = analyzer.analyze_file(os.path.join(tests_path, "test.ts"))
    console.print(metrics)
    console.print("--------------------------------")

    # Test Rust analyzer
    console.print("\n[bold]Testing Rust analyzer...[/bold]")
    analyzer = RustStubASTAnalyzer()
    metrics = analyzer.analyze_file(os.path.join(tests_path, "test.rs"))
    console.print(metrics)
    console.print("--------------------------------")
