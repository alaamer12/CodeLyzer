import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, TypeVar, Literal, Optional

from codelyzer.metrics import ProjectMetrics, SecurityLevel

T = TypeVar('T', bound='ChartData')

# Theme constants
ThemeType = Literal["light", "dark"]

class ThemeColors:
    """Theme color constants for report styling"""
    
    # Light theme colors
    LIGHT = {
        # Base colors
        "bg_primary": "#f9fafb",
        "bg_secondary": "#ffffff",
        "text_primary": "#1f2937",
        "text_secondary": "#4b5563",
        "border": "#e5e7eb",
        "border_secondary": "#d1d5db",
        
        # Brand colors
        "brand_primary": "#3b82f6",
        "brand_primary_dark": "#2563eb",
        "brand_secondary": "#60a5fa",
        "brand_gradient_from": "#3b82f6",
        "brand_gradient_to": "#2563eb",
        
        # Status colors
        "success": "#22c55e",
        "success_light": "#dcfce7",
        "success_dark": "#16a34a",
        "warning": "#eab308",
        "warning_light": "#fef9c3",
        "warning_dark": "#ca8a04",
        "danger": "#ef4444",
        "danger_light": "#fee2e2",
        "danger_dark": "#dc2626",
        "info": "#06b6d4",
        "info_light": "#cffafe",
        "info_dark": "#0891b2",
        
        # UI Element colors
        "card_shadow": "rgba(0, 0, 0, 0.1)",
        "header_pattern": "rgba(255, 255, 255, 0.1)",
        "header_gradient_overlay": "rgba(255, 255, 255, 0.1)",
        
        # Selection colors
        "selection_bg": "#3b82f620",
        "selection_text": "#2563eb",
        
        # Chart colors
        "chart_colors": [
            "#3b82f6", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6",
            "#06b6d4", "#f97316", "#84cc16", "#ec4899", "#6366f1"
        ],
        
        # Component specific colors
        "complexity_low": "bg-green-100 text-green-800",
        "complexity_medium": "bg-yellow-100 text-yellow-800",
        "complexity_high": "bg-orange-100 text-orange-800",
        "complexity_very_high": "bg-red-100 text-red-800",
    }
    
    # Dark theme colors
    DARK = {
        # Base colors
        "bg_primary": "#111827",
        "bg_secondary": "#1f2937",
        "text_primary": "#f9fafb",
        "text_secondary": "#d1d5db",
        "border": "#374151",
        "border_secondary": "#4b5563",
        
        # Brand colors
        "brand_primary": "#3b82f6",
        "brand_primary_dark": "#2563eb",
        "brand_secondary": "#60a5fa",
        "brand_gradient_from": "#3b82f6",
        "brand_gradient_to": "#2563eb",
        
        # Status colors
        "success": "#22c55e",
        "success_light": "#064e3b",
        "success_dark": "#16a34a",
        "warning": "#eab308",
        "warning_light": "#422006",
        "warning_dark": "#ca8a04",
        "danger": "#ef4444",
        "danger_light": "#450a0a",
        "danger_dark": "#dc2626",
        "info": "#06b6d4",
        "info_light": "#083344",
        "info_dark": "#0891b2",
        
        # UI Element colors
        "card_shadow": "rgba(0, 0, 0, 0.25)",
        "header_pattern": "rgba(0, 0, 0, 0.2)",
        "header_gradient_overlay": "rgba(0, 0, 0, 0.3)",
        
        # Selection colors
        "selection_bg": "#3b82f630",
        "selection_text": "#60a5fa",
        
        # Chart colors - same as light theme for consistency
        "chart_colors": [
            "#3b82f6", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6",
            "#06b6d4", "#f97316", "#84cc16", "#ec4899", "#6366f1"
        ],
        
        # Component specific colors
        "complexity_low": "bg-green-900 text-green-100",
        "complexity_medium": "bg-yellow-900 text-yellow-100",
        "complexity_high": "bg-orange-900 text-orange-100",
        "complexity_very_high": "bg-red-900 text-red-100",
    }

# Function to copy favicon to output directory
def copy_favicon_to_output(output_dir: str) -> str:
    """
    Copy the favicon.png file from assets directory to the specified output directory
    
    Args:
        output_dir: The output directory path
        
    Returns:
        The path to the copied favicon file relative to the output directory
    """
    # Create assets/static directory in the output directory
    assets_dir = Path(output_dir) / "assets" / "static"
    assets_dir.mkdir(parents=True, exist_ok=True)
    
    # Path to the favicon in the assets directory
    src_favicon_path = Path(__file__).parent.parent / "assets" / "favicon.png"
    
    # Path to the destination favicon
    dest_favicon_path = assets_dir / "favicon.png"
    
    # Copy the favicon file
    shutil.copy2(src_favicon_path, dest_favicon_path)
    
    # Return the relative path to be used in HTML
    return "assets/static/favicon.png"

class ReportComponent:
    """Base class for HTML report components"""

    @staticmethod
    def render(metrics: 'ProjectMetrics') -> str:
        """Render the HTML component"""
        return ""


class TableComponent(ReportComponent):
    """Base class for table components"""

    @staticmethod
    def render(metrics: 'ProjectMetrics') -> str:
        """Render the table component
        
        Args:
            metrics: ProjectMetrics object containing analysis data
            
        Returns:
            HTML string for the table component
        """
        return ""


class ChartData:
    """Base class for chart data preparation"""

    @staticmethod
    def prepare_data(metrics: 'ProjectMetrics') -> Dict[str, Any]:
        """Prepare data for a chart
        
        Args:
            metrics: ProjectMetrics object containing analysis data
            
        Returns:
            Dictionary with prepared data for chart
        """
        return {}


class LanguageChartData(ChartData):
    """Language distribution chart data"""

    @staticmethod
    def prepare_data(metrics: 'ProjectMetrics', *args, **kwargs) -> Dict[str, Any]:
        """Prepare language distribution data
        
        Args:
            metrics: ProjectMetrics object containing analysis data
            
        Returns:
            Dictionary with language labels and values
        """
        languages = metrics.language_distribution
        labels = list(languages.keys())
        values = list(languages.values())

        # Sort by value in descending order for better visualization
        sorted_data = sorted(zip(labels, values), key=lambda x: x[1], reverse=True)

        # Unpack the sorted data
        sorted_labels, sorted_values = zip(*sorted_data) if sorted_data else ([], [])

        return {
            "labels": list(sorted_labels),
            "values": list(sorted_values)
        }


class ComplexityChartData(ChartData):
    """Complexity distribution chart data"""

    @staticmethod
    def prepare_data(metrics: 'ProjectMetrics') -> Dict[str, Any]:
        """Prepare complexity distribution data
        
        Args:
            metrics: ProjectMetrics object containing analysis data
            
        Returns:
            Dictionary with complexity labels and values
        """
        complexity_counts = {
            "Low": 0,
            "Medium": 0,
            "High": 0,
            "Very High": 0
        }

        for file_metric in metrics.file_metrics:
            complexity_score = file_metric.complexity_score
            if complexity_score < 10:
                complexity_counts["Low"] += 1
            elif complexity_score < 20:
                complexity_counts["Medium"] += 1
            elif complexity_score < 30:
                complexity_counts["High"] += 1
            else:
                complexity_counts["Very High"] += 1

        return {
            "labels": list(complexity_counts.keys()),
            "values": list(complexity_counts.values())
        }


class SecurityIssuesChartData(ChartData):
    """Security issues chart data"""

    @staticmethod
    def prepare_data(metrics: 'ProjectMetrics') -> Dict[str, Any]:
        """Prepare security issues data
        
        Args:
            metrics: ProjectMetrics object containing analysis data
            
        Returns:
            Dictionary with security issue severity labels and values
        """
        security_counts = {
            "Critical": 0,
            "High": 0,
            "Medium": 0,
            "Low": 0
        }

        for file_metric in metrics.file_metrics:
            for issue in file_metric.security_issues:
                level = issue.get('level', SecurityLevel.MEDIUM_RISK)
                severity = issue.get('severity', 'medium').lower()

                if level == SecurityLevel.CRITICAL or severity == 'critical':
                    security_counts["Critical"] += 1
                elif level == SecurityLevel.HIGH_RISK or severity == 'high':
                    security_counts["High"] += 1
                elif level == SecurityLevel.MEDIUM_RISK or severity == 'medium':
                    security_counts["Medium"] += 1
                else:
                    security_counts["Low"] += 1

        return {
            "labels": list(security_counts.keys()),
            "values": list(security_counts.values()),
            "colors": ["#ef4444", "#f97316", "#eab308", "#22c55e"]
        }


