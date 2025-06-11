import json
import os
from datetime import datetime
from pathlib import Path

from codelyzer.config import ProjectMetrics, ComplexityLevel


import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Tuple

class PlotReportGenerator:
    """Generate plotting components for codebase analysis reports."""
    
    def __init__(self):
        self._language_labels_json = ""
        self._language_data_json = ""
        self._complexity_labels_json = ""
        self._complexity_data_json = ""
    
    def prepare_chart_data(self, metrics: 'ProjectMetrics') -> None:
        """Prepare JSON data for charts."""
        self._language_labels_json = json.dumps(list(metrics.languages.keys()))
        self._language_data_json = json.dumps(list(metrics.languages.values()))
        
        complexity_labels = [level.replace('_', ' ').title() for level in ComplexityLevel]
        complexity_data = [metrics.complexity_distribution.get(level, 0) for level in ComplexityLevel]
        
        self._complexity_labels_json = json.dumps(complexity_labels)
        self._complexity_data_json = json.dumps(complexity_data)
    
    def get_charts_grid_html(self) -> str:
        """Get the charts grid HTML section."""
        return '''
        <div class="charts-grid fade-in">
            <div class="chart-container">
                <h3><i class="fas fa-globe"></i> Language Distribution</h3>
                <div class="chart-wrapper">
                    <canvas id="languageChart"></canvas>
                </div>
            </div>
            
            <div class="chart-container">
                <h3><i class="fas fa-layer-group"></i> Complexity Distribution</h3>
                <div class="chart-wrapper">
                    <canvas id="complexityChart"></canvas>
                </div>
            </div>
        </div>'''
    
    def get_chart_javascript(self) -> str:
        """Get the JavaScript section for charts and animations."""
        return f'''
        const chartOptions = {{
            responsive: true,
            maintainAspectRatio: false,
            plugins: {{
                legend: {{
                    position: 'bottom',
                    labels: {{
                        usePointStyle: true,
                        padding: 20,
                        font: {{
                            size: 12
                        }}
                    }}
                }}
            }}
        }};

        // Language Distribution Chart
        const languageCtx = document.getElementById('languageChart').getContext('2d');
        new Chart(languageCtx, {{
            type: 'doughnut',
            data: {{
                labels: {self._language_labels_json},
                datasets: [{{
                    data: {self._language_data_json},
                    backgroundColor: [
                        '#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6',
                        '#06b6d4', '#f97316', '#84cc16', '#ec4899', '#6366f1'
                    ],
                    borderWidth: 2,
                    borderColor: '#ffffff',
                    hoverBorderWidth: 3
                }}]
            }},
            options: {{
                ...chartOptions,
                cutout: '60%',
                plugins: {{
                    ...chartOptions.plugins,
                    tooltip: {{
                        callbacks: {{
                            label: function(context) {{
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = ((context.raw / total) * 100).toFixed(1);
                                return context.label + ': ' + context.raw + ' files (' + percentage + '%)';
                            }}
                        }}
                    }}
                }}
            }}
        }});
        
        // Complexity Distribution Chart
        const complexityCtx = document.getElementById('complexityChart').getContext('2d');
        new Chart(complexityCtx, {{
            type: 'bar',
            data: {{
                labels: {self._complexity_labels_json},
                datasets: [{{
                    label: 'Number of Files',
                    data: {self._complexity_data_json},
                    backgroundColor: [
                        '#10b981', '#22c55e', '#f59e0b', '#f97316', '#ef4444', '#dc2626'
                    ],
                    borderRadius: 6,
                    borderSkipped: false,
                }}]
            }},
            options: {{
                ...chartOptions,
                plugins: {{
                    ...chartOptions.plugins,
                    legend: {{
                        display: false
                    }}
                }},
                scales: {{
                    x: {{
                        grid: {{
                            display: false
                        }},
                        ticks: {{
                            font: {{
                                size: 11
                            }}
                        }}
                    }},
                    y: {{
                        beginAtZero: true,
                        grid: {{
                            color: '#f3f4f6'
                        }},
                        ticks: {{
                            font: {{
                                size: 11
                            }}
                        }}
                    }}
                }}
            }}
        }});'''


