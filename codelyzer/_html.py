import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Tuple, Dict, Any

from codelyzer.config import ProjectMetrics, ComplexityLevel


"""Enhanced HTML Report Generator with improved styling and linting fixes."""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from your_project import ProjectMetrics, ComplexityLevel


class PlotReportGenerator:
    """Generate plotting components for codebase analysis reports using Plotly."""
    
    def __init__(self) -> None:
        """Initialize the plot generator with empty data containers."""
        self._language_data: Dict[str, Any] = {}
        self._complexity_data: Dict[str, Any] = {}
    
    def prepare_chart_data(self, metrics: 'ProjectMetrics') -> None:
        """Prepare data for Plotly charts.
        
        Args:
            metrics: ProjectMetrics object containing analysis data
        """
        # Language distribution data
        self._language_data = {
            'labels': list(metrics.languages.keys()),
            'values': list(metrics.languages.values()),
            'colors': [
                '#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6',
                '#06b6d4', '#f97316', '#84cc16', '#ec4899', '#6366f1'
            ]
        }
        
        # Complexity distribution data
        from your_project import ComplexityLevel  # Import here to avoid circular imports
        complexity_labels = [
            level.replace('_', ' ').title() for level in ComplexityLevel
        ]
        complexity_values = [
            metrics.complexity_distribution.get(level, 0) 
            for level in ComplexityLevel
        ]
        
        self._complexity_data = {
            'labels': complexity_labels,
            'values': complexity_values,
            'colors': ['#10b981', '#22c55e', '#f59e0b', '#f97316', '#ef4444', '#dc2626']
        }
    
    def get_charts_grid_html(self) -> str:
        """Get the charts grid HTML section.
        
        Returns:
            HTML string for the charts grid
        """
        return '''
        <div class="charts-grid fade-in">
            <div class="chart-container">
                <h3><i class="fas fa-globe" aria-hidden="true"></i> Language Distribution</h3>
                <div class="chart-wrapper">
                    <div id="languageChart" style="width: 100%; height: 100%;"></div>
                </div>
            </div>
            
            <div class="chart-container">
                <h3><i class="fas fa-layer-group" aria-hidden="true"></i> Complexity Distribution</h3>
                <div class="chart-wrapper">
                    <div id="complexityChart" style="width: 100%; height: 100%;"></div>
                </div>
            </div>
        </div>'''
    
    def get_chart_javascript(self) -> str:
        """Get the JavaScript section for Plotly charts and animations.
        
        Returns:
            JavaScript code for rendering charts
        """
        language_config = json.dumps(self._language_data, indent=2)
        complexity_config = json.dumps(self._complexity_data, indent=2)
        
        return f'''
        // Language Distribution Chart
        const languageConfig = {language_config};
        const languagePlot = document.getElementById('languageChart');
        
        if (languagePlot && languageConfig.labels.length > 0) {{
            Plotly.newPlot(
                languagePlot, 
                [{{
                    labels: languageConfig.labels,
                    values: languageConfig.values,
                    type: 'pie',
                    hole: 0.6,
                    marker: {{
                        colors: languageConfig.colors,
                        line: {{
                            color: '#ffffff',
                            width: 2
                        }}
                    }},
                    textinfo: 'label+percent',
                    hovertemplate: '%{{label}}: %{{value}} files (%{{percent}})<extra></extra>',
                    textposition: 'outside',
                    textfont: {{
                        size: 12,
                        color: '#374151'
                    }}
                }}], 
                {{
                    margin: {{t: 20, b: 20, l: 20, r: 20}},
                    showlegend: true,
                    legend: {{
                        orientation: 'h',
                        yanchor: 'bottom',
                        y: -0.3,
                        xanchor: 'center',
                        x: 0.5,
                        font: {{
                            size: 11,
                            color: '#6b7280'
                        }}
                    }},
                    paper_bgcolor: 'transparent',
                    plot_bgcolor: 'transparent'
                }}, 
                {{responsive: true, displayModeBar: false}}
            );
        }}
        
        // Complexity Distribution Chart
        const complexityConfig = {complexity_config};
        const complexityPlot = document.getElementById('complexityChart');
        
        if (complexityPlot && complexityConfig.labels.length > 0) {{
            Plotly.newPlot(
                complexityPlot, 
                [{{
                    x: complexityConfig.labels,
                    y: complexityConfig.values,
                    type: 'bar',
                    marker: {{
                        color: complexityConfig.colors,
                        line: {{
                            color: 'rgba(255,255,255,0.6)',
                            width: 1
                        }},
                        opacity: 0.8
                    }},
                    hovertemplate: '%{{x}}: %{{y}} files<extra></extra>',
                    text: complexityConfig.values,
                    textposition: 'auto',
                    textfont: {{
                        color: '#ffffff',
                        size: 11,
                        family: 'Inter, sans-serif'
                    }}
                }}], 
                {{
                    margin: {{t: 20, r: 30, l: 50, b: 60}},
                    xaxis: {{
                        title: {{
                            text: 'Complexity Level',
                            font: {{
                                size: 12,
                                color: '#6b7280'
                            }}
                        }},
                        tickangle: -45,
                        tickfont: {{
                            size: 10,
                            color: '#6b7280'
                        }},
                        gridcolor: 'rgba(0,0,0,0.1)'
                    }},
                    yaxis: {{
                        title: {{
                            text: 'Number of Files',
                            font: {{
                                size: 12,
                                color: '#6b7280'
                            }}
                        }},
                        tickfont: {{
                            size: 10,
                            color: '#6b7280'
                        }},
                        gridcolor: 'rgba(0,0,0,0.1)'
                    }},
                    paper_bgcolor: 'transparent',
                    plot_bgcolor: 'transparent'
                }}, 
                {{responsive: true, displayModeBar: false}}
            );
        }}'''


