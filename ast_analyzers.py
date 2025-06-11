import ast
import json
import os
import subprocess
import tempfile
from abc import ABC, abstractmethod
from typing import Optional, Type, ClassVar, Dict, List, Any

from config import FileMetrics, FILE_SIZE_LIMIT, TIMEOUT_SECONDS
from console import console
from utils import FunctionWithTimeout


class ASTAnalyzer(ABC):
    """Base class for language-specific AST analyzers"""
    
    # Class attribute mapping file extension to analyzer class
    ANALYZERS: ClassVar[Dict[str, Type['ASTAnalyzer']]] = {}
    
    # Class attribute for extensions supported by this analyzer
    extensions: ClassVar[List[str]] = []
    
    def __init_subclass__(cls, **kwargs):
        """Register each analyzer subclass with its supported extensions"""
        super().__init_subclass__(**kwargs)
        for ext in cls.extensions:
            ASTAnalyzer.ANALYZERS[ext] = cls
    
    @classmethod
    def get_analyzer_for_extension(cls, extension: str) -> Optional[Type['ASTAnalyzer']]:
        """Factory method to get the appropriate analyzer for a file extension"""
        return cls.ANALYZERS.get(extension.lower())
    
    def analyze_file(self, file_path: str) -> Optional[FileMetrics]:
        """Analyze a file and return its metrics - common implementation with template pattern"""
        try:
            # Check file size first to avoid hanging on massive files
            file_size = os.path.getsize(file_path)
            if file_size > FILE_SIZE_LIMIT:
                metrics = self._create_metrics_for_file(file_path)
                metrics.loc = metrics.sloc = file_size // 100  # Rough estimate
                return metrics

            # Read file content with appropriate error handling
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
            except Exception:
                # Handle read errors
                metrics = self._create_metrics_for_file(file_path)
                metrics.loc = metrics.sloc = 0
                return metrics

            # Parse AST with thread-based timeout - language specific
            ast_data = self._parse_with_timeout(content, file_path)

            # Handle parsing errors
            if isinstance(ast_data, Exception):
                metrics = self._create_metrics_for_file(file_path)
                lines = content.count('\n') + 1
                metrics.loc = metrics.sloc = lines
                return metrics

            # Initialize metrics
            metrics = self._create_metrics_for_file(file_path)

            # Calculate AST-based metrics - language specific
            try:
                self._calculate_metrics(ast_data, metrics, content)
            except Exception as e:
                # Fill with default values
                lines = content.count('\n') + 1
                metrics.loc = metrics.sloc = lines
                console.print(f"[yellow]Warning: Error calculating metrics: {str(e)}[/yellow]")

            # Calculate common metrics like lines of code if not already set
            if metrics.loc == 0:
                self._calculate_line_counts(content, metrics)

            return metrics

        except Exception as e:
            # Return minimal metrics object rather than None
            console.print(f"[yellow]Warning: Error analyzing {file_path}: {str(e)}[/yellow]")
            metrics = self._create_metrics_for_file(file_path)
            metrics.loc = metrics.sloc = 0
            return metrics
    
    def _calculate_line_counts(self, content: str, metrics: FileMetrics) -> None:
        """Count different types of lines in the file content"""
        if not content:
            metrics.loc = metrics.sloc = metrics.blanks = metrics.comments = 0
            return
            
        lines = content.split('\n')
        metrics.loc = len(lines)
        metrics.blanks = sum(1 for line in lines if not line.strip())
        
        # Comments need to be counted by language-specific logic
        comment_lines = self._count_comment_lines(content)
        metrics.comments = comment_lines
        metrics.sloc = metrics.loc - metrics.blanks - metrics.comments
    
    def _create_metrics_for_file(self, file_path: str) -> FileMetrics:
        """Create a FileMetrics object with the appropriate language"""
        language = self._detect_language(file_path)
        return FileMetrics(file_path=file_path, language=language)
    
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
    
    def _parse_with_timeout(self, content: str, file_path: str) -> ast.AST:
        """Parse Python code into AST with a timeout to handle large files"""
        def parse_ast():
            try:
                return ast.parse(content, filename=file_path)
            except SyntaxError as e:
                return e
            except Exception as e:
                return e

        # Use thread-based timeout
        timeout_runner = FunctionWithTimeout(timeout=TIMEOUT_SECONDS)
        return timeout_runner.run_with_timeout(parse_ast)

    def _calculate_metrics(self, tree: ast.AST, metrics: FileMetrics, content: str = None) -> None:
        """Calculate various metrics from the AST"""
        # Count classes and functions
        classes = [node for node in tree.body if isinstance(node, ast.ClassDef)]
        functions = [node for node in tree.body if isinstance(node, ast.FunctionDef)]

        metrics.classes = len(classes)
        metrics.functions = len(functions)

        # Methods per class
        for cls in classes:
            methods = [n for n in cls.body if isinstance(n, ast.FunctionDef)]
            metrics.methods_per_class[cls.name] = len(methods)
            metrics.methods += len(methods)

        # Imports
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name.split('.')[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(node.module.split('.')[0])

        metrics.imports = sorted(imports)

        # Cyclomatic complexity
        metrics.cyclomatic_complexity = self._calculate_cyclomatic_complexity(tree)
        
        # Calculate line counts if content was provided
        if content and metrics.loc == 0:
            self._calculate_line_counts(content, metrics)

    def _calculate_cyclomatic_complexity(self, tree: ast.AST) -> int:
        """Calculate cyclomatic complexity of Python code"""
        complexity = 1  # Base complexity

        # Count branches that increase complexity
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(node, ast.ExceptHandler):
                complexity += 1
            elif isinstance(node, (ast.ListComp, ast.DictComp, ast.SetComp, ast.GeneratorExp)):
                complexity += 1
            elif isinstance(node, ast.BoolOp):
                complexity += len(node.values) - 1

        return complexity
        
    def _count_comment_lines(self, content: str) -> int:
        """Count comment lines in Python code"""
        if not content:
            return 0
            
        lines = content.split('\n')
        comment_count = 0
        in_multiline_comment = False
        
        for line in lines:
            stripped = line.strip()
            
            # Handle multiline comments (docstrings)
            if in_multiline_comment:
                comment_count += 1
                if '"""' in stripped or "'''" in stripped:
                    in_multiline_comment = False
            elif stripped.startswith('#'):
                comment_count += 1
            elif stripped.startswith('"""') or stripped.startswith("'''"):
                comment_count += 1
                if not (stripped.endswith('"""') and len(stripped) > 3) and not (stripped.endswith("'''") and len(stripped) > 3):
                    in_multiline_comment = True
                    
        return comment_count


class JavaScriptASTAnalyzer(ASTAnalyzer):
    """Analyzer for JavaScript/TypeScript files using Abstract Syntax Tree"""
    
    extensions = ['.js', '.jsx', '.ts', '.tsx']
    
    def __init__(self):
        # Check if esprima is available
        self.use_python_esprima = self._ensure_esprima_available()

    def _ensure_esprima_available(self) -> bool:
        """Ensure esprima is available for parsing JavaScript"""
        try:
            # Try to import esprima first
            import esprima
            return True
        except ImportError:
            # Fall back to Node.js esprima if available
            try:
                result = subprocess.run(['node', '-e', 'console.log("ok")'],
                                        capture_output=True, text=True, timeout=2)
                if result.returncode == 0:
                    return False
                else:
                    raise Exception("Node.js not available")
            except Exception:
                # Install python esprima as fallback
                try:
                    console.print("[yellow]Installing esprima for JavaScript parsing...[/yellow]")
                    subprocess.check_call(['pip', 'install', 'esprima'],
                                          stdout=subprocess.DEVNULL,
                                          stderr=subprocess.DEVNULL)
                    import esprima
                    return True
                except Exception:
                    raise Exception("Cannot install or use JavaScript parser")
    
    @classmethod
    def _get_language_name(cls) -> str:
        return "javascript"  # Base language name, more specific detection in _detect_language

    def _detect_language(self, file_path: str) -> str:
        """Determine language based on file extension"""
        ext = os.path.splitext(file_path)[1].lower()
        if ext in ['.ts', '.tsx']:
            return 'typescript'
        elif ext in ['.jsx']:
            return 'jsx'
        else:
            return 'javascript'

    def _parse_with_timeout(self, content: str, file_path: str):
        """Parse JavaScript code into AST with timeout"""
        def parse_ast():
            try:
                if self.use_python_esprima:
                    return self._parse_with_python_esprima(content)
                else:
                    return self._parse_with_node_esprima(content)
            except Exception as e:
                return e

        timeout_runner = FunctionWithTimeout(timeout=TIMEOUT_SECONDS)
        return timeout_runner.run_with_timeout(parse_ast)

    def _parse_with_python_esprima(self, content: str):
        """Parse using Python esprima library"""
        import esprima
        # Try different parsing modes for better compatibility
        try:
            return esprima.parseScript(content, options={'loc': True, 'range': True})
        except:
            try:
                return esprima.parseModule(content, options={'loc': True, 'range': True})
            except:
                # Last resort: try without strict mode
                return esprima.parseScript(content, options={'loc': True, 'range': True, 'tolerant': True})

    @staticmethod
    def _parse_with_node_esprima(content: str):
        """Parse using Node.js esprima as fallback"""
        # Create temporary file for parsing
        with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        try:
            # Use Node.js to parse the file
            node_script = f"""
            const esprima = require('esprima');
            const fs = require('fs');
            try {{
                const code = fs.readFileSync('{tmp_path}', 'utf8');
                const ast = esprima.parseScript(code, {{ loc: true, range: true }});
                console.log(JSON.stringify(ast));
            }} catch (e) {{
                try {{
                    const code = fs.readFileSync('{tmp_path}', 'utf8');
                    const ast = esprima.parseModule(code, {{ loc: true, range: true }});
                    console.log(JSON.stringify(ast));
                }} catch (e2) {{
                    throw e2;
                }}
            }}
            """

            result = subprocess.run(['node', '-e', node_script],
                                    capture_output=True, text=True, timeout=TIMEOUT_SECONDS)

            if result.returncode == 0:
                return json.loads(result.stdout)
            else:
                raise Exception(f"Node parsing failed: {result.stderr}")
        finally:
            os.unlink(tmp_path)

    def _calculate_metrics(self, ast_data: Dict, metrics: FileMetrics, content: str = None) -> None:
        """Calculate various metrics from the AST"""
        if content:
            self._calculate_line_counts(content, metrics)
            
        # Analyze AST structure for metrics
        context = self._analyze_ast_structure(ast_data)
        metrics.classes = context['classes']
        metrics.functions = context['functions']
        metrics.methods = context['methods']
        metrics.methods_per_class = context['methods_per_class'] 
        metrics.imports = sorted(context['imports'])

        # Calculate complexity
        metrics.cyclomatic_complexity = self._calculate_cyclomatic_complexity(ast_data)

    def _analyze_ast_structure(self, node, context=None):
        """Analyze AST structure and count various elements"""
        if context is None:
            context = {
                'classes': 0,
                'functions': 0,
                'methods': 0,
                'methods_per_class': {},
                'imports': set(),
                'current_class': None
            }

        if not isinstance(node, dict):
            return context

        node_type = node.get('type', '')

        # Count classes
        if node_type in ['ClassDeclaration', 'ClassExpression']:
            context['classes'] += 1
            class_name = self._get_identifier_name(node.get('id'))
            if class_name:
                context['current_class'] = class_name
                context['methods_per_class'][class_name] = 0

        # Count functions
        elif node_type in ['FunctionDeclaration', 'FunctionExpression', 'ArrowFunctionExpression']:
            if context.get('current_class'):
                context['methods'] += 1
                context['methods_per_class'][context['current_class']] += 1
            else:
                context['functions'] += 1

        # Count method definitions
        elif node_type == 'MethodDefinition':
            context['methods'] += 1
            if context.get('current_class'):
                context['methods_per_class'][context['current_class']] += 1

        # Count imports
        elif node_type in ['ImportDeclaration', 'ImportExpression']:
            source = node.get('source', {})
            if source and source.get('type') == 'Literal':
                import_path = source.get('value', '')
                if import_path:
                    # Extract package name
                    package_name = import_path.split('/')[0].replace('@', '')
                    if not import_path.startswith('.'):  # External imports only
                        context['imports'].add(package_name)

        # Handle require calls
        elif (node_type == 'CallExpression' and
              node.get('callee', {}).get('name') == 'require'):
            args = node.get('arguments', [])
            if args and args[0].get('type') == 'Literal':
                import_path = args[0].get('value', '')
                if import_path and not import_path.startswith('.'):
                    package_name = import_path.split('/')[0].replace('@', '')
                    context['imports'].add(package_name)

        # Recursively process child nodes
        for key, value in node.items():
            if isinstance(value, list):
                old_class = context.get('current_class')
                for item in value:
                    self._analyze_ast_structure(item, context)
                # Reset class context after processing body
                if key == 'body' and node_type in ['ClassDeclaration', 'ClassExpression']:
                    context['current_class'] = old_class
            elif isinstance(value, dict):
                self._analyze_ast_structure(value, context)

        return context

    @staticmethod
    def _get_identifier_name(identifier_node):
        """Extract name from identifier node"""
        if isinstance(identifier_node, dict) and identifier_node.get('type') == 'Identifier':
            return identifier_node.get('name')
        return None

    def _count_comment_lines(self, content: str) -> int:
        """Count comment lines in JavaScript code"""
        if not content:
            return 0
            
        lines = content.split('\n')
        comment_count = 0
        in_block_comment = False

        for line in lines:
            stripped = line.strip()

            # Handle block comments
            if in_block_comment:
                comment_count += 1
                if '*/' in stripped:
                    in_block_comment = False
            elif '/*' in stripped and '*/' in stripped:
                # Single line block comment
                comment_count += 1
            elif '/*' in stripped:
                # Start of block comment
                in_block_comment = True
                comment_count += 1
            elif stripped.startswith('//'):
                # Single line comment
                comment_count += 1

        return comment_count

    @staticmethod
    def _calculate_cyclomatic_complexity(ast_data) -> int:
        """Calculate cyclomatic complexity of JavaScript code"""
        complexity = 1  # Base complexity

        def count_complexity(node):
            nonlocal complexity
            if not isinstance(node, dict):
                return

            node_type = node.get('type', '')

            # Control flow statements that increase complexity
            if node_type in [
                'IfStatement', 'ConditionalExpression',  # if/ternary
                'WhileStatement', 'DoWhileStatement', 'ForStatement', 'ForInStatement', 'ForOfStatement',  # loops
                'SwitchCase',  # switch cases
                'CatchClause',  # try-catch
                'LogicalExpression'  # && ||
            ]:
                complexity += 1

            # Recursively process children
            for key, value in node.items():
                if isinstance(value, list):
                    for item in value:
                        count_complexity(item)
                elif isinstance(value, dict):
                    count_complexity(value)

        count_complexity(ast_data)
        return complexity


if __name__ == "__main__":
    analyzer = JavaScriptASTAnalyzer()
    metrics = analyzer.analyze_file("test.js")
    print(metrics)
