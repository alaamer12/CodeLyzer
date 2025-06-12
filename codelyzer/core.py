#!/usr/bin/env python3
"""
Enhanced Codebase Analyzer
A powerful, robust tool for analyzing code repositories with beautiful terminal output.
Supports multiple programming languages with detailed metrics and visualizations.
"""
from __future__ import annotations

import json
import os
import time
from typing import Dict, List, Set, Optional, Tuple

import pandas as pd

from codelyzer.analyzers import SecurityAnalyzer, CodeSmellAnalyzer, ComplexityAnalyzer, \
    PatternBasedAnalyzer
from codelyzer.ast_analyzers import ASTAnalyzer, PythonASTAnalyzer, JavaScriptASTAnalyzer, \
    TypeScriptASTAnalyzer, RustStubASTAnalyzer
from codelyzer.config import DEFAULT_EXCLUDED_DIRS, LANGUAGE_CONFIGS, TIMEOUT_SECONDS
from codelyzer.console import (
    console, create_analysis_progress_bar, create_finding_files_progress_bar,
    logger, debug, debug_log
)
from codelyzer.helpers import StandardFileDiscovery, ProjectMetricsProcessor, Scoring
from codelyzer.metrics import FileMetrics, ProjectMetrics, create_file_metrics
from codelyzer.utils import FunctionWithTimeout


@debug
def register_metric_providers() -> None:
    """Register all metric providers to the ASTAnalyzer base class"""
    logger.info("Registering metric providers")

    # Register each provider
    ASTAnalyzer.register_metric_provider(SecurityAnalyzer())
    ASTAnalyzer.register_metric_provider(ComplexityAnalyzer())
    ASTAnalyzer.register_metric_provider(CodeSmellAnalyzer())
    ASTAnalyzer.register_metric_provider(PatternBasedAnalyzer())
    
    logger.debug("All metric providers registered successfully")


@debug
def initialize_analyzers() -> Dict[str, ASTAnalyzer]:
    """Initialize analyzers for different languages (strategy pattern)"""
    logger.info("Initializing language analyzers")
    
    # Register metric providers (once for all analyzers)
    register_metric_providers()
    
    # Define analyzers configuration
    analyzer_config = {
        'python': {
            'class': PythonASTAnalyzer,
            'aliases': []
        },
        'javascript': {
            'class': JavaScriptASTAnalyzer,
            'aliases': ['jsx']
        },
        'typescript': {
            'class': TypeScriptASTAnalyzer,
            'aliases': ['tsx']
        },
        'rust': {
            'class': RustStubASTAnalyzer,
            'aliases': []
        }
    }
    
    analyzers = {}
    
    # Initialize each analyzer with error handling
    for language, config in analyzer_config.items():
        try:
            analyzer = config['class']()
            analyzers[language] = analyzer
            
            # Add any language aliases
            for alias in config['aliases']:
                analyzers[alias] = analyzer
            
            logger.debug(f"Initialized {language} analyzer successfully")
                
        except Exception as e:
            logger.warning(f"{language.capitalize()} analyzer not available: {str(e)}")
            console.print(f"[yellow]Warning: {language.capitalize()} analyzer not available: {str(e)}[/yellow]")
    
    logger.info(f"Initialized {len(analyzers)} language analyzers")
    return analyzers


def get_file_size(file_path: str) -> int:
    """Get the size of a file safely"""
    try:
        size = os.path.getsize(file_path)
        debug_log(f"File size for {file_path}: {size} bytes")
        return size
    except OSError as e:
        logger.warning(f"Failed to get file size for {file_path}: {str(e)}")
        return 0


def read_content(file_path: str) -> Optional[str]:
    """Read file content safely"""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            debug_log(f"Read {len(content)} chars from {file_path}")
            return content
    except Exception as e:
        logger.warning(f"Failed to read content from {file_path}: {str(e)}")
        return None


