import platform
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Dict, List

# Language configurations
LANGUAGE_CONFIGS = {
    'python': {
        'extensions': ['.py'],
        'comment_patterns': [r'#.*$', r'"""[\s\S]*?"""', r"'''[\s\S]*?'''"],
        'exclude_files': ['__init__.py', '__main__.py'],
        'keywords': ['def', 'class', 'import', 'from', 'if', 'for', 'while', 'try', 'except'],
        'complexity_weights': {'loc': 1.0, 'classes': 2.0, 'functions': 1.5, 'methods': 1.2}
    },
    'javascript': {
        'extensions': ['.js', '.jsx', '.ts', '.tsx'],
        'comment_patterns': [r'//.*$', r'/\*[\s\S]*?\*/'],
        'exclude_files': [],
        'keywords': ['function', 'class', 'const', 'let', 'var', 'if', 'for', 'while', 'try', 'catch'],
        'complexity_weights': {'loc': 1.0, 'classes': 2.0, 'functions': 1.5, 'methods': 1.2}
    },
    'java': {
        'extensions': ['.java'],
        'comment_patterns': [r'//.*$', r'/\*[\s\S]*?\*/'],
        'exclude_files': [],
        'keywords': ['class', 'interface', 'public', 'private', 'protected', 'static', 'final'],
        'complexity_weights': {'loc': 1.0, 'classes': 2.5, 'functions': 1.8, 'methods': 1.5}
    },
    'cpp': {
        'extensions': ['.cpp', '.cc', '.cxx', '.c', '.h', '.hpp'],
        'comment_patterns': [r'//.*$', r'/\*[\s\S]*?\*/'],
        'exclude_files': [],
        'keywords': ['class', 'struct', 'namespace', 'public', 'private', 'protected', 'virtual'],
        'complexity_weights': {'loc': 1.2, 'classes': 2.5, 'functions': 1.8, 'methods': 1.5}
    },
    'go': {
        'extensions': ['.go'],
        'comment_patterns': [r'//.*$', r'/\*[\s\S]*?\*/'],
        'exclude_files': [],
        'keywords': ['func', 'type', 'struct', 'interface', 'package', 'import'],
        'complexity_weights': {'loc': 1.0, 'classes': 2.0, 'functions': 1.5, 'methods': 1.2}
    },
    'rust': {
        'extensions': ['.rs'],
        'comment_patterns': [r'//.*$', r'/\*[\s\S]*?\*/'],
        'exclude_files': [],
        'keywords': ['fn', 'struct', 'enum', 'impl', 'trait', 'mod', 'use'],
        'complexity_weights': {'loc': 1.1, 'classes': 2.2, 'functions': 1.6, 'methods': 1.3}
    }
}

# Default directories to exclude
DEFAULT_EXCLUDED_DIRS = {
    '.venv', 'venv', 'env', '__pycache__', '.git', 'node_modules',
    'build', 'dist', '.next', '.nuxt', 'target', 'bin', 'obj',
    'example', 'examples', 'template', 'templates', 'benchmark',
    'coverage', '.coverage', '.pytest_cache', '.mypy_cache',
    'vendor', 'third_party', 'external', 'deps'
}

DEFAULT_EXCLUDED_FILES = {
    '.DS_Store', 'Thumbs.db', '*.pyc', '*.pyo', '*.pyd',
    '*.so', '*.dll', '*.dylib', '*.o', '*.obj', '*.exe',
    'package-lock.json', 'yarn.lock', 'Cargo.lock'
}


class ComplexityLevel(StrEnum):
    TRIVIAL = 'trivial'
    LOW = 'low'
    MODERATE = 'moderate'
    HIGH = 'high'
    VERY_HIGH = 'very_high'
    EXTREME = 'extreme'


class SecurityLevel(StrEnum):
    SECURE = 'secure'
    LOW_RISK = 'low_risk'
    MEDIUM_RISK = 'medium_risk'
    HIGH_RISK = 'high_risk'
    CRITICAL = 'critical'


@dataclass
class FileMetrics:
    """Metrics for a single file"""
    file_path: str
    language: str
    loc: int = 0
    sloc: int = 0  # Source lines of code (excluding comments/blanks)
    comments: int = 0
    blanks: int = 0
    classes: int = 0
    functions: int = 0
    methods: int = 0
    imports: List[str] = field(default_factory=list)
    methods_per_class: Dict[str, int] = field(default_factory=dict)
    complexity_score: float = 0.0
    cyclomatic_complexity: int = 0
    maintainability_index: float = 0.0
    technical_debt_ratio: float = 0.0
    duplicated_lines: int = 0
    security_issues: List[str] = field(default_factory=list)
    code_smells: List[str] = field(default_factory=list)
    file_size: int = 0
    last_modified: float = 0.0


@dataclass
class ProjectMetrics:
    """Aggregated project metrics"""
    total_files: int = 0
    total_loc: int = 0
    total_sloc: int = 0
    total_comments: int = 0
    total_blanks: int = 0
    total_classes: int = 0
    total_functions: int = 0
    total_methods: int = 0
    languages: Dict[str, int] = field(default_factory=dict)
    file_metrics: List[FileMetrics] = field(default_factory=list)
    complexity_distribution: Dict[ComplexityLevel, int] = field(default_factory=dict)
    most_complex_files: List[FileMetrics] = field(default_factory=list)
    largest_files: List[FileMetrics] = field(default_factory=list)
    hotspots: List[FileMetrics] = field(default_factory=list)
    dependencies: Dict[str, int] = field(default_factory=dict)
    duplicate_blocks: List[Dict] = field(default_factory=list)
    security_summary: Dict[SecurityLevel, int] = field(default_factory=dict)
    code_quality_score: float = 0.0
    maintainability_score: float = 0.0
    analysis_duration: float = 0.0
    project_size: int = 0
    git_stats: Dict = field(default_factory=dict)


# Constants for file processing
FILE_SIZE_LIMIT = 10 * 1024 * 1024  # 10MB
TIMEOUT_SECONDS = 5  # seconds
MAX_REPO_SIZE = 1 * 1024 * 1024 * 1024  # 1GB
IS_WINDOWS = platform.system() == 'Windows'
