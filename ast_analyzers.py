import os
import ast
from typing import Optional

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