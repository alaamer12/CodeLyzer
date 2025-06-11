# Contributing to CodeLyzer

First off, thank you for considering contributing to CodeLyzer! It's people like you that make this tool better for everyone. This document provides guidelines and instructions for contributing to this project.

## Table of Contents
- [Code of Conduct](#code-of-conduct)
- [Development Environment Setup](#development-environment-setup)
- [Branching Strategy](#branching-strategy)
- [Commit Conventions](#commit-conventions)
- [Code Style Guidelines](#code-style-guidelines)
- [Testing Requirements](#testing-requirements)
- [Pull Request Process](#pull-request-process)
- [Documentation](#documentation)

## Code of Conduct

This project follows the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code. Please report unacceptable behavior to the project maintainers.

## Development Environment Setup

### Prerequisites
- Python 3.9 or higher
- Poetry (for dependency management)

### Setting Up the Development Environment

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/codelyzer.git
   cd codelyzer
   ```

2. Set up a virtual environment with Poetry:
   ```bash
   poetry install
   ```

3. Activate the virtual environment:
   ```bash
   poetry shell
   ```

4. Install pre-commit hooks:
   ```bash
   pre-commit install
   ```

### Running Tests

Run all tests with pytest:
```bash
pytest
```

For tests with coverage:
```bash
pytest --cov=codelyzer
```

## Branching Strategy

We follow a simplified GitFlow branching strategy:

- `main`: The production branch, containing stable releases
- `develop`: The development branch, where feature branches are merged
- `feature/*`: Feature branches for new features or improvements
- `bugfix/*`: Branches for bug fixes
- `release/*`: Temporary branches for preparing releases
- `hotfix/*`: Urgent fixes to production code

### Creating a New Branch

Always create your branch from `develop` (unless it's a hotfix):

```bash
git checkout develop
git pull
git checkout -b feature/your-feature-name
```

## Commit Conventions

We use semantic commits to make the commit history more readable and to automate versioning.

### Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- `feat`: A new feature
- `fix`: A bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, missing semicolons, etc.)
- `refactor`: Code refactoring (no functional changes)
- `test`: Adding or modifying tests
- `chore`: Changes to the build process, tools, etc.
- `perf`: Performance improvements

### Scope

The scope should be the name of the module or component affected by the change.

### Examples

```
feat(analyzer): add support for JavaScript ES2020
fix(metrics): correct calculation of cyclomatic complexity
docs(README): update installation instructions
refactor(core): improve modular architecture
```

## Code Style Guidelines

We follow strict Python style conventions to maintain code quality and consistency.

### General Principles

- Follow PEP 8 and modern PEP practices (e.g., PEP 484, 561, 585, 604)
- Use Python 3 features
- All functions must be fully typed (parameters and return type)
- Use 4 spaces for indentation
- Keep functions under 20 lines if possible
- Refactor functions exceeding 40 lines into a dedicated class

### Imports

- Group imports into three categories:
  1. Standard libraries
  2. Third-party libraries
  3. Local imports
- Use absolute imports

```python
# Standard libraries
import os
import typing
from pathlib import Path

# Third-party libraries
import click
from rich.console import Console

# Local imports
from codelyzer.config import DEFAULT_EXCLUDED_DIRS
from codelyzer.utils import FunctionWithTimeout
```

### Docstrings

- Use Google-style docstrings for public functions:
  ```python
  def process_file(file_path: str, options: dict) -> FileMetrics:
      """Process a file and generate metrics.
      
      Args:
          file_path: Path to the file to analyze
          options: Analysis options dictionary
          
      Returns:
          FileMetrics object containing analysis results
          
      Raises:
          FileNotFoundError: If the file doesn't exist
      """
  ```

- Use inline PEP-style for small functions (<10 lines):
  ```python
  def get_line_count(text: str) -> int:
      """Return the number of lines in the text."""
      return text.count('\n') + 1
  ```

## Testing Requirements

All code should be well-tested. We aim for a minimum of 80% code coverage.

### Test Requirements

- Write tests for all public functions, classes, and API endpoints
- Use fixtures and factory methods to reduce boilerplate
- Name test files with `test_` prefix
- Organize tests to mirror the structure of the main code

### Types of Tests

- **Unit tests**: For testing individual functions or classes
- **Integration tests**: For testing interactions between components
- **Functional tests**: For testing complete features

## Pull Request Process

1. Ensure all tests pass and linting issues are resolved
2. Update documentation to reflect any changes
3. Add your changes to the CHANGELOG.md file
4. Submit a pull request to the `develop` branch
5. The PR will be reviewed by maintainers
6. Address any feedback from code review
7. Once approved, the PR will be merged by a maintainer

### PR Template

When creating a PR, please use the following template:

```
## Description
[Provide a brief description of the changes]

## Type of change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Refactoring
- [ ] Other (please describe)

## How Has This Been Tested?
[Describe the tests you ran]

## Checklist
- [ ] My code follows the style guidelines
- [ ] I have performed a self-review
- [ ] I have added tests that prove my fix/feature works
- [ ] I have updated the documentation
```

## Documentation

Documentation is a crucial part of this project:

- Update the README.md with any relevant changes
- Add docstrings to all public functions, classes, and methods
- Include code examples where appropriate
- Keep the CHANGELOG.md up-to-date

Thank you for contributing to CodeLyzer! 