class HTMLReportGenerator:
    """Generate HTML reports for codebase analysis metrics."""
    
    def __init__(self) -> None:
        """Initialize the HTML report generator."""
        self._timestamp: str = ""
        self._complex_files_rows: str = ""
        self._dependencies_rows: str = ""
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
        self._timestamp = self._format_timestamp()
        self._complex_files_rows = self._generate_complex_files_rows(metrics)
        self._dependencies_rows = self._generate_dependencies_rows(metrics)
        self._plot_generator.prepare_chart_data(metrics)
    
    def _format_timestamp(self) -> str:
        """Format the current timestamp for display.
        
        Returns:
            Formatted timestamp string
        """
        return datetime.now().strftime("%B %d, %Y at %H:%M:%S")
    
    def _generate_complex_files_rows(self, metrics: 'ProjectMetrics') -> str:
        """Generate HTML rows for the most complex files table.
        
        Args:
            metrics: ProjectMetrics object containing analysis data
            
        Returns:
            HTML string containing table rows
        """
        rows = ""
        for file_metrics in metrics.most_complex_files[:15]:
            relative_path = self._get_relative_path(file_metrics.file_path)
            issues = len(file_metrics.security_issues) + len(file_metrics.code_smells)
            
            complexity_badge = self._get_complexity_badge(file_metrics.complexity_score)
            issues_display = self._get_issues_display(issues)
            
            rows += f'''
        <tr>
            <td>
                <div class="file-path" title="{relative_path}">
                    <i class="fas fa-file-code" aria-hidden="true"></i>
                    {relative_path}
                </div>
            </td>
            <td><span class="stat-number">{file_metrics.sloc:,}</span></td>
            <td><span class="badge {complexity_badge}">{file_metrics.complexity_score:.0f}</span></td>
            <td>{issues_display}</td>
        </tr>'''
        
        return rows
    
    def _get_relative_path(self, file_path: str) -> str:
        """Get relative path for display, handling cross-drive issues.
        
        Args:
            file_path: Absolute file path
            
        Returns:
            Relative path string safe for display
        """
        try:
            return os.path.relpath(file_path)
        except ValueError:
            path_obj = Path(file_path)
            if path_obj.parent.name:
                return str(Path(path_obj.parent.name) / path_obj.name)
            return path_obj.name
    
    def _get_complexity_badge(self, complexity_score: float) -> str:
        """Get the appropriate badge class for complexity score.
        
        Args:
            complexity_score: Numeric complexity score
            
        Returns:
            CSS class name for the badge
        """
        if complexity_score > 500:
            return "danger"
        elif complexity_score > 200:
            return "warning"
        return "success"
    
    def _get_issues_display(self, issues_count: int) -> str:
        """Get the HTML display for issues count.
        
        Args:
            issues_count: Number of issues found
            
        Returns:
            HTML string for displaying issue count
        """
        if issues_count == 0:
            return '<span class="badge success"><i class="fas fa-check" aria-hidden="true"></i> Clean</span>'
        elif issues_count < 3:
            return f'<span class="badge warning"><i class="fas fa-exclamation-triangle" aria-hidden="true"></i> {issues_count} Issues</span>'
        return f'<span class="badge danger"><i class="fas fa-times-circle" aria-hidden="true"></i> {issues_count} Issues</span>'
    
    def _generate_dependencies_rows(self, metrics: 'ProjectMetrics') -> str:
        """Generate HTML rows for the dependencies table.
        
        Args:
            metrics: ProjectMetrics object containing analysis data
            
        Returns:
            HTML string containing table rows
        """
        rows = ""
        top_deps = self._get_top_dependencies(metrics)
        max_usage = max([count for _, count in top_deps]) if top_deps else 1
        
        for module, count in top_deps:
            usage_percent = (count / max_usage) * 100
            rows += f'''
        <tr>
            <td>
                <code class="module-name">
                    <i class="fas fa-cube" aria-hidden="true"></i>
                    {module}
                </code>
            </td>
            <td><span class="stat-number">{count:,}</span></td>
            <td>
                <div class="usage-display">
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: {usage_percent}%"></div>
                    </div>
                    <span class="usage-percent">{usage_percent:.0f}%</span>
                </div>
            </td>
        </tr>'''
        
        return rows
    
    def _get_top_dependencies(self, metrics: 'ProjectMetrics') -> List[Tuple[str, int]]:
        """Get the top 15 dependencies sorted by usage count.
        
        Args:
            metrics: ProjectMetrics object containing analysis data
            
        Returns:
            List of tuples containing (module_name, usage_count)
        """
        return sorted(
            metrics.dependencies.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:15]
    
    def _build_html_template(self, metrics: 'ProjectMetrics') -> str:
        """Build the complete HTML template with all data inserted.
        
        Args:
            metrics: ProjectMetrics object containing analysis data
            
        Returns:
            Complete HTML document as a string
        """
        return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Codebase Analysis Report</title>
    <meta name="description" content="Comprehensive codebase analysis report with metrics, charts, and insights">
    <script src="https://cdn.plot.ly/plotly-2.24.1.min.js"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        {self._get_css_styles()}
    </style>
