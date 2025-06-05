import os
import ast
from collections import defaultdict
from enum import StrEnum
import typer
from typing import List, Optional

app = typer.Typer()

# Define default directories to exclude
DEFAULT_EXCLUDED_DIRS = {'.venv', "venv", "example", "examples", "template", "templates", "benchmark" '__pycache__',
                         '.git', 'node_modules', 'env', 'build', 'dist', 'tests', 'test', 'docs'}
EXCLUDED_FILES = ('__init__.py', '__main__.py')


class ComplexityState(StrEnum):
    LOW = 'low'
    MEDIUM = 'medium'
    HIGH = 'high'


def is_python_file(filename: str) -> bool:
    """
    Check if a file is a Python file and not excluded (__init__.py or __main__.py).
    """
    return (
            filename.endswith('.py') and
            filename not in EXCLUDED_FILES
    )


def count_loc(file_path: str, only_code: bool = True) -> int:
    """
    Count the number of lines of code in a file.

    Args:
        file_path (str): Path to the Python file.
        only_code (bool): If True, exclude blank lines and comment lines.
                          If False, count all lines.

    Returns:
        int: Lines of Code (LOC).
    """
    loc = 0
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            in_multiline_comment = False
            for line in f:
                stripped = line.strip()
                if only_code:
                    # Handle multi-line comments and docstrings
                    if in_multiline_comment:
                        if stripped.endswith("'''") or stripped.endswith('"""'):
                            in_multiline_comment = False
                        continue
                    if stripped.startswith("'''") or stripped.startswith('"""'):
                        if not (stripped.endswith("'''") or stripped.endswith('"""') and len(stripped) > 3):
                            in_multiline_comment = True
                        continue
                    if not stripped or stripped.startswith('#'):
                        continue
                    loc += 1
                else:
                    loc += 1
    except (UnicodeDecodeError, FileNotFoundError) as e:
        typer.echo(f"Error reading file {file_path}: {e}", err=True)
    return loc


