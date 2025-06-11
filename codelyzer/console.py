"""
Console and display utilities for CodeLyzer.
Centralizes all console output, logging, progress bars, and rich display components.
"""
from ast import Dict
from pathlib import Path
from typing import Any, List

from rich import box
from rich.console import Console
from rich.layout import Layout
from rich.markdown import Markdown
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn, TimeRemainingColumn
from rich.table import Table
from rich.box import Box

from codelyzer.metrics import ProjectMetrics, ComplexityLevel

# Main console instance used throughout the application
console = Console()


def create_summary_panel(metrics: ProjectMetrics) -> Panel:
    """Create a summary panel with project metrics."""
    summary_text = f"""
📊 **Project Overview**
• Files analyzed: {metrics.total_files:,}
• Lines of code: {metrics.total_loc:,}
• Source lines: {metrics.total_sloc:,}
• Comments: {metrics.total_comments:,}
• Blank lines: {metrics.total_blanks:,}

🏗️ **Code Structure**
• Classes: {metrics.total_classes:,}
• Functions: {metrics.total_functions:,}
• Methods: {metrics.total_methods:,}

📈 **Quality Metrics**
• Code quality: {metrics.code_quality_score:.1f}/100
• Maintainability: {metrics.maintainability_score:.1f}/100
• Analysis time: {metrics.analysis_duration:.2f}s
"""

    return Panel(
        Markdown(summary_text),
        title="📋 Analysis Summary",
        border_style="blue",
        padding=(1, 2),
        title_align="center",
        highlight=True
    )


def create_language_distribution_table(metrics: ProjectMetrics) -> Table:
    """Create a table showing language distribution."""
    table = Table(
        title="🌐 Language Distribution",
        box=box.ROUNDED,
        title_style="bold blue",
        border_style="cyan",
        highlight=True
    )
    table.add_column("Language", style="cyan", no_wrap=True)
    table.add_column("Files", justify="right", style="magenta")
    table.add_column("Percentage", justify="right", style="green")

    total_files = sum(metrics.languages.values())
    for language, count in sorted(metrics.languages.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / total_files) * 100 if total_files > 0 else 0
        table.add_row(
            language.title(),
            str(count),
            f"{percentage:.1f}%"
        )

    return table


def create_complexity_table(metrics: ProjectMetrics) -> Table:
    """Create a table showing code complexity distribution."""
    table = Table(
        title="⚡ Complexity Distribution",
        box=box.ROUNDED,
        title_style="bold blue",
        border_style="cyan",
        highlight=True
    )
    table.add_column("Complexity Level", style="cyan")
    table.add_column("Files", justify="right", style="magenta")
    table.add_column("Percentage", justify="right", style="green")

    total_files = sum(metrics.complexity_distribution.values())

    for level in ComplexityLevel:
        # noinspection PyTypeChecker
        count = metrics.complexity_distribution.get(level, 0)
        percentage = (count / total_files) * 100 if total_files > 0 else 0

        # Color coding
        if level in [ComplexityLevel.TRIVIAL, ComplexityLevel.LOW]:
            style = "green"
        elif level == ComplexityLevel.MODERATE:
            style = "yellow"
        else:
            style = "red"

        table.add_row(
            level.replace('_', ' ').title(),
            f"[{style}]{count}[/{style}]",
            f"[{style}]{percentage:.1f}%[/{style}]"
        )

    return table

def create_table(title: str, box: Box, title_style: str, border_style: str, highlight: bool) -> Table:
    """Create a table with the given parameters."""
    return Table(
        title=title,
        box=box,
        title_style=title_style,
        border_style=border_style,
        highlight=highlight
    )

def create_table_columns(table: Table, columns: Dict[str, Dict[str, Any]]) -> Table:
    """Update a table with the given columns."""
    for column_name, column_config in columns.items():
        table.add_column(column_name, **column_config)
    return table

