#!/usr/bin/env python3
"""
Enhanced Codebase Analyzer
A powerful, robust tool for analyzing code repositories with beautiful terminal output.
Supports multiple programming languages with detailed metrics and visualizations.
"""

import os
import json
import time
from typing import Dict, List, Optional, Set

from ast_analyzers import ASTAnalyzer, PythonASTAnalyzer, JavaScriptASTAnalyzer
from config import DEFAULT_EXCLUDED_DIRS, LANGUAGE_CONFIGS, FileMetrics, ProjectMetrics, TIMEOUT_SECONDS
from utils import FunctionWithTimeout, TimeoutError
from console import console, create_analysis_progress_bar
from helpers import StandardFileDiscovery, SecurityAnalyzer, CodeSmellAnalyzer, ComplexityAnalyzer, \
    PatternBasedAnalyzer, ProjectMetricsProcessor


def initialize_analyzers() -> Dict[str, ASTAnalyzer]:
    """Initialize analyzers for different languages (strategy pattern)"""
    analyzers = {}

    # Add Python analyzer
    python_analyzer = PythonASTAnalyzer()
    analyzers['python'] = python_analyzer

    # Add JavaScript analyzer
    try:
        js_analyzer = JavaScriptASTAnalyzer()
        analyzers['javascript'] = js_analyzer
        analyzers['typescript'] = js_analyzer  # Same analyzer handles both
        analyzers['jsx'] = js_analyzer
    except Exception as e:
        console.print(f"[yellow]Warning: JavaScript analyzer not available: {str(e)}[/yellow]")

    # Add other analyzers as needed
    # analyzers['java'] = JavaASTAnalyzer()

    return analyzers


def get_file_size(file_path: str) -> int:
    """Get the size of a file safely"""
    try:
        return os.path.getsize(file_path)
    except OSError:
        return 0


def read_content(file_path: str) -> Optional[str]:
    """Read file content safely"""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()
    except Exception:
        return None


