# CodeLyzer

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/downloads/)
[![Code Style: Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/charliermarsh/ruff/main/assets/badge/v2.json)](https://github.com/charliermarsh/ruff)
[![Imports: isort](https://img.shields.io/badge/%20imports-isort-%231674b1?style=flat&labelColor=ef8336)](https://pycqa.github.io/isort/)

A powerful, extensible static code analyzer with multi-language support, beautiful terminal output, and comprehensive metrics.

## Features

- **Multi-Language Support**: Analyze Python, JavaScript, TypeScript, and more (extensible architecture)
- **Comprehensive Metrics**: Code complexity, quality scores, maintainability index, and more
- **Security Analysis**: Detect common security vulnerabilities in your code
- **Code Smell Detection**: Find problematic patterns and anti-patterns
- **Beautiful Reports**: Terminal, HTML, and JSON reporting options
- **Modular Architecture**: Easily extend with new languages and analyzers

## Installation

### Using pip (recommended)

```bash
pip install codelyzer
```

### Using Poetry

```bash
poetry add codelyzer
```

### From Source

```bash
git clone https://github.com/yourusername/codelyzer.git
cd codelyzer
poetry install
```

## Quick Start

Analyze your project with a single command:

```bash
codelyzer analyze /path/to/your/project
```

## Usage

### Basic Usage

```bash
codelyzer analyze [PATH] [OPTIONS]
```

If no path is specified, the current directory is analyzed.

### Options

```
--exclude, -e TEXT       Additional directories to exclude
--include-tests          Include test directories in analysis
--format, -f [terminal|html|json|all]
                         Output format (default: terminal)
--verbose                Show detailed progress and information
--help                   Show this message and exit.
```

### Examples

Analyze current directory and output to terminal:
```bash
codelyzer analyze
```

Analyze specific project with HTML report:
```bash
codelyzer analyze /path/to/project --format html
```

Exclude specific directories:
```bash
codelyzer analyze --exclude vendor --exclude node_modules
```

Include test directories in analysis:
```bash
codelyzer analyze --include-tests
```

## Output Formats

### Terminal Output

The default output provides a detailed terminal report with color-coded sections for:
- Summary statistics
- Language distribution
- Complexity metrics
- Most complex files
- Largest files
- Security issues
- Code smells

### HTML Report

Generate a beautiful HTML report with:
```bash
codelyzer analyze --format html
```

The report will be saved to `codelyzer_report.html` in the current directory.

### JSON Output

Export detailed analysis data in JSON format for further processing:
```bash
codelyzer analyze --format json
```

The JSON data will be saved to `codelyzer_report.json` in the current directory.

## Project Structure

```
codelyzer/
├── ast_analyzers/       # Language-specific AST analyzers
├── cli.py               # Command-line interface
├── config.py            # Configuration and constants
├── console.py           # Console output utilities
├── core.py              # Core analyzer implementation
└── utils.py             # Utility functions
```

## Extending CodeLyzer

CodeLyzer is designed with extensibility in mind. You can create new analyzers for additional languages by:

1. Creating a new class that inherits from `ASTAnalyzer`
2. Implementing the required methods
3. Registering the analyzer with the appropriate file extensions

See the [CONTRIBUTING.md](CONTRIBUTING.md) for more details.

## Contributing

Contributions are welcome! Please check out our [Contributing Guide](CONTRIBUTING.md) for details on:

- Setting up the development environment
- Code style guidelines
- Commit conventions
- Pull request process

## Security

For information about reporting security vulnerabilities, please see our [Security Policy](SECURITY.md).

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [Rich](https://github.com/Textualize/rich) for beautiful terminal output
- [AST](https://docs.python.org/3/library/ast.html) for Python parsing
- [Esprima](https://github.com/Kronuz/esprima-python) for JavaScript parsing