import json
import os
from datetime import datetime
from typing import Dict, Any, TypeVar

from codelyzer.metrics import ProjectMetrics, SecurityLevel, CodeSmellSeverity

T = TypeVar('T', bound='ChartData')


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
    def prepare_data(metrics: 'ProjectMetrics') -> Dict[str, Any]:
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
                if issue.level == SecurityLevel.CRITICAL:
                    security_counts["Critical"] += 1
                elif issue.level == SecurityLevel.HIGH:
                    security_counts["High"] += 1
                elif issue.level == SecurityLevel.MEDIUM:
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
                if smell.severity == CodeSmellSeverity.CRITICAL:
                    smell_counts["Critical"] += 1
                elif smell.severity == CodeSmellSeverity.MAJOR:
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
        for file_metrics in metrics.most_complex_files[:15]:
            # Extract the relative path
            file_path = file_metrics.file_path
            relative_path = file_path.replace(os.getcwd(), "").lstrip(os.sep).replace("\\", "/")

            # Count issues
            issues = len(file_metrics.security_issues) + len(file_metrics.code_smells_list)

            # Get complexity badge class based on score
            if file_metrics.complexity_score >= 30:
                complexity_badge = "bg-red-100 text-red-800"
            elif file_metrics.complexity_score >= 20:
                complexity_badge = "bg-orange-100 text-orange-800"
            elif file_metrics.complexity_score >= 10:
                complexity_badge = "bg-yellow-100 text-yellow-800"
            else:
                complexity_badge = "bg-green-100 text-green-800"

            # Format issues display
            if issues > 0:
                issues_display = f'<span class="text-red-600 font-semibold">{issues}</span>'
            else:
                issues_display = '<span class="text-green-600">0</span>'

            rows += f'''
        <tr class="hover:bg-gray-50 hover:scale-[1.005] transition-all duration-200">
            <td class="px-6 py-4 border-b border-gray-200">
                <div class="flex items-center gap-2 font-mono text-sm text-gray-600 max-w-xs overflow-hidden text-ellipsis whitespace-nowrap bg-gray-50 px-2 py-1 rounded border border-gray-200" title="{relative_path}">
                    <i class="fas fa-file-code" aria-hidden="true"></i>
                    {relative_path}
                </div>
            </td>
            <td class="px-6 py-4 border-b border-gray-200"><span class="font-semibold text-gray-900 tabular-nums">{file_metrics.sloc:,}</span></td>
            <td class="px-6 py-4 border-b border-gray-200"><span class="inline-flex items-center px-3 py-1 rounded-lg text-xs font-medium uppercase tracking-wide {complexity_badge}">{file_metrics.complexity_score:.0f}</span></td>
            <td class="px-6 py-4 border-b border-gray-200">{issues_display}</td>
        </tr>'''

        return f'''
        <div class="bg-white p-6 rounded-2xl shadow-md border border-gray-200 h-full">
            <h3 class="text-lg font-semibold mb-4 flex items-center gap-2 text-gray-800">
                <i class="fas fa-exclamation-triangle text-orange-500" aria-hidden="true"></i> 
                Most Complex Files
            </h3>
            <div class="overflow-x-auto">
                <table class="min-w-full">
                    <thead>
                        <tr>
                            <th class="px-6 py-3 border-b-2 border-gray-300 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">File</th>
                            <th class="px-6 py-3 border-b-2 border-gray-300 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">LOC</th>
                            <th class="px-6 py-3 border-b-2 border-gray-300 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">Complexity</th>
                            <th class="px-6 py-3 border-b-2 border-gray-300 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">Issues</th>
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
        rows = ""
        if hasattr(metrics, 'dependencies'):
            for dep in metrics.dependencies[:15]:
                rows += f'''
            <tr class="hover:bg-gray-50 hover:scale-[1.005] transition-all duration-200">
                <td class="px-6 py-4 border-b border-gray-200">
                    <div class="flex items-center gap-2 font-mono text-sm text-gray-600 max-w-xs overflow-hidden text-ellipsis whitespace-nowrap bg-gray-50 px-2 py-1 rounded border border-gray-200">
                        <i class="fas fa-cubes" aria-hidden="true"></i>
                        {dep.name}
                    </div>
                </td>
                <td class="px-6 py-4 border-b border-gray-200"><span class="font-semibold text-gray-900">{dep.version}</span></td>
                <td class="px-6 py-4 border-b border-gray-200">
                    {dep.license if dep.license else '<span class="text-gray-400">Unknown</span>'}
                </td>
            </tr>'''

        return f'''
        <div class="bg-white p-6 rounded-2xl shadow-md border border-gray-200 h-full">
            <h3 class="text-lg font-semibold mb-4 flex items-center gap-2 text-gray-800">
                <i class="fas fa-cubes text-blue-500" aria-hidden="true"></i> 
                Dependencies
            </h3>
            <div class="overflow-x-auto">
                <table class="min-w-full">
                    <thead>
                        <tr>
                            <th class="px-6 py-3 border-b-2 border-gray-300 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">Name</th>
                            <th class="px-6 py-3 border-b-2 border-gray-300 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">Version</th>
                            <th class="px-6 py-3 border-b-2 border-gray-300 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">License</th>
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
            'languages': '<i class="fas fa-code text-blue-500" aria-hidden="true"></i>',
            'complexity': '<i class="fas fa-layer-group text-orange-500" aria-hidden="true"></i>',
            'security': '<i class="fas fa-shield-alt text-red-500" aria-hidden="true"></i>',
            'code_smells': '<i class="fas fa-bug text-purple-500" aria-hidden="true"></i>'
        }

        icon = icon_map.get(chart_id, '<i class="fas fa-chart-pie text-blue-500" aria-hidden="true"></i>')

        return f'''
        <div class="bg-white p-6 rounded-2xl shadow-md border border-gray-200 h-full">
            <h3 class="text-lg font-semibold mb-4 flex items-center gap-2 text-gray-800">
                {icon} {title}
            </h3>
            <div class="h-64 w-full">
                <canvas id="chart-{chart_id}" data-chart-type="{chart_type}" data-chart-data="{chart_id}"></canvas>
            </div>
        </div>'''