class AdvancedCodeAnalyzer:
    """Advanced code analyzer with multi-language support and modular architecture"""

    def __init__(self, exclude_dirs: Set[str] = None, include_tests: bool = False):
        # Prepare exclude dirs
        self.exclude_dirs = (exclude_dirs or set()) | DEFAULT_EXCLUDED_DIRS
        if not include_tests:
            self.exclude_dirs.update({'test', 'tests', '__tests__', 'spec', 'specs'})

        # Initialize components (dependency injection)
        self.file_discovery = StandardFileDiscovery(self.exclude_dirs, LANGUAGE_CONFIGS)
        self.security_analyzer = SecurityAnalyzer()
        self.code_smell_analyzer = CodeSmellAnalyzer()
        self.complexity_analyzer = ComplexityAnalyzer(LANGUAGE_CONFIGS)
        self.pattern_analyzer = PatternBasedAnalyzer(LANGUAGE_CONFIGS)
        self.metrics_processor = ProjectMetricsProcessor()

        # Initialize language-specific analyzers
        self.language_analyzers = initialize_analyzers()

    def analyze_file(self, file_path: str) -> Optional[FileMetrics]:
        """Analyze a single file using the appropriate analyzer"""
        try:
            if not self._should_analyze_file(file_path):
                return None

            language = self.file_discovery.detect_language(file_path)
            file_size = get_file_size(file_path)

            metrics, content = self._get_file_metrics_and_content(file_path, language, file_size)

            if metrics and content:
                self._apply_additional_analysis(file_path, content, metrics)

            return metrics

        except Exception as e:
            return self._create_fallback_metrics(file_path, e)

    def _should_analyze_file(self, file_path: str) -> bool:
        """Check if the file should be analyzed"""
        if not self.file_discovery.should_include_file(file_path):
            return False

        language = self.file_discovery.detect_language(file_path)
        return language is not None

    def _get_file_metrics_and_content(self, file_path: str, language: str, file_size: int) -> tuple[
                                        Optional[FileMetrics], Optional[str]]:
        """Get metrics and content for a file using appropriate analyzer"""
        analyzer = self.language_analyzers.get(language)
        content = None

        if analyzer:
            metrics = analyzer.analyze_file(file_path)
            if metrics:
                metrics.file_size = file_size
                content = read_content(file_path)
        else:
            # Fall back to pattern-based analysis
            result = self.pattern_analyzer.analyze_file(file_path, language)
            if isinstance(result, tuple):
                metrics, content = result
            else:
                metrics = result
                content = None

            if metrics:
                metrics.file_size = file_size

        return metrics, content

    def _apply_additional_analysis(self, file_path: str, content: str, metrics: FileMetrics) -> None:
        """Apply additional analyzers to the file content"""
        self.security_analyzer.analyze(file_path, content, metrics)
        self.code_smell_analyzer.analyze(file_path, content, metrics)
        self.complexity_analyzer.analyze(file_path, content, metrics)

    def _create_fallback_metrics(self, file_path: str, error: Exception) -> FileMetrics:
        """Create minimal metrics when analysis fails"""
        console.print(f"[yellow]Warning: Error analyzing {file_path}: {str(error)}[/yellow]")
        language = self.file_discovery.detect_language(file_path) or "unknown"
        metrics = FileMetrics(file_path=file_path, language=language)
        metrics.loc = metrics.sloc = 0
        return metrics

    def analyze_project(self, project_path: str) -> ProjectMetrics:
        """Analyze entire project"""
        start_time = time.time()
        project_metrics = ProjectMetrics()

        # Discover files
        all_files = self._discover_project_files(project_path)

        # Handle empty file list
        if not all_files:
            console.print("[yellow]No files to analyze[/yellow]")
            return project_metrics

        # Process files with progress bar
        self._process_files_with_progress(all_files, project_metrics, start_time)

        # Process final metrics
        self._finalize_project_metrics(project_metrics)
        project_metrics.analysis_duration = time.time() - start_time

        return project_metrics

    def _discover_project_files(self, project_path: str) -> List[str]:
        """Discover files to analyze in the project"""
        console.print("[bold blue]🔍 Finding files to analyze...[/bold blue]")
        all_files = self.file_discovery.discover_files(project_path)
        console.print(f"[bold green]🔍 Found {len(all_files)} files to analyze[/bold green]")
        return all_files

    def _process_files_with_progress(self, all_files: List[str], project_metrics: ProjectMetrics,
                                     start_time: float) -> None:
        """Process all files with progress tracking"""
        with create_analysis_progress_bar() as progress:
            task = progress.add_task("[cyan]Analyzing files...", total=len(all_files))

            # Track language stats for periodic updates
            stats_counter = 0
            stats_interval = max(100, len(all_files) // 10)
            language_stats = {}

            for i, file_path in enumerate(all_files):
                # Update progress
                progress.update(task, advance=1, description=f"[cyan]Analyzing {os.path.basename(file_path)}")

                # Analyze file with timeout protection
                metrics = self._analyze_file_with_timeout(file_path)

                if metrics:
                    self._update_project_metrics(project_metrics, metrics, language_stats)

                    # Show periodic stats
                    stats_counter += 1
                    if stats_counter >= stats_interval:
                        self._show_progress_stats(i, len(all_files), start_time, language_stats)
                        stats_counter = 0

    def _analyze_file_with_timeout(self, file_path: str) -> Optional[FileMetrics]:
        """Analyze a file with timeout protection"""

        def analyze_with_timeout():
            return self.analyze_file(file_path)

        timeout_runner = FunctionWithTimeout(timeout=TIMEOUT_SECONDS)
        result = timeout_runner.run_with_timeout(analyze_with_timeout)

        if isinstance(result, (TimeoutError, Exception)):
            return None
        return result

    def _finalize_project_metrics(self, project_metrics: ProjectMetrics) -> None:
        """Process and finalize project metrics"""
        console.print(
            f"\n[bold green]✅ Processing complete. {project_metrics.total_files} files successfully analyzed.[/bold green]")
        self.metrics_processor.process_metrics(project_metrics)

    def _update_project_metrics(self, project_metrics: ProjectMetrics, metrics: FileMetrics,
                                language_stats: Dict) -> None:
        """Update project metrics with file metrics"""
        project_metrics.file_metrics.append(metrics)

        # Update aggregate metrics
        project_metrics = self._update_aggregate_metrics(project_metrics, metrics)

        # Language stats
        if metrics.language:
            project_metrics.languages[metrics.language] = project_metrics.languages.get(metrics.language, 0) + 1
            language_stats[metrics.language] = language_stats.get(metrics.language, 0) + 1

        # Dependencies
        if metrics.imports:
            for imp in metrics.imports:
                project_metrics.dependencies[imp] = project_metrics.dependencies.get(imp, 0) + 1

    @staticmethod
    def _update_aggregate_metrics(project_metrics: ProjectMetrics, metrics: FileMetrics) -> ProjectMetrics:
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
    def _show_progress_stats(current: int, total: int, start_time: float, language_stats: Dict) -> None:
        """Show progress statistics"""
        elapsed = time.time() - start_time
        files_per_sec = current / elapsed if elapsed > 0 else 0
        console.print(
            f"\n[bold green]📊 Progress: {current + 1}/{total} files processed ({files_per_sec:.1f} files/sec)[/bold green]")

        # Show top languages
        if language_stats:
            top_langs = sorted(language_stats.items(), key=lambda x: x[1], reverse=True)[:3]
            lang_summary = ", ".join(f"{lang}: {count}" for lang, count in top_langs)
            console.print(f"[green]Top languages: {lang_summary}[/green]")


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
