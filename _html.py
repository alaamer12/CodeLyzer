import os
import json
from pathlib import Path
from datetime import datetime

from config import ProjectMetrics, ComplexityLevel, console


def generate_html_template():
    """Generate enhanced professional HTML template"""
    return '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Codebase Analysis Report</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/3.9.1/chart.min.js"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        :root {{
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
        }}

        * {{ 
            margin: 0; 
            padding: 0; 
            box-sizing: border-box; 
        }}

        body {{ 
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6; 
            color: var(--gray-800); 
            background: linear-gradient(135deg, var(--gray-50) 0%, #ffffff 100%);
            font-size: 14px;
        }}

        .container {{ 
            max-width: 1400px; 
            margin: 0 auto; 
            padding: 24px;
        }}

        .header {{ 
            background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%);
            color: white; 
            padding: 48px 0; 
            text-align: center; 
            margin-bottom: 32px; 
            border-radius: 16px;
            box-shadow: var(--shadow-xl);
            position: relative;
            overflow: hidden;
        }}

        .header::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><pattern id="grid" width="10" height="10" patternUnits="userSpaceOnUse"><path d="M 10 0 L 0 0 0 10" fill="none" stroke="rgba(255,255,255,0.1)" stroke-width="0.5"/></pattern></defs><rect width="100" height="100" fill="url(%23grid)"/></svg>');
            opacity: 0.3;
        }}

        .header-content {{ 
            position: relative; 
            z-index: 1; 
        }}

        .header h1 {{ 
            font-size: 2.5rem; 
            font-weight: 700; 
            margin-bottom: 12px;
            text-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}

        .header p {{ 
            font-size: 1.1rem; 
            opacity: 0.9; 
            font-weight: 300;
        }}

        .metrics-grid {{ 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); 
            gap: 24px; 
            margin-bottom: 40px; 
        }}

        .metric-card {{ 
            background: white; 
            padding: 28px; 
            border-radius: 12px; 
            box-shadow: var(--shadow-md);
            border: 1px solid var(--gray-200);
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }}

        .metric-card::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: linear-gradient(90deg, var(--primary-color), var(--accent-color));
        }}

        .metric-card:hover {{ 
            transform: translateY(-4px); 
            box-shadow: var(--shadow-lg);
        }}

        .metric-header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 16px;
        }}

        .metric-icon {{
            width: 48px;
            height: 48px;
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 20px;
            color: white;
        }}

        .metric-icon.files {{ background: var(--primary-color); }}
        .metric-icon.code {{ background: var(--success-color); }}
        .metric-icon.classes {{ background: var(--warning-color); }}
        .metric-icon.functions {{ background: var(--danger-color); }}
        .metric-icon.quality {{ background: var(--accent-color); }}
        .metric-icon.maintainability {{ background: #8b5cf6; }}

        .metric-value {{ 
            font-size: 2.5rem; 
            font-weight: 700; 
            color: var(--gray-900);
            line-height: 1;
        }}

        .metric-label {{ 
            color: var(--gray-600); 
            margin-top: 8px; 
            font-weight: 500;
            text-transform: uppercase;
            font-size: 0.75rem;
            letter-spacing: 0.05em;
        }}

        .charts-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 32px;
            margin-bottom: 40px;
        }}

        @media (max-width: 1024px) {{
            .charts-grid {{
                grid-template-columns: 1fr;
            }}
        }}

        .chart-container {{ 
            background: white; 
            padding: 32px; 
            border-radius: 12px; 
            box-shadow: var(--shadow-md);
            border: 1px solid var(--gray-200);
            position: relative;
        }}

        .chart-container h3 {{
            font-size: 1.25rem;
            font-weight: 600;
            margin-bottom: 24px;
            color: var(--gray-900);
            display: flex;
            align-items: center;
            gap: 12px;
        }}

        .chart-wrapper {{
            position: relative;
            height: 300px;
            width: 100%;
        }}

        .tables-grid {{
            display: grid;
            grid-template-columns: 1fr;
            gap: 32px;
        }}

        .table-container {{ 
            background: white; 
            border-radius: 12px; 
            box-shadow: var(--shadow-md);
            border: 1px solid var(--gray-200);
            overflow: hidden;
        }}

        .table-header {{
            background: var(--gray-50);
            padding: 24px 32px;
            border-bottom: 1px solid var(--gray-200);
        }}

        .table-header h3 {{
            font-size: 1.25rem;
            font-weight: 600;
            color: var(--gray-900);
            display: flex;
            align-items: center;
            gap: 12px;
        }}

        .table-wrapper {{
            overflow-x: auto;
        }}

        table {{ 
            width: 100%; 
            border-collapse: collapse; 
        }}

        th, td {{ 
            padding: 16px 24px; 
            text-align: left; 
            border-bottom: 1px solid var(--gray-200);
        }}

        th {{ 
            background-color: var(--gray-50); 
            font-weight: 600;
            color: var(--gray-700);
            font-size: 0.875rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}

        tbody tr {{ 
            transition: background-color 0.2s ease;
        }}

        tbody tr:hover {{ 
            background-color: var(--gray-50);
        }}

        tbody tr:last-child td {{
            border-bottom: none;
        }}

        .complexity-low {{ 
            color: var(--success-color); 
            font-weight: 600;
        }}

        .complexity-medium {{ 
            color: var(--warning-color); 
            font-weight: 600;
        }}

        .complexity-high {{ 
            color: var(--danger-color); 
            font-weight: 600;
        }}

        .progress-bar {{ 
            width: 100%; 
            height: 8px; 
            background-color: var(--gray-200); 
            border-radius: 4px; 
            overflow: hidden;
        }}

        .progress-fill {{ 
            height: 100%; 
            background: linear-gradient(90deg, var(--success-color), var(--warning-color), var(--danger-color)); 
            transition: width 0.3s ease;
            border-radius: 4px;
        }}

        .badge {{
            display: inline-flex;
            align-items: center;
            padding: 4px 12px;
            border-radius: 6px;
            font-size: 0.75rem;
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 0.025em;
        }}

        .badge.success {{
            background-color: #dcfce7;
            color: #166534;
        }}

        .badge.warning {{
            background-color: #fef3c7;
            color: #92400e;
        }}

        .badge.danger {{
            background-color: #fee2e2;
            color: #991b1b;
        }}

        .file-path {{
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
            font-size: 0.8rem;
            color: var(--gray-600);
            max-width: 300px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }}

        .stat-number {{
            font-weight: 600;
            color: var(--gray-900);
        }}

        @media (max-width: 768px) {{
            .container {{
                padding: 16px;
            }}
            
            .metrics-grid {{
                grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
                gap: 16px;
            }}
            
            .metric-card {{
                padding: 20px;
            }}
            
            .metric-value {{
                font-size: 2rem;
            }}
            
            .header h1 {{
                font-size: 2rem;
            }}
            
            th, td {{
                padding: 12px 16px;
            }}
        }}

        .loading {{
            opacity: 0.7;
            pointer-events: none;
        }}

        .fade-in {{
            animation: fadeIn 0.6s ease-in;
        }}

        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(20px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="header-content">
                <h1><i class="fas fa-chart-line"></i> Codebase Analysis Report</h1>
                <p>Generated on {timestamp}</p>
            </div>
        </div>
        
        <div class="metrics-grid fade-in">
            <div class="metric-card">
                <div class="metric-header">
                    <div class="metric-icon files"><i class="fas fa-file-code"></i></div>
                </div>
                <div class="metric-value">{total_files:,}</div>
                <div class="metric-label">Files Analyzed</div>
            </div>
            <div class="metric-card">
                <div class="metric-header">
                    <div class="metric-icon code"><i class="fas fa-code"></i></div>
                </div>
                <div class="metric-value">{total_loc:,}</div>
                <div class="metric-label">Lines of Code</div>
            </div>
            <div class="metric-card">
                <div class="metric-header">
                    <div class="metric-icon classes"><i class="fas fa-cube"></i></div>
                </div>
                <div class="metric-value">{total_classes:,}</div>
                <div class="metric-label">Classes</div>
            </div>
            <div class="metric-card">
                <div class="metric-header">
                    <div class="metric-icon functions"><i class="fas fa-cogs"></i></div>
                </div>
                <div class="metric-value">{total_functions:,}</div>
                <div class="metric-label">Functions</div>
            </div>
            <div class="metric-card">
                <div class="metric-header">
                    <div class="metric-icon quality"><i class="fas fa-star"></i></div>
                </div>
                <div class="metric-value">{code_quality:.1f}%</div>
                <div class="metric-label">Code Quality</div>
            </div>
            <div class="metric-card">
                <div class="metric-header">
                    <div class="metric-icon maintainability"><i class="fas fa-tools"></i></div>
                </div>
                <div class="metric-value">{maintainability:.1f}%</div>
                <div class="metric-label">Maintainability</div>
            </div>
        </div>
        
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
        </div>
        
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
                            {complex_files_rows}
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
                            {dependencies_rows}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        // Enhanced chart configurations with proper sizing
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
                labels: {language_labels},
                datasets: [{{
                    data: {language_data},
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
                labels: {complexity_labels},
                datasets: [{{
                    label: 'Number of Files',
                    data: {complexity_data},
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
        }});

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
    </script>
</body>
</html>
'''
    


def generate_html_report(metrics: ProjectMetrics, output_path: str):
    """Generate comprehensive HTML report with enhanced styling"""
    html_template = generate_html_template()
    
    # Enhanced complex files rows with better styling
    complex_files_rows = ""
    for file_metrics in metrics.most_complex_files[:15]:
        # Handle paths on different drives by using Path
        try:
            relative_path = os.path.relpath(file_metrics.file_path)
        except ValueError:
            path_obj = Path(file_metrics.file_path)
            if path_obj.parent.name:
                relative_path = str(Path(path_obj.parent.name) / path_obj.name)
            else:
                relative_path = path_obj.name
                
        issues = len(file_metrics.security_issues) + len(file_metrics.code_smells)
        
        # Enhanced complexity classification
        if file_metrics.complexity_score > 500:
            complexity_class = "complexity-high"
            complexity_badge = "danger"
        elif file_metrics.complexity_score > 200:
            complexity_class = "complexity-medium" 
            complexity_badge = "warning"
        else:
            complexity_class = "complexity-low"
            complexity_badge = "success"
        
        # Issues badge
        if issues == 0:
            issues_display = '<span class="badge success">✓ Clean</span>'
        elif issues < 3:
            issues_display = f'<span class="badge warning">{issues} Issues</span>'
        else:
            issues_display = f'<span class="badge danger">{issues} Issues</span>'
        
        complex_files_rows += f'''
        <tr>
            <td><div class="file-path" title="{relative_path}">{relative_path}</div></td>
            <td><span class="stat-number">{file_metrics.sloc:,}</span></td>
            <td><span class="badge {complexity_badge}">{file_metrics.complexity_score:.0f}</span></td>
            <td>{issues_display}</td>
        </tr>'''
    
    # Enhanced dependencies rows with better progress visualization
    dependencies_rows = ""
    top_deps = sorted(metrics.dependencies.items(), key=lambda x: x[1], reverse=True)[:15]
    max_usage = max([count for _, count in top_deps]) if top_deps else 1
    
    for module, count in top_deps:
        usage_percent = (count / max_usage) * 100
        dependencies_rows += f'''
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
    
    # Chart data preparation
    language_labels = list(metrics.languages.keys())
    language_data = list(metrics.languages.values())
    
    complexity_labels = [level.replace('_', ' ').title() for level in ComplexityLevel]
    complexity_data = [metrics.complexity_distribution.get(level, 0) for level in ComplexityLevel]
    
    # Fill template with error handling
    try:
        html_content = html_template.format(
            timestamp=datetime.now().strftime("%B %d, %Y at %H:%M:%S"),
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
    except KeyError as e:
        console.print(f"[red]Error in HTML template formatting: {str(e)}[/red]")
        # Fallback to minimal report
        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Codebase Analysis Report</title>
            <style>
                body {{ 
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    max-width: 800px;
                    margin: 0 auto;
                    padding: 40px 20px;
                    background: #f8fafc;
                }}
                .card {{ 
                    background: white;
                    padding: 32px;
                    border-radius: 12px;
                    box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);
                    margin-bottom: 24px;
                }}
                h1 {{ color: #1e293b; margin-bottom: 8px; }}
                .metric {{ display: flex; justify-content: space-between; margin: 12px 0; }}
                .metric-label {{ color: #64748b; }}
                .metric-value {{ font-weight: 600; color: #0f172a; }}
            </style>
        </head>
        <body>
            <div class="card">
                <h1>🔍 Codebase Analysis Summary</h1>
                <p style="color: #64748b; margin-bottom: 24px;">Generated on {datetime.now().strftime("%B %d, %Y at %H:%M:%S")}</p>
                
                <div class="metric">
                    <span class="metric-label">Files analyzed:</span>
                    <span class="metric-value">{metrics.total_files:,}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Lines of code:</span>
                    <span class="metric-value">{metrics.total_loc:,}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Classes:</span>
                    <span class="metric-value">{metrics.total_classes:,}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Functions:</span>
                    <span class="metric-value">{metrics.total_functions:,}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Code quality:</span>
                    <span class="metric-value">{metrics.code_quality_score:.1f}%</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Maintainability:</span>
                    <span class="metric-value">{metrics.maintainability_score:.1f}%</span>
                </div>
                
                <p style="color: #64748b; font-size: 14px; margin-top: 24px;">
                    <em>Note: Enhanced report generation encountered an error. This is a simplified version.</em>
                </p>
            </div>
        </body>
        </html>
        """
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
