#!/usr/bin/env python3
"""
Enhanced Codebase Analyzer
A powerful, robust tool for analyzing code repositories with beautiful terminal output.
Supports multiple programming languages with detailed metrics and visualizations.
"""

import os
import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
import re
import math
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn, TimeRemainingColumn
from rich.markdown import Markdown
from rich import box

from ast_analyzers import PythonASTAnalyzer
from config import DEFAULT_EXCLUDED_DIRS, DEFAULT_EXCLUDED_FILES, LANGUAGE_CONFIGS, FileMetrics, ProjectMetrics, \
    ComplexityLevel, console, FILE_SIZE_LIMIT, TIMEOUT_SECONDS
from utils import FunctionWithTimeout, TimeoutError



class AdvancedCodeAnalyzer:
    """Advanced code analyzer with multi-language support"""

    def __init__(self, exclude_dirs: Set[str] = None, include_tests: bool = False):
        self.exclude_dirs = (exclude_dirs or set()) | DEFAULT_EXCLUDED_DIRS
        self.include_tests = include_tests
        self.language_detectors = self._build_language_detectors()
        self.security_patterns = self._build_security_patterns()
        self.code_smell_patterns = self._build_code_smell_patterns()
        self.python_analyzer = PythonASTAnalyzer()

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
        """Analyze Python file using the dedicated PythonASTAnalyzer"""
        return self.python_analyzer.analyze_file(file_path)

    def analyze_generic_file(self, file_path: str, language: str) -> Optional[FileMetrics]:
        """Analyze non-Python files with generic patterns"""
        try:
            # Check file size first to avoid hanging on massive files
            file_size = os.path.getsize(file_path)
            if file_size > FILE_SIZE_LIMIT:
                # No console output for large files
                metrics = FileMetrics(file_path=file_path, language=language)
                metrics.loc = metrics.sloc = file_size // 100  # Rough estimate
                return metrics

            metrics = FileMetrics(file_path=file_path, language=language)

            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
            except Exception:
                # Create basic metrics without console output
                metrics.loc = metrics.sloc = 0
                return metrics

            config = LANGUAGE_CONFIGS.get(language, LANGUAGE_CONFIGS['python'])

            # Pattern matching with thread-based timeout
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
            result = timeout_runner.run_with_timeout(pattern_matching)

            if isinstance(result, TimeoutError) or isinstance(result, Exception):
                # Count lines as fallback without console output
                try:
                    lines = content.count('\n') + 1
                    metrics.loc = metrics.sloc = lines
                except Exception:
                    metrics.loc = metrics.sloc = 0
                return metrics

            # Count lines manually
            try:
                lines = content.count('\n') + 1
                metrics.loc = metrics.sloc = lines
            except Exception:
                metrics.loc = metrics.sloc = 0

            # If no errors, return metrics
            return metrics

        except Exception:
            # Return minimal metrics object without console output
            metrics = FileMetrics(file_path=file_path, language=language)
            metrics.loc = metrics.sloc = 0
            return metrics

    def count_lines(self, file_path: str, language: str) -> Tuple[int, int, int, int]:
        """Count different types of lines in a file"""
        try:
            # Check file size first to avoid hanging on massive files
            try:
                file_size = os.path.getsize(file_path)
            except OSError:
                return 0, 0, 0, 0

            if file_size > FILE_SIZE_LIMIT:
                # Provide rough estimates for large files without console output
                total_lines = file_size // 50  # Approx 50 bytes per line as rough estimate
                source_lines = int(total_lines * 0.7)  # Estimate 70% of lines are source code
                comment_lines = int(total_lines * 0.2)  # Estimate 20% are comments
                blank_lines = total_lines - source_lines - comment_lines  # Remaining are blank
                return total_lines, source_lines, comment_lines, blank_lines

            # For normal-sized files, count lines with thread-based timeout
            total_lines = 0
            blank_lines = 0
            comment_lines = 0

            config = LANGUAGE_CONFIGS.get(language, LANGUAGE_CONFIGS['python'])
            comment_patterns = [re.compile(pattern) for pattern in config['comment_patterns']]

            def count_file_lines():
                nonlocal total_lines, blank_lines, comment_lines
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        for line in f:
                            total_lines += 1
                            stripped = line.strip()
                            if not stripped:
                                blank_lines += 1
                            elif any(pattern.match(stripped) for pattern in comment_patterns):
                                comment_lines += 1
                    return True
                except Exception:
                    return False

            timeout_runner = FunctionWithTimeout(timeout=TIMEOUT_SECONDS)
            result = timeout_runner.run_with_timeout(count_file_lines)

            if result is False or isinstance(result, Exception) or isinstance(result, TimeoutError):
                # Provide rough estimates without console output
                total_lines = file_size // 50
                source_lines = int(total_lines * 0.7)
                comment_lines = int(total_lines * 0.2)
                blank_lines = total_lines - source_lines - comment_lines
                return total_lines, source_lines, comment_lines, blank_lines

            # Calculate source lines
            source_lines = total_lines - blank_lines - comment_lines

            return total_lines, source_lines, comment_lines, blank_lines

        except Exception:
            # Return zeros without console output
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
        try:
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

            # Create basic metrics object
            metrics = FileMetrics(file_path=file_path, language=language)
            metrics.file_size = file_size
            metrics.last_modified = last_modified

            # Check file size first to avoid hanging on massive files
            if file_size > FILE_SIZE_LIMIT:
                console.print(
                    f"[yellow]Warning: Large file {file_path} ({file_size / 1024 / 1024:.1f} MB), using basic metrics[/yellow]")
                metrics.loc = metrics.sloc = file_size // 100  # Rough estimate
                return metrics

            # Analyze based on language
            timeout_runner = FunctionWithTimeout(timeout=TIMEOUT_SECONDS)

            if language == 'python':
                result = timeout_runner.run_with_timeout(self.analyze_python_file, file_path)
            else:
                result = timeout_runner.run_with_timeout(self.analyze_generic_file, file_path, language)

            if isinstance(result, TimeoutError):
                console.print(f"[yellow]Warning: Analysis timed out for {file_path}, using basic metrics[/yellow]")
                # Fill in count_lines data at minimum
                try:
                    total, source, comments, blanks = self.count_lines(file_path, language)
                    metrics.loc = total
                    metrics.sloc = source
                    metrics.comments = comments
                    metrics.blanks = blanks
                except Exception as e:
                    console.print(f"[yellow]Warning: Failed to count lines in {file_path}: {str(e)}[/yellow]")
                return metrics
            elif isinstance(result, Exception):
                console.print(f"[yellow]Warning: Error analyzing {file_path}: {str(result)}[/yellow]")
                return metrics

            # If analysis succeeded, use the detailed metrics
            if result:
                metrics = result

            # Count lines if not already set
            if metrics.loc == 0:
                try:
                    total, source, comments, blanks = self.count_lines(file_path, language)
                    metrics.loc = total
                    metrics.sloc = source
                    metrics.comments = comments
                    metrics.blanks = blanks
                except Exception as e:
                    console.print(f"[yellow]Warning: Failed to count lines in {file_path}: {str(e)}[/yellow]")

            # Security and quality analysis (with timeouts)
            try:
                def security_analysis():
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                        return (self.detect_security_issues(content),
                                self.detect_code_smells(content))
                    except Exception as e:
                        console.print(f"[yellow]Warning: Error in security analysis for {file_path}: {str(e)}[/yellow]")
                        return [], []

                timeout_runner = FunctionWithTimeout(timeout=TIMEOUT_SECONDS // 2)  # Use shorter timeout
                security_result = timeout_runner.run_with_timeout(security_analysis)

                if isinstance(security_result, Exception) or isinstance(security_result, TimeoutError):
                    console.print(f"[yellow]Warning: Security analysis timed out for {file_path}[/yellow]")
                else:
                    security_issues, code_smells = security_result
                    metrics.security_issues = security_issues
                    metrics.code_smells = code_smells
            except Exception:
                pass

            # Calculate complexity metrics
            try:
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
                                                        0.23 * (metrics.cyclomatic_complexity or 1) -
                                                        16.2 * math.log(max(1, len(metrics.imports or []))))
            except Exception as e:
                console.print(
                    f"[yellow]Warning: Error calculating complexity metrics for {file_path}: {str(e)}[/yellow]")

            return metrics

        except Exception as e:
            console.print(f"[red]Error analyzing {file_path}: {str(e)}[/red]")
            # Return minimal metrics object rather than None
            metrics = FileMetrics(file_path=file_path, language=language if 'language' in locals() else 'unknown')
            metrics.loc = metrics.sloc = 0
            return metrics

    def analyze_project(self, project_path: str) -> ProjectMetrics:
        """Analyze entire project"""
        start_time = time.time()
        project_metrics = ProjectMetrics()

        # Get all files
        console.print("[bold blue]🔍 Finding files to analyze...[/bold blue]")
        all_files = []
        for root, dirs, files in os.walk(project_path):
            # Filter directories
            dirs[:] = [d for d in dirs if d not in self.exclude_dirs]

            for file in files:
                file_path = os.path.join(root, file)
                if self.detect_language(file_path) and not self.should_exclude_file(file_path):
                    all_files.append(file_path)

        console.print(f"[bold green]🔍 Found {len(all_files)} files to analyze[/bold green]")

        # Set up a progress display
        total_files = len(all_files)
        if total_files == 0:
            console.print("[yellow]No files to analyze[/yellow]")
            return project_metrics

        with Progress(
                SpinnerColumn(),
                TextColumn("[bold blue]Processing...", justify="right"),
                BarColumn(bar_width=40),
                "[progress.percentage]{task.percentage:>3.1f}%",
                "•",
                TextColumn("[cyan]{task.completed}/{task.total}[/cyan]", justify="right"),
                "•",
                TimeElapsedColumn(),
                "•",
                TimeRemainingColumn(),
                console=console
        ) as progress:
            task = progress.add_task("[cyan]Analyzing files...", total=total_files)

            # Process files
            stats_interval = max(100, total_files // 10)  # Show stats every ~10% or 100 files
            stats_counter = 0
            language_stats = {}

            for i, file_path in enumerate(all_files):
                # Update progress
                progress.update(task, advance=1, description=f"[cyan]Analyzing {os.path.basename(file_path)}")

                try:
                    # Process this file with a timeout and additional safeguards
                    def analyze_single_file():
                        try:
                            return self.analyze_file(file_path)
                        except Exception as e:
                            console.print(f"[red]❌ Exception in analyze_file: {str(e)}[/red]")
                            return None

                    timeout_runner = FunctionWithTimeout(timeout=TIMEOUT_SECONDS)
                    result = timeout_runner.run_with_timeout(analyze_single_file)

                    if isinstance(result, TimeoutError):
                        # Quietly log timeouts rather than printing to console
                        continue
                    elif isinstance(result, Exception):
                        # Quietly log errors rather than printing to console
                        continue

                    metrics = result
                    if metrics:
                        project_metrics.file_metrics.append(metrics)

                        # Update aggregated stats - add safeguards for None values
                        project_metrics.total_files += 1
                        project_metrics.total_loc += metrics.loc or 0
                        project_metrics.total_sloc += metrics.sloc or 0
                        project_metrics.total_comments += metrics.comments or 0
                        project_metrics.total_blanks += metrics.blanks or 0
                        project_metrics.total_classes += metrics.classes or 0
                        project_metrics.total_functions += metrics.functions or 0
                        project_metrics.total_methods += metrics.methods or 0
                        project_metrics.project_size += metrics.file_size or 0

                        # Language distribution
                        if metrics.language:
                            project_metrics.languages[metrics.language] = project_metrics.languages.get(
                                metrics.language, 0) + 1
                            language_stats[metrics.language] = language_stats.get(metrics.language, 0) + 1

                        # Dependencies
                        if metrics.imports:
                            for imp in metrics.imports:
                                project_metrics.dependencies[imp] = project_metrics.dependencies.get(imp, 0) + 1

                        # Print occasional stats rather than per-file messages
                        stats_counter += 1
                        if stats_counter >= stats_interval:
                            # Show summary stats periodically
                            elapsed = time.time() - start_time
                            files_per_sec = i / elapsed if elapsed > 0 else 0
                            console.print(
                                f"\n[bold green]📊 Progress: {i + 1}/{total_files} files processed ({files_per_sec:.1f} files/sec)[/bold green]")

                            # Show top languages
                            if language_stats:
                                top_langs = sorted(language_stats.items(), key=lambda x: x[1], reverse=True)[:3]
                                lang_summary = ", ".join(f"{lang}: {count}" for lang, count in top_langs)
                                console.print(f"[green]Top languages: {lang_summary}[/green]")

                            stats_counter = 0

                except Exception as e:
                    # Continue with next file after error (without printing)
                    continue

        console.print(
            f"\n[bold green]✅ Processing complete. {project_metrics.total_files} files successfully analyzed.[/bold green]")

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
                                                      int(100 - (sum(len(f.security_issues) + len(f.code_smells)
                                                                 for f in
                                                                 metrics.file_metrics) / metrics.total_files * 10))))

            avg_maintainability = sum(f.maintainability_index for f in metrics.file_metrics) / len(metrics.file_metrics)
            metrics.maintainability_score = max(0, min(100, int(avg_maintainability)))


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
        padding=(1, 2),
        title_align="center",
        highlight=True
    )


