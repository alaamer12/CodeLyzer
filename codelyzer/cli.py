import logging
from pathlib import Path
from typing import List

import typer
from rich import box
from rich.panel import Panel
from rich.table import Table

from codelyzer._html import generate_direct_html
from codelyzer.config import LANGUAGE_CONFIGS
from codelyzer.console import (
    console, create_summary_panel, display_initial_info, display_final_summary,
    display_verbose_info, create_and_display_layout, logger, debug, debug_log,
    set_log_level
)
from codelyzer.core import AdvancedCodeAnalyzer, ReportExport

app = typer.Typer(
    name="codelyzer",
    help="🔍 Advanced Codebase Analyzer - Analyze your code repositories with detailed metrics and beautiful reports",
    rich_markup_mode="rich"
)


@debug
def validate_project_path(path: str) -> Path:
    """Validate the provided path and return a Path object."""
    project_path = Path(path).resolve()
    if not project_path.exists() or not project_path.is_dir():
        logger.error(f"Invalid directory path: {path}")
        console.print(f"[red]❌ Path '{path}' is not a valid directory[/red]")
        raise typer.Exit(1)
    return project_path


def generate_reports(metrics, output_format: str, output_dir: str, project_path: Path, no_about: bool = False) -> None:
    """Generate reports based on the specified format."""
    logger.info(f"Generating reports in format: {output_format}")
    debug_log(f"Output directory: {output_dir}")
    
    if output_format in ["html", "all"]:
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)

        html_file = output_path / f"{project_path.name}_analysis.html"
        logger.info(f"Generating HTML report: {html_file}")

        # Generate HTML content using our direct method and pass the output directory
        html_content = generate_direct_html(metrics, str(output_path), no_about=no_about)

        # Write to file
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)

        console.print(f"[green]✅ HTML report saved:[/green] [link]file://{html_file.resolve()}[/link]")

    if output_format in ["json", "all"]:
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)

        json_file = output_path / f"{project_path.name}_analysis.json"
        logger.info(f"Generating JSON report: {json_file}")
        ReportExport(metrics, str(json_file)).to_json()
        logger.info(f"JSON report saved to {json_file}")
        console.print(f"[green]✅ JSON report saved:[/green] [link]{json_file}[/link]")


@app.command()
def analyze(
        path: str = typer.Argument(".", help="🎯 Path to analyze (default: current directory)"),
        exclude: List[str] = typer.Option([], "--exclude", "-e", help="📁 Additional directories to exclude"),
        include_tests: bool = typer.Option(False, "--include-tests", help="🧪 Include test directories"),
        output_format: str = typer.Option("terminal", "--format", "-f",
                                          help="📄 Output format: terminal, html, json, all"),
        output_dir: str = typer.Option("reports", "--output", "-o", help="📂 Output directory for reports"),
        verbose: bool = typer.Option(False, "--verbose", "-v", help="�� Verbose output"),
        no_about: bool = typer.Option(False, "--no-about", help="📄 Do not include about page in HTML report"),
        debug_mode: bool = typer.Option(False, "--debug", "-d", help="🐛 Enable debug logging"),
):
    """
    🚀 Analyze your codebase with advanced metrics and beautiful reports
    """
    # Set log level based on verbose/debug flags
    if debug_mode:
        set_log_level(logging.DEBUG)
        logger.debug("Debug mode enabled")
    elif verbose:
        set_log_level(logging.INFO)
        logger.info("Verbose mode enabled")

    logger.info(f"Starting analysis of {path}")
    logger.info(f"CLI options: exclude={exclude}, include_tests={include_tests}, output_format={output_format}")

    # Validate path
    project_path = validate_project_path(path)

    # Display initial information
    display_initial_info(project_path, exclude, include_tests)

    # Initialize analyzer
    logger.info("Initializing code analyzer")
    analyzer = AdvancedCodeAnalyzer(
        exclude_dirs=set(exclude) if exclude else None,
        include_tests=include_tests
    )

    # Direct call to analyzer - let it handle its own progress
    logger.info(f"Analyzing project: {project_path}")
    metrics = analyzer.analyze_project(str(project_path))

    if metrics.total_files == 0:
        logger.error("No supported files found in the specified directory")
        console.print("[red]❌ No supported files found in the specified directory[/red]")
        raise typer.Exit(1)

    # Display results
    console.print("\n")

    # Summary panel
    logger.info("Displaying summary panel")
    console.print(create_summary_panel(metrics))
    console.print()

    # Create and display layout with tables
    logger.info("Displaying metrics tables")
    create_and_display_layout(metrics)

    # Additional verbose information
    if verbose:
        logger.info("Displaying verbose metrics information")
        display_verbose_info(metrics)

    # Generate reports
    generate_reports(metrics, output_format, output_dir, project_path, no_about=no_about)

    # Final summary
    display_final_summary(metrics)


@app.command()
def compare(
        path1: str = typer.Argument(..., help="🎯 First project path"),
        path2: str = typer.Argument(..., help="🎯 Second project path"),
        exclude: List[str] = typer.Option([], "--exclude", "-e", help="📁 Directories to exclude"),
        debug_mode: bool = typer.Option(False, "--debug", "-d", help="🐛 Enable debug logging"),
):
    """
    ⚖️ Compare two codebases side by side
    """
    # Set log level if debug mode is enabled
    if debug_mode:
        set_log_level(logging.DEBUG)
        logger.debug("Debug mode enabled for comparison")
    
    logger.info(f"Starting comparison between {path1} and {path2}")
    
    console.print(Panel.fit(
        "⚖️ [bold blue]Codebase Comparison[/bold blue]",
        border_style="blue"
    ))

    # Analyze both projects
    logger.info("Initializing code analyzer for comparison")
    analyzer = AdvancedCodeAnalyzer(exclude_dirs=set(exclude) if exclude else None)

    # Avoid nested live displays
    logger.info(f"Analyzing first project: {path1}")
    console.print("[bold green]🔄 Analyzing first project...[/bold green]")
    metrics1 = analyzer.analyze_project(path1)

    logger.info(f"Analyzing second project: {path2}")
    console.print("[bold green]🔄 Analyzing second project...[/bold green]")
    metrics2 = analyzer.analyze_project(path2)

    # Create comparison table
    logger.info("Creating comparison table")
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
        
        logger.debug(f"Comparison - {label}: {val1} vs {val2}, diff: {diff}")

    console.print(comparison_table)
    logger.info("Comparison complete")


@app.command()
def languages():
    """
    🌐 Show supported programming languages
    """
    logger.info("Displaying supported languages information")
    
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
        logger.debug(f"Language support: {lang.title()} - Extensions: {extensions}")

    console.print(lang_table)


def main():
    # Import logging here to avoid circular imports
    import logging
    # Just call app() to fix pyproject.toml script section
    app()


if __name__ == "__main__":
    main()
