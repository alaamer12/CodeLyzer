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
    import tree_sitter_rust
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

    extensions = ['.ts', '.tsx']
    language_name = "typescript"
    # TypeScript module provides separate language objects for ts and tsx
    language_module = None  # Will be set in _parse_with_timeout based on file extension
    comment_types = ["comment", "comment_block", "jsx_comment", "multiline_comment"]

    def __init__(self):
        """Initialize the TypeScript analyzer"""
        self.language_parser = None  # Reset to ensure it's initialized for the correct variant

    @classmethod
    def _get_language_name(cls) -> str:
        """Return specific language name based on file extension"""
        return "typescript"  # Base language name, more specific detection in _detect_language

    def _detect_language(self, file_path: str) -> str:
        """Detect specific TS variant from file extension"""
        ext = os.path.splitext(file_path)[1].lower()
        if ext == '.tsx':
            return "tsx"
        return "typescript"

    def _parse_with_timeout(self, content: str, file_path: str) -> Any:
        """Parse the file content into an AST with timeout handling"""
        # Determine which language module to use based on file extension
        if self.language_parser is None:
            ext = os.path.splitext(file_path)[1].lower()
            if ext == '.tsx':
                # Use the TSX language module
                try:
                    self.language_module = tree_sitter_typescript.language_tsx()
                    language = Language(tree_sitter_typescript.language_typescript())
                    parser = Parser()
                    parser.language = language
                    self.language_parser = parser
                    console.print(f"[green]Successfully initialized TSX parser[/green]")
                except Exception as e:
                    console.print(f"[red]Error initializing TSX parser: {str(e)}[/red]")
                    self.language_parser = None
                    return Exception(f"Parser for TSX could not be initialized: {str(e)}")
            else:
                # Use the TypeScript language module
                try:
                    self.language_module = tree_sitter_typescript.language_tsx()
                    language = Language(tree_sitter_typescript.language_typescript())
                    parser = Parser()
                    parser.language = language
                    self.language_parser = parser
                    console.print(f"[green]Successfully initialized TypeScript parser[/green]")
                except Exception as e:
                    console.print(f"[red]Error initializing TypeScript parser: {str(e)}[/red]")
                    self.language_parser = None
                    return Exception(f"Parser for TypeScript could not be initialized: {str(e)}")

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


class RustASTAnalyzer(TreeSitterASTAnalyzer):
    """Analyzer for Rust files using tree-sitter"""

    extensions = ['.rs']
    language_name = "rust"
    language_module = tree_sitter_rust if TREE_SITTER_AVAILABLE else None
    comment_types = ["line_comment", "block_comment"]

    def __init__(self):
        """Initialize the Rust analyzer"""
        self.language_parser = None  # We'll initialize it properly in _parse_with_timeout

    @classmethod
    def _get_language_name(cls) -> str:
        return "rust"

    def _parse_with_timeout(self, content: str, file_path: str) -> Any:
        """Parse the file content into an AST with timeout handling"""
        if self.language_parser is None:
            try:
                # Try using tree_sitter_languages if available (it handles version compatibility)
                try:
                    from tree_sitter_languages import get_parser
                    self.language_parser = get_parser('rust')
                    console.print(f"[green]Successfully initialized Rust parser using tree_sitter_languages[/green]")
                except ImportError:
                    get_parser = None
                    # Fall back to direct initialization, but this might have version issues
                    try:
                        language = Language(tree_sitter_rust.language())
                        parser = Parser()
                        parser.language = language
                        self.language_parser = parser
                        console.print(f"[green]Successfully initialized Rust parser[/green]")
                    except Exception as e:
                        console.print(f"[red]Error initializing Rust parser: {str(e)}[/red]")
                        console.print("[yellow]Try installing tree_sitter_languages for better compatibility:[/yellow]")
                        console.print("[yellow]pip install tree_sitter_languages[/yellow]")
                        self.language_parser = None
                        return Exception(f"Parser for Rust could not be initialized: {str(e)}")
            except Exception as e:
                console.print(f"[red]Error initializing Rust parser: {str(e)}[/red]")
                self.language_parser = None
                return Exception(f"Parser for Rust could not be initialized: {str(e)}")

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

    def _calculate_metrics(self, ast_data: Any, metrics: FileMetrics, content: str = None) -> None:
        """Calculate Rust-specific metrics from the tree-sitter AST"""
        if ast_data is None or isinstance(ast_data, Exception):
            return

        root_node = ast_data.root_node

        # Initialize counters
        struct_count = 0
        function_count = 0
        trait_count = 0
        impl_count = 0
        enum_count = 0
        mod_count = 0
        imports_list = []

        # Process the AST
        def process_node(node):
            nonlocal struct_count, function_count, trait_count, impl_count, enum_count, mod_count, imports_list

            if node.type == "struct_item":
                struct_count += 1
            elif node.type == "function_item":
                function_count += 1
            elif node.type == "trait_item":
                trait_count += 1
            elif node.type == "impl_item":
                impl_count += 1
            elif node.type == "enum_item":
                enum_count += 1
            elif node.type == "mod_item":
                mod_count += 1
            elif node.type == "use_declaration":
                imports_list.append(node.text.decode('utf8').split('\n')[0])

            # Process children
            for child in node.children:
                process_node(child)

        # Start processing from root
        process_node(root_node)

        # Update metrics
        metrics.structure.classes = struct_count + trait_count  # Use classes for structs and traits
        metrics.structure.functions = function_count
        metrics.structure.imports = imports_list
        
        # Add Rust specific metrics as custom metrics
        rust_metrics = FileMetricCategory()
        rust_metrics.add_metric("structs", struct_count)
        rust_metrics.add_metric("traits", trait_count)
        rust_metrics.add_metric("impls", impl_count)
        rust_metrics.add_metric("enums", enum_count)
        rust_metrics.add_metric("modules", mod_count)
        metrics.add_custom_metric_category("rust", rust_metrics)

        # Calculate cyclomatic complexity
        complexity = self._calculate_cyclomatic_complexity(root_node)
        metrics.complexity.cyclomatic_complexity = complexity
        metrics.complexity.complexity_score = float(complexity)

    @staticmethod
    def _calculate_cyclomatic_complexity(root_node: Any) -> int:
        """Calculate cyclomatic complexity for Rust code"""
        complexity = 1  # Start with 1

        # Branch keywords and operators
        branch_types = [
            "if_expression", "else_clause",
            "for_expression", "while_expression", "loop_expression",
            "match_expression", "match_arm",
            "macro_invocation",  # Some macros like try! increase complexity
            "binary_expression",  # For && and ||
            "question_mark_expression"  # ? operator for error handling
        ]

        def traverse(node):
            nonlocal complexity

            if node.type in branch_types:
                # For binary expressions, only count && and || operators
                if node.type == "binary_expression":
                    operator = node.child_by_field_name("operator")
                    if operator and operator.type in ["&&", "||"]:
                        complexity += 1
                else:
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
        console.print("[yellow]Install them with: pip install tree-sitter tree-sitter-python tree-sitter-javascript tree-sitter-typescript tree-sitter-languages[/yellow]")
        return
    
    PythonASTAnalyzer.initialize_parser()
    JavaScriptASTAnalyzer.initialize_parser()
    # TypeScript and Rust parsers are initialized when needed
    console.print("[green]Initialized tree-sitter parsers for: Python, JavaScript[/green]")
    console.print("[blue]TypeScript and Rust parsers will be initialized when needed[/blue]")


if __name__ == "__main__":
    analyzer = JavaScriptASTAnalyzer()
    metrics = analyzer.analyze_file("test.js")
    print(metrics)