class HeaderComponent(ReportComponent):
    """Header component for HTML report"""

    @staticmethod
    def render(metrics: 'ProjectMetrics', timestamp: str) -> str:
        """Render the header HTML section"""
        return f'''
        <div class="bg-gradient-to-r from-blue-600 to-blue-800 text-white p-12 text-center mb-8 rounded-3xl shadow-2xl relative overflow-hidden">
            <div class="absolute inset-0 opacity-30">
                <div class="absolute inset-0" style="background-image: url('data:image/svg+xml,<svg xmlns=\\"http://www.w3.org/2000/svg\\" viewBox=\\"0 0 100 100\\"><defs><pattern id=\\"grid\\" width=\\"10\\" height=\\"10\\" patternUnits=\\"userSpaceOnUse\\"><path d=\\"M 10 0 L 0 0 0 10\\" fill=\\"none\\" stroke=\\"rgba(255,255,255,0.1)\\" stroke-width=\\"0.5\\"/></pattern></defs><rect width=\\"100\\" height=\\"100\\" fill=\\"url(%23grid)\\"/></svg>');"></div>
            </div>
            <div class="absolute -top-1/2 -left-1/2 w-[200%] h-[200%] bg-gradient-radial from-white/10 to-transparent animate-float"></div>
            <div class="relative z-10">
                <h1 class="text-4xl lg:text-5xl font-bold mb-3 drop-shadow-sm flex items-center justify-center gap-4 flex-col sm:flex-row">
                    <i class="fas fa-chart-line" aria-hidden="true"></i> 
                    Codebase Analysis Report
                </h1>
                <p class="text-lg opacity-90 font-light">Generated on {timestamp}</p>
            </div>
        </div>'''