class CodeSmellsChartData(ChartData):
    """Code smells chart data"""

    @staticmethod
    def prepare_data(metrics: 'ProjectMetrics') -> Dict[str, Any]:
        """Prepare code smells data
        
        Args:
            metrics: ProjectMetrics object containing analysis data
            
        Returns:
            Dictionary with code smell severity labels and values
        """
        smell_counts = {
            "Critical": 0,
            "Major": 0,
            "Minor": 0
        }

        for file_metric in metrics.file_metrics:
            for smell in file_metric.code_smells_list:
                severity = smell.get('severity', 'minor').lower()

                if severity == 'critical':
                    smell_counts["Critical"] += 1
                elif severity == 'major':
                    smell_counts["Major"] += 1
                else:
                    smell_counts["Minor"] += 1

        return {
            "labels": list(smell_counts.keys()),
            "values": list(smell_counts.values()),
            "colors": ["#ef4444", "#f97316", "#22c55e"]
        }


class ComplexFilesTableComponent(TableComponent):
    """Complex files table component"""

    @staticmethod
    def render(metrics: 'ProjectMetrics') -> str:
        """Render the complex files table component
        
        Args:
            metrics: ProjectMetrics object containing analysis data
            
        Returns:
            HTML string for the complex files table
        """
        rows = ""

        # Create a mapping of file paths to file metrics for quick lookup
        file_metrics_map = {fm.file_path: fm for fm in metrics.file_metrics}
        
        # Ensure we have the most complex files
        # If most_complex_files is empty or doesn't have enough entries, recreate it based on complexity score
        if len(metrics.most_complex_files) < 15:
            # Sort files by complexity score in descending order
            sorted_files = sorted(metrics.file_metrics, key=lambda f: f.complexity_score, reverse=True)
            most_complex = [f.file_path for f in sorted_files[:15]]
            
            # Use these sorted files for display
            display_files = most_complex
        else:
            # Use the existing most_complex_files but ensure we only show the top 15
            display_files = metrics.most_complex_files[:15]

        # Loop through the most complex file paths and find corresponding FileMetrics objects
        for file_path in display_files:
            # Get the FileMetrics object for this file path
            file_metrics = file_metrics_map.get(file_path)

            if not file_metrics:
                continue

            # Extract the relative path
            relative_path = file_path.replace(os.getcwd(), "").lstrip(os.sep).replace("\\", "/")

            # Count issues
            issues = len(file_metrics.security_issues) + len(file_metrics.code_smells_list)

            # Get complexity badge class based on score
            if file_metrics.complexity_score >= 30:
                complexity_badge = ThemeColors.LIGHT["complexity_very_high"] + " dark:" + ThemeColors.DARK["complexity_very_high"]
            elif file_metrics.complexity_score >= 20:
                complexity_badge = ThemeColors.LIGHT["complexity_high"] + " dark:" + ThemeColors.DARK["complexity_high"]
            elif file_metrics.complexity_score >= 10:
                complexity_badge = ThemeColors.LIGHT["complexity_medium"] + " dark:" + ThemeColors.DARK["complexity_medium"]
            else:
                complexity_badge = ThemeColors.LIGHT["complexity_low"] + " dark:" + ThemeColors.DARK["complexity_low"]

            # Format issues display
            if issues > 0:
                issues_display = f'<span class="text-red-600 dark:text-red-400 font-semibold">{issues}</span>'
            else:
                issues_display = '<span class="text-green-600 dark:text-green-400">0</span>'

            # Add data attributes for sorting
            rows += f'''
        <tr class="hover:bg-gray-50 dark:hover:bg-gray-800 hover:scale-[1.005] transition-all duration-200" data-complexity="{file_metrics.complexity_score}" data-loc="{file_metrics.sloc}">
            <td class="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
                <div class="flex items-center gap-2 font-mono text-sm text-gray-600 dark:text-gray-400 max-w-xs overflow-hidden text-ellipsis whitespace-nowrap bg-gray-50 dark:bg-gray-800 px-2 py-1 rounded border border-gray-200 dark:border-gray-700" title="{relative_path}">
                    <i class="fas fa-file-code" aria-hidden="true"></i>
                    {relative_path}
                </div>
            </td>
            <td class="px-6 py-4 border-b border-gray-200 dark:border-gray-700"><span class="font-semibold text-gray-900 dark:text-gray-100 tabular-nums">{file_metrics.sloc:,}</span></td>
            <td class="px-6 py-4 border-b border-gray-200 dark:border-gray-700"><span class="inline-flex items-center px-3 py-1 rounded-lg text-xs font-medium uppercase tracking-wide {complexity_badge}">{file_metrics.complexity_score:.0f}</span></td>
            <td class="px-6 py-4 border-b border-gray-200 dark:border-gray-700">{issues_display}</td>
        </tr>'''

        # Add sortable class and click handlers to the table headers
        return f'''
        <div class="bg-card p-6 rounded-2xl shadow-md border border-theme h-full">
            <h3 class="text-lg font-semibold mb-4 flex items-center gap-2 text-body">
                <i class="fas fa-exclamation-triangle text-orange-500" aria-hidden="true"></i> 
                Most Complex Files
            </h3>
            <div class="overflow-x-auto">
                <table class="min-w-full complex-files-table" id="complex-files-table">
                    <thead>
                        <tr>
                            <th class="px-6 py-3 border-b-2 border-gray-300 dark:border-gray-700 text-left text-xs font-semibold text-gray-600 dark:text-gray-400 uppercase tracking-wider">File</th>
                            <th class="px-6 py-3 border-b-2 border-gray-300 dark:border-gray-700 text-left text-xs font-semibold text-gray-600 dark:text-gray-400 uppercase tracking-wider sortable cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800" data-sort="loc">
                                LOC
                                <i class="fas fa-sort ml-1 text-gray-400"></i>
                            </th>
                            <th class="px-6 py-3 border-b-2 border-gray-300 dark:border-gray-700 text-left text-xs font-semibold text-gray-600 dark:text-gray-400 uppercase tracking-wider sortable cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800" data-sort="complexity">
                                Complexity
                                <i class="fas fa-sort-down ml-1 text-blue-500"></i>
                            </th>
                            <th class="px-6 py-3 border-b-2 border-gray-300 dark:border-gray-700 text-left text-xs font-semibold text-gray-600 dark:text-gray-400 uppercase tracking-wider">Issues</th>
                        </tr>
                    </thead>
                    <tbody>
                        {rows}
                    </tbody>
                </table>
            </div>
        </div>'''