def analyze_file(file_path: str, only_code: bool = True) -> Optional[dict]:
    """
    Analyze a single Python file to extract LOC, classes, methods, functions, and imports.

    Args:
        file_path (str): Path to the Python file.
        only_code (bool): If True, count only lines of code. Otherwise, count all lines.

    Returns:
        Optional[dict]: Analysis results or None if there was a syntax error.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            file_content = f.read()
            tree = ast.parse(file_content, filename=file_path)
    except SyntaxError as e:
        typer.echo(f"Syntax error in file {file_path}: {e}", err=True)
        return None
    except Exception as e:
        typer.echo(f"Error processing file {file_path}: {e}", err=True)
        return None

    classes = [node for node in tree.body if isinstance(node, ast.ClassDef)]
    functions = [node for node in tree.body if isinstance(node, ast.FunctionDef)]

    methods_per_class = {}
    for cls in classes:
        methods = [n for n in cls.body if isinstance(n, ast.FunctionDef)]
        methods_per_class[cls.name] = len(methods)

    functions_count = len(functions)

    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name.split('.')[0])  # Get the top-level module
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.add(node.module.split('.')[0])  # Get the top-level module

    return {
        'file_path': file_path,
        'loc': count_loc(file_path, only_code=only_code),
        'classes': len(classes),
        'methods_per_class': methods_per_class,
        'functions': functions_count,
        'imports': list(imports)
    }


def analyze_repository(repo_path: str, excluded_dirs: Optional[set] = None, include_tests: bool = False) -> dict:
    """
    Traverse the repository and analyze each Python file, excluding specified directories.

    Args:
        repo_path (str): Path to the repository.
        excluded_dirs (Optional[set]): Additional directories to exclude.
        include_tests (bool): If True, include test directories in the analysis.

    Returns:
        dict: Aggregated analysis report.
    """
    if excluded_dirs is None:
        excluded_dirs = set()
    else:
        excluded_dirs = set(excluded_dirs)

    # Combine default excluded directories with any additional ones
    combined_excluded_dirs = DEFAULT_EXCLUDED_DIRS.copy()
    if not include_tests:
        combined_excluded_dirs.update({'tests', 'test'})

    report = {
        'modules': [],
        'used_modules': set(),
        'total_loc': 0,
        'modules_count': 0,
        'total_classes': 0,
        'total_methods': 0,
        'total_functions': 0,
        'total_lines': 0  # If needed in future
    }

    for root, dirs, files in os.walk(repo_path):
        # Modify dirs in-place to exclude certain directories
        dirs[:] = [d for d in dirs if d not in combined_excluded_dirs]

        for file in files:
            if is_python_file(file):
                file_path = os.path.join(root, file)
                analysis = analyze_file(file_path, only_code=True)
                if analysis:
                    report['modules'].append(analysis)
                    report['modules_count'] += 1
                    report['total_loc'] += analysis['loc']
                    report['total_classes'] += analysis['classes']
                    report['total_functions'] += analysis['functions']
                    report['total_methods'] += sum(analysis['methods_per_class'].values())
                    report['used_modules'].update(analysis['imports'])

    # Calculate complexity score
    # You can adjust the weights as needed
    score = (
            report['total_loc'] +
            (report['total_classes'] * 1.5) +
            (report['total_methods'] * 1.15) +
            (report['total_functions'] * 1.2) +
            (len(report['used_modules']) * 1.05)
    )
    report['score'] = score
    report['complexity'] = ComplexityState.HIGH if score > 2000 \
        else ComplexityState.MEDIUM \
        if score > 1200 \
        else ComplexityState.LOW

    report['used_modules'] = sorted(list(report['used_modules']))
    return report


def generate_html_report(report: dict, output_file: str = "report.html"):
    """
    Generate a beautifully formatted HTML report.

    Args:
        report (dict): Analysis report.
        output_file (str): Path to the output HTML file.
    """
    html_content = f"""
    <html>
    <head>
        <title>Repository Complexity Report</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            h1, h2, h3 {{ color: #333; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
            tr:nth-child(even) {{ background-color: #f9f9f9; }}
            tr:hover {{ background-color: #f1f1f1; }}
            .complexity-low {{ color: green; }}
            .complexity-medium {{ color: orange; }}
            .complexity-high {{ color: red; }}
        </style>
    </head>
    <body>
        <h1>Repository Complexity Report</h1>
        <h2>Overview</h2>
        <p><strong>Total Modules Analyzed:</strong> {report['modules_count']}</p>
        <p><strong>Total Lines of Code (LOC):</strong> {report['total_loc']}</p>
        <p><strong>Total Classes:</strong> {report['total_classes']}</p>
        <p><strong>Total Methods:</strong> {report['total_methods']}</p>
        <p><strong>Total Functions:</strong> {report['total_functions']}</p>
        <p><strong>Used Modules:</strong> {', '.join(report['used_modules'])}</p>

        <h2>Modules Details</h2>
        <table>
            <tr>
                <th>File Path</th>
                <th>LOC</th>
                <th>Classes</th>
                <th>Methods Per Class</th>
                <th>Functions</th>
                <th>Imports</th>
            </tr>
    """

    for module in report['modules']:
        methods_per_class = "<br>".join(
            [f"Class '{cls}': {methods} method(s)" for cls, methods in module['methods_per_class'].items()])
        imports = ", ".join(module['imports']) if module['imports'] else "None"

        html_content += f"""
            <tr>
                <td>{module['file_path']}</td>
                <td>{module['loc']}</td>
                <td>{module['classes']}</td>
                <td>{methods_per_class}</td>
                <td>{module['functions']}</td>
                <td>{imports}</td>
            </tr>
        """

    html_content += f"""
        </table>
        <h2>Complexity</h2>
        <p><strong>Overall Complexity Score:</strong> {report['score']:.2f}</p>
        <p><strong>Overall Complexity State:</strong> <span class="complexity-{report['complexity']}">{report['complexity'].capitalize()}</span></p>
    </body>
    </html>
    """

    # Write the HTML content to the specified file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)

    typer.echo(f"HTML report generated: {output_file}")


def generate_report(report: dict):
    """
    Generate and print the complexity report.

    Args:
        report (dict): Analysis report.
    """
    typer.echo("\n===== Repository Complexity Report =====\n")
    typer.echo(f"Total Modules Analyzed: {report['modules_count']}")
    typer.echo(f"Total Lines of Code (LOC): {report['total_loc']}")
    typer.echo(f"Total Classes: {report['total_classes']}")
    typer.echo(f"Total Methods: {report['total_methods']}")
    typer.echo(f"Total Functions: {report['total_functions']}")
    typer.echo(f"Used Modules: {', '.join(report['used_modules'])}\n")

    typer.echo("---- Modules Details ----")
    for module in report['modules']:
        typer.echo(f"\nFile: {module['file_path']}")
        typer.echo(f"  LOC: {module['loc']}")
        typer.echo(f"  Classes: {module['classes']}")
        for cls, methods in module['methods_per_class'].items():
            typer.echo(f"    Class '{cls}': {methods} method(s)")
        typer.echo(f"  Functions: {module['functions']}")
        typer.echo(f"  Imports: {', '.join(module['imports']) if module['imports'] else 'None'}")

    typer.echo("\n----------------------------------------")
    typer.echo(f"Overall Complexity Score: {report['score']:.2f}")
    typer.echo(f"Overall Complexity State: {report['complexity']}")
    typer.echo("========================================\n")


@app.command()
def main(
        path: str = typer.Argument(
            ".",
            help="Path to the repository to analyze (default: current directory)."
        ),
        exclude: List[str] = typer.Option(
            [],
            "--exclude",
            "-e",
            help="Additional directories to exclude (space-separated). Example: --exclude dir1 dir2"
        ),
        include_tests: bool = typer.Option(
            False,
            "--include-tests",
            help="Include test directories (tests, test) in the analysis."
        ),
        html: bool = typer.Option(
            False,
            "--html",
            "-h",
            help="Generate HTML report."
        )

):
    """
    Assess the complexity of a Python repository.
    """
    repo_path = os.path.abspath(path)
    repo_name = os.path.basename(repo_path)
    if not os.path.isdir(repo_path):
        typer.echo(f"The path '{repo_path}' is not a valid directory.", err=True)
        raise typer.Exit(code=1)

    if exclude:
        typer.echo(f"Additional Excluding directories: {', '.join(exclude)}")

    if include_tests:
        typer.echo("Including test directories in the analysis.")

    typer.echo(f"Analyzing repository at: {repo_path}")
    report = analyze_repository(repo_path, excluded_dirs=set(exclude), include_tests=include_tests)

    if html:
        typer.echo("Generating HTML report...")
        os.makedirs("reports", exist_ok=True)
        html_repo_name = f"reports/{repo_name}.html"
        generate_html_report(report, output_file=html_repo_name)
    else:
        generate_report(report)


if __name__ == "__main__":
    app()
