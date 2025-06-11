import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Tuple, Dict, Any

from codelyzer.config import ProjectMetrics, ComplexityLevel

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
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8 opacity-0 transition-opacity duration-500" id="charts-grid">
            <div class="bg-white dark:bg-gray-800 rounded-lg shadow-md p-4 hover:shadow-lg transition-shadow">
                <h3 class="text-lg font-semibold text-gray-800 dark:text-gray-200 mb-3 flex items-center">
                    <i class="fas fa-globe text-blue-500 mr-2" aria-hidden="true"></i> Language Distribution
                </h3>
                <div class="h-64 relative">
                    <div id="languageChart" class="w-full h-full"></div>
                </div>
            </div>
            
            <div class="bg-white dark:bg-gray-800 rounded-lg shadow-md p-4 hover:shadow-lg transition-shadow">
                <h3 class="text-lg font-semibold text-gray-800 dark:text-gray-200 mb-3 flex items-center">
                    <i class="fas fa-layer-group text-green-500 mr-2" aria-hidden="true"></i> Complexity Distribution
                </h3>
                <div class="h-64 relative">
                    <div id="complexityChart" class="w-full h-full"></div>
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
                        color: 'var(--text-primary)'
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
                            color: 'var(--text-secondary)'
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
                                color: 'var(--text-secondary)'
                            }}
                        }},
                        tickangle: -45,
                        tickfont: {{
                            size: 10,
                            color: 'var(--text-secondary)'
                        }},
                        gridcolor: 'rgba(0,0,0,0.1)'
                    }},
                    yaxis: {{
                        title: {{
                            text: 'Number of Files',
                            font: {{
                                size: 12,
                                color: 'var(--text-secondary)'
                            }}
                        }},
                        tickfont: {{
                            size: 10,
                            color: 'var(--text-secondary)'
                        }},
                        gridcolor: 'rgba(0,0,0,0.1)'
                    }},
                    paper_bgcolor: 'transparent',
                    plot_bgcolor: 'transparent'
                }}, 
                {{responsive: true, displayModeBar: false}}
            );
        }}
        
        // Show charts with fade-in effect
        setTimeout(() => {{
            const chartsGrid = document.getElementById('charts-grid');
            if (chartsGrid) {{
                chartsGrid.classList.remove('opacity-0');
                chartsGrid.classList.add('opacity-100');
            }}
        }}, 300);'''


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
            return "bg-gradient-to-r from-red-100 to-red-200 text-red-800 border border-red-300"
        elif complexity_score > 200:
            return "bg-gradient-to-r from-yellow-100 to-yellow-200 text-yellow-800 border border-yellow-300"
        return "bg-gradient-to-r from-green-100 to-green-200 text-green-800 border border-green-300"
    
    def _get_issues_display(self, issues_count: int) -> str:
        """Get the HTML display for issues count.
        
        Args:
            issues_count: Number of issues found
            
        Returns:
            HTML string for displaying issue count
        """
        if issues_count == 0:
            return '<span class="inline-flex items-center gap-1 px-3 py-1 rounded-lg text-xs font-medium uppercase tracking-wide bg-gradient-to-r from-green-100 to-green-200 text-green-800 border border-green-300 hover:scale-105 transition-transform"><i class="fas fa-check" aria-hidden="true"></i> Clean</span>'
        elif issues_count < 3:
            return f'<span class="inline-flex items-center gap-1 px-3 py-1 rounded-lg text-xs font-medium uppercase tracking-wide bg-gradient-to-r from-yellow-100 to-yellow-200 text-yellow-800 border border-yellow-300 hover:scale-105 transition-transform"><i class="fas fa-exclamation-triangle" aria-hidden="true"></i> {issues_count} Issues</span>'
        return f'<span class="inline-flex items-center gap-1 px-3 py-1 rounded-lg text-xs font-medium uppercase tracking-wide bg-gradient-to-r from-red-100 to-red-200 text-red-800 border border-red-300 hover:scale-105 transition-transform"><i class="fas fa-times-circle" aria-hidden="true"></i> {issues_count} Issues</span>'
    
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
        <tr class="hover:bg-gray-50 hover:scale-[1.005] transition-all duration-200">
            <td class="px-6 py-4 border-b border-gray-200">
                <code class="flex items-center gap-2 bg-gray-50 px-2 py-1 rounded border border-gray-200 text-sm">
                    <i class="fas fa-cube" aria-hidden="true"></i>
                    {module}
                </code>
            </td>
            <td class="px-6 py-4 border-b border-gray-200"><span class="font-semibold text-gray-900 tabular-nums">{count:,}</span></td>
            <td class="px-6 py-4 border-b border-gray-200">
                <div class="flex items-center gap-3">
                    <div class="w-full h-2.5 bg-gray-200 rounded-full shadow-inner overflow-hidden">
                        <div class="h-full bg-gradient-to-r from-green-500 via-yellow-500 to-red-500 rounded-full transition-all duration-700 ease-out relative" style="width: {usage_percent}%">
                            <div class="absolute inset-0 bg-gradient-to-r from-transparent via-white/30 to-transparent animate-pulse"></div>
                        </div>
                    </div>
                    <span class="text-xs text-gray-600 font-medium min-w-[40px] tabular-nums">{usage_percent:.0f}%</span>
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
    <script src="https://cdn.tailwindcss.com"></script>
    <script>
        tailwind.config = {{
            theme: {{
                extend: {{
                    fontFamily: {{
                        'inter': ['Inter', 'system-ui', 'sans-serif'],
                    }},
                    animation: {{
                        'float': 'float 6s ease-in-out infinite',
                        'shimmer': 'shimmer 2s infinite',
                        'fade-in': 'fadeIn 0.8s cubic-bezier(0.4, 0, 0.2, 1)',
                    }},
                    keyframes: {{
                        float: {{
                            '0%, 100%': {{ transform: 'translateY(0px) rotate(0deg)' }},
                            '50%': {{ transform: 'translateY(-20px) rotate(2deg)' }},
                        }},
                        shimmer: {{
                            '0%': {{ transform: 'translateX(-100%)' }},
                            '100%': {{ transform: 'translateX(200%)' }},
                        }},
                        fadeIn: {{
                            'from': {{ opacity: '0', transform: 'translateY(30px) scale(0.95)' }},
                            'to': {{ opacity: '1', transform: 'translateY(0) scale(1)' }},
                        }},
                    }},
                }}
            }}
        }}
    </script>
    <style>
        .chart-wrapper {{
            height: 400px;
        }}
        @media (max-width: 768px) {{
            .chart-wrapper {{
                height: 300px;
            }}
        }}
        @media (max-width: 480px) {{
            .chart-wrapper {{
                height: 250px;
            }}
        }}
        .progress-shimmer::after {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: linear-gradient(45deg, transparent 40%, rgba(255,255,255,0.3) 50%, transparent 60%);
            animation: shimmer 2s infinite;
        }}
        /* Accessibility and print styles */
        @media (prefers-reduced-motion: reduce) {{
            *, *::before, *::after {{
                animation-duration: 0.01ms !important;
                animation-iteration-count: 1 !important;
                transition-duration: 0.01ms !important;
            }}
        }}
        @media print {{
            body {{
                background: white !important;
                font-size: 12px;
            }}
        }}
    </style>
</head>
<body class="font-inter bg-gradient-to-br from-gray-50 via-white to-gray-50 text-gray-800 text-sm min-h-screen">
    <div class="max-w-7xl mx-auto p-6">
        {self._get_header_html()}
        {self._get_metrics_grid_html(metrics)}
        {self._plot_generator.get_charts_grid_html()}
        {self._get_tables_grid_html()}
        {self._get_footer_html()}
    </div>
    {self._get_javascript()}
</body>
</html>'''
    
    def _get_header_html(self) -> str:
        """Get the header HTML section.
        
        Returns:
            HTML string for the header
        """
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
                <p class="text-lg opacity-90 font-light">Generated on {self._timestamp}</p>
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
    
    def _get_tables_grid_html(self) -> str:
        """Get the tables grid HTML section.
        
        Returns:
            HTML string for the tables grid
        """
        return f'''
        <div class="space-y-8 fade-in">
            <div class="bg-white rounded-2xl shadow-md border border-gray-200 overflow-hidden transition-all duration-300 hover:shadow-lg">
                <div class="bg-gradient-to-r from-gray-50 to-gray-100 px-8 py-6 border-b border-gray-200">
                    <h3 class="text-xl font-semibold text-gray-900 flex items-center gap-3">
                        <i class="fas fa-fire" aria-hidden="true"></i> 
                        Most Complex Files
                    </h3>
                </div>
                <div class="overflow-x-auto">
                    <table class="w-full border-collapse" role="table">
                        <thead>
                            <tr role="row" class="bg-gray-50">
                                <th scope="col" class="px-6 py-4 text-left font-semibold text-gray-700 text-sm uppercase tracking-wide sticky top-0 z-10 bg-gray-50">File</th>
                                <th scope="col" class="px-6 py-4 text-left font-semibold text-gray-700 text-sm uppercase tracking-wide sticky top-0 z-10 bg-gray-50">Lines</th>
                                <th scope="col" class="px-6 py-4 text-left font-semibold text-gray-700 text-sm uppercase tracking-wide sticky top-0 z-10 bg-gray-50">Complexity</th>
                                <th scope="col" class="px-6 py-4 text-left font-semibold text-gray-700 text-sm uppercase tracking-wide sticky top-0 z-10 bg-gray-50">Issues</th>
                            </tr>
                        </thead>
                        <tbody>
                            {self._complex_files_rows}
                        </tbody>
                    </table>
                </div>
            </div>
            
            <div class="bg-white rounded-2xl shadow-md border border-gray-200 overflow-hidden transition-all duration-300 hover:shadow-lg">
                <div class="bg-gradient-to-r from-gray-50 to-gray-100 px-8 py-6 border-b border-gray-200">
                    <h3 class="text-xl font-semibold text-gray-900 flex items-center gap-3">
                        <i class="fas fa-box" aria-hidden="true"></i> 
                        Top Dependencies
                    </h3>
                </div>
                <div class="overflow-x-auto">
                    <table class="w-full border-collapse" role="table">
                        <thead>
                            <tr role="row" class="bg-gray-50">
                                <th scope="col" class="px-6 py-4 text-left font-semibold text-gray-700 text-sm uppercase tracking-wide sticky top-0 z-10 bg-gray-50">Module</th>
                                <th scope="col" class="px-6 py-4 text-left font-semibold text-gray-700 text-sm uppercase tracking-wide sticky top-0 z-10 bg-gray-50">Usage Count</th>
                                <th scope="col" class="px-6 py-4 text-left font-semibold text-gray-700 text-sm uppercase tracking-wide sticky top-0 z-10 bg-gray-50">Usage Distribution</th>
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
        <div class="text-center py-8 text-gray-500 text-sm border-t border-gray-200 mt-10 bg-gradient-to-r from-gray-50 to-transparent rounded-xl fade-in">
            <p class="mb-2">Report generated by Codebase Analysis Tool</p>
            <p class="flex items-center justify-center gap-2">
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