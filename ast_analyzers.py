import ast
import ast
import json
import os
import subprocess
import tempfile
from typing import Optional, Dict

from config import FileMetrics, FILE_SIZE_LIMIT, TIMEOUT_SECONDS
from utils import FunctionWithTimeout


class PythonASTAnalyzer:
    """Analyzer for Python files using the Abstract Syntax Tree"""

    def analyze_file(self, file_path: str) -> Optional[FileMetrics]:
        """Analyze a Python file and return its metrics"""
        try:
            # Check file size first to avoid hanging on massive files
            file_size = os.path.getsize(file_path)
            if file_size > FILE_SIZE_LIMIT:
                # No console output for large files
                metrics = FileMetrics(file_path=file_path, language='python')
                metrics.loc = metrics.sloc = file_size // 100  # Rough estimate
                return metrics

            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
            except Exception:
                # Silently handle read errors
                metrics = FileMetrics(file_path=file_path, language='python')
                metrics.loc = metrics.sloc = 0
                return metrics

            # Parse AST with thread-based timeout
            tree = self._parse_ast_with_timeout(content, file_path)

            # Handle parsing errors
            if isinstance(tree, Exception):
                metrics = FileMetrics(file_path=file_path, language='python')
                lines = content.count('\n') + 1
                metrics.loc = metrics.sloc = lines
                return metrics

            # Initialize metrics
            metrics = FileMetrics(file_path=file_path, language='python')

            # Calculate AST-based metrics
            try:
                self._calculate_ast_metrics(tree, metrics)
            except Exception:
                # Fill with default values without console output
                lines = content.count('\n') + 1
                metrics.loc = metrics.sloc = lines

            return metrics

        except Exception:
            # Return minimal metrics object rather than None, without console output
            metrics = FileMetrics(file_path=file_path, language='python')
            metrics.loc = metrics.sloc = 0
            return metrics

    def _parse_ast_with_timeout(self, content: str, file_path: str) -> ast.AST:
        """Parse Python code into AST with a timeout to handle large files"""

        # Define a function to parse the AST
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

    def _calculate_ast_metrics(self, tree: ast.AST, metrics: FileMetrics) -> None:
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