class DependenciesTableComponent(TableComponent):
    """Dependencies table component"""

    @staticmethod
    def render(metrics: 'ProjectMetrics') -> str:
        """Render the dependencies table component
        
        Args:
            metrics: ProjectMetrics object containing analysis data
            
        Returns:
            HTML string for the dependencies table
        """
        rows = DependenciesTableComponent._generate_dependency_rows(metrics)
        return DependenciesTableComponent._create_dependencies_table(rows)

    @staticmethod
    def _generate_dependency_rows(metrics: 'ProjectMetrics') -> str:
        """Generate HTML rows for dependencies
        
        Args:
            metrics: ProjectMetrics object containing analysis data
            
        Returns:
            HTML string containing table rows
        """
        # Check if dependencies exist and are structured as expected
        if not DependenciesTableComponent._has_valid_dependencies(metrics):
            return DependenciesTableComponent._create_empty_row()

        try:
            return DependenciesTableComponent._format_dependency_rows(metrics.structure.dependencies)
        except Exception:
            return DependenciesTableComponent._create_error_row()

    @staticmethod
    def _has_valid_dependencies(metrics: 'ProjectMetrics') -> bool:
        """Check if metrics contains valid dependencies
        
        Args:
            metrics: ProjectMetrics object containing analysis data
            
        Returns:
            True if dependencies exist and are properly structured
        """
        return hasattr(metrics.structure, 'dependencies') and isinstance(metrics.structure.dependencies, dict)

    @staticmethod
    def _format_dependency_rows(dependencies: dict) -> str:
        """Format dependency data into HTML rows
        
        Args:
            dependencies: Dictionary of dependencies with name->count mapping
            
        Returns:
            HTML string with formatted rows
        """
        rows = ""
        for name, count in list(dependencies.items())[:15]:  # Limit to 15 items
            rows += f'''
                <tr class="hover:bg-gray-50 dark:hover:bg-gray-800 hover:scale-[1.005] transition-all duration-200">
                    <td class="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
                        <div class="flex items-center gap-2 font-mono text-sm text-gray-600 dark:text-gray-400 max-w-xs overflow-hidden text-ellipsis whitespace-nowrap bg-gray-50 dark:bg-gray-800 px-2 py-1 rounded border border-gray-200 dark:border-gray-700">
                            <i class="fas fa-cubes" aria-hidden="true"></i>
                            {name}
                        </div>
                    </td>
                    <td class="px-6 py-4 border-b border-gray-200 dark:border-gray-700"><span class="font-semibold text-gray-900 dark:text-gray-100">{count}</span></td>
                    <td class="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
                        <span class="text-gray-400 dark:text-gray-500">-</span>
                    </td>
                </tr>'''
        return rows

    @staticmethod
    def _create_empty_row() -> str:
        """Create a placeholder row when no dependencies exist
        
        Returns:
            HTML string for empty state
        """
        return '''
            <tr>
                <td class="px-6 py-4 border-b border-gray-200 dark:border-gray-700" colspan="3">
                    <div class="text-center text-muted">No dependency information available</div>
                </td>
            </tr>'''

    @staticmethod
    def _create_error_row() -> str:
        """Create a placeholder row when an error occurs processing dependencies
        
        Returns:
            HTML string for error state
        """
        return '''
                <tr>
                    <td class="px-6 py-4 border-b border-gray-200 dark:border-gray-700" colspan="3">
                        <div class="text-center text-muted">No dependency information available</div>
                    </td>
                </tr>'''

    @staticmethod
    def _create_dependencies_table(rows: str) -> str:
        """Create the complete dependencies table with header and rows
        
        Args:
            rows: HTML string containing table rows
            
        Returns:
            Complete HTML table with container
        """
        return f'''
        <div class="bg-card p-6 rounded-2xl shadow-md border border-theme h-full">
            <h3 class="text-lg font-semibold mb-4 flex items-center gap-2 text-body">
                <i class="fas fa-cubes text-blue-500" aria-hidden="true"></i> 
                Dependencies
            </h3>
            <div class="overflow-x-auto">
                <table class="min-w-full">
                    <thead>
                        <tr>
                            <th class="px-6 py-3 border-b-2 border-gray-300 dark:border-gray-700 text-left text-xs font-semibold text-gray-600 dark:text-gray-400 uppercase tracking-wider">Name</th>
                            <th class="px-6 py-3 border-b-2 border-gray-300 dark:border-gray-700 text-left text-xs font-semibold text-gray-600 dark:text-gray-400 uppercase tracking-wider">Version</th>
                            <th class="px-6 py-3 border-b-2 border-gray-300 dark:border-gray-700 text-left text-xs font-semibold text-gray-600 dark:text-gray-400 uppercase tracking-wider">License</th>
                        </tr>
                    </thead>
                    <tbody>
                        {rows}
                    </tbody>
                </table>
            </div>
        </div>'''


class PlotReportGenerator:
    """Generate chart visualizations for the HTML report."""

    def __init__(self) -> None:
        """Initialize the plot report generator."""
        self.charts_data: Dict[str, Dict[str, Any]] = {}
        self.chart_classes = {
            'languages': LanguageChartData,
            'complexity': ComplexityChartData,
            'security': SecurityIssuesChartData,
            'code_smells': CodeSmellsChartData
        }

    def prepare_chart_data(self, metrics: 'ProjectMetrics') -> None:
        """Prepare all charts data for plotting.
        
        Args:
            metrics: ProjectMetrics object containing analysis data
        """
        for chart_id, chart_class in self.chart_classes.items():
            self.charts_data[chart_id] = chart_class.prepare_data(metrics)

    def get_charts_grid_html(self) -> str:
        """Get the HTML grid for all charts.
        
        Returns:
            HTML string for the charts grid
        """
        return f'''
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-10 fade-in">
            {self._get_chart_container_html('languages', 'Language Distribution', 'doughnut')}
            {self._get_chart_container_html('complexity', 'Complexity Distribution', 'bar')}
            {self._get_chart_container_html('security', 'Security Issues', 'bar')}
            {self._get_chart_container_html('code_smells', 'Code Smells', 'bar')}
        </div>'''

    @staticmethod
    def _get_chart_container_html(chart_id: str, title: str, chart_type: str) -> str:
        """Get the HTML container for a single chart.
        
        Args:
            chart_id: Unique identifier for the chart
            title: Title to display above the chart
            chart_type: Type of chart to display
            
        Returns:
            HTML string for the chart container
        """
        icon_map = {
            'languages': '<i class="fas fa-code text-blue-500 animate-icon-pulse" aria-hidden="true"></i>',
            'complexity': '<i class="fas fa-layer-group text-orange-500 animate-icon-pulse" aria-hidden="true"></i>',
            'security': '<i class="fas fa-shield-alt text-red-500 animate-icon-pulse" aria-hidden="true"></i>',
            'code_smells': '<i class="fas fa-bug text-purple-500 animate-icon-pulse" aria-hidden="true"></i>'
        }

        icon = icon_map.get(chart_id, '<i class="fas fa-chart-pie text-blue-500 animate-icon-pulse" aria-hidden="true"></i>')
        
        hover_effect_class = "card-3d-effect"
        
        # Add specific hover effects for different chart types
        hover_effects = {
            'languages': '''
                <div class="absolute -top-1 -right-1 w-2 h-2 bg-blue-400 rounded-full opacity-0 group-hover:opacity-100 transition-all duration-500 group-hover:animate-ping" style="animation-delay: 0.1s;"></div>
                <div class="absolute top-1 right-1 w-1.5 h-1.5 bg-green-400 rounded-full opacity-0 group-hover:opacity-100 transition-all duration-500 group-hover:animate-ping" style="animation-delay: 0.2s;"></div>
                <div class="absolute -bottom-1 right-2 w-1 h-1 bg-yellow-400 rounded-full opacity-0 group-hover:opacity-100 transition-all duration-500 group-hover:animate-ping" style="animation-delay: 0.3s;"></div>
            ''',
            'complexity': '''
                <div class="absolute bottom-0 left-0 h-1 bg-gradient-to-r from-green-500 via-yellow-500 to-red-500 transform origin-left scale-x-0 group-hover:scale-x-100 transition-transform duration-1000 ease-out"></div>
            ''',
            'security': '''
                <div class="absolute inset-0 rounded-2xl border-2 border-red-500/0 group-hover:border-red-500/20 transition-all duration-500"></div>
                <div class="absolute top-4 right-4 opacity-0 group-hover:opacity-30 transition-opacity duration-500">
                    <div class="w-10 h-0.5 bg-red-500/50 group-hover:animate-pulse"></div>
                    <div class="w-7 h-0.5 bg-red-500/30 mt-1 group-hover:animate-pulse" style="animation-delay: 0.2s;"></div>
                    <div class="w-4 h-0.5 bg-red-500/20 mt-1 group-hover:animate-pulse" style="animation-delay: 0.4s;"></div>
                </div>
            ''',
            'code_smells': '''
                <div class="absolute inset-0 bg-purple-500/5 opacity-0 group-hover:opacity-100 transition-opacity duration-700 rounded-2xl group-hover:animate-pulse"></div>
                <div class="absolute bottom-0 left-0 h-1 bg-gradient-to-r from-purple-600 via-purple-400 to-purple-600 transform origin-left scale-x-0 group-hover:scale-x-100 transition-transform duration-1200 ease-in-out"></div>
            '''
        }
        
        hover_effect = hover_effects.get(chart_id, '''
            <div class="absolute bottom-0 left-0 h-1 bg-gradient-to-r from-blue-500 to-blue-300 transform origin-left scale-x-0 group-hover:scale-x-100 transition-transform duration-1000 ease-out"></div>
        ''')

        return f'''
        <div class="stat-card {hover_effect_class} bg-card p-6 rounded-2xl shadow-md border border-theme h-full transition-all duration-500 hover:shadow-xl relative overflow-hidden group hover:scale-105">
            <h3 class="text-lg font-semibold mb-4 flex items-center gap-2 text-body transition-all duration-300 group-hover:translate-x-2">
                {icon} 
                <span class="transition-all duration-300 group-hover:text-blue-500">{title}</span>
            </h3>
            {hover_effect}
            <div class="h-64 w-full relative z-10 card-inner">
                <canvas id="chart-{chart_id}" data-chart-type="{chart_type}" data-chart-data="{chart_id}" class="transition-all duration-500 group-hover:scale-105"></canvas>
            </div>
        </div>'''


