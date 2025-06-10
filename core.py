#!/usr/bin/env python3
"""
Enhanced Codebase Analyzer
A powerful, robust tool for analyzing code repositories with beautiful terminal output.
Supports multiple programming languages with detailed metrics and visualizations.
"""

import os
import ast
import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
import re
import math
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.markdown import Markdown
from rich import box
from datetime import datetime

from config import DEFAULT_EXCLUDED_DIRS, DEFAULT_EXCLUDED_FILES, LANGUAGE_CONFIGS, FileMetrics, ProjectMetrics, ComplexityLevel, console



class AdvancedCodeAnalyzer:
    """Advanced code analyzer with multi-language support"""
    
    def __init__(self, exclude_dirs: Set[str] = None, include_tests: bool = False):
        self.exclude_dirs = (exclude_dirs or set()) | DEFAULT_EXCLUDED_DIRS
        self.include_tests = include_tests
        self.language_detectors = self._build_language_detectors()
        self.security_patterns = self._build_security_patterns()
        self.code_smell_patterns = self._build_code_smell_patterns()
        
        if not include_tests:
            self.exclude_dirs.update({'test', 'tests', '__tests__', 'spec', 'specs'})
    
    def _build_language_detectors(self) -> Dict[str, List[str]]:
        """Build file extension to language mapping"""
        detectors = {}
        for lang, config in LANGUAGE_CONFIGS.items():
            for ext in config['extensions']:
                if ext not in detectors:
                    detectors[ext] = []
                detectors[ext].append(lang)
        return detectors
    
    def _build_security_patterns(self) -> Dict[str, List[str]]:
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
    
    def _build_code_smell_patterns(self) -> Dict[str, List[str]]:
        """Build code smell patterns"""
        return {
            'long_methods': r'def\s+\w+.*:\s*\n(?:\s+.*\n){50,}',
            'duplicate_code': r'(.{50,})\n(?:.*\n)*?\1',
            'magic_numbers': r'\b(?<![\w.])\d{3,}\b(?![\w.])',
            'god_class': r'class\s+\w+.*:\s*\n(?:\s+.*\n){200,}',
            'feature_envy': r'(\w+)\.(\w+)\.(\w+)\.(\w+)',
        }
    
    def detect_language(self, file_path: str) -> Optional[str]:
        """Detect programming language from file extension"""
        ext = Path(file_path).suffix.lower()
        languages = self.language_detectors.get(ext, [])
        return languages[0] if languages else None
    
    def should_exclude_file(self, file_path: str) -> bool:
        """Check if file should be excluded from analysis"""
        path = Path(file_path)
        
        # Check if any part of the path contains excluded directories
        for part in path.parts:
            if part in self.exclude_dirs:
                return True
        
        # Check excluded file patterns
        for pattern in DEFAULT_EXCLUDED_FILES:
            if path.match(pattern):
                return True
        
        return False
    
    def analyze_python_file(self, file_path: str) -> Optional[FileMetrics]:
        """Analyze Python file using AST"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Parse AST
            try:
                tree = ast.parse(content, filename=file_path)
            except SyntaxError:
                return None
            
            metrics = FileMetrics(file_path=file_path, language='python')
            
            # Count AST nodes
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
            
            return metrics
            
        except Exception as e:
            console.print(f"[red]Error analyzing {file_path}: {e}[/red]")
            return None
    
    def _calculate_cyclomatic_complexity(self, tree: ast.AST) -> int:
        """Calculate cyclomatic complexity for Python AST"""
        complexity = 1  # Base complexity
        
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
    
    def analyze_generic_file(self, file_path: str, language: str) -> Optional[FileMetrics]:
        """Analyze non-Python files with generic patterns"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            metrics = FileMetrics(file_path=file_path, language=language)
            config = LANGUAGE_CONFIGS.get(language, LANGUAGE_CONFIGS['python'])
            
            # Count keywords/patterns
            for keyword in config['keywords']:
                pattern = rf'\b{keyword}\b'
                matches = re.findall(pattern, content, re.IGNORECASE)
                
                if keyword in ['def', 'function', 'func', 'fn']:
                    metrics.functions += len(matches)
                elif keyword in ['class', 'struct', 'interface']:
                    metrics.classes += len(matches)
            
            return metrics
            
        except Exception as e:
            console.print(f"[red]Error analyzing {file_path}: {e}[/red]")
            return None
    
    def count_lines(self, file_path: str, language: str) -> Tuple[int, int, int, int]:
        """Count different types of lines in a file"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            total_lines = len(lines)
            blank_lines = 0
            comment_lines = 0
            source_lines = 0
            
            config = LANGUAGE_CONFIGS.get(language, LANGUAGE_CONFIGS['python'])
            comment_patterns = [re.compile(pattern, re.MULTILINE) for pattern in config['comment_patterns']]
            
            content = ''.join(lines)
            
            # Remove comments
            for pattern in comment_patterns:
                content = pattern.sub('', content)
            
            # Count lines
            for line in lines:
                stripped = line.strip()
                if not stripped:
                    blank_lines += 1
                elif any(pattern.match(stripped) for pattern in comment_patterns):
                    comment_lines += 1
                else:
                    source_lines += 1
            
            return total_lines, source_lines, comment_lines, blank_lines
            
        except Exception:
            return 0, 0, 0, 0
    
    def detect_security_issues(self, content: str) -> List[str]:
        """Detect potential security issues"""
        issues = []
        for category, patterns in self.security_patterns.items():
            for pattern in patterns:
                if re.search(pattern, content, re.MULTILINE | re.IGNORECASE):
                    issues.append(category)
                    break
        return issues
    
    def detect_code_smells(self, content: str) -> List[str]:
        """Detect code smells"""
        smells = []
        for smell, pattern in self.code_smell_patterns.items():
            if re.search(pattern, content, re.MULTILINE):
                smells.append(smell)
        return smells
    
    def analyze_file(self, file_path: str) -> Optional[FileMetrics]:
        """Analyze a single file"""
        if self.should_exclude_file(file_path):
            return None
        
        language = self.detect_language(file_path)
        if not language:
            return None
        
        # Get file stats
        try:
            stat = os.stat(file_path)
            file_size = stat.st_size
            last_modified = stat.st_mtime
        except OSError:
            file_size = 0
            last_modified = 0.0
        
        # Analyze based on language
        if language == 'python':
            metrics = self.analyze_python_file(file_path)
        else:
            metrics = self.analyze_generic_file(file_path, language)
        
        if not metrics:
            return None
        
        # Count lines
        metrics.loc, metrics.sloc, metrics.comments, metrics.blanks = self.count_lines(file_path, language)
        metrics.file_size = file_size
        metrics.last_modified = last_modified
        
        # Security and quality analysis
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            metrics.security_issues = self.detect_security_issues(content)
            metrics.code_smells = self.detect_code_smells(content)
        except Exception:
            pass
        
        # Calculate complexity metrics
        config = LANGUAGE_CONFIGS.get(language, LANGUAGE_CONFIGS['python'])
        weights = config['complexity_weights']
        
        metrics.complexity_score = (
            metrics.sloc * weights['loc'] +
            metrics.classes * weights['classes'] +
            metrics.functions * weights['functions'] +
            metrics.methods * weights['methods']
        )
        
        # Maintainability index (simplified)
        if metrics.sloc > 0:
            metrics.maintainability_index = max(0, 171 - 5.2 * math.log(metrics.sloc) - 
                                               0.23 * metrics.cyclomatic_complexity - 
                                               16.2 * math.log(max(1, len(metrics.imports))))
        
        return metrics
    
    def analyze_project(self, project_path: str) -> ProjectMetrics:
        """Analyze entire project"""
        start_time = time.time()
        project_metrics = ProjectMetrics()
        
        # Get all files
        all_files = []
        for root, dirs, files in os.walk(project_path):
            # Filter directories
            dirs[:] = [d for d in dirs if d not in self.exclude_dirs]
            
            for file in files:
                file_path = os.path.join(root, file)
                if self.detect_language(file_path) and not self.should_exclude_file(file_path):
                    all_files.append(file_path)
        
        # Analyze files with progress
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console
        ) as progress:
            
            task = progress.add_task("🔍 Analyzing files...", total=len(all_files))
            
            for file_path in all_files:
                metrics = self.analyze_file(file_path)
                if metrics:
                    project_metrics.file_metrics.append(metrics)
                    
                    # Update aggregated stats
                    project_metrics.total_files += 1
                    project_metrics.total_loc += metrics.loc
                    project_metrics.total_sloc += metrics.sloc
                    project_metrics.total_comments += metrics.comments
                    project_metrics.total_blanks += metrics.blanks
                    project_metrics.total_classes += metrics.classes
                    project_metrics.total_functions += metrics.functions
                    project_metrics.total_methods += metrics.methods
                    project_metrics.project_size += metrics.file_size
                    
                    # Language distribution
                    project_metrics.languages[metrics.language] = project_metrics.languages.get(
                        metrics.language, 0) + 1
                    
                    # Dependencies
                    for imp in metrics.imports:
                        project_metrics.dependencies[imp] = project_metrics.dependencies.get(imp, 0) + 1
                
                progress.advance(task)
        
        # Post-processing
        self._calculate_derived_metrics(project_metrics)
        project_metrics.analysis_duration = time.time() - start_time
        
        return project_metrics
    
    def _calculate_derived_metrics(self, metrics: ProjectMetrics):
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
        for file_metrics in metrics.file_metrics:
            if file_metrics.complexity_score < 50:
                level = ComplexityLevel.TRIVIAL
            elif file_metrics.complexity_score < 200:
                level = ComplexityLevel.LOW
            elif file_metrics.complexity_score < 500:
                level = ComplexityLevel.MODERATE
            elif file_metrics.complexity_score < 1000:
                level = ComplexityLevel.HIGH
            elif file_metrics.complexity_score < 2000:
                level = ComplexityLevel.VERY_HIGH
            else:
                level = ComplexityLevel.EXTREME
            
            metrics.complexity_distribution[level] = metrics.complexity_distribution.get(level, 0) + 1
        
        # Quality scores
        if metrics.total_sloc > 0:
            metrics.code_quality_score = min(100, max(0, 
                100 - (sum(len(f.security_issues) + len(f.code_smells) 
                          for f in metrics.file_metrics) / metrics.total_files * 10)))
            
            avg_maintainability = sum(f.maintainability_index for f in metrics.file_metrics) / len(metrics.file_metrics)
            metrics.maintainability_score = max(0, min(100, avg_maintainability))

def create_summary_panel(metrics: ProjectMetrics) -> Panel:
    """Create summary panel"""
    summary_text = f"""