class HTMLReportGenerator:
    """Generate HTML reports for codebase analysis metrics."""
    
    def __init__(self):
        self._timestamp = None
        self._complex_files_rows = ""
        self._dependencies_rows = ""
        self._plot_generator = PlotReportGenerator()
    
    def create(self, metrics: 'ProjectMetrics') -> str:
        """Generate HTML report for the given metrics."""
        self._prepare_data(metrics)
        return self._build_html_template(metrics)
    
    def _prepare_data(self, metrics: 'ProjectMetrics') -> None:
        """Prepare all data components for the HTML template."""
        self._timestamp = self._format_timestamp()
        self._complex_files_rows = self._generate_complex_files_rows(metrics)
        self._dependencies_rows = self._generate_dependencies_rows(metrics)
        self._plot_generator.prepare_chart_data(metrics)
    
    def _format_timestamp(self) -> str:
        """Format the current timestamp for display."""
        return datetime.now().strftime("%B %d, %Y at %H:%M:%S")
    
    def _generate_complex_files_rows(self, metrics: 'ProjectMetrics') -> str:
        """Generate HTML rows for the most complex files table."""
        rows = ""
        for file_metrics in metrics.most_complex_files[:15]:
            relative_path = self._get_relative_path(file_metrics.file_path)
            issues = len(file_metrics.security_issues) + len(file_metrics.code_smells)
            
            complexity_badge = self._get_complexity_badge(file_metrics.complexity_score)
            issues_display = self._get_issues_display(issues)
            
            rows += f'''
        <tr>
            <td><div class="file-path" title="{relative_path}">{relative_path}</div></td>
            <td><span class="stat-number">{file_metrics.sloc:,}</span></td>
            <td><span class="badge {complexity_badge}">{file_metrics.complexity_score:.0f}</span></td>
            <td>{issues_display}</td>
        </tr>'''
        
        return rows
    
    def _get_relative_path(self, file_path: str) -> str:
        """Get relative path for display, handling cross-drive issues."""
        try:
            return os.path.relpath(file_path)
        except ValueError:
            path_obj = Path(file_path)
            if path_obj.parent.name:
                return str(Path(path_obj.parent.name) / path_obj.name)
            else:
                return path_obj.name
    
    def _get_complexity_badge(self, complexity_score: float) -> str:
        """Get the appropriate badge class for complexity score."""
        if complexity_score > 500:
            return "danger"
        elif complexity_score > 200:
            return "warning"
        else:
            return "success"
    
    def _get_issues_display(self, issues_count: int) -> str:
        """Get the HTML display for issues count."""
        if issues_count == 0:
            return '<span class="badge success">✓ Clean</span>'
        elif issues_count < 3:
            return f'<span class="badge warning">{issues_count} Issues</span>'
        else:
            return f'<span class="badge danger">{issues_count} Issues</span>'
    
    def _generate_dependencies_rows(self, metrics: 'ProjectMetrics') -> str:
        """Generate HTML rows for the dependencies table."""
        rows = ""
        top_deps = self._get_top_dependencies(metrics)
        max_usage = max([count for _, count in top_deps]) if top_deps else 1
        
        for module, count in top_deps:
            usage_percent = (count / max_usage) * 100
            rows += f'''
        <tr>
            <td><code>{module}</code></td>
            <td><span class="stat-number">{count:,}</span></td>
            <td>
                <div style="display: flex; align-items: center; gap: 12px;">
                    <div class="progress-bar" style="flex: 1;">
                        <div class="progress-fill" style="width: {usage_percent}%"></div>
                    </div>
                    <span style="font-size: 0.75rem; color: var(--gray-600); min-width: 40px;">{usage_percent:.0f}%</span>
                </div>
            </td>
        </tr>'''
        
        return rows
    
    def _get_top_dependencies(self, metrics: 'ProjectMetrics') -> List[Tuple[str, int]]:
        """Get the top 15 dependencies sorted by usage count."""
        return sorted(metrics.dependencies.items(), key=lambda x: x[1], reverse=True)[:15]
    
    def _build_html_template(self, metrics: 'ProjectMetrics') -> str:
        """Build the complete HTML template with all data inserted."""
        return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Codebase Analysis Report</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/3.9.1/chart.min.js"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
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
    </div>
    {self._get_javascript()}