class AdvancedCodeAnalyzer:
    """Advanced code analyzer with multi-language support and modular architecture"""

    def __init__(self, exclude_dirs: Set[str] = None, include_tests: bool = False):
        logger.info("Initializing AdvancedCodeAnalyzer")
        
        # Prepare exclude dirs
        self.exclude_dirs = (exclude_dirs or set()) | DEFAULT_EXCLUDED_DIRS
        if not include_tests:
            self.exclude_dirs.update({'test', 'tests', '__tests__', 'spec', 'specs'})
            
        logger.debug(f"Exclusion list contains {len(self.exclude_dirs)} directories")

        # Initialize components (dependency injection)
        self.file_discovery = StandardFileDiscovery(self.exclude_dirs, LANGUAGE_CONFIGS)
        self.security_analyzer = SecurityAnalyzer()
        self.code_smell_analyzer = CodeSmellAnalyzer()
        self.complexity_analyzer = ComplexityAnalyzer()
        self.pattern_analyzer = PatternBasedAnalyzer()
        self.metrics_processor = ProjectMetricsProcessor()
        self.scoring = Scoring()

        # Initialize language-specific analyzers
        self.language_analyzers = initialize_analyzers()
        logger.info("AdvancedCodeAnalyzer initialization complete")

    @debug
    def analyze_file(self, file_path: str) -> Optional[FileMetrics]:
        """Analyze a single file using the appropriate analyzer"""
        try:
            if not self._should_analyze_file(file_path):
                debug_log(f"Skipping file: {file_path}")
                return None

            language = self.file_discovery.detect_language(file_path)
            file_size = get_file_size(file_path)
            logger.debug(f"Analyzing file: {file_path} (language: {language}, size: {file_size})")

            metrics, content = self._get_file_metrics_and_content(file_path, language, file_size)

            # If an AST analyzer was used, it already ran all metric providers.
            # Otherwise, run the remaining analyzers for non-AST (e.g., pattern-based) analysis.
            if metrics and content and not self.language_analyzers.get(language):
                logger.debug(f"Applying additional analysis for {file_path}")
                self._apply_additional_analysis(file_path, content, metrics)

            if metrics:
                logger.debug(f"File analysis complete: {file_path}, complexity: {metrics.complexity_score:.1f}")
            
            return metrics

        except Exception as e:
            logger.error(f"Error analyzing file {file_path}: {str(e)}", exc_info=True)
            return self._create_fallback_metrics(file_path, e)

    def _should_analyze_file(self, file_path: str) -> bool:
        """Check if the file should be analyzed"""
        if not self.file_discovery.should_include_file(file_path):
            debug_log(f"File excluded by pattern: {file_path}")
            return False

        language = self.file_discovery.detect_language(file_path)
        if language is None:
            debug_log(f"Unsupported language for file: {file_path}")
            
        return language is not None

    @debug
    def _get_file_metrics_and_content(self, file_path: str, language: str, file_size: int) -> Tuple[
                                    Optional[FileMetrics], Optional[str]]:
        """Get metrics and content for a file using appropriate analyzer"""
        analyzer = self.language_analyzers.get(language)
        content = None
        metrics = None

        if analyzer:
            logger.debug(f"Using {language} AST analyzer for {file_path}")
            metrics = analyzer.analyze_file(file_path)
            if metrics:
                metrics.base.file_size = file_size
                # Content is read inside the analyzer, but we might need it here for other analyzers
                # if the AST-based one doesn't also run them. Let's read it if not present.
                content = read_content(file_path)
        else:
            # Fall back to creating basic metrics for non-AST languages
            logger.debug(f"No AST analyzer available for {language}, using pattern analysis")
            metrics = create_file_metrics(file_path, language, file_size)
            content = read_content(file_path)

        return metrics, content

    def _apply_additional_analysis(self, file_path: str, content: str, metrics: FileMetrics) -> None:
        """Apply additional analyzers to the file content"""
        logger.debug(f"Applying security analysis to {file_path}")
        self.security_analyzer.analyze_file(metrics, content, None)
        
        logger.debug(f"Applying code smell analysis to {file_path}")
        self.code_smell_analyzer.analyze_file(metrics, content, None)
        
        logger.debug(f"Applying complexity analysis to {file_path}")
        self.complexity_analyzer.analyze_file(metrics, content, None)

    def _create_fallback_metrics(self, file_path: str, error: Exception) -> FileMetrics:
        """Create minimal metrics when analysis fails"""
        logger.warning(f"Creating fallback metrics for {file_path} due to error: {str(error)}")
        console.print(f"[yellow]Warning: Error analyzing {file_path}: {str(error)}[/yellow]")
        language = self.file_discovery.detect_language(file_path) or "unknown"
        metrics = create_file_metrics(file_path, language)
        metrics.base.loc = 0
        metrics.base.sloc = 0
        return metrics

    @debug
    def analyze_project(self, project_path: str) -> ProjectMetrics:
        """Analyze entire project"""
        logger.info(f"Starting project analysis: {project_path}")
        start_time = time.time()
        project_metrics = ProjectMetrics()

        # Discover files
        all_files = self._discover_project_files(project_path)

        # Handle empty file list
        if not all_files:
            logger.warning("No files found to analyze")
            console.print("[yellow]No files to analyze[/yellow]")
            return project_metrics

        logger.info(f"Beginning analysis of {len(all_files)} files")
        
        # Process files with progress bar
        self._process_files_with_progress(all_files, project_metrics, start_time)

        # Process final metrics
        self._finalize_project_metrics(project_metrics)
        project_metrics.analysis_duration = time.time() - start_time
        
        logger.info(f"Project analysis complete: {project_path}")
        logger.info(f"Found {project_metrics.total_files} files with {project_metrics.total_loc} lines of code")
        logger.info(f"Analysis took {project_metrics.analysis_duration:.2f} seconds")

        return project_metrics

    @debug
    def _discover_project_files(self, project_path: str) -> List[str]:
        """Discover files to analyze in the project"""
        logger.info(f"Discovering files in: {project_path}")
        finding_files_progress = create_finding_files_progress_bar()
        with finding_files_progress as progress:
            task = progress.add_task("[cyan]Finding files...", total=100)
            all_files = self.file_discovery.discover_files(project_path)
            progress.update(task, completed=len(all_files), total=len(all_files))
        
        logger.info(f"Found {len(all_files)} files to analyze")
        console.print(f"[bold green]🔍 Found {len(all_files)} files to analyze[/bold green]")
        return all_files

    def _process_files_with_progress(self, all_files: List[str], project_metrics: ProjectMetrics,
                                     start_time: float) -> None:
        """Process all files with progress tracking"""
        logger.info(f"Processing {len(all_files)} files with progress tracking")
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
        
        logger.info("File processing complete")

    @debug
    def _analyze_file_with_timeout(self, file_path: str) -> Optional[FileMetrics]:
        """Analyze a file with timeout protection"""
        debug_log(f"Analyzing with timeout: {file_path}")

        def analyze_with_timeout():
            return self.analyze_file(file_path)

        timeout_runner = FunctionWithTimeout(timeout=TIMEOUT_SECONDS)
        result = timeout_runner.run_with_timeout(analyze_with_timeout)
        
        if result is None:
            logger.warning(f"Analysis timeout for file: {file_path}")
            
        return result

    def _finalize_project_metrics(self, project_metrics: ProjectMetrics) -> None:
        """Calculate final project metrics"""
        logger.info("Finalizing project metrics")
        self.metrics_processor.process(project_metrics)
        project_metrics.code_quality_score = self.scoring.calculate_code_quality_score(project_metrics)
        project_metrics.maintainability_score = self.scoring.calculate_maintainability_score(project_metrics)
        logger.info(f"Quality score: {project_metrics.code_quality_score:.1f}, Maintainability: {project_metrics.maintainability_score:.1f}")

    def _update_project_metrics(self, project_metrics: ProjectMetrics, metrics: FileMetrics,
                                language_stats: Dict) -> None:
        """Update project metrics with file metrics"""
        language = metrics.language.lower()
        language_stats[language] = language_stats.get(language, 0) + 1
        
        # Add to project metrics
        project_metrics.file_metrics.append(metrics)
        
        # Track top complex files
        if metrics.complexity_score > 0:
            self._add_complex_file(project_metrics, metrics.file_path)
        
        debug_log(f"Updated project metrics with file: {metrics.file_path}")
    
    def _add_complex_file(self, project_metrics: ProjectMetrics, file_path: str) -> None:
        """Add a file to the most complex files list, sort and keep only top 100"""
        # Add file to the list if not already present
        if file_path not in project_metrics.most_complex_files:
            project_metrics.complexity.most_complex_files.append(file_path)
        
        # Sort the list by complexity
        project_metrics.complexity.most_complex_files.sort(
            key=lambda f: next((fm.complexity_score for fm in project_metrics.file_metrics if fm.file_path == f), 0),
            reverse=True
        )
        
        # Trim the list to the top 100 files
        if len(project_metrics.complexity.most_complex_files) > 100:
            project_metrics.complexity.most_complex_files = project_metrics.complexity.most_complex_files[:100]

    @staticmethod
    def _show_progress_stats(current: int, total: int, start_time: float, language_stats: Dict) -> None:
        """Show progress statistics during analysis"""
        elapsed = time.time() - start_time
        files_per_second = current / elapsed if elapsed > 0 else 0
        percent_done = (current / total) * 100 if total > 0 else 0
        
        # Calculate estimated time remaining
        if files_per_second > 0:
            remaining_files = total - current
            eta_seconds = remaining_files / files_per_second
            eta_str = f"{eta_seconds:.1f}s" if eta_seconds < 60 else f"{eta_seconds/60:.1f}m"
        else:
            eta_str = "N/A"
        
        logger.info(f"Progress: {percent_done:.1f}% ({current}/{total}), ETA: {eta_str}")
        debug_log(f"Language stats: {language_stats}")
        
        console.print(f"[dim]⏳ Progress: {percent_done:.1f}% ({current}/{total}) at {files_per_second:.1f} files/sec, ETA: {eta_str}[/dim]")