def create_hotspots_table(metrics: ProjectMetrics) -> Table:
    """Create a table showing code hotspots (most complex files)."""
    table = create_table(
        title="🔥 Code Hotspots (Most Complex Files)",
        box=box.ROUNDED,
        title_style="bold blue",
        border_style="cyan",
        highlight=True
    )
    columns = {
        "file": {"style": "cyan", "max_width": 50},
        "lines": {"justify": "right", "style": "magenta"},
        "complexity": {"justify": "right", "style": "red"},
        "issues": {"justify": "right", "style": "yellow"}
    }
    create_table_columns(table, columns)

    # Create a mapping of file paths to file metrics for quick lookup
    file_metrics_map = {fm.file_path: fm for fm in metrics.file_metrics}
    
    # Loop through the most complex file paths and find their corresponding FileMetrics objects
    for file_path in metrics.most_complex_files[:10]:
        # Get the FileMetrics object for this file path
        file_metrics = file_metrics_map.get(file_path)
        
        if file_metrics:
            # Handle paths on different drives by using Path
            try:
                # Try relative path first
                relative_path = str(Path(file_metrics.file_path).relative_to(Path.cwd()))
            except ValueError:
                # If on a different drive, just use the basename or full path
                path_obj = Path(file_metrics.file_path)
                # Use parent directory + filename for better context
                if path_obj.parent.name:
                    relative_path = str(Path(path_obj.parent.name) / path_obj.name)
                else:
                    relative_path = path_obj.name

            issues = len(file_metrics.security_issues) + len(file_metrics.code_smells_list)

            # Color code based on issue count
            issue_style = "green" if issues == 0 else "yellow" if issues < 3 else "red"

            table.add_row(
                relative_path,
                str(file_metrics.sloc),
                f"{file_metrics.complexity_score:.0f}",
                f"[{issue_style}]{issues if issues > 0 else '✅'}[/{issue_style}]"
            )

    return table


def create_dependencies_table(metrics: ProjectMetrics) -> Table:
    """Create a table showing top dependencies."""
    table = Table(
        title="📦 Top Dependencies",
        box=box.ROUNDED,
        title_style="bold blue",
        border_style="cyan",
        highlight=True
    )
    table.add_column("Module", style="cyan")
    table.add_column("Usage Count", justify="right", style="magenta")

    # Get top 15 dependencies
    top_deps = sorted(metrics.structure.dependencies.items(), key=lambda x: x[1], reverse=True)[:15]

    for module, count in top_deps:
        table.add_row(module, str(count))

    return table


def create_analysis_progress_bar() -> Progress:
    """Create a standardized progress bar for analysis operations."""
    return Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]Processing...", justify="right"),
        BarColumn(bar_width=40),
        "[progress.percentage]{task.percentage:>3.1f}%",
        "•",
        TextColumn("[cyan]{task.completed}/{task.total}[/cyan]", justify="right"),
        "•",
        TimeElapsedColumn(),
        "•",
        TimeRemainingColumn(),
        console=console
    )


def create_and_display_layout(metrics: ProjectMetrics) -> None:
    """Create and display the layout with all metric tables."""
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


def display_initial_info(project_path: Path, exclude: List[str], include_tests: bool) -> None:
    """Display initial information about the analysis."""
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


def display_final_summary(metrics: ProjectMetrics) -> None:
    """Display the final analysis summary."""
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


def display_verbose_info(metrics: ProjectMetrics) -> None:
    """Display additional verbose information."""
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

    display_security_issues(metrics)


def display_security_issues(metrics: ProjectMetrics) -> None:
    """Display security issues if any exist."""
    from collections import Counter

    if any(f.security_issues for f in metrics.file_metrics):
        security_table = Table(title="🔒 Security Issues", box=box.ROUNDED)
        security_table.add_column("Issue Type", style="red")
        security_table.add_column("Files Affected", justify="right", style="magenta")

        security_counts = Counter()
        for file_metrics in metrics.file_metrics:
            for issue in file_metrics.security_issues:
                issue_type = issue.get('type', 'unknown')
                security_counts[issue_type] += 1

        for issue_type, count in security_counts.most_common():
            security_table.add_row(issue_type.replace('_', ' ').title(), str(count))

        console.print(security_table)
        console.print()