class JavaScriptASTAnalyzer:
    """Analyzer for JavaScript/TypeScript files using Abstract Syntax Tree"""

    def __init__(self):
        # Check if esprima is available
        self._ensure_esprima_available()

    def _ensure_esprima_available(self):
        """Ensure esprima is available for parsing JavaScript"""
        try:
            # Try to import esprima first
            import esprima
            self.use_python_esprima = True
        except ImportError:
            # Fall back to Node.js esprima if available
            try:
                result = subprocess.run(['node', '-e', 'console.log("ok")'],
                                        capture_output=True, text=True, timeout=2)
                if result.returncode == 0:
                    self.use_python_esprima = False
                else:
                    raise Exception("Node.js not available")
            except Exception:
                # Install python esprima as fallback
                try:
                    subprocess.check_call(['pip', 'install', 'esprima'],
                                          stdout=subprocess.DEVNULL,
                                          stderr=subprocess.DEVNULL)
                    import esprima
                    self.use_python_esprima = True
                except Exception:
                    raise Exception("Cannot install or use JavaScript parser")

    def analyze_file(self, file_path: str) -> Optional[FileMetrics]:
        """Analyze a JavaScript/TypeScript file and return its metrics"""
        try:
            # Determine language based on extension
            ext = os.path.splitext(file_path)[1].lower()
            language = self._determine_language(ext)

            # Check file size first to avoid hanging on massive files
            file_size = os.path.getsize(file_path)
            if file_size > FILE_SIZE_LIMIT:
                metrics = FileMetrics(file_path=file_path, language=language)
                metrics.loc = metrics.sloc = file_size // 120  # Rough estimate for JS
                return metrics

            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
            except Exception:
                metrics = FileMetrics(file_path=file_path, language=language)
                metrics.loc = metrics.sloc = 0
                return metrics

            # Parse AST with timeout
            ast_data = self._parse_ast_with_timeout(content, file_path)

            # Handle parsing errors
            if isinstance(ast_data, Exception):
                metrics = FileMetrics(file_path=file_path, language=language)
                lines = content.count('\n') + 1
                metrics.loc = metrics.sloc = lines
                return metrics

            # Initialize metrics
            metrics = FileMetrics(file_path=file_path, language=language)

            # Calculate AST-based metrics
            try:
                self._calculate_ast_metrics(ast_data, metrics, content)
            except Exception:
                lines = content.count('\n') + 1
                metrics.loc = metrics.sloc = lines

            return metrics

        except Exception:
            metrics = FileMetrics(file_path=file_path, language='javascript')
            metrics.loc = metrics.sloc = 0
            return metrics

    def _determine_language(self, ext: str) -> str:
        """Determine language based on file extension"""
        if ext in ['.ts', '.tsx']:
            return 'typescript'
        elif ext in ['.jsx']:
            return 'jsx'
        else:
            return 'javascript'

    def _parse_ast_with_timeout(self, content: str, file_path: str):
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

    def _parse_with_node_esprima(self, content: str):
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

    def _calculate_ast_metrics(self, ast_data: Dict, metrics: FileMetrics, content: str) -> None:
        """Calculate various metrics from the AST"""
        # Basic line counting
        lines = content.split('\n')
        metrics.loc = len(lines)

        # Count blank and comment lines
        metrics.blanks = sum(1 for line in lines if not line.strip())
        metrics.comments = self._count_comment_lines(content)
        metrics.sloc = metrics.loc - metrics.blanks - metrics.comments

        # Initialize counters
        classes = 0
        functions = 0
        methods = 0
        methods_per_class = {}
        imports = set()

        # Walk through AST
        self._walk_ast(ast_data, {
            'classes': lambda node, ctx: self._count_classes(node, ctx),
            'functions': lambda node, ctx: self._count_functions(node, ctx),
            'methods': lambda node, ctx: self._count_methods(node, ctx),
            'imports': lambda node, ctx: self._count_imports(node, ctx),
        }, {
                           'classes': 0,
                           'functions': 0,
                           'methods': 0,
                           'methods_per_class': {},
                           'imports': set(),
                           'current_class': None
                       })

        # Set metrics from context
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

    def _get_identifier_name(self, identifier_node):
        """Extract name from identifier node"""
        if isinstance(identifier_node, dict) and identifier_node.get('type') == 'Identifier':
            return identifier_node.get('name')
        return None

    def _count_comment_lines(self, content: str) -> int:
        """Count comment lines in JavaScript code"""
        lines = content.split('\n')
        comment_count = 0
        in_block_comment = False

        for line in lines:
            stripped = line.strip()

            # Handle block comments
            if '/*' in stripped and '*/' in stripped:
                # Single line block comment
                comment_count += 1
            elif '/*' in stripped:
                # Start of block comment
                in_block_comment = True
                comment_count += 1
            elif '*/' in stripped and in_block_comment:
                # End of block comment
                in_block_comment = False
                comment_count += 1
            elif in_block_comment:
                # Inside block comment
                comment_count += 1
            elif stripped.startswith('//'):
                # Single line comment
                comment_count += 1

        return comment_count

    def _walk_ast(self, node, visitors, context):
        """Walk through AST and apply visitors"""
        if not isinstance(node, dict):
            return

        node_type = node.get('type', '')

        # Apply visitors
        for visitor_name, visitor_func in visitors.items():
            visitor_func(node, context)

        # Recursively walk children
        for key, value in node.items():
            if isinstance(value, list):
                for item in value:
                    self._walk_ast(item, visitors, context)
            elif isinstance(value, dict):
                self._walk_ast(value, visitors, context)

    def _count_classes(self, node, context):
        """Count class declarations"""
        if node.get('type') in ['ClassDeclaration', 'ClassExpression']:
            context['classes'] += 1

    def _count_functions(self, node, context):
        """Count function declarations"""
        if node.get('type') in ['FunctionDeclaration', 'FunctionExpression', 'ArrowFunctionExpression']:
            context['functions'] += 1

    def _count_methods(self, node, context):
        """Count method definitions"""
        if node.get('type') == 'MethodDefinition':
            context['methods'] += 1

    def _count_imports(self, node, context):
        """Count import statements"""
        if node.get('type') == 'ImportDeclaration':
            source = node.get('source', {})
            if source.get('type') == 'Literal':
                import_path = source.get('value', '')
                if import_path and not import_path.startswith('.'):
                    package_name = import_path.split('/')[0]
                    context['imports'].add(package_name)

    def _calculate_cyclomatic_complexity(self, ast_data) -> int:
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
