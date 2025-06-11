from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, List, Optional, Set, Protocol

from codelyzer.config import DEFAULT_EXCLUDED_FILES
from codelyzer.metrics import FileMetrics, ProjectMetrics, ComplexityLevel, SecurityLevel


class FileDiscovery(Protocol):
    """Interface for file discovery components"""

    def discover_files(self, root_path: str) -> List[str]:
        """Discover files to analyze in the given path"""
        ...

    def should_include_file(self, file_path: str) -> bool:
        """Determine if a file should be included in analysis"""
        ...

    def detect_language(self, file_path: str) -> Optional[str]:
        """Detect the programming language of a file"""
        ...


class CodeQualityAnalyzer(Protocol):
    """Interface for code quality analysis components"""

    def analyze(self, file_path: str, content: str, metrics: FileMetrics) -> None:
        """Analyze code quality aspects and update metrics"""
        ...


class MetricsProcessor(Protocol):
    """Interface for metrics processing components"""

    def process_metrics(self, project_metrics: ProjectMetrics) -> None:
        """Process and calculate derived metrics"""
        ...


# ===== Component Implementations =====

class StandardFileDiscovery:
    """Standard implementation of file discovery"""

    def __init__(self, exclude_dirs: Set[str], language_configs: Dict):
        self.exclude_dirs = exclude_dirs
        self.language_detectors = self._build_language_detectors(language_configs)

    @staticmethod
    def _build_language_detectors(language_configs: Dict) -> Dict[str, List[str]]:
        """Build file extension to language mapping"""
        detectors = {}
        for lang, config in language_configs.items():
            for ext in config['extensions']:
                if ext not in detectors:
                    detectors[ext] = []
                detectors[ext].append(lang)
        return detectors

    def discover_files(self, root_path: str) -> List[str]:
        """Discover all analyzable files in the given path"""
        all_files = []
        for root, dirs, files in os.walk(root_path):
            # Filter directories
            dirs[:] = [d for d in dirs if d not in self.exclude_dirs]

            for file in files:
                file_path = os.path.join(root, file)
                if self.detect_language(file_path) and self.should_include_file(file_path):
                    all_files.append(file_path)

        return all_files

    def should_include_file(self, file_path: str) -> bool:
        """Determine if a file should be included in analysis"""
        path = Path(file_path)

        # Check if any part of the path contains excluded directories
        for part in path.parts:
            if part in self.exclude_dirs:
                return False

        # Check excluded file patterns
        for pattern in DEFAULT_EXCLUDED_FILES:
            if path.match(pattern):
                return False

        return True

    def detect_language(self, file_path: str) -> Optional[str]:
        """Detect programming language from file extension"""
        ext = Path(file_path).suffix.lower()
        languages = self.language_detectors.get(ext, [])
        return languages[0] if languages else None


class ProjectMetricsProcessor:
    """Processes project metrics to calculate derived metrics"""

    @staticmethod
    def process_metrics(metrics: ProjectMetrics) -> None:
        """Calculate derived metrics and rankings"""
        if not metrics.file_metrics:
            return

        # Sort by complexity
        metrics.file_metrics.sort(key=lambda x: x.complexity_score, reverse=True)
        # Update most complex files - use nested attribute instead of top-level property
        metrics.complexity.most_complex_files = [file.file_path for file in metrics.file_metrics[:10]]

        # Sort by size
        sorted_by_size = sorted(metrics.file_metrics, key=lambda x: x.sloc, reverse=True)
        # Update largest files - use nested attribute instead of top-level property
        metrics.code_quality.largest_files = [file.file_path for file in sorted_by_size[:10]]

        # Complexity distribution
        Scoring.calculate_complexity_distribution(metrics)

        # Quality scores
        Scoring.calculate_quality_scores(metrics)