def create_language_distribution_table(metrics: ProjectMetrics) -> Table:
    """Create language distribution table"""
    table = Table(
        title="🌐 Language Distribution",
        box=box.ROUNDED,
        title_style="bold blue",
        border_style="cyan",
        highlight=True
    )
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
    table = Table(
        title="⚡ Complexity Distribution",
        box=box.ROUNDED,
        title_style="bold blue",
        border_style="cyan",
        highlight=True
    )
    table.add_column("Complexity Level", style="cyan")
    table.add_column("Files", justify="right", style="magenta")
    table.add_column("Percentage", justify="right", style="green")

    total_files = sum(metrics.complexity_distribution.values())

    for level in ComplexityLevel:
        # noinspection PyTypeChecker
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
    table = Table(
        title="🔥 Code Hotspots (Most Complex Files)",
        box=box.ROUNDED,
        title_style="bold blue",
        border_style="cyan",
        highlight=True
    )
    table.add_column("File", style="cyan", max_width=50)
    table.add_column("Lines", justify="right", style="magenta")
    table.add_column("Complexity", justify="right", style="red")
    table.add_column("Issues", justify="right", style="yellow")

    for file_metrics in metrics.most_complex_files[:10]:
        # Handle paths on different drives by using Path
        try:
            # Try relative path first
            relative_path = os.path.relpath(file_metrics.file_path)
        except ValueError:
            # If on a different drive, just use the basename or full path
            path_obj = Path(file_metrics.file_path)
            # Use parent directory + filename for better context
            if path_obj.parent.name:
                relative_path = str(Path(path_obj.parent.name) / path_obj.name)
            else:
                relative_path = path_obj.name

        issues = len(file_metrics.security_issues) + len(file_metrics.code_smells)

        # Color code based on issue count
        issue_style = "green" if issues == 0 else "yellow" if issues < 3 else "red"

        table.add_row(
            relative_path,
            str(file_metrics.sloc),
            f"{file_metrics.complexity_score:.0f}",
            f"[{issue_style}]{issues if issues > 0 else '✅'}[/{issue_style}]"
        )

    return table


def create_dependencies_table(metrics: ProjectMetrics) -> Table:
    """Create top dependencies table"""
    table = Table(
        title="📦 Top Dependencies",
        box=box.ROUNDED,
        title_style="bold blue",
        border_style="cyan",
        highlight=True
    )
    table.add_column("Module", style="cyan")
    table.add_column("Usage Count", justify="right", style="magenta")

    # Get top 15 dependencies
    top_deps = sorted(metrics.dependencies.items(), key=lambda x: x[1], reverse=True)[:15]

    for module, count in top_deps:
        table.add_row(module, str(count))

    return table


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