📊 **Project Overview**
• Files analyzed: {metrics.total_files:,}
• Lines of code: {metrics.total_loc:,}
• Source lines: {metrics.total_sloc:,}
• Comments: {metrics.total_comments:,}
• Blank lines: {metrics.total_blanks:,}

🏗️ **Code Structure**
• Classes: {metrics.total_classes:,}
• Functions: {metrics.total_functions:,}
• Methods: {metrics.total_methods:,}

📈 **Quality Metrics**
• Code quality: {metrics.code_quality_score:.1f}/100
• Maintainability: {metrics.maintainability_score:.1f}/100
• Analysis time: {metrics.analysis_duration:.2f}s
"""
    
    return Panel(
        Markdown(summary_text),
        title="📋 Analysis Summary",
        border_style="blue",
        padding=(1, 2)
    )

def create_language_distribution_table(metrics: ProjectMetrics) -> Table:
    """Create language distribution table"""
    table = Table(title="🌐 Language Distribution", box=box.ROUNDED)
    table.add_column("Language", style="cyan", no_wrap=True)
    table.add_column("Files", justify="right", style="magenta")
    table.add_column("Percentage", justify="right", style="green")
    
    total_files = sum(metrics.languages.values())
    for language, count in sorted(metrics.languages.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / total_files) * 100 if total_files > 0 else 0
        table.add_row(
            language.title(),
            str(count),
            f"{percentage:.1f}%"
        )
    
    return table

def create_complexity_table(metrics: ProjectMetrics) -> Table:
    """Create complexity distribution table"""
    table = Table(title="⚡ Complexity Distribution", box=box.ROUNDED)
    table.add_column("Complexity Level", style="cyan")
    table.add_column("Files", justify="right", style="magenta")
    table.add_column("Percentage", justify="right", style="green")
    
    total_files = sum(metrics.complexity_distribution.values())
    
    for level in ComplexityLevel:
        count = metrics.complexity_distribution.get(level, 0)
        percentage = (count / total_files) * 100 if total_files > 0 else 0
        
        # Color coding
        if level in [ComplexityLevel.TRIVIAL, ComplexityLevel.LOW]:
            style = "green"
        elif level == ComplexityLevel.MODERATE:
            style = "yellow"
        else:
            style = "red"
        
        table.add_row(
            level.replace('_', ' ').title(),
            f"[{style}]{count}[/{style}]",
            f"[{style}]{percentage:.1f}%[/{style}]"
        )
    
    return table

def create_hotspots_table(metrics: ProjectMetrics) -> Table:
    """Create code hotspots table"""
    table = Table(title="🔥 Code Hotspots (Most Complex Files)", box=box.ROUNDED)
    table.add_column("File", style="cyan", max_width=50)
    table.add_column("Lines", justify="right", style="magenta")
    table.add_column("Complexity", justify="right", style="red")
    table.add_column("Issues", justify="right", style="yellow")
    
    for file_metrics in metrics.most_complex_files[:10]:
        relative_path = os.path.relpath(file_metrics.file_path)
        issues = len(file_metrics.security_issues) + len(file_metrics.code_smells)
        
        table.add_row(
            relative_path,
            str(file_metrics.sloc),
            f"{file_metrics.complexity_score:.0f}",
            str(issues) if issues > 0 else "✅"
        )
    
    return table

def create_dependencies_table(metrics: ProjectMetrics) -> Table:
    """Create top dependencies table"""
    table = Table(title="📦 Top Dependencies", box=box.ROUNDED)
    table.add_column("Module", style="cyan")
    table.add_column("Usage Count", justify="right", style="magenta")
    
    # Get top 15 dependencies
    top_deps = sorted(metrics.dependencies.items(), key=lambda x: x[1], reverse=True)[:15]
    
    for module, count in top_deps:
        table.add_row(module, str(count))
    
    return table

def generate_html_template():
    """Generate HTML template"""
    return '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Codebase Analysis Report</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/3.9.1/chart.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; background: #f5f7fa; }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 40px 0; text-align: center; margin-bottom: 30px; border-radius: 10px; }
        .metrics-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .metric-card { background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .metric-value { font-size: 2em; font-weight: bold; color: #667eea; }
        .metric-label { color: #666; margin-top: 5px; }
        .chart-container { background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); margin-bottom: 20px; }
        .table-container { background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); margin-bottom: 20px; }
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background-color: #f8f9fa; font-weight: 600; }
        tr:hover { background-color: #f5f5f5; }
        .complexity-low { color: #28a745; }
        .complexity-medium { color: #ffc107; }
        .complexity-high { color: #dc3545; }
        .progress-bar { width: 100%; height: 20px; background-color: #e9ecef; border-radius: 10px; overflow: hidden; }
        .progress-fill { height: 100%; background: linear-gradient(90deg, #28a745, #ffc107, #dc3545); transition: width 0.3s ease; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔍 Codebase Analysis Report</h1>
            <p>Generated on {timestamp}</p>
        </div>
        
        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-value">{total_files}</div>
                <div class="metric-label">Files Analyzed</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{total_loc:,}</div>
                <div class="metric-label">Lines of Code</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{total_classes}</div>
                <div class="metric-label">Classes</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{total_functions}</div>
                <div class="metric-label">Functions</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{code_quality:.1f}%</div>
                <div class="metric-label">Code Quality</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{maintainability:.1f}%</div>
                <div class="metric-label">Maintainability</div>
            </div>
        </div>
        
        <div class="chart-container">
            <h3>Language Distribution</h3>
            <canvas id="languageChart"></canvas>
        </div>
        
        <div class="chart-container">
            <h3>Complexity Distribution</h3>
            <canvas id="complexityChart"></canvas>
        </div>
        
        <div class="table-container">
            <h3>🔥 Most Complex Files</h3>
            <table>
                <thead>
                    <tr>
                        <th>File</th>
                        <th>Lines</th>
                        <th>Complexity Score</th>
                        <th>Issues</th>
                    </tr>
                </thead>
                <tbody>
                    {complex_files_rows}
                </tbody>
            </table>
        </div>
        
        <div class="table-container">
            <h3>📦 Top Dependencies</h3>
            <table>
                <thead>
                    <tr>
                        <th>Module</th>
                        <th>Usage Count</th>
                        <th>Usage</th>
                    </tr>
                </thead>
                <tbody>
                    {dependencies_rows}
                </tbody>
            </table>
        </div>
    </div>
    
    <script>
        // Language Distribution Chart
        const languageCtx = document.getElementById('languageChart').getContext('2d');
        new Chart(languageCtx, {{
            type: 'doughnut',
            data: {{
                labels: {language_labels},
                datasets: [{{
                    data: {language_data},
                    backgroundColor: [
                        '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF',
                        '#FF9F40', '#FF6384', '#C9CBCF', '#4BC0C0', '#FF6384'
                    ]
                }}]
            }},
            options: {{
                responsive: true,
                plugins: {{
                    legend: {{ position: 'bottom' }}
                }}
            }}
        }});
        
        // Complexity Distribution Chart
        const complexityCtx = document.getElementById('complexityChart').getContext('2d');
        new Chart(complexityCtx, {{
            type: 'bar',
            data: {{
                labels: {complexity_labels},
                datasets: [{{
                    label: 'Number of Files',
                    data: {complexity_data},
                    backgroundColor: ['#28a745', '#28a745', '#ffc107', '#fd7e14', '#dc3545', '#6f42c1']
                }}]
            }},
            options: {{
                responsive: true,
                plugins: {{
                    legend: {{ display: false }}
                }},
                scales: {{
                    y: {{ beginAtZero: true }}
                }}
            }}
        }});
    </script>
</body>
</html>
'''
    

def generate_html_report(metrics: ProjectMetrics, output_path: str):
    """Generate comprehensive HTML report"""
    html_template = generate_html_template()
    
    # Complex files rows
    complex_files_rows = ""
    for file_metrics in metrics.most_complex_files[:15]:
        relative_path = os.path.relpath(file_metrics.file_path)
        issues = len(file_metrics.security_issues) + len(file_metrics.code_smells)
        complexity_class = "complexity-high" if file_metrics.complexity_score > 500 else "complexity-medium" if file_metrics.complexity_score > 200 else "complexity-low"
        
        complex_files_rows += f'''
        <tr>
            <td>{relative_path}</td>
            <td>{file_metrics.sloc}</td>
            <td class="{complexity_class}">{file_metrics.complexity_score:.0f}</td>
            <td>{'✅' if issues == 0 else str(issues)}</td>
        </tr>'''
    
    # Dependencies rows
    dependencies_rows = ""
    top_deps = sorted(metrics.dependencies.items(), key=lambda x: x[1], reverse=True)[:15]
    max_usage = max([count for _, count in top_deps]) if top_deps else 1
    
    for module, count in top_deps:
        usage_percent = (count / max_usage) * 100
        dependencies_rows += f'''
        <tr>
            <td>{module}</td>
            <td>{count}</td>
            <td>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: {usage_percent}%"></div>
                </div>
            </td>
        </tr>'''
    
    # Chart data
    language_labels = list(metrics.languages.keys())
    language_data = list(metrics.languages.values())
    
    complexity_labels = [level.replace('_', ' ').title() for level in ComplexityLevel]
    complexity_data = [metrics.complexity_distribution.get(level, 0) for level in ComplexityLevel]
    
    # Fill template
    html_content = html_template.format(
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        total_files=metrics.total_files,
        total_loc=metrics.total_loc,
        total_classes=metrics.total_classes,
        total_functions=metrics.total_functions,
        code_quality=metrics.code_quality_score,
        maintainability=metrics.maintainability_score,
        complex_files_rows=complex_files_rows,
        dependencies_rows=dependencies_rows,
        language_labels=json.dumps(language_labels),
        language_data=json.dumps(language_data),
        complexity_labels=json.dumps(complexity_labels),
        complexity_data=json.dumps(complexity_data)
    )
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)

def export_json_report(metrics: ProjectMetrics, output_path: str):
    """Export detailed JSON report"""
    report_data = {
        'summary': {
            'total_files': metrics.total_files,
            'total_loc': metrics.total_loc,
            'total_sloc': metrics.total_sloc,
            'total_comments': metrics.total_comments,
            'total_blanks': metrics.total_blanks,
            'total_classes': metrics.total_classes,
            'total_functions': metrics.total_functions,
            'total_methods': metrics.total_methods,
            'project_size': metrics.project_size,
            'analysis_duration': metrics.analysis_duration,
            'code_quality_score': metrics.code_quality_score,
            'maintainability_score': metrics.maintainability_score
        },
        'languages': dict(metrics.languages),
        'complexity_distribution': dict(metrics.complexity_distribution),
        'dependencies': dict(metrics.dependencies),
        'files': []
    }
    
    for file_metrics in metrics.file_metrics:
        report_data['files'].append({
            'path': file_metrics.file_path,
            'language': file_metrics.language,
            'loc': file_metrics.loc,
            'sloc': file_metrics.sloc,
            'comments': file_metrics.comments,
            'blanks': file_metrics.blanks,
            'classes': file_metrics.classes,
            'functions': file_metrics.functions,
            'methods': file_metrics.methods,
            'complexity_score': file_metrics.complexity_score,
            'cyclomatic_complexity': file_metrics.cyclomatic_complexity,
            'maintainability_index': file_metrics.maintainability_index,
            'security_issues': file_metrics.security_issues,
            'code_smells': file_metrics.code_smells,
            'file_size': file_metrics.file_size,
            'imports': file_metrics.imports,
            'methods_per_class': file_metrics.methods_per_class
        })
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report_data, f, indent=2, default=str)