class Scoring:
    """Class for handling code scoring and metrics aggregation"""

    @staticmethod
    def update_aggregate_metrics(project_metrics: ProjectMetrics, file_metrics: FileMetrics) -> ProjectMetrics:
        """Update aggregate metrics"""
        # Update base metrics
        project_metrics.base.total_files += 1
        project_metrics.base.total_loc += file_metrics.loc or 0
        project_metrics.base.total_sloc += file_metrics.sloc or 0
        project_metrics.base.total_comments += file_metrics.comments or 0
        project_metrics.base.total_blanks += file_metrics.blanks or 0
        project_metrics.base.project_size += file_metrics.file_size or 0

        # Update language statistics
        lang = file_metrics.language
        project_metrics.base.languages[lang] = project_metrics.base.languages.get(lang, 0) + 1

        # Update structure metrics
        project_metrics.structure.total_classes += file_metrics.classes or 0
        project_metrics.structure.total_functions += file_metrics.functions or 0
        project_metrics.structure.total_methods += file_metrics.methods or 0

        # Track dependencies
        for imp in file_metrics.imports:
            project_metrics.structure.dependencies[imp] = project_metrics.structure.dependencies.get(imp, 0) + 1

        return project_metrics

    @staticmethod
    def calculate_complexity_distribution(metrics: ProjectMetrics) -> None:
        """Calculate complexity distribution across files"""
        for file_metrics in metrics.file_metrics:
            level = Scoring.determine_complexity_level(file_metrics.complexity_score)
            metrics.complexity.complexity_distribution[level] = metrics.complexity.complexity_distribution.get(level,
                                                                                                               0) + 1

    @staticmethod
    def determine_complexity_level(score: float) -> ComplexityLevel:
        """Determine complexity level based on score"""
        if score < 50:
            return ComplexityLevel.TRIVIAL
        elif score < 200:
            return ComplexityLevel.LOW
        elif score < 500:
            return ComplexityLevel.MODERATE
        elif score < 1000:
            return ComplexityLevel.HIGH
        elif score < 2000:
            return ComplexityLevel.VERY_HIGH
        else:
            return ComplexityLevel.EXTREME

    @staticmethod
    def calculate_quality_scores(metrics: ProjectMetrics) -> None:
        """Calculate code quality scores"""
        if metrics.total_sloc <= 0:
            return

        # Calculate security score
        security_issues = sum(len(file_metrics.security_issues) for file_metrics in metrics.file_metrics)
        if security_issues > 0:
            metrics.security.security_score = max(0.0, 100 - (security_issues / metrics.total_files * 20))

        # Calculate code quality score (based on code smells and security issues)
        total_issues = sum(len(file_metrics.security_issues) + len(file_metrics.code_smells_list)
                           for file_metrics in metrics.file_metrics)
        if total_issues > 0:
            metrics.code_quality.code_quality_score = max(0, min(100,
                                                                 int(100 - (total_issues / metrics.total_files * 10))))
        else:
            metrics.code_quality.code_quality_score = 100

        # Calculate maintainability score
        valid_files = [f for f in metrics.file_metrics if
                       hasattr(f.complexity, 'maintainability_index') and f.complexity.maintainability_index > 0]
        if valid_files:
            avg_maintainability = sum(f.maintainability_index for f in valid_files) / len(valid_files)
            metrics.complexity.maintainability_score = max(0, min(100, int(avg_maintainability)))
            metrics.complexity.avg_maintainability_index = avg_maintainability

        # Calculate average cyclomatic complexity
        valid_cc_files = [f for f in metrics.file_metrics if f.cyclomatic_complexity > 0]
        if valid_cc_files:
            metrics.complexity.avg_cyclomatic_complexity = sum(f.cyclomatic_complexity for f in valid_cc_files) / len(
                valid_cc_files)

    @staticmethod
    def identify_hotspots(metrics: ProjectMetrics) -> None:
        """Identify code hotspots based on complexity and issues"""
        # Sort files by complexity
        sorted_by_complexity = sorted(metrics.file_metrics, key=lambda f: f.complexity_score, reverse=True)

        # Get most complex files
        metrics.complexity.most_complex_files = [f.file_path for f in sorted_by_complexity[:10]]

        # Get largest files
        sorted_by_size = sorted(metrics.file_metrics, key=lambda f: f.file_size, reverse=True)
        metrics.code_quality.largest_files = [f.file_path for f in sorted_by_size[:10]]

        # Identify hotspots (complex + security issues or code smells)
        hotspots = []
        for file_metrics in metrics.file_metrics:
            if (file_metrics.complexity_score > 200 and
                    (len(file_metrics.security_issues) > 0 or len(file_metrics.code_smells_list) > 0)):
                hotspots.append(file_metrics.file_path)
        metrics.code_quality.hotspots = hotspots[:10]  # Top 10 hotspots

    @staticmethod
    def calculate_security_summary(metrics: ProjectMetrics) -> None:
        """Calculate security summary statistics"""
        for file_metrics in metrics.file_metrics:
            for issue in file_metrics.security_issues:
                level = issue.get('level', SecurityLevel.MEDIUM_RISK)
                metrics.security.security_summary[level] = metrics.security.security_summary.get(level, 0) + 1

                # Track critical vulnerabilities
                if level == SecurityLevel.CRITICAL:
                    metrics.security.critical_vulnerabilities.append({
                        'file': file_metrics.file_path,
                        'issue': issue
                    })

    @staticmethod
    def process_metrics(project_metrics: ProjectMetrics) -> ProjectMetrics:
        """Process all metrics and calculate derived values"""
        Scoring.calculate_complexity_distribution(project_metrics)
        Scoring.calculate_quality_scores(project_metrics)
        Scoring.identify_hotspots(project_metrics)
        Scoring.calculate_security_summary(project_metrics)
        return project_metrics
