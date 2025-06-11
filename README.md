# 🔍 CodeLyzer - Advanced Codebase Analysis Tool

[![Python Version](https://img.shields.io/badge/python-3.7%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

CodeLyzer is a powerful, feature-rich static code analysis tool designed to help developers understand, maintain, and improve codebases of any size. With support for multiple programming languages and beautiful visualizations, CodeLyzer makes it easy to identify code quality issues, complexity hotspots, and architectural patterns.

## ✨ Features

- **Multi-Language Support**: Analyze Python, JavaScript, Java, C++, Go, Rust, and more
- **Comprehensive Metrics**: Lines of code, complexity, maintainability, and more
- **Code Quality Assessment**: Detect code smells, security vulnerabilities, and anti-patterns
- **Beautiful Visualizations**: Rich terminal output with tables, progress bars, and charts
- **HTML & JSON Reports**: Generate detailed reports for sharing and further analysis
- **Project Comparison**: Compare metrics between different codebases or versions
- **Hotspot Detection**: Identify the most complex and problematic files

## 📋 Requirements

- Python 3.7+
- Dependencies listed in requirements.txt

## 🚀 Installation

1. Clone this repository:

```bash
git clone https://github.com/yourusername/codelyzer.git
cd codelyzer
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

## 📊 Usage

### Basic Analysis

Analyze the current directory:

```bash
python cli.py analyze
```

Analyze a specific directory:

```bash
python cli.py analyze /path/to/project
```

### Excluding Directories

```bash
python cli.py analyze --exclude node_modules --exclude dist
```

### Include Test Directories

By default, test directories are excluded. Include them with:

```bash
python cli.py analyze --include-tests
```

### Output Formats

Generate HTML and JSON reports:

```bash
python cli.py analyze --format all --output ./reports
```

### Comparing Projects

```bash
python cli.py compare /path/to/project1 /path/to/project2
```

### View Supported Languages

```bash
python cli.py languages
```

### Verbose Output

```bash
python cli.py analyze --verbose
```

## 📊 Sample Output

```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃           📋 Analysis Summary                     ┃
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫
┃ 📊 Project Overview                              ┃
┃ • Files analyzed: 42                             ┃
┃ • Lines of code: 5,280                           ┃
┃ • Source lines: 3,847                            ┃
┃                                                  ┃
┃ 🏗️ Code Structure                               ┃
┃ • Classes: 15                                    ┃
┃ • Functions: 87                                  ┃
┃ • Methods: 53                                    ┃
┃                                                  ┃
┃ 📈 Quality Metrics                              ┃
┃ • Code quality: 82.5/100                         ┃
┃ • Maintainability: 76.3/100                      ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
```

## 📁 Project Structure

```
codebase_analyzer/
├── cli.py           # Command-line interface
├── config.py        # Configuration settings
├── core.py          # Core analysis logic
├── requirements.txt # Package dependencies
├── LICENSE          # MIT License
└── README.md        # This documentation
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.