class MetricsGridComponent(ReportComponent):
    """Metrics grid component for HTML report"""

    @staticmethod
    def render(metrics: 'ProjectMetrics') -> str:
        """Render the metrics grid HTML section"""
        return f'''
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 mb-10 fade-in">
            <div class="bg-white p-7 rounded-2xl shadow-md border border-gray-200 transition-all duration-300 hover:-translate-y-2 hover:scale-105 hover:shadow-xl relative overflow-hidden group focus-within:outline-2 focus-within:outline-blue-600 focus-within:outline-offset-2" tabindex="0">
                <div class="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-blue-600 to-blue-400 transition-all duration-300 group-hover:h-1.5"></div>
                <div class="flex items-center justify-between mb-5">
                    <div class="w-13 h-13 rounded-xl bg-gradient-to-br from-blue-600 to-blue-800 flex items-center justify-center text-white text-xl shadow-md transition-all duration-300 group-hover:scale-110 group-hover:rotate-6">
                        <i class="fas fa-file-code" aria-hidden="true"></i>
                    </div>
                </div>
                <div class="text-5xl font-bold text-gray-900 leading-none mb-2 bg-gradient-to-r from-gray-900 to-gray-700 bg-clip-text text-transparent">{metrics.total_files:,}</div>
                <div class="text-gray-600 font-medium uppercase text-xs tracking-wider">Files Analyzed</div>
            </div>
            <div class="bg-white p-7 rounded-2xl shadow-md border border-gray-200 transition-all duration-300 hover:-translate-y-2 hover:scale-105 hover:shadow-xl relative overflow-hidden group focus-within:outline-2 focus-within:outline-blue-600 focus-within:outline-offset-2" tabindex="0">
                <div class="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-green-500 to-green-400 transition-all duration-300 group-hover:h-1.5"></div>
                <div class="flex items-center justify-between mb-5">
                    <div class="w-13 h-13 rounded-xl bg-gradient-to-br from-green-500 to-green-600 flex items-center justify-center text-white text-xl shadow-md transition-all duration-300 group-hover:scale-110 group-hover:rotate-6">
                        <i class="fas fa-code" aria-hidden="true"></i>
                    </div>
                </div>
                <div class="text-5xl font-bold text-gray-900 leading-none mb-2 bg-gradient-to-r from-gray-900 to-gray-700 bg-clip-text text-transparent">{metrics.total_loc:,}</div>
                <div class="text-gray-600 font-medium uppercase text-xs tracking-wider">Lines of Code</div>
            </div>
            <div class="bg-white p-7 rounded-2xl shadow-md border border-gray-200 transition-all duration-300 hover:-translate-y-2 hover:scale-105 hover:shadow-xl relative overflow-hidden group focus-within:outline-2 focus-within:outline-blue-600 focus-within:outline-offset-2" tabindex="0">
                <div class="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-yellow-500 to-yellow-400 transition-all duration-300 group-hover:h-1.5"></div>
                <div class="flex items-center justify-between mb-5">
                    <div class="w-13 h-13 rounded-xl bg-gradient-to-br from-yellow-500 to-yellow-600 flex items-center justify-center text-white text-xl shadow-md transition-all duration-300 group-hover:scale-110 group-hover:rotate-6">
                        <i class="fas fa-cube" aria-hidden="true"></i>
                    </div>
                </div>
                <div class="text-5xl font-bold text-gray-900 leading-none mb-2 bg-gradient-to-r from-gray-900 to-gray-700 bg-clip-text text-transparent">{metrics.total_classes:,}</div>
                <div class="text-gray-600 font-medium uppercase text-xs tracking-wider">Classes</div>
            </div>
            <div class="bg-white p-7 rounded-2xl shadow-md border border-gray-200 transition-all duration-300 hover:-translate-y-2 hover:scale-105 hover:shadow-xl relative overflow-hidden group focus-within:outline-2 focus-within:outline-blue-600 focus-within:outline-offset-2" tabindex="0">
                <div class="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-red-500 to-red-400 transition-all duration-300 group-hover:h-1.5"></div>
                <div class="flex items-center justify-between mb-5">
                    <div class="w-13 h-13 rounded-xl bg-gradient-to-br from-red-500 to-red-600 flex items-center justify-center text-white text-xl shadow-md transition-all duration-300 group-hover:scale-110 group-hover:rotate-6">
                        <i class="fas fa-cogs" aria-hidden="true"></i>
                    </div>
                </div>
                <div class="text-5xl font-bold text-gray-900 leading-none mb-2 bg-gradient-to-r from-gray-900 to-gray-700 bg-clip-text text-transparent">{metrics.total_functions:,}</div>
                <div class="text-gray-600 font-medium uppercase text-xs tracking-wider">Functions</div>
            </div>
            <div class="bg-white p-7 rounded-2xl shadow-md border border-gray-200 transition-all duration-300 hover:-translate-y-2 hover:scale-105 hover:shadow-xl relative overflow-hidden group focus-within:outline-2 focus-within:outline-blue-600 focus-within:outline-offset-2" tabindex="0">
                <div class="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-blue-400 to-blue-500 transition-all duration-300 group-hover:h-1.5"></div>
                <div class="flex items-center justify-between mb-5">
                    <div class="w-13 h-13 rounded-xl bg-gradient-to-br from-blue-400 to-blue-500 flex items-center justify-center text-white text-xl shadow-md transition-all duration-300 group-hover:scale-110 group-hover:rotate-6">
                        <i class="fas fa-star" aria-hidden="true"></i>
                    </div>
                </div>
                <div class="text-5xl font-bold text-gray-900 leading-none mb-2 bg-gradient-to-r from-gray-900 to-gray-700 bg-clip-text text-transparent">{metrics.code_quality_score:.1f}%</div>
                <div class="text-gray-600 font-medium uppercase text-xs tracking-wider">Code Quality</div>
            </div>
            <div class="bg-white p-7 rounded-2xl shadow-md border border-gray-200 transition-all duration-300 hover:-translate-y-2 hover:scale-105 hover:shadow-xl relative overflow-hidden group focus-within:outline-2 focus-within:outline-blue-600 focus-within:outline-offset-2" tabindex="0">
                <div class="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-purple-500 to-purple-400 transition-all duration-300 group-hover:h-1.5"></div>
                <div class="flex items-center justify-between mb-5">
                    <div class="w-13 h-13 rounded-xl bg-gradient-to-br from-purple-500 to-purple-600 flex items-center justify-center text-white text-xl shadow-md transition-all duration-300 group-hover:scale-110 group-hover:rotate-6">
                        <i class="fas fa-tools" aria-hidden="true"></i>
                    </div>
                </div>
                <div class="text-5xl font-bold text-gray-900 leading-none mb-2 bg-gradient-to-r from-gray-900 to-gray-700 bg-clip-text text-transparent">{metrics.maintainability_score:.1f}%</div>
                <div class="text-gray-600 font-medium uppercase text-xs tracking-wider">Maintainability</div>
            </div>
        </div>'''