class ReportExport:
    """Export analysis results to various formats"""

    def __init__(self, metrics: ProjectMetrics, output_path: str):
        """Initialize with metrics and output path"""
        self.metrics = metrics
        self.output_path = output_path
        logger.info(f"Initializing report export to: {output_path}")

    def _prepare_report_data(self) -> Dict:
        """Prepare metrics data for export"""
        logger.debug("Preparing report data for export")
        
        # Prepare file metrics for serialization
        files_data = []
        for file_metric in self.metrics.file_metrics:
            file_data = {
                "path": file_metric.file_path,
                "language": file_metric.language,
                "loc": file_metric.loc,
                "sloc": file_metric.sloc,
                "complexity": file_metric.complexity_score,
                "classes": file_metric.classes,
                "functions": file_metric.functions,
                "methods": file_metric.methods,
                "security_issues": len(file_metric.security_issues),
                "code_smells": len(file_metric.code_smells_list)
            }
            files_data.append(file_data)
        
        # Main report structure
        report_data = {
            "project": {
                "total_files": self.metrics.total_files,
                "total_loc": self.metrics.total_loc,
                "total_sloc": self.metrics.total_sloc,
                "total_blanks": self.metrics.total_blanks,
                "total_comments": self.metrics.total_comments,
                "total_classes": self.metrics.total_classes,
                "total_functions": self.metrics.total_functions,
                "total_methods": self.metrics.total_methods,
                "code_quality_score": self.metrics.code_quality_score,
                "maintainability_score": self.metrics.maintainability_score,
                "languages": dict(self.metrics.languages),
                "language_distribution": dict(self.metrics.language_distribution),
                "complexity_distribution": {k: v for k, v in self.metrics.complexity_distribution.items() if isinstance(k, str)},
                "analysis_duration": self.metrics.analysis_duration
            },
            "files": files_data
        }
        
        logger.debug(f"Prepared report with {len(files_data)} file entries")
        return report_data

    @debug
    def to_json(self) -> None:
        """Export metrics to JSON format"""
        logger.info(f"Exporting metrics to JSON: {self.output_path}")
        report_data = self._prepare_report_data()
        
        try:
            with open(self.output_path, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2)
            logger.info(f"JSON export complete: {self.output_path}")
        except Exception as e:
            logger.error(f"Failed to export JSON: {str(e)}", exc_info=True)
            console.print(f"[red]Error exporting to JSON: {str(e)}[/red]")

    @debug
    def to_df(self) -> pd.DataFrame:
        """Convert file metrics to pandas DataFrame"""
        logger.debug("Converting metrics to DataFrame")
        report_data = self._prepare_report_data()
        df = pd.DataFrame(report_data["files"])
        return df