class HeaderComponent(ReportComponent):
    """Header component for HTML report"""

    @staticmethod
    def render(metrics: 'ProjectMetrics') -> str:
        """Render the header HTML section"""
        timestamp = format_timestamp()
        return f'''
        <div class="bg-gradient-to-r from-blue-600 to-blue-800 text-white p-12 text-center mb-8 rounded-3xl shadow-2xl relative overflow-hidden">
            <div class="absolute inset-0 opacity-30">
                <div class="absolute inset-0" style="background-image: url('data:image/svg+xml,%3Csvg xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22 viewBox%3D%220 0 100 100%22%3E%3Cdefs%3E%3Cpattern id%3D%22grid%22 width%3D%2210%22 height%3D%2210%22 patternUnits%3D%22userSpaceOnUse%22%3E%3Cpath d%3D%22M 10 0 L 0 0 0 10%22 fill%3D%22none%22 stroke%3D%22var(--header-pattern)%22 stroke-width%3D%220.5%22%2F%3E%3C%2Fpattern%3E%3C%2Fdefs%3E%3Crect width%3D%22100%22 height%3D%22100%22 fill%3D%22url(%23grid)%22%2F%3E%3C%2Fsvg%3E');"></div>
            </div>
            <div class="absolute -top-1/2 -left-1/2 w-[200%] h-[200%] bg-gradient-radial animate-float"></div>
            <div class="relative z-10">
                <h1 class="text-4xl lg:text-5xl font-bold mb-3 drop-shadow-sm flex items-center justify-center gap-4 flex-col sm:flex-row">
                    <span class="bg-clip-text text-transparent bg-gradient-to-r from-white to-blue-200">CodeLyzer Analysis Report</span>
                </h1>
                <p class="text-lg opacity-90 font-light tracking-wide">Generated on {timestamp}</p>
                <div class="flex justify-center mt-6">
                    <div class="bg-white/10 backdrop-blur-sm px-4 py-2 rounded-full text-sm font-medium inline-flex items-center gap-2 border border-white/20 shadow-inner">
                        <i class="fas fa-code-branch mr-1"></i>
                        <span>Analyzing code quality since {timestamp.split()[0]}</span>
                    </div>
                </div>
            </div>
        </div>'''