</head>
<body>
    <div class="container">
        {self._get_header_html()}
        {self._get_metrics_grid_html(metrics)}
        {self._plot_generator.get_charts_grid_html()}
        {self._get_tables_grid_html()}
        {self._get_footer_html()}
    </div>
    {self._get_javascript()}
</body>
</html>'''
    
    def _get_css_styles(self) -> str:
        """Get the enhanced CSS styles for the HTML template.
        
        Returns:
            CSS styles as a string
        """
        return '''
        :root {
            --primary-color: #2563eb;
            --primary-dark: #1d4ed8;
            --secondary-color: #1e40af;
            --accent-color: #3b82f6;
            --success-color: #10b981;
            --success-light: #34d399;
            --warning-color: #f59e0b;
            --warning-light: #fbbf24;
            --danger-color: #ef4444;
            --danger-light: #f87171;
            --gray-50: #f9fafb;
            --gray-100: #f3f4f6;
            --gray-200: #e5e7eb;
            --gray-300: #d1d5db;
            --gray-400: #9ca3af;
            --gray-500: #6b7280;
            --gray-600: #4b5563;
            --gray-700: #374151;
            --gray-800: #1f2937;
            --gray-900: #111827;
            --shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
            --shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
            --shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1);
            --shadow-xl: 0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1);
            --shadow-2xl: 0 25px 50px -12px rgb(0 0 0 / 0.25);
            --transition-all: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            --transition-colors: color 0.15s ease-in-out, background-color 0.15s ease-in-out, border-color 0.15s ease-in-out;
        }

        * { 
            margin: 0; 
            padding: 0; 
            box-sizing: border-box; 
        }

        body { 
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6; 
            color: var(--gray-800); 
            background: linear-gradient(135deg, var(--gray-50) 0%, #ffffff 50%, var(--gray-50) 100%);
            font-size: 14px;
            min-height: 100vh;
            scroll-behavior: smooth;
        }

        .container { 
            max-width: 1400px; 
            margin: 0 auto; 
            padding: 24px;
        }

        .metrics-grid { 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); 
            gap: 24px; 
            margin-bottom: 40px; 
        }

        .charts-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 32px;
            margin-bottom: 40px;
        }

        .tables-grid {
            display: grid;
            grid-template-columns: 1fr;
            gap: 32px;
            margin-bottom: 40px;
        }

        .header { 
            background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%);
            color: white; 
            padding: 48px 0; 
            text-align: center; 
            margin-bottom: 32px; 
            border-radius: 20px;
            box-shadow: var(--shadow-2xl);
            position: relative;
            overflow: hidden;
        }

        .header::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><pattern id="grid" width="10" height="10" patternUnits="userSpaceOnUse"><path d="M 10 0 L 0 0 0 10" fill="none" stroke="rgba(255,255,255,0.1)" stroke-width="0.5"/></pattern></defs><rect width="100" height="100" fill="url(%23grid)"/></svg>');
            opacity: 0.3;
        }

        .header::after {
            content: '';
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);
            animation: float 6s ease-in-out infinite;
        }

        .header-content { 
            position: relative; 
            z-index: 1; 
        }

        .header h1 { 
            font-size: 2.5rem; 
            font-weight: 700; 
            margin-bottom: 12px;
            text-shadow: 0 2px 4px rgba(0,0,0,0.1);
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 16px;
        }

        .header p { 
            font-size: 1.1rem; 
            opacity: 0.9; 
            font-weight: 300;
        }

        .metric-card { 
            background: white; 
            padding: 28px; 
            border-radius: 16px; 
            box-shadow: var(--shadow-md);
            border: 1px solid var(--gray-200);
            transition: var(--transition-all);
            position: relative;
            overflow: hidden;
        }

        .metric-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: linear-gradient(90deg, var(--primary-color), var(--accent-color));
            transition: var(--transition-all);
        }

        .metric-card:hover { 
            transform: translateY(-8px) scale(1.02); 
            box-shadow: var(--shadow-xl);
        }

        .metric-card:hover::before {
            height: 6px;
        }

        .metric-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 20px;
        }

        .metric-icon {
            width: 52px;
            height: 52px;
            border-radius: 14px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 22px;
            color: white;
            transition: var(--transition-all);
            box-shadow: var(--shadow-md);
        }

        .metric-card:hover .metric-icon {
            transform: scale(1.1) rotate(5deg);
        }

        .metric-icon.files { background: linear-gradient(135deg, var(--primary-color), var(--primary-dark)); }
        .metric-icon.code { background: linear-gradient(135deg, var(--success-color), var(--success-light)); }
        .metric-icon.classes { background: linear-gradient(135deg, var(--warning-color), var(--warning-light)); }
        .metric-icon.functions { background: linear-gradient(135deg, var(--danger-color), var(--danger-light)); }
        .metric-icon.quality { background: linear-gradient(135deg, var(--accent-color), #60a5fa); }
        .metric-icon.maintainability { background: linear-gradient(135deg, #8b5cf6, #a78bfa); }

        .metric-value { 
            font-size: 2.75rem; 
            font-weight: 700; 
            color: var(--gray-900);
            line-height: 1;
            margin-bottom: 8px;
            background: linear-gradient(135deg, var(--gray-900), var(--gray-700));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }

        .metric-label { 
            color: var(--gray-600); 
            font-weight: 500;
            text-transform: uppercase;
            font-size: 0.75rem;
            letter-spacing: 0.05em;
        }

        .chart-container { 
            background: white; 
            padding: 32px; 
            border-radius: 16px; 
            box-shadow: var(--shadow-md);
            border: 1px solid var(--gray-200);
            position: relative;
            transition: var(--transition-all);
        }

        .chart-container:hover {
            box-shadow: var(--shadow-lg);
            transform: translateY(-2px);
        }

        .chart-container h3 {
            font-size: 1.25rem;
            font-weight: 600;
            margin-bottom: 24px;
            color: var(--gray-900);
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .chart-wrapper {
            position: relative;
            height: 400px;
            width: 100%;
            border-radius: 12px;
            overflow: hidden;
        }

        .table-container { 
            background: white; 
            border-radius: 16px; 
            box-shadow: var(--shadow-md);
            border: 1px solid var(--gray-200);
            overflow: hidden;
            transition: var(--transition-all);
        }

        .table-container:hover {
            box-shadow: var(--shadow-lg);
        }

        .table-header {
            background: linear-gradient(135deg, var(--gray-50), var(--gray-100));
            padding: 24px 32px;
            border-bottom: 1px solid var(--gray-200);
        }

        .table-header h3 {
            font-size: 1.25rem;
            font-weight: 600;
            color: var(--gray-900);
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .table-wrapper {
            overflow-x: auto;
        }

        table { 
            width: 100%; 
            border-collapse: collapse; 
        }

        th, td { 
            padding: 16px 24px; 
            text-align: left; 
            border-bottom: 1px solid var(--gray-200);
        }

        th { 
            background-color: var(--gray-50); 
            font-weight: 600;
            color: var(--gray-700);
            font-size: 0.875rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            position: sticky;
            top: 0;
            z-index: 10;
        }

        tbody tr { 
            transition: var(--transition-colors);
        }

        tbody tr:hover { 
            background-color: var(--gray-50);
            transform: scale(1.005);
        }

        tbody tr:last-child td {
            border-bottom: none;
        }

        .progress-bar { 
            width: 100%; 
            height: 10px; 
            background-color: var(--gray-200); 
            border-radius: 6px; 
            overflow: hidden;
            box-shadow: inset 0 1px 2px rgba(0,0,0,0.1);
        }

        .progress-fill { 
            height: 100%; 
            background: linear-gradient(90deg, var(--success-color), var(--warning-color), var(--danger-color)); 
            transition: width 0.8s cubic-bezier(0.4, 0, 0.2, 1);
            border-radius: 6px;
            position: relative;
        }

        .progress-fill::after {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: linear-gradient(45deg, transparent 40%, rgba(255,255,255,0.3) 50%, transparent 60%);
            animation: shimmer 2s infinite;
        }

        .usage-display {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .usage-percent {
            font-size: 0.75rem;
            color: var(--gray-600);
            min-width: 40px;
            font-weight: 500;
        }

        .badge {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 6px 12px;
            border-radius: 8px;
            font-size: 0.75rem;
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 0.025em;
            transition: var(--transition-all);
        }

        .badge:hover {
            transform: scale(1.05);
        }

        .badge.success {
            background: linear-gradient(135deg, #dcfce7, #bbf7d0);
            color: #166534;
            border: 1px solid #86efac;
        }

        .badge.warning {
            background: linear-gradient(135deg, #fef3c7, #fde68a);
            color: #92400e;
            border: 1px solid #fcd34d;
        }

        .badge.danger {
            background: linear-gradient(135deg, #fee2e2, #fecaca);
            color: #991b1b;
            border: 1px solid #fca5a5;
        }

        .file-path {
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
            font-size: 0.8rem;
            color: var(--gray-600);
            max-width: 300px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 4px 8px;
            background: var(--gray-50);
            border-radius: 6px;
            border: 1px solid var(--gray-200);
        }

        .module-name {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 4px 8px;
            background: var(--gray-50);
            border-radius: 6px;
            border: 1px solid var(--gray-200);
            font-size: 0.85rem;
        }

        .stat-number {
            font-weight: 600;
            color: var(--gray-900);
            font-variant-numeric: tabular-nums;
        }

        .footer {
            text-align: center;
            padding: 32px 0;
            color: var(--gray-500);
            font-size: 0.875rem;
            border-top: 1px solid var(--gray-200);
            margin-top: 40px;
            background: linear-gradient(135deg, var(--gray-50), transparent);
            border-radius: 12px;
        }

        .footer p {
            margin-bottom: 8px;
        }

        .footer a {
            color: var(--primary-color);
            text-decoration: none;
            font-weight: 500;
            transition: var(--transition-colors);
        }

        .footer a:hover {
            color: var(--primary-dark);
            text-decoration: underline;
        }

        .loading {
            opacity: 0.7;
            pointer-events: none;
        }

        .fade-in {
            animation: fadeIn 0.8s cubic-bezier(0.4, 0, 0.2, 1);
        }

        .pulse {
            animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
        }

        /* Animations */
        @keyframes fadeIn {
            from { 
                opacity: 0; 
                transform: translateY(30px) scale(0.95); 
            }
            to { 
                opacity: 1; 
                transform: translateY(0) scale(1); 
            }
        }

        @keyframes float {
            0%, 100% { 
                transform: translateY(0px) rotate(0deg); 
            }
            50% { 
                transform: translateY(-20px) rotate(2deg); 
            }
        }

        @keyframes shimmer {
            0% { 
                transform: translateX(-100%); 
            }
            100% { 
                transform: translateX(200%); 
            }
        }

        @keyframes pulse {
            0%, 100% { 
                opacity: 1; 
            }
            50% { 
                opacity: .5; 
            }
        }

        /* Responsive Design */
        @media (max-width: 1200px) {
            .container {
                max-width: 100%;
                padding: 20px;
            }
        }

        @media (max-width: 1024px) {
            .charts-grid {
                grid-template-columns: 1fr;
                gap: 24px;
            }
            
            .metric-value {
                font-size: 2.25rem;
            }
        }

        @media (max-width: 768px) {
            .container {
                padding: 16px;
            }
            
            .metrics-grid {
                grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
                gap: 16px;
            }
            
            .metric-card {
                padding: 20px;
            }
            
            .metric-value {
                font-size: 2rem;
            }
            
            .header {
                padding: 32px 20px;
                margin-bottom: 24px;
            }
            
            .header h1 {
                font-size: 2rem;
                flex-direction: column;
                gap: 8px;
            }
            
            .chart-container, .table-container {
                padding: 20px;
            }
            
            .chart-wrapper {
                height: 300px;
            }
            
            th, td {
                padding: 12px 16px;
                font-size: 0.8rem;
            }
            
            .file-path, .module-name {
                max-width: 200px;
                font-size: 0.75rem;
            }
        }

        @media (max-width: 480px) {
            .metrics-grid {
                grid-template-columns: 1fr;
            }
            
            .header h1 {
                font-size: 1.75rem;
            }
            
            .metric-value {
                font-size: 1.75rem;
            }
            
            .chart-wrapper {
                height: 250px;
            }
            
            .table-wrapper {
                font-size: 0.75rem;
            }
        }

        /* Print Styles */
        @media print {
            body {
                background: white;
                font-size: 12px;
            }
            
            .container {
                max-width: none;
                padding: 0;
            }
            
            .header {
                background: var(--gray-100) !important;
                color: var(--gray-900) !important;
                box-shadow: none;
            }
            
            .metric-card, .chart-container, .table-container {
                box-shadow: none;
                border: 1px solid var(--gray-300);
                break-inside: avoid;
            }
            
            .charts-grid {
                break-inside: avoid;
            }
        }

        /* Accessibility Improvements */
        @media (prefers-reduced-motion: reduce) {
            *, *::before, *::after {
                animation-duration: 0.01ms !important;
                animation-iteration-count: 1 !important;
                transition-duration: 0.01ms !important;
            }
        }

        /* Focus styles for keyboard navigation */
        .metric-card:focus-within,
        .chart-container:focus-within,
        .table-container:focus-within {
            outline: 2px solid var(--primary-color);
            outline-offset: 2px;
        }

        /* High contrast mode support */
        @media (prefers-contrast: high) {
            :root {
                --gray-100: #e0e0e0;
                --gray-200: #c0c0c0;
                --gray-600: #404040;
                --gray-800: #202020;
            }
        }
        '''
    
    def _get_header_html(self) -> str:
        """Get the header HTML section.
        
        Returns:
            HTML string for the header
        """
        return f'''
        <div class="header">
            <div class="header-content">
                <h1>
                    <i class="fas fa-chart-line" aria-hidden="true"></i> 
                    Codebase Analysis Report
                </h1>
                <p>Generated on {self._timestamp}</p>
            </div>
        </div>'''
    
    def _get_metrics_grid_html(self, metrics: 'ProjectMetrics') -> str:
        """Get the metrics grid HTML section.
        
        Args:
            metrics: ProjectMetrics object containing analysis data
            
        Returns:
            HTML string for the metrics grid
        """
        return f'''
        <div class="metrics-grid fade-in">
            <div class="metric-card" tabindex="0">
                <div class="metric-header">
                    <div class="metric-icon files">
                        <i class="fas fa-file-code" aria-hidden="true"></i>
                    </div>
                </div>
                <div class="metric-value">{metrics.total_files:,}</div>
                <div class="metric-label">Files Analyzed</div>
            </div>
            <div class="metric-card" tabindex="0">
                <div class="metric-header">
                    <div class="metric-icon code">
                        <i class="fas fa-code" aria-hidden="true"></i>
                    </div>
                </div>
                <div class="metric-value">{metrics.total_loc:,}</div>
                <div class="metric-label">Lines of Code</div>
            </div>
            <div class="metric-card" tabindex="0">
                <div class="metric-header">
                    <div class="metric-icon classes">
                        <i class="fas fa-cube" aria-hidden="true"></i>
                    </div>
                </div>
                <div class="metric-value">{metrics.total_classes:,}</div>
                <div class="metric-label">Classes</div>
            </div>
            <div class="metric-card" tabindex="0">
                <div class="metric-header">
                    <div class="metric-icon functions">
                        <i class="fas fa-cogs" aria-hidden="true"></i>
                    </div>
                </div>
                <div class="metric-value">{metrics.total_functions:,}</div>
                <div class="metric-label">Functions</div>
            </div>
            <div class="metric-card" tabindex="0">
                <div class="metric-header">
                    <div class="metric-icon quality">
                        <i class="fas fa-star" aria-hidden="true"></i>
                    </div>
                </div>
                <div class="metric-value">{metrics.code_quality_score:.1f}%</div>
                <div class="metric-label">Code Quality</div>
            </div>
            <div class="metric-card" tabindex="0">
                <div class="metric-header">
                    <div class="metric-icon maintainability">
                        <i class="fas fa-tools" aria-hidden="true"></i>
                    </div>
                </div>
                <div class="metric-value">{metrics.maintainability_score:.1f}%</div>
                <div class="metric-label">Maintainability</div>
            </div>
        </div>'''
    
    def _get_tables_grid_html(self) -> str:
        """Get the tables grid HTML section.
        
        Returns:
            HTML string for the tables grid
        """
        return f'''
        <div class="tables-grid fade-in">
            <div class="table-container">
                <div class="table-header">
                    <h3>
                        <i class="fas fa-fire" aria-hidden="true"></i> 
                        Most Complex Files
                    </h3>
                </div>
                <div class="table-wrapper">
                    <table role="table">
                        <thead>
                            <tr role="row">
                                <th scope="col">File</th>
                                <th scope="col">Lines</th>
                                <th scope="col">Complexity</th>
                                <th scope="col">Issues</th>
                            </tr>
                        </thead>
                        <tbody>
                            {self._complex_files_rows}
                        </tbody>
                    </table>
                </div>
            </div>
            
            <div class="table-container">
                <div class="table-header">
                    <h3>
                        <i class="fas fa-box" aria-hidden="true"></i> 
                        Top Dependencies
                    </h3>
                </div>
                <div class="table-wrapper">
                    <table role="table">
                        <thead>
                            <tr role="row">
                                <th scope="col">Module</th>
                                <th scope="col">Usage Count</th>
                                <th scope="col">Usage Distribution</th>
                            </tr>
                        </thead>
                        <tbody>
                            {self._dependencies_rows}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>'''
    
    def _get_footer_html(self) -> str:
        """Get the footer HTML section.
        
        Returns:
            HTML string for the footer
        """
        return '''
        <div class="footer fade-in">
            <p>Report generated by Codebase Analysis Tool</p>
            <p>
                <i class="fas fa-clock" aria-hidden="true"></i> 
                For best results, run analysis regularly to track code quality trends
            </p>
        </div>'''
    
    def _get_javascript(self) -> str:
        """Get the JavaScript section for charts and animations.
        
        Returns:
            JavaScript code as a string
        """
        return f'''
    <script>
        {self._plot_generator.get_chart_javascript()}
        
        // Enhanced loading states and animations
        document.addEventListener('DOMContentLoaded', function() {{
            // Staggered fade-in animation
            const elements = document.querySelectorAll('.fade-in');
            elements.forEach((el, index) => {{
                el.style.opacity = '0';
                el.style.transform = 'translateY(30px) scale(0.95)';
                setTimeout(() => {{
                    el.style.transition = 'all 0.8s cubic-bezier(0.4, 0, 0.2, 1)';
                    el.style.opacity = '1';
                    el.style.transform = 'translateY(0) scale(1)';
                }}, index * 150);
            }});
            
            // Animate progress bars
            setTimeout(() => {{
                const progressBars = document.querySelectorAll('.progress-fill');
                progressBars.forEach(bar => {{
                    const width = bar.style.width;
                    bar.style.width = '0%';
                    setTimeout(() => {{
                        bar.style.width = width;
                    }}, 100);
                }});
            }}, 1000);
            
            // Add hover effects to metric cards
            const metricCards = document.querySelectorAll('.metric-card');
            metricCards.forEach(card => {{
                card.addEventListener('mouseenter', function() {{
                    this.style.transform = 'translateY(-8px) scale(1.02)';
                }});
                
                card.addEventListener('mouseleave', function() {{
                    this.style.transform = 'translateY(0) scale(1)';
                }});
            }});
            
            // Smooth scroll for focus navigation
            document.addEventListener('keydown', function(e) {{
                if (e.key === 'Tab') {{
                    setTimeout(() => {{
                        const focusedElement = document.activeElement;
                        if (focusedElement && focusedElement.scrollIntoView) {{
                            focusedElement.scrollIntoView({{
                                behavior: 'smooth',
                                block: 'center'
                            }});
                        }}
                    }}, 100);
                }}
            }});
            
            // Add loading indicator for charts
            const chartContainers = document.querySelectorAll('.chart-container');
            chartContainers.forEach(container => {{
                const wrapper = container.querySelector('.chart-wrapper');
                if (wrapper) {{
                    wrapper.innerHTML = '<div class="loading-indicator" style="display: flex; align-items: center; justify-content: center; height: 100%; color: var(--gray-500);"><i class="fas fa-spinner fa-spin fa-2x"></i></div>' + wrapper.innerHTML;
                    
                    // Remove loading indicator after charts load
                    setTimeout(() => {{
                        const loadingIndicator = wrapper.querySelector('.loading-indicator');
                        if (loadingIndicator) {{
                            loadingIndicator.remove();
                        }}
                    }}, 2000);
                }}
            }});
            
            // Error handling for charts
            window.addEventListener('error', function(e) {{
                if (e.message && e.message.includes('Plotly')) {{
                    console.warn('Chart rendering issue detected, attempting fallback...');
                    // Could implement fallback chart rendering here
                }}
            }});
        }});
        
        // Performance monitoring
        window.addEventListener('load', function() {{
            if (performance.mark) {{
                performance.mark('report-loaded');
                console.log('Report fully loaded and interactive');
            }}
        }});
    </script>'''

def generate_direct_html(metrics: 'ProjectMetrics') -> str:
    """Generate HTML directly without using format strings to avoid issues"""
    generator = HTMLReportGenerator()
    return generator.create(metrics)