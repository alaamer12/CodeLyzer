from collections import Counter
from pathlib import Path
from typing import List
import typer
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich import box

from core import AdvancedCodeAnalyzer, create_summary_panel, create_language_distribution_table, create_complexity_table, create_hotspots_table, create_dependencies_table, generate_html_report, export_json_report
from config import LANGUAGE_CONFIGS, console

app = typer.Typer(
    name="codelyzer",
    help="🔍 Advanced Codebase Analyzer - Analyze your code repositories with detailed metrics and beautiful reports",
    rich_markup_mode="rich"
)

@app.command()
def analyze(
    path: str = typer.Argument(".", help="🎯 Path to analyze (default: current directory)"),
    exclude: List[str] = typer.Option([], "--exclude", "-e", help="📁 Additional directories to exclude"),
    include_tests: bool = typer.Option(False, "--include-tests", help="🧪 Include test directories"),
    output_format: str = typer.Option("terminal", "--format", "-f", help="📄 Output format: terminal, html, json, all"),
    output_dir: str = typer.Option("reports", "--output", "-o", help="📂 Output directory for reports"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="🔍 Verbose output"),
):
    """
    🚀 Analyze your codebase with advanced metrics and beautiful reports
    """
    
    # Validate path
    project_path = Path(path).resolve()
    if not project_path.exists() or not project_path.is_dir():
        console.print(f"[red]❌ Path '{path}' is not a valid directory[/red]")
        raise typer.Exit(1)
    
    # Setup
    console.print(Panel.fit(
        f"🔍 [bold blue]Advanced Codebase Analysis[/bold blue]\n"
        f"📁 Project: [cyan]{project_path.name}[/cyan]\n"
        f"📂 Path: [dim]{project_path}[/dim]",
        border_style="blue"
    ))
    
    if exclude:
        console.print(f"[yellow]📁 Excluding directories:[/yellow] {', '.join(exclude)}")
    
    if include_tests:
        console.print("[yellow]🧪 Including test directories[/yellow]")
    
    # Initialize analyzer
    analyzer = AdvancedCodeAnalyzer(
        exclude_dirs=set(exclude) if exclude else None,
        include_tests=include_tests
    )
    
    # Direct call to analyzer - let it handle its own progress
    metrics = analyzer.analyze_project(str(project_path))
    
    if metrics.total_files == 0:
        console.print("[red]❌ No supported files found in the specified directory[/red]")
        raise typer.Exit(1)
    
    # Display results
    console.print("\n")
    
    # Summary panel
    console.print(create_summary_panel(metrics))
    console.print()
    
    # Create layout for tables
    layout = Layout()
    layout.split_column(
        Layout(name="top"),
        Layout(name="bottom")
    )
    
    layout["top"].split_row(
        Layout(create_language_distribution_table(metrics), name="languages"),
        Layout(create_complexity_table(metrics), name="complexity")
    )
    
    layout["bottom"].split_row(
        Layout(create_hotspots_table(metrics), name="hotspots"),
        Layout(create_dependencies_table(metrics), name="dependencies")
    )
    
    console.print(layout)
    
    # Additional verbose information
    if verbose:
        console.rule("[bold blue]📊 Detailed Analysis")
        
        # File size distribution
        size_table = Table(title="📏 File Size Distribution", box=box.ROUNDED)
        size_table.add_column("Size Range", style="cyan")
        size_table.add_column("Files", justify="right", style="magenta")
        
        size_ranges = [(0, 100), (100, 500), (500, 1000), (1000, 5000), (5000, float('inf'))]
        size_labels = ["< 100 lines", "100-500 lines", "500-1K lines", "1K-5K lines", "> 5K lines"]
        
        for (min_size, max_size), label in zip(size_ranges, size_labels):
            count = sum(1 for f in metrics.file_metrics 
                       if min_size <= f.sloc < max_size)
            size_table.add_row(label, str(count))
        
        console.print(size_table)
        console.print()
        
        # Security issues summary
        if any(f.security_issues for f in metrics.file_metrics):
            security_table = Table(title="🔒 Security Issues", box=box.ROUNDED)
            security_table.add_column("Issue Type", style="red")
            security_table.add_column("Files Affected", justify="right", style="magenta")
            
            security_counts = Counter()
            for file_metrics in metrics.file_metrics:
                for issue in file_metrics.security_issues:
                    security_counts[issue] += 1
            
            for issue, count in security_counts.most_common():
                security_table.add_row(issue.replace('_', ' ').title(), str(count))
            
            console.print(security_table)
            console.print()
    
    # Generate reports
    if output_format in ["html", "all"]:
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        html_file = output_path / f"{project_path.name}_analysis.html"
        generate_html_report(metrics, str(html_file))
        console.print(f"[green]✅ HTML report saved:[/green] [link]{html_file}[/link]")
    
    if output_format in ["json", "all"]:
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        json_file = output_path / f"{project_path.name}_analysis.json"
        export_json_report(metrics, str(json_file))
        console.print(f"[green]✅ JSON report saved:[/green] [link]{json_file}[/link]")
    
    # Final summary
    console.rule("[bold green]🎉 Analysis Complete")
    
    quality_emoji = "🟢" if metrics.code_quality_score >= 80 else "🟡" if metrics.code_quality_score >= 60 else "🔴"
    maintainability_emoji = "🟢" if metrics.maintainability_score >= 80 else "🟡" if metrics.maintainability_score >= 60 else "🔴"
    
    console.print(f"""
[bold]📈 Final Assessment:[/bold]
{quality_emoji} Code Quality: {metrics.code_quality_score:.1f}/100
{maintainability_emoji} Maintainability: {metrics.maintainability_score:.1f}/100
⏱️  Analysis completed in {metrics.analysis_duration:.2f} seconds
🎯 Focus on the {len(metrics.most_complex_files)} most complex files for maximum impact
""")