class MetricsGridComponent(ReportComponent):
    """Metrics grid component for HTML report"""

    @staticmethod
    def render(metrics: 'ProjectMetrics') -> str:
        """Render the metrics grid HTML section"""
        return f'''
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 mb-10 fade-in">
            <div class="stat-card card-3d-effect bg-card p-7 rounded-2xl shadow-md border border-theme transition-all duration-500 hover:shadow-xl relative overflow-hidden group focus-within:outline-2 focus-within:outline-blue-600 focus-within:outline-offset-2 hover:scale-105" tabindex="0">
                <div class="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-blue-600 to-blue-400 transform origin-left scale-x-0 group-hover:scale-x-100 transition-transform duration-1000 ease-out"></div>
                <div class="card-inner flex items-center justify-between mb-5">
                    <div class="w-13 h-13 rounded-xl bg-gradient-to-br from-blue-600 to-blue-800 flex items-center justify-center text-white text-xl shadow-md transition-all duration-700 group-hover:scale-110 group-hover:rotate-6 relative">
                        <i class="fas fa-file-code animate-icon-pulse" aria-hidden="true"></i>
                        <div class="absolute -top-1 -right-1 w-2 h-2 bg-blue-500 rounded-full opacity-0 group-hover:opacity-100 transition-all duration-500 group-hover:animate-ping" style="animation-delay: 0.1s;"></div>
                        <div class="absolute -bottom-1 -left-1 w-1.5 h-1.5 bg-blue-400 rounded-full opacity-0 group-hover:opacity-100 transition-all duration-500 group-hover:animate-ping" style="animation-delay: 0.3s;"></div>
                    </div>
                </div>
                <div class="transform transition-all duration-700 group-hover:translate-x-2">
                    <div class="text-5xl font-bold text-body leading-none mb-2 transition-all duration-700 group-hover:scale-110 group-hover:text-blue-600">{metrics.total_files:,}</div>
                    <div class="text-muted font-medium uppercase text-xs tracking-wider transition-colors duration-300 group-hover:text-blue-600">Files Analyzed</div>
                </div>
                <div class="absolute inset-0 bg-blue-500/5 opacity-0 group-hover:opacity-100 transition-opacity duration-700 rounded-lg"></div>
            </div>

            <div class="stat-card card-3d-effect bg-card p-7 rounded-2xl shadow-md border border-theme transition-all duration-500 hover:shadow-xl relative overflow-hidden group focus-within:outline-2 focus-within:outline-green-600 focus-within:outline-offset-2 hover:scale-105" tabindex="0">
                <div class="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-green-500 to-green-400 transform origin-left scale-x-0 group-hover:scale-x-100 transition-transform duration-1000 ease-out"></div>
                <div class="card-inner flex items-center justify-between mb-5">
                    <div class="w-13 h-13 rounded-xl bg-gradient-to-br from-green-500 to-green-600 flex items-center justify-center text-white text-xl shadow-md transition-all duration-700 group-hover:scale-110 group-hover:rotate-6 relative">
                        <i class="fas fa-code animate-icon-pulse" aria-hidden="true"></i>
                        <div class="absolute top-2 left-1 w-1 h-1 bg-green-500 rounded-full opacity-0 group-hover:opacity-100 group-hover:animate-ping transition-all duration-300" style="animation-delay: 0s;"></div>
                        <div class="absolute top-4 left-2 w-1 h-1 bg-green-400 rounded-full opacity-0 group-hover:opacity-100 group-hover:animate-ping transition-all duration-300" style="animation-delay: 0.2s;"></div>
                        <div class="absolute top-6 left-3 w-1 h-1 bg-green-300 rounded-full opacity-0 group-hover:opacity-100 group-hover:animate-ping transition-all duration-300" style="animation-delay: 0.4s;"></div>
                    </div>
                </div>
                <div class="transform transition-all duration-700 group-hover:translate-x-2">
                    <div class="text-5xl font-bold text-body leading-none mb-2 transition-all duration-700 group-hover:scale-110 group-hover:text-green-600">{metrics.total_loc:,}</div>
                    <div class="text-muted font-medium uppercase text-xs tracking-wider transition-colors duration-300 group-hover:text-green-600">Lines of Code</div>
                </div>
                <div class="absolute inset-0 bg-green-500/5 opacity-0 group-hover:opacity-100 transition-opacity duration-700 rounded-lg"></div>
            </div>

            <div class="stat-card card-3d-effect bg-card p-7 rounded-2xl shadow-md border border-theme transition-all duration-500 hover:shadow-xl relative overflow-hidden group focus-within:outline-2 focus-within:outline-yellow-600 focus-within:outline-offset-2 hover:scale-105" tabindex="0">
                <div class="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-yellow-500 to-yellow-400 transform origin-left scale-x-0 group-hover:scale-x-100 transition-transform duration-1000 ease-out"></div>
                <div class="card-inner flex items-center justify-between mb-5">
                    <div class="w-13 h-13 rounded-xl bg-gradient-to-br from-yellow-500 to-yellow-600 flex items-center justify-center text-white text-xl shadow-md transition-all duration-700 group-hover:scale-110 group-hover:rotate-6 relative">
                        <i class="fas fa-cube animate-icon-pulse" aria-hidden="true"></i>
                        <div class="absolute -top-1 -left-1 w-1 h-1 bg-yellow-400 rounded-full opacity-0 group-hover:opacity-100 group-hover:animate-ping transition-all duration-300" style="animation-delay: 0s;"></div>
                        <div class="absolute -top-2 -right-1 w-1.5 h-1.5 bg-yellow-300 rounded-full opacity-0 group-hover:opacity-100 group-hover:animate-ping transition-all duration-300" style="animation-delay: 0.3s;"></div>
                        <div class="absolute -bottom-1 -left-2 w-1 h-1 bg-yellow-200 rounded-full opacity-0 group-hover:opacity-100 group-hover:animate-ping transition-all duration-300" style="animation-delay: 0.6s;"></div>
                    </div>
                </div>
                <div class="transform transition-all duration-700 group-hover:translate-x-2">
                    <div class="text-5xl font-bold text-body leading-none mb-2 transition-all duration-700 group-hover:scale-110 group-hover:text-yellow-600">{metrics.total_classes:,}</div>
                    <div class="text-muted font-medium uppercase text-xs tracking-wider transition-colors duration-300 group-hover:text-yellow-600">Classes</div>
                </div>
                <div class="absolute inset-0 bg-yellow-500/5 opacity-0 group-hover:opacity-100 transition-opacity duration-700 rounded-lg"></div>
            </div>

            <div class="stat-card card-3d-effect bg-card p-7 rounded-2xl shadow-md border border-theme transition-all duration-500 hover:shadow-xl relative overflow-hidden group focus-within:outline-2 focus-within:outline-red-600 focus-within:outline-offset-2 hover:scale-105" tabindex="0">
                <div class="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-red-500 to-red-400 transform origin-left scale-x-0 group-hover:scale-x-100 transition-transform duration-1000 ease-out"></div>
                <div class="card-inner flex items-center justify-between mb-5">
                    <div class="w-13 h-13 rounded-xl bg-gradient-to-br from-red-500 to-red-600 flex items-center justify-center text-white text-xl shadow-md transition-all duration-700 group-hover:scale-110 group-hover:rotate-6 relative">
                        <i class="fas fa-cogs animate-icon-pulse" aria-hidden="true"></i>
                        <!-- Ripple effects for activity -->
                        <div class="absolute inset-0 rounded-full bg-red-500/20 opacity-0 group-hover:opacity-100 group-hover:animate-ping transition-all duration-700"></div>
                        <div class="absolute inset-1 rounded-full bg-red-500/15 opacity-0 group-hover:opacity-100 group-hover:animate-ping transition-all duration-700" style="animation-delay: 0.3s;"></div>
                        <div class="absolute inset-2 rounded-full bg-red-500/10 opacity-0 group-hover:opacity-100 group-hover:animate-ping transition-all duration-700" style="animation-delay: 0.6s;"></div>
                    </div>
                </div>
                <div class="transform transition-all duration-700 group-hover:translate-x-2">
                    <div class="text-5xl font-bold text-body leading-none mb-2 transition-all duration-700 group-hover:scale-110 group-hover:text-red-600">{metrics.total_functions:,}</div>
                    <div class="text-muted font-medium uppercase text-xs tracking-wider transition-colors duration-300 group-hover:text-red-600">Functions</div>
                </div>
                <div class="absolute inset-0 bg-red-500/5 opacity-0 group-hover:opacity-100 transition-opacity duration-700 rounded-lg"></div>
            </div>

            <div class="stat-card card-3d-effect bg-card p-7 rounded-2xl shadow-md border border-theme transition-all duration-500 hover:shadow-xl relative overflow-hidden group focus-within:outline-2 focus-within:outline-blue-600 focus-within:outline-offset-2 hover:scale-105" tabindex="0">
                <div class="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-blue-400 via-blue-300 to-blue-400 transform origin-left scale-x-0 group-hover:scale-x-100 transition-transform duration-1000 ease-out"></div>
                <div class="card-inner flex items-center justify-between mb-5">
                    <div class="w-13 h-13 rounded-xl bg-gradient-to-br from-blue-400 to-blue-500 flex items-center justify-center text-white text-xl shadow-md transition-all duration-700 group-hover:scale-110 group-hover:rotate-6 relative">
                        <i class="fas fa-star animate-icon-pulse" aria-hidden="true"></i>
                        <!-- Sparkle effects around the star -->
                        <div class="absolute -top-1 -right-1 w-2 h-2 bg-blue-400 rounded-full opacity-0 group-hover:opacity-100 transition-all duration-500 group-hover:animate-ping" style="animation-delay: 0.1s;"></div>
                        <div class="absolute -top-2 right-1 w-1.5 h-1.5 bg-blue-300 rounded-full opacity-0 group-hover:opacity-100 transition-all duration-500 group-hover:animate-ping" style="animation-delay: 0.2s;"></div>
                        <div class="absolute top-0 -right-2 w-1 h-1 bg-blue-200 rounded-full opacity-0 group-hover:opacity-100 transition-all duration-500 group-hover:animate-ping" style="animation-delay: 0.3s;"></div>
                    </div>
                </div>
                <div class="transform transition-all duration-700 group-hover:translate-x-2">
                    <div class="text-5xl font-bold text-body leading-none mb-2 transition-all duration-700 group-hover:scale-110 group-hover:text-blue-400 group-hover:drop-shadow-lg">{metrics.code_quality_score:.1f}%</div>
                    <div class="text-muted font-medium uppercase text-xs tracking-wider transition-colors duration-300 group-hover:text-blue-400">Code Quality</div>
                </div>
                <div class="absolute inset-0 bg-blue-400/5 opacity-0 group-hover:opacity-100 transition-opacity duration-700 rounded-lg group-hover:animate-pulse"></div>
            </div>

            <div class="stat-card card-3d-effect bg-card p-7 rounded-2xl shadow-md border border-theme transition-all duration-500 hover:shadow-xl relative overflow-hidden group focus-within:outline-2 focus-within:outline-purple-600 focus-within:outline-offset-2 hover:scale-105" tabindex="0">
                <div class="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-purple-500 via-purple-400 to-purple-300 transform origin-left scale-x-0 group-hover:scale-x-100 transition-transform duration-1200 ease-in-out"></div>
                <div class="card-inner flex items-center justify-between mb-5">
                    <div class="w-13 h-13 rounded-xl bg-gradient-to-br from-purple-500 to-purple-600 flex items-center justify-center text-white text-xl shadow-md transition-all duration-700 group-hover:scale-110 group-hover:rotate-6 relative">
                        <i class="fas fa-tools animate-icon-pulse" aria-hidden="true"></i>
                        <!-- Floating mini boxes to represent tools -->
                        <div class="absolute top-4 right-4 opacity-0 group-hover:opacity-30 transition-opacity duration-500">
                            <div class="w-8 h-0.5 bg-purple-300 group-hover:animate-pulse"></div>
                            <div class="w-6 h-0.5 bg-purple-300/70 mt-1 group-hover:animate-pulse" style="animation-delay: 0.2s;"></div>
                            <div class="w-4 h-0.5 bg-purple-300/50 mt-1 group-hover:animate-pulse" style="animation-delay: 0.4s;"></div>
                        </div>
                    </div>
                </div>
                <div class="transform transition-all duration-700 group-hover:translate-x-2">
                    <div class="text-5xl font-bold text-body leading-none mb-2 transition-all duration-700 group-hover:scale-110 group-hover:text-purple-500">{metrics.maintainability_score:.1f}%</div>
                    <div class="text-muted font-medium uppercase text-xs tracking-wider transition-colors duration-300 group-hover:text-purple-500">Maintainability</div>
                </div>
                <div class="absolute inset-0 bg-purple-500/5 opacity-0 group-hover:opacity-100 transition-opacity duration-700 rounded-lg"></div>
            </div>
        </div>'''