class FooterComponent(ReportComponent):
    """Footer component for HTML report"""

    @staticmethod
    def render(metrics: 'ProjectMetrics') -> str:
        """Render the footer HTML section"""
        return '''
        <div class="text-center py-8 text-gray-500 text-sm border-t border-gray-200 mt-10 bg-gradient-to-r from-gray-50 to-transparent rounded-xl fade-in">
            <p class="mb-2">Report generated by Codebase Analysis Tool</p>
            <p class="flex items-center justify-center gap-2">
                <i class="fas fa-clock" aria-hidden="true"></i> 
                For best results, run analysis regularly to track code quality trends
            </p>
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
        self._timestamp: str = ""
        self._plot_generator = PlotReportGenerator()

    def create(self, metrics: 'ProjectMetrics') -> str:
        """Generate HTML report for the given metrics.
        
        Args:
            metrics: ProjectMetrics object containing analysis data
            
        Returns:
            Complete HTML report as a string
        """
        self._prepare_data(metrics)
        return self._build_html_template(metrics)

    def _prepare_data(self, metrics: 'ProjectMetrics') -> None:
        """Prepare all data components for the HTML template.
        
        Args:
            metrics: ProjectMetrics object containing analysis data
        """
        self._timestamp = format_timestamp()
        self._plot_generator.prepare_chart_data(metrics)

    def _build_html_template(self, metrics: 'ProjectMetrics') -> str:
        """Build the complete HTML template for the report.
        
        Args:
            metrics: ProjectMetrics object containing analysis data
            
        Returns:
            Complete HTML report as a string
        """
        return f'''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Codebase Analysis Report</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.3.0/dist/chart.umd.min.js"></script>
    <style>
        :root {{
            --text-primary: #1f2937;
            --text-secondary: #4b5563;
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
            background-color: #f9fafb;
        }}
        
        .animate-float {{
            animation: float 10s ease-in-out infinite;
        }}
        
        @keyframes float {{
            0%, 100% {{ transform: translateY(0); opacity: 0.05; }}
            50% {{ transform: translateY(-15px); opacity: 0.1; }}
        }}
        
        @keyframes fadein {{
            from {{ opacity: 0; transform: translateY(10px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        
        .fade-in {{
            animation: fadein 0.6s ease-out forwards;
        }}
        
        .bg-gradient-radial {{
            background: radial-gradient(circle, var(--tw-gradient-from) 0%, var(--tw-gradient-to) 100%);
        }}
        
        .w-13 {{
            width: 3.25rem;
        }}
        
        .h-13 {{
            height: 3.25rem;
        }}
    </style>
</head>
<body class="font-inter bg-gradient-to-br from-gray-50 via-white to-gray-50 text-gray-800 text-sm min-h-screen">
    <div class="max-w-7xl mx-auto p-6">
        {HeaderComponent.render(metrics, self._timestamp)}
        {MetricsGridComponent.render(metrics)}
        {self._plot_generator.get_charts_grid_html()}
        
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-10 fade-in">
            {ComplexFilesTableComponent.render(metrics)}
            {DependenciesTableComponent.render(metrics)}
        </div>
        
        {FooterComponent.render(metrics)}
    </div>
    {self._get_javascript()}
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
                            }}
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
                            }}
                        }}
                    }},
                    x: {{
                        title: {{
                            display: true,
                            text: 'Complexity Level',
                            font: {{
                                family: "'Inter', sans-serif",
                                size: 12
                            }}
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
                            }}
                        }}
                    }},
                    x: {{
                        title: {{
                            display: true,
                            text: 'Severity Level',
                            font: {{
                                family: "'Inter', sans-serif",
                                size: 12
                            }}
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
                            }}
                        }}
                    }},
                    x: {{
                        title: {{
                            display: true,
                            text: 'Severity Level',
                            font: {{
                                family: "'Inter', sans-serif",
                                size: 12
                            }}
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
    const defaultColors = [
        '#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6',
        '#06b6d4', '#f97316', '#84cc16', '#ec4899', '#6366f1'
    ];
    
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
            new Chart(canvas, {{
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
        }});
    }});
</script>'''


def generate_direct_html(metrics: 'ProjectMetrics') -> str:
    """Generate HTML directly without using format strings to avoid issues"""
    generator = HTMLReportGenerator()
    return generator.create(metrics)