@app.command()
def compare(
    path1: str = typer.Argument(..., help="🎯 First project path"),
    path2: str = typer.Argument(..., help="🎯 Second project path"),
    exclude: List[str] = typer.Option([], "--exclude", "-e", help="📁 Directories to exclude"),
):
    """
    ⚖️ Compare two codebases side by side
    """
    console.print(Panel.fit(
        "⚖️ [bold blue]Codebase Comparison[/bold blue]",
        border_style="blue"
    ))
    
    # Analyze both projects
    analyzer = AdvancedCodeAnalyzer(exclude_dirs=set(exclude) if exclude else None)
    
    # Avoid nested live displays
    console.print("[bold green]🔄 Analyzing first project...[/bold green]")
    metrics1 = analyzer.analyze_project(path1)
    
    console.print("[bold green]🔄 Analyzing second project...[/bold green]")
    metrics2 = analyzer.analyze_project(path2)
    
    # Create comparison table
    comparison_table = Table(title="📊 Project Comparison", box=box.ROUNDED)
    comparison_table.add_column("Metric", style="cyan", no_wrap=True)
    comparison_table.add_column(f"📁 {Path(path1).name}", justify="right", style="magenta")
    comparison_table.add_column(f"📁 {Path(path2).name}", justify="right", style="green")
    comparison_table.add_column("Difference", justify="right", style="yellow")
    
    metrics_to_compare = [
        ("Files", "total_files"),
        ("Lines of Code", "total_loc"),
        ("Source Lines", "total_sloc"),
        ("Classes", "total_classes"),
        ("Functions", "total_functions"),
        ("Methods", "total_methods"),
        ("Code Quality", "code_quality_score"),
        ("Maintainability", "maintainability_score"),
    ]
    
    for label, attr in metrics_to_compare:
        val1 = getattr(metrics1, attr)
        val2 = getattr(metrics2, attr)
        
        if attr in ["code_quality_score", "maintainability_score"]:
            diff = val2 - val1
            diff_str = f"{diff:+.1f}"
        else:
            diff = val2 - val1
            diff_str = f"{diff:+,}" if diff != 0 else "0"
        
        comparison_table.add_row(
            label,
            f"{val1:,.1f}" if isinstance(val1, float) else f"{val1:,}",
            f"{val2:,.1f}" if isinstance(val2, float) else f"{val2:,}",
            diff_str
        )
    
    console.print(comparison_table)

@app.command()
def languages():
    """
    🌐 Show supported programming languages
    """
    console.print(Panel.fit(
        "🌐 [bold blue]Supported Programming Languages[/bold blue]",
        border_style="blue"
    ))
    
    lang_table = Table(box=box.ROUNDED)
    lang_table.add_column("Language", style="cyan", no_wrap=True)
    lang_table.add_column("Extensions", style="magenta")
    lang_table.add_column("Features", style="green")
    
    for lang, config in LANGUAGE_CONFIGS.items():
        extensions = ", ".join(config['extensions'])
        features = "AST Analysis" if lang == "python" else "Pattern Matching"
        lang_table.add_row(lang.title(), extensions, features)
    
    console.print(lang_table)

if __name__ == "__main__":
    app()