class FooterComponent(ReportComponent):
    """Footer component for HTML report"""

    @staticmethod
    def render(metrics: 'ProjectMetrics') -> str:
        """Render the footer HTML section"""
        current_year = datetime.now().year
        return f'''
        <div class="mt-16 border-t border-theme py-10 bg-gradient-to-r from-gray-50 dark:from-gray-900 to-transparent rounded-xl fade-in">
            <div class="text-center">
                <div class="flex items-center justify-center mb-4">
                    <img src="assets/static/favicon.png" alt="CodeLyzer Logo" class="w-8 h-8 mr-2" />
                    <span class="text-xl font-semibold bg-clip-text text-transparent bg-gradient-to-r from-blue-600 to-blue-400">CodeLyzer</span>
                </div>
                <p class="text-muted mb-2 text-sm max-w-md mx-auto">
                    Delivering deep insights into your codebase quality, security, and maintainability
                </p>
                <div class="flex items-center justify-center gap-4 text-xs text-muted mt-4">
                    <span>© {current_year} CodeLyzer</span>
                    <span class="w-1 h-1 rounded-full bg-gray-300 dark:bg-gray-700"></span>
                    <span>Advanced Code Analysis</span>
                    <span class="w-1 h-1 rounded-full bg-gray-300 dark:bg-gray-700"></span>
                    <span>v1.0.0</span>
                </div>
            </div>
        </div>'''


class ThemeToggleComponent(ReportComponent):
    """Theme toggle button component for HTML report"""
    
    @staticmethod
    def render(metrics: 'ProjectMetrics') -> str:
        """Render the theme toggle button HTML section"""
        return '''
        <div class="fixed top-4 right-4 z-50">
            <button id="theme-toggle" class="p-3 rounded-full bg-white/80 dark:bg-gray-800/80 shadow-md hover:shadow-xl transition-all duration-300 backdrop-blur-md border border-gray-200 dark:border-gray-700 text-gray-800 dark:text-gray-200 group relative overflow-hidden">
                <!-- Animated background pulse -->
                <div class="absolute inset-0 bg-gradient-to-tr from-blue-500/10 to-purple-500/10 opacity-0 group-hover:opacity-100 transition-opacity duration-300 dark:from-yellow-500/10 dark:to-orange-500/10"></div>
                
                <!-- Rotation container for smooth spinning transition -->
                <div class="transform transition-all duration-500 group-hover:rotate-180 group-active:scale-90">
                    <!-- Sun icon (shown in dark mode) -->
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 hidden dark:block transform transition-transform duration-1000 group-hover:scale-110" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
                    </svg>
                    <!-- Moon icon (shown in light mode) -->
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 block dark:hidden transform transition-transform duration-1000 group-hover:scale-110" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
                    </svg>
                </div>
                
                <!-- Light particles around sun (in dark mode) -->
                <div class="absolute inset-0 hidden dark:block">
                    <div class="absolute top-0 left-1/2 w-0.5 h-0.5 bg-yellow-300 rounded-full opacity-0 group-hover:opacity-100 transition-all duration-300 group-hover:animate-ping" style="animation-delay: 0.1s;"></div>
                    <div class="absolute top-1/4 right-0 w-0.5 h-0.5 bg-yellow-300 rounded-full opacity-0 group-hover:opacity-100 transition-all duration-300 group-hover:animate-ping" style="animation-delay: 0.2s;"></div>
                    <div class="absolute bottom-0 left-1/2 w-0.5 h-0.5 bg-yellow-300 rounded-full opacity-0 group-hover:opacity-100 transition-all duration-300 group-hover:animate-ping" style="animation-delay: 0.3s;"></div>
                    <div class="absolute top-1/4 left-0 w-0.5 h-0.5 bg-yellow-300 rounded-full opacity-0 group-hover:opacity-100 transition-all duration-300 group-hover:animate-ping" style="animation-delay: 0.4s;"></div>
                </div>
                
                <!-- Stars around moon (in light mode) -->
                <div class="absolute inset-0 block dark:hidden">
                    <div class="absolute top-0 right-0 w-0.5 h-0.5 bg-blue-400 rounded-full opacity-0 group-hover:opacity-100 transition-all duration-300 group-hover:animate-ping" style="animation-delay: 0.1s;"></div>
                    <div class="absolute bottom-0 right-1/4 w-0.5 h-0.5 bg-blue-400 rounded-full opacity-0 group-hover:opacity-100 transition-all duration-300 group-hover:animate-ping" style="animation-delay: 0.3s;"></div>
                    <div class="absolute top-1/3 left-0 w-0.5 h-0.5 bg-blue-400 rounded-full opacity-0 group-hover:opacity-100 transition-all duration-300 group-hover:animate-ping" style="animation-delay: 0.5s;"></div>
                </div>
                
                <!-- Glowing border that appears on hover -->
                <div class="absolute inset-0 rounded-full border border-transparent group-hover:border-blue-500/30 dark:group-hover:border-yellow-500/30 transition-all duration-300"></div>
            </button>
        </div>'''


def format_timestamp() -> str:
    """Format the current timestamp for display.

    Returns:
        Formatted timestamp string
    """
    return datetime.now().strftime("%B %d, %Y at %H:%M:%S")