</body>
</html>'''
    
    def _get_css_styles(self) -> str:
        """Get the CSS styles for the HTML template."""
        return '''
        :root {
            --primary-color: #2563eb;
            --secondary-color: #1e40af;
            --accent-color: #3b82f6;
            --success-color: #10b981;
            --warning-color: #f59e0b;
            --danger-color: #ef4444;
            --gray-50: #f9fafb;
            --gray-100: #f3f4f6;
            --gray-200: #e5e7eb;
            --gray-600: #4b5563;
            --gray-800: #1f2937;
            --gray-900: #111827;
            --shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
            --shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
            --shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1);
            --shadow-xl: 0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1);
        }

        * { 
            margin: 0; 
            padding: 0; 
            box-sizing: border-box; 
        }

        body { 
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6; 
            color: var(--gray-800); 
            background: linear-gradient(135deg, var(--gray-50) 0%, #ffffff 100%);
            font-size: 14px;
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
        }

        .header { 
            background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%);
            color: white; 
            padding: 48px 0; 
            text-align: center; 
            margin-bottom: 32px; 
            border-radius: 16px;
            box-shadow: var(--shadow-xl);
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

        .header-content { 
            position: relative; 
            z-index: 1; 
        }

        .header h1 { 
            font-size: 2.5rem; 
            font-weight: 700; 
            margin-bottom: 12px;
            text-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }

        .header p { 
            font-size: 1.1rem; 
            opacity: 0.9; 
            font-weight: 300;
        }

        .metric-card { 
            background: white; 
            padding: 28px; 
            border-radius: 12px; 
            box-shadow: var(--shadow-md);
            border: 1px solid var(--gray-200);
            transition: all 0.3s ease;
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
        }

        .metric-card:hover { 
            transform: translateY(-4px); 
            box-shadow: var(--shadow-lg);
        }

        .metric-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 16px;
        }

        .metric-icon {
            width: 48px;
            height: 48px;
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 20px;
            color: white;
        }

        .metric-icon.files { background: var(--primary-color); }
        .metric-icon.code { background: var(--success-color); }
        .metric-icon.classes { background: var(--warning-color); }
        .metric-icon.functions { background: var(--danger-color); }
        .metric-icon.quality { background: var(--accent-color); }
        .metric-icon.maintainability { background: #8b5cf6; }

        .metric-value { 
            font-size: 2.5rem; 
            font-weight: 700; 
            color: var(--gray-900);
            line-height: 1;
        }

        .metric-label { 
            color: var(--gray-600); 
            margin-top: 8px; 
            font-weight: 500;
            text-transform: uppercase;
            font-size: 0.75rem;
            letter-spacing: 0.05em;
        }

        .chart-container { 
            background: white; 
            padding: 32px; 
            border-radius: 12px; 
            box-shadow: var(--shadow-md);
            border: 1px solid var(--gray-200);
            position: relative;
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
            height: 300px;
            width: 100%;
        }

        .table-container { 
            background: white; 
            border-radius: 12px; 
            box-shadow: var(--shadow-md);
            border: 1px solid var(--gray-200);
            overflow: hidden;
        }

        .table-header {
            background: var(--gray-50);
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
        }

        tbody tr { 
            transition: background-color 0.2s ease;
        }

        tbody tr:hover { 
            background-color: var(--gray-50);
        }

        tbody tr:last-child td {
            border-bottom: none;
        }

        .complexity-low { 
            color: var(--success-color); 
            font-weight: 600;
        }

        .complexity-medium { 
            color: var(--warning-color); 
            font-weight: 600;
        }

        .complexity-high { 
            color: var(--danger-color); 
            font-weight: 600;
        }

        .progress-bar { 
            width: 100%; 
            height: 8px; 
            background-color: var(--gray-200); 
            border-radius: 4px; 
            overflow: hidden;
        }

        .progress-fill { 
            height: 100%; 
            background: linear-gradient(90deg, var(--success-color), var(--warning-color), var(--danger-color)); 
            transition: width 0.3s ease;
            border-radius: 4px;
        }

        .badge {
            display: inline-flex;
            align-items: center;
            padding: 4px 12px;
            border-radius: 6px;
            font-size: 0.75rem;
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 0.025em;
        }

        .badge.success {
            background-color: #dcfce7;
            color: #166534;
        }

        .badge.warning {
            background-color: #fef3c7;
            color: #92400e;
        }

        .badge.danger {
            background-color: #fee2e2;
            color: #991b1b;
        }

        .file-path {
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
            font-size: 0.8rem;
            color: var(--gray-600);
            max-width: 300px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }

        .stat-number {
            font-weight: 600;
            color: var(--gray-900);
        }

        .loading {
            opacity: 0.7;
            pointer-events: none;
        }

        .fade-in {
            animation: fadeIn 0.6s ease-in;
        }

        @media (max-width: 1024px) {
            .charts-grid {
                grid-template-columns: 1fr;
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
            
            .header h1 {
                font-size: 2rem;
            }
            
            th, td {
                padding: 12px 16px;
            }
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        '''
    
    def _get_header_html(self) -> str:
        """Get the header HTML section."""
        return f'''
        <div class="header">
            <div class="header-content">
                <h1><i class="fas fa-chart-line"></i> Codebase Analysis Report</h1>
                <p>Generated on {self._timestamp}</p>
            </div>
        </div>'''
    
    def _get_metrics_grid_html(self, metrics: 'ProjectMetrics') -> str:
        """Get the metrics grid HTML section."""
        return f'''
        <div class="metrics-grid fade-in">
            <div class="metric-card">
                <div class="metric-header">
                    <div class="metric-icon files"><i class="fas fa-file-code"></i></div>
                </div>
                <div class="metric-value">{metrics.total_files:,}</div>
                <div class="metric-label">Files Analyzed</div>
            </div>
            <div class="metric-card">
                <div class="metric-header">
                    <div class="metric-icon code"><i class="fas fa-code"></i></div>
                </div>
                <div class="metric-value">{metrics.total_loc:,}</div>
                <div class="metric-label">Lines of Code</div>
            </div>
            <div class="metric-card">
                <div class="metric-header">
                    <div class="metric-icon classes"><i class="fas fa-cube"></i></div>
                </div>
                <div class="metric-value">{metrics.total_classes:,}</div>
                <div class="metric-label">Classes</div>
            </div>
            <div class="metric-card">
                <div class="metric-header">
                    <div class="metric-icon functions"><i class="fas fa-cogs"></i></div>
                </div>
                <div class="metric-value">{metrics.total_functions:,}</div>
                <div class="metric-label">Functions</div>
            </div>
            <div class="metric-card">
                <div class="metric-header">
                    <div class="metric-icon quality"><i class="fas fa-star"></i></div>
                </div>
                <div class="metric-value">{metrics.code_quality_score:.1f}%</div>
                <div class="metric-label">Code Quality</div>
            </div>
            <div class="metric-card">
                <div class="metric-header">
                    <div class="metric-icon maintainability"><i class="fas fa-tools"></i></div>
                </div>
                <div class="metric-value">{metrics.maintainability_score:.1f}%</div>
                <div class="metric-label">Maintainability</div>
            </div>
        </div>'''
    
    def _get_tables_grid_html(self) -> str:
        """Get the tables grid HTML section."""
        return f'''
        <div class="tables-grid fade-in">
            <div class="table-container">
                <div class="table-header">
                    <h3><i class="fas fa-fire"></i> Most Complex Files</h3>
                </div>
                <div class="table-wrapper">
                    <table>
                        <thead>
                            <tr>
                                <th>File</th>
                                <th>Lines</th>
                                <th>Complexity</th>
                                <th>Issues</th>
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
                    <h3><i class="fas fa-box"></i> Top Dependencies</h3>
                </div>
                <div class="table-wrapper">
                    <table>
                        <thead>
                            <tr>
                                <th>Module</th>
                                <th>Usage Count</th>
                                <th>Usage Distribution</th>
                            </tr>
                        </thead>
                        <tbody>
                            {self._dependencies_rows}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>'''
    
    def _get_javascript(self) -> str:
        """Get the JavaScript section for charts and animations."""
        return f'''
    <script>
        {self._plot_generator.get_chart_javascript()}
        
        // Add loading states and animations
        document.addEventListener('DOMContentLoaded', function() {{
            const elements = document.querySelectorAll('.fade-in');
            elements.forEach((el, index) => {{
                setTimeout(() => {{
                    el.style.opacity = '1';
                    el.style.transform = 'translateY(0)';
                }}, index * 100);
            }});
        }});
    </script>'''


def generate_direct_html(metrics: 'ProjectMetrics') -> str:
    """Generate HTML directly without using format strings to avoid issues"""
    generator = HTMLReportGenerator()
    return generator.create(metrics)