class HTMLReportGenerator:
    """Generate HTML reports for codebase analysis metrics."""

    def __init__(self) -> None:
        """Initialize the HTML report generator."""
        self._plot_generator = PlotReportGenerator()
        self._default_theme = "light"

    def create(self, metrics: 'ProjectMetrics', output_dir: str = "reports") -> str:
        """Generate HTML report for the given metrics.
        
        Args:
            metrics: ProjectMetrics object containing analysis data
            output_dir: Directory to save the report and assets (default: reports)
            
        Returns:
            Complete HTML report as a string
        """
        self._prepare_data(metrics)
        
        # Copy favicon to output directory
        favicon_path = copy_favicon_to_output(output_dir)
        
        return self._build_html_template(metrics, favicon_path)

    def _prepare_data(self, metrics: 'ProjectMetrics') -> None:
        """Prepare all data components for the HTML template.
        
        Args:
            metrics: ProjectMetrics object containing analysis data
        """
        self._plot_generator.prepare_chart_data(metrics)

    def _build_html_template(self, metrics: 'ProjectMetrics', favicon_path: str = "") -> str:
        """Build the complete HTML template for the report.
        
        Args:
            metrics: ProjectMetrics object containing analysis data
            favicon_path: Path to the favicon file
            
        Returns:
            Complete HTML report as a string
        """
        return f'''
<!DOCTYPE html>
<html lang="en" class="{self._default_theme}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CodeLyzer - Advanced Code Analysis Report</title>
    <link rel="icon" href="{favicon_path}" type="image/png">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.3.0/dist/chart.umd.min.js"></script>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        :root {{
            color-scheme: light dark;
            
            /* Light theme variables */
            --bg-primary: {ThemeColors.LIGHT["bg_primary"]};
            --bg-secondary: {ThemeColors.LIGHT["bg_secondary"]};
            --text-primary: {ThemeColors.LIGHT["text_primary"]};
            --text-secondary: {ThemeColors.LIGHT["text_secondary"]};
            --border-color: {ThemeColors.LIGHT["border"]};
            --border-secondary: {ThemeColors.LIGHT["border_secondary"]};
            
            --brand-primary: {ThemeColors.LIGHT["brand_primary"]};
            --brand-primary-dark: {ThemeColors.LIGHT["brand_primary_dark"]};
            --brand-secondary: {ThemeColors.LIGHT["brand_secondary"]};
            --brand-gradient-from: {ThemeColors.LIGHT["brand_gradient_from"]};
            --brand-gradient-to: {ThemeColors.LIGHT["brand_gradient_to"]};
            
            --card-shadow: {ThemeColors.LIGHT["card_shadow"]};
            --header-pattern: {ThemeColors.LIGHT["header_pattern"]};
            --header-gradient-overlay: {ThemeColors.LIGHT["header_gradient_overlay"]};
            
            /* Selection colors */
            --selection-bg: {ThemeColors.LIGHT["selection_bg"]};
            --selection-text: {ThemeColors.LIGHT["selection_text"]};
        }}
        
        .dark {{
            /* Dark theme variables */
            --bg-primary: {ThemeColors.DARK["bg_primary"]};
            --bg-secondary: {ThemeColors.DARK["bg_secondary"]};
            --text-primary: {ThemeColors.DARK["text_primary"]};
            --text-secondary: {ThemeColors.DARK["text_secondary"]};
            --border-color: {ThemeColors.DARK["border"]};
            --border-secondary: {ThemeColors.DARK["border_secondary"]};
            
            --brand-primary: {ThemeColors.DARK["brand_primary"]};
            --brand-primary-dark: {ThemeColors.DARK["brand_primary_dark"]};
            --brand-secondary: {ThemeColors.DARK["brand_secondary"]};
            --brand-gradient-from: {ThemeColors.DARK["brand_gradient_from"]};
            --brand-gradient-to: {ThemeColors.DARK["brand_gradient_to"]};
            
            --card-shadow: {ThemeColors.DARK["card_shadow"]};
            --header-pattern: {ThemeColors.DARK["header_pattern"]};
            --header-gradient-overlay: {ThemeColors.DARK["header_gradient_overlay"]};
            
            /* Selection colors */
            --selection-bg: {ThemeColors.DARK["selection_bg"]};
            --selection-text: {ThemeColors.DARK["selection_text"]};
        }}
        
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Inter', sans-serif;
            line-height: 1.5;
            color: var(--text-primary);
            background-color: var(--bg-primary);
            transition: background-color 0.3s ease, color 0.3s ease;
        }}
        
        /* Selection styling */
        ::selection {{
            background-color: var(--selection-bg);
            color: var(--selection-text);
        }}
        
        /* Monospace font for code elements */
        .font-mono, code, pre {{
            font-family: 'JetBrains Mono', monospace;
        }}
        
        /* Custom scrollbar styling */
        ::-webkit-scrollbar {{
            width: 12px;
            height: 12px;
        }}
        
        ::-webkit-scrollbar-track {{
            background-color: var(--bg-primary);
        }}
        
        ::-webkit-scrollbar-thumb {{
            background-color: var(--brand-primary);
            border-radius: 6px;
            border: 3px solid var(--bg-primary);
        }}
        
        ::-webkit-scrollbar-thumb:hover {{
            background-color: var(--brand-primary-dark);
        }}
        
        @keyframes fadein {{
            from {{ opacity: 0; transform: translateY(10px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        
        .fade-in {{
            animation: fadein 0.6s ease-out forwards;
        }}
        
        .bg-gradient-radial {{
            background: radial-gradient(circle, var(--header-gradient-overlay) 0%, transparent 100%);
        }}
        
        .w-13 {{
            width: 3.25rem;
        }}
        
        .h-13 {{
            height: 3.25rem;
        }}
        
        /* Theme-aware Tailwind utilities */
        .bg-card {{
            background-color: var(--bg-secondary);
            border-color: var(--border-color);
            box-shadow: 0 4px 6px var(--card-shadow);
        }}
        
        .text-body {{
            color: var(--text-primary);
        }}
        
        .text-muted {{
            color: var(--text-secondary);
        }}
        
        .border-theme {{
            border-color: var(--border-color);
        }}
        
        /* Advanced card animations */
        .card-3d-effect {{
            transform-style: preserve-3d;
            perspective: 1000px;
            transition: all 0.3s ease;
        }}
        
        .card-3d-effect:hover {{
            transform: scale(1.05) translateY(-5px) rotateX(2deg) rotateY(2deg);
            box-shadow: 0 15px 30px rgba(0, 0, 0, 0.15), 0 10px 15px rgba(0, 0, 0, 0.08);
        }}
        
        .card-inner {{
            transform: translateZ(10px);
            transition: all 0.3s ease;
        }}
        
        @keyframes iconPulse {{
            0% {{ transform: scale(1); }}
            50% {{ transform: scale(1.1); }}
            100% {{ transform: scale(1); }}
        }}
        
        .animate-icon-pulse {{
            animation: iconPulse 2s ease-in-out infinite;
        }}
        
        @keyframes ping {{
            0% {{ transform: scale(1); opacity: 1; }}
            75%, 100% {{ transform: scale(2); opacity: 0; }}
        }}
        
        .animate-ping {{
            animation: ping 1.5s cubic-bezier(0, 0, 0.2, 1) infinite;
        }}
        
        @keyframes pulse {{
            0%, 100% {{ opacity: 1; }}
            50% {{ opacity: 0.5; }}
        }}
        
        .animate-pulse {{
            animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
        }}
        
        @keyframes float {{
            0%, 100% {{ transform: translateY(0); opacity: 0.05; }}
            50% {{ transform: translateY(-15px); opacity: 0.1; }}
        }}
        
        .animate-float {{
            animation: float 10s ease-in-out infinite;
        }}
        
        @keyframes pulse-subtle {{
            0% {{ opacity: 0.9; transform: scale(1); }}
            50% {{ opacity: 1; transform: scale(1.05); }}
            100% {{ opacity: 0.9; transform: scale(1); }}
        }}
        
        .animate-pulse-subtle {{
            animation: pulse-subtle 3s ease-in-out infinite;
        }}
    </style>
    <script>
        tailwind.config = {{
            darkMode: 'class',
            theme: {{
                extend: {{
                    colors: {{
                        brand: {{
                            primary: 'var(--brand-primary)',
                            secondary: 'var(--brand-secondary)',
                        }}
                    }}
                }}
            }}
        }}
    </script>
</head>
<body class="font-inter text-sm min-h-screen">
    {ThemeToggleComponent.render(metrics)}
    <div class="max-w-7xl mx-auto p-6">
        {HeaderComponent.render(metrics)}
        {MetricsGridComponent.render(metrics)}
        {self._plot_generator.get_charts_grid_html()}
        
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-10 fade-in">
            {ComplexFilesTableComponent.render(metrics)}
            {DependenciesTableComponent.render(metrics)}
        </div>
        
        {FooterComponent.render(metrics)}
    </div>
    {self._get_javascript()}
    {self._get_theme_javascript()}
</body>
</html>'''

    def _get_javascript(self) -> str:
        """Get the JavaScript section for charts and animations.
        
        Returns:
            JavaScript code for the report
        """
        chart_data_json = json.dumps(self._plot_generator.charts_data)

        return f'''
<script>
    // Chart data from Python
    const chartData = {chart_data_json};
    
    // Common chart options and setup
    const chartOptions = {{
        languages: {{
            type: 'doughnut',
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{
                        position: 'bottom',
                        labels: {{
                            font: {{
                                family: "'Inter', sans-serif",
                                size: 11
                            }},
                            color: 'var(--text-primary)'
                        }}
                    }},
                    tooltip: {{
                        callbacks: {{
                            label: function(context) {{
                                const label = context.label || '';
                                const value = context.raw || 0;
                                const total = context.chart.data.datasets[0].data.reduce((a, b) => a + b, 0);
                                const percentage = Math.round((value / total) * 100);
                                return `${{label}}: ${{value}} files (${{percentage}}%)`;
                            }}
                        }}
                    }}
                }}
            }}
        }},
        complexity: {{
            type: 'bar',
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                scales: {{
                    y: {{
                        beginAtZero: true,
                        title: {{
                            display: true,
                            text: 'Number of Files',
                            font: {{
                                family: "'Inter', sans-serif",
                                size: 12
                            }},
                            color: 'var(--text-primary)'
                        }},
                        ticks: {{
                            color: 'var(--text-secondary)'
                        }},
                        grid: {{
                            color: 'var(--border-color)'
                        }}
                    }},
                    x: {{
                        title: {{
                            display: true,
                            text: 'Complexity Level',
                            font: {{
                                family: "'Inter', sans-serif",
                                size: 12
                            }},
                            color: 'var(--text-primary)'
                        }},
                        ticks: {{
                            color: 'var(--text-secondary)'
                        }},
                        grid: {{
                            color: 'var(--border-color)'
                        }}
                    }}
                }},
                plugins: {{
                    legend: {{
                        display: false
                    }}
                }}
            }}
        }},
        security: {{
            type: 'bar',
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                scales: {{
                    y: {{
                        beginAtZero: true,
                        title: {{
                            display: true,
                            text: 'Number of Issues',
                            font: {{
                                family: "'Inter', sans-serif",
                                size: 12
                            }},
                            color: 'var(--text-primary)'
                        }},
                        ticks: {{
                            color: 'var(--text-secondary)'
                        }},
                        grid: {{
                            color: 'var(--border-color)'
                        }}
                    }},
                    x: {{
                        title: {{
                            display: true,
                            text: 'Severity Level',
                            font: {{
                                family: "'Inter', sans-serif",
                                size: 12
                            }},
                            color: 'var(--text-primary)'
                        }},
                        ticks: {{
                            color: 'var(--text-secondary)'
                        }},
                        grid: {{
                            color: 'var(--border-color)'
                        }}
                    }}
                }},
                plugins: {{
                    legend: {{
                        display: false
                    }}
                }}
            }}
        }},
        code_smells: {{
            type: 'bar',
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                scales: {{
                    y: {{
                        beginAtZero: true,
                        title: {{
                            display: true,
                            text: 'Number of Issues',
                            font: {{
                                family: "'Inter', sans-serif",
                                size: 12
                            }},
                            color: 'var(--text-primary)'
                        }},
                        ticks: {{
                            color: 'var(--text-secondary)'
                        }},
                        grid: {{
                            color: 'var(--border-color)'
                        }}
                    }},
                    x: {{
                        title: {{
                            display: true,
                            text: 'Severity Level',
                            font: {{
                                family: "'Inter', sans-serif",
                                size: 12
                            }},
                            color: 'var(--text-primary)'
                        }},
                        ticks: {{
                            color: 'var(--text-secondary)'
                        }},
                        grid: {{
                            color: 'var(--border-color)'
                        }}
                    }}
                }},
                plugins: {{
                    legend: {{
                        display: false
                    }}
                }}
            }}
        }}
    }};
    
    // Default colors for charts
    const defaultColors = {json.dumps(ThemeColors.LIGHT["chart_colors"])};
    
    // Set up charts after DOM is loaded
    document.addEventListener('DOMContentLoaded', function() {{
        // Find all canvas elements with data-chart-data attribute
        const chartElements = document.querySelectorAll('[data-chart-data]');
        
        // Initialize each chart
        chartElements.forEach(canvas => {{
            const dataKey = canvas.getAttribute('data-chart-data');
            const data = chartData[dataKey];
            
            if (!data || !data.labels || !data.values) return;
            
            const chartType = canvas.getAttribute('data-chart-type') || chartOptions[dataKey]?.type || 'bar';
            const bgColors = data.colors || defaultColors;
            
            // Create chart
            const chart = new Chart(canvas, {{
                type: chartType,
                data: {{
                    labels: data.labels,
                    datasets: [
                        {{
                            data: data.values,
                            backgroundColor: bgColors,
                            borderColor: 'rgba(255, 255, 255, 0.8)',
                            borderWidth: 1,
                            hoverOffset: 4
                        }}
                    ]
                }},
                options: chartOptions[dataKey]?.options || {{}}
            }});
            
            // Store chart instance for later theme updates
            window.chartInstances = window.chartInstances || {{}};
            window.chartInstances[dataKey] = chart;
        }});

        // Set up table sorting functionality
        setupTableSorting();
    }});
    
    // Table sorting functionality
    function setupTableSorting() {{
        const table = document.getElementById('complex-files-table');
        if (!table) return;
        
        const headers = table.querySelectorAll('th.sortable');
        const tbody = table.querySelector('tbody');
        
        // Sort by complexity by default (descending)
        sortTableByColumn(tbody, 'complexity', true);
        
        headers.forEach(header => {{
            header.addEventListener('click', () => {{
                const sortKey = header.getAttribute('data-sort');
                
                // Toggle sort direction if clicking the same header again
                let isDescending = true;
                if (header.querySelector('.fa-sort-down')) {{
                    isDescending = false;
                }}
                
                // Reset all header icons
                headers.forEach(h => {{
                    const icon = h.querySelector('i');
                    if (icon) {{
                        icon.className = 'fas fa-sort ml-1 text-gray-400';
                    }}
                }});
                
                // Update clicked header icon
                const icon = header.querySelector('i');
                if (icon) {{
                    icon.className = isDescending 
                        ? 'fas fa-sort-down ml-1 text-blue-500' 
                        : 'fas fa-sort-up ml-1 text-blue-500';
                }}
                
                // Sort the table
                sortTableByColumn(tbody, sortKey, isDescending);
            }});
        }});
    }}
    
    function sortTableByColumn(tbody, column, isDescending = true) {{
        const rows = Array.from(tbody.querySelectorAll('tr'));
        
        // Sort rows based on the selected column
        const sortedRows = rows.sort((a, b) => {{
            const aValue = parseFloat(a.getAttribute(`data-${{column}}`)) || 0;
            const bValue = parseFloat(b.getAttribute(`data-${{column}}`)) || 0;
            
            return isDescending ? bValue - aValue : aValue - bValue;
        }});
        
        // Clear table body
        while (tbody.firstChild) {{
            tbody.removeChild(tbody.firstChild);
        }}
        
        // Append sorted rows
        sortedRows.forEach(row => {{
            tbody.appendChild(row);
        }});
    }}
</script>'''

    def _get_theme_javascript(self) -> str:
        """Get the JavaScript for theme switching.
        
        Returns:
            JavaScript code for theme switching
        """
        return '''
<script>
    // Theme switching functionality
    document.addEventListener('DOMContentLoaded', function() {
        const themeToggle = document.getElementById('theme-toggle');
        const html = document.documentElement;
        
        // Check for saved theme preference or use system preference
        const savedTheme = localStorage.getItem('theme');
        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        
        // Apply the saved theme or system preference
        if (savedTheme === 'dark' || (!savedTheme && prefersDark)) {
            html.classList.add('dark');
        } else {
            html.classList.remove('dark');
        }
        
        // Handle theme toggle button click
        themeToggle.addEventListener('click', function() {
            // Toggle theme
            html.classList.toggle('dark');
            
            // Save preference
            localStorage.setItem('theme', html.classList.contains('dark') ? 'dark' : 'light');
            
            // Update charts with theme-aware colors if they exist
            if (window.chartInstances) {
                Object.values(window.chartInstances).forEach(chart => {
                    // Update colors that should change with theme
                    if (chart.options.scales) {
                        if (chart.options.scales.y) {
                            chart.options.scales.y.grid.color = 'var(--border-color)';
                            chart.options.scales.y.ticks.color = 'var(--text-secondary)';
                            chart.options.scales.y.title.color = 'var(--text-primary)';
                        }
                        if (chart.options.scales.x) {
                            chart.options.scales.x.grid.color = 'var(--border-color)';
                            chart.options.scales.x.ticks.color = 'var(--text-secondary)';
                            chart.options.scales.x.title.color = 'var(--text-primary)';
                        }
                    }
                    
                    if (chart.options.plugins && chart.options.plugins.legend) {
                        chart.options.plugins.legend.labels.color = 'var(--text-primary)';
                    }
                    
                    chart.update();
                });
            }
        });
        
        // Listen for system theme changes
        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', event => {
            if (!localStorage.getItem('theme')) {  // Only if user hasn't set a preference
                if (event.matches) {
                    html.classList.add('dark');
                } else {
                    html.classList.remove('dark');
                }
            }
        });
    });
</script>'''


def generate_direct_html(metrics: 'ProjectMetrics', output_dir: str = "reports") -> str:
    """Generate HTML directly without using format strings to avoid issues"""
    generator = HTMLReportGenerator()
    return generator.create(metrics, output_dir)
