from datetime import datetime
import os
from pathlib import Path
import platform

# Language configurations
LANGUAGE_CONFIGS = {
    'python': {
        'extensions': ['.py'],
        'comment_patterns': [r'#.*$', r'"""[\s\S]*?"""', r"'''[\s\S]*?'''"],
        'exclude_files': ['__init__.py', '__main__.py'],
        'keywords': ['def', 'class', 'import', 'from', 'if', 'for', 'while', 'try', 'except', 'with', 'async', 'await',
                     'yield', 'lambda', 'return'],
        'complexity_weights': {'loc': 1.0, 'classes': 2.0, 'functions': 1.5, 'methods': 1.2, 'nested_blocks': 1.3,
                               'exception_handlers': 1.1}
    },
    'javascript': {
        'extensions': ['.js', '.jsx', '.ts', '.tsx'],
        'comment_patterns': [r'//.*$', r'/\*[\s\S]*?\*/'],
        'exclude_files': ['*.min.js', '*.bundle.js'],
        'keywords': ['function', 'class', 'const', 'let', 'var', 'if', 'for', 'while', 'try', 'catch', 'import',
                     'export', 'async', 'await', 'return', 'switch', 'case'],
        'complexity_weights': {'loc': 1.0, 'classes': 2.0, 'functions': 1.5, 'methods': 1.2, 'callbacks': 1.4,
                               'promises': 1.1, 'async_functions': 1.3}
    },
    'java': {
        'extensions': ['.java'],
        'comment_patterns': [r'//.*$', r'/\*[\s\S]*?\*/'],
        'exclude_files': ['package-info.java', 'module-info.java'],
        'keywords': ['class', 'interface', 'enum', 'public', 'private', 'protected', 'static', 'final', 'abstract',
                     'synchronized', 'volatile', 'transient', 'implements', 'extends'],
        'complexity_weights': {'loc': 1.0, 'classes': 2.5, 'functions': 1.8, 'methods': 1.5, 'interfaces': 1.2,
                               'annotations': 0.8, 'generics': 1.3}
    },
    'cpp': {
        'extensions': ['.cpp', '.cc', '.cxx', '.c', '.h', '.hpp', '.hxx', '.hh'],
        'comment_patterns': [r'//.*$', r'/\*[\s\S]*?\*/'],
        'exclude_files': ['*.generated.h', '*.generated.cpp'],
        'keywords': ['class', 'struct', 'namespace', 'public', 'private', 'protected', 'virtual', 'template',
                     'typename', 'const', 'constexpr', 'inline', 'friend', 'operator'],
        'complexity_weights': {'loc': 1.2, 'classes': 2.5, 'functions': 1.8, 'methods': 1.5, 'templates': 2.0,
                               'macros': 1.7, 'pointers': 1.4}
    },
    'go': {
        'extensions': ['.go'],
        'comment_patterns': [r'//.*$', r'/\*[\s\S]*?\*/'],
        'exclude_files': ['*_test.go', '*_mock.go'],
        'keywords': ['func', 'type', 'struct', 'interface', 'package', 'import', 'map', 'chan', 'go', 'defer', 'select',
                     'case', 'fallthrough'],
        'complexity_weights': {'loc': 1.0, 'classes': 2.0, 'functions': 1.5, 'methods': 1.2, 'interfaces': 1.3,
                               'goroutines': 1.4, 'channels': 1.3}
    },
    'rust': {
        'extensions': ['.rs'],
        'comment_patterns': [r'//.*$', r'/\*[\s\S]*?\*/'],
        'exclude_files': ['*_test.rs', '*_mock.rs'],
        'keywords': ['fn', 'struct', 'enum', 'impl', 'trait', 'mod', 'use', 'pub', 'mut', 'async', 'await', 'match',
                     'let', 'const', 'static', 'unsafe'],
        'complexity_weights': {'loc': 1.1, 'classes': 2.2, 'functions': 1.6, 'methods': 1.3, 'traits': 1.5,
                               'generics': 1.4, 'lifetimes': 1.7}
    },
    'csharp': {
        'extensions': ['.cs'],
        'comment_patterns': [r'//.*$', r'/\*[\s\S]*?\*/'],
        'exclude_files': ['*.Designer.cs', '*.generated.cs'],
        'keywords': ['class', 'interface', 'struct', 'enum', 'namespace', 'using', 'public', 'private', 'protected',
                     'internal', 'static', 'readonly', 'const', 'async', 'await'],
        'complexity_weights': {'loc': 1.1, 'classes': 2.3, 'functions': 1.7, 'methods': 1.4, 'properties': 1.0,
                               'events': 1.2, 'delegates': 1.5, 'linq': 1.3}
    },
    'ruby': {
        'extensions': ['.rb', '.rake'],
        'comment_patterns': [r'#.*$', r'=begin[\s\S]*?=end'],
        'exclude_files': ['Gemfile', 'Rakefile'],
        'keywords': ['def', 'class', 'module', 'include', 'extend', 'attr_accessor', 'attr_reader', 'attr_writer',
                     'require', 'require_relative', 'yield', 'lambda'],
        'complexity_weights': {'loc': 0.9, 'classes': 1.8, 'functions': 1.4, 'methods': 1.1, 'blocks': 1.3,
                               'metaprogramming': 2.0, 'symbols': 0.8}
    },
    'php': {
        'extensions': ['.php', '.phtml', '.php5', '.php7'],
        'comment_patterns': [r'//.*$', r'/\*[\s\S]*?\*/', r'#.*$'],
        'exclude_files': [],
        'keywords': ['function', 'class', 'interface', 'trait', 'namespace', 'public', 'private', 'protected', 'static',
                     'abstract', 'final', 'use', 'require', 'include'],
        'complexity_weights': {'loc': 1.0, 'classes': 2.0, 'functions': 1.5, 'methods': 1.2, 'traits': 1.4,
                               'namespaces': 0.9, 'globals': 1.6}
    },
    'swift': {
        'extensions': ['.swift'],
        'comment_patterns': [r'//.*$', r'/\*[\s\S]*?\*/'],
        'exclude_files': [],
        'keywords': ['func', 'class', 'struct', 'enum', 'protocol', 'extension', 'var', 'let', 'guard', 'if', 'else',
                     'switch', 'case', 'import'],
        'complexity_weights': {'loc': 1.0, 'classes': 2.1, 'functions': 1.6, 'methods': 1.3, 'protocols': 1.4,
                               'extensions': 1.2, 'closures': 1.5}
    },
    'kotlin': {
        'extensions': ['.kt', '.kts'],
        'comment_patterns': [r'//.*$', r'/\*[\s\S]*?\*/'],
        'exclude_files': [],
        'keywords': ['fun', 'class', 'interface', 'object', 'val', 'var', 'when', 'companion', 'data', 'sealed', 'open',
                     'override', 'suspend', 'coroutine'],
        'complexity_weights': {'loc': 1.0, 'classes': 2.0, 'functions': 1.5, 'methods': 1.2, 'extensions': 1.1,
                               'coroutines': 1.4, 'lambdas': 1.3}
    }
}

# Default directories to exclude
DEFAULT_EXCLUDED_DIRS = {
    # Virtual environments and package management
    '.venv', 'venv', 'env', 'virtualenv', '__pycache__', '.git', 'node_modules',
    '.npm', '.yarn', 'bower_components', 'jspm_packages', '.pnpm-store',

    # Build artifacts and distribution
    'build', 'dist', '.next', '.nuxt', 'target', 'bin', 'obj', 'out',
    'output', 'artifacts', '.gradle', '.maven', 'cmake-build-*',

    # Documentation and examples
    'example', 'examples', 'template', 'templates', 'sample', 'samples',
    'docs', 'documentation', 'javadoc', 'apidoc', 'man', 'manual',

    # Testing and coverage
    'benchmark', 'benchmarks', 'coverage', '.coverage', '.pytest_cache',
    '.mypy_cache', '.ruff_cache', '.eslintcache', 'jest-cache', '.nyc_output',
    'htmlcov', 'test-results', '.tox', '.hypothesis',

    # Third-party code
    'vendor', 'third_party', 'external', 'deps', 'lib', 'libs',
    'packages', 'ext', 'extern', 'third-party', 'thirdparty',

    # IDE and editor files
    '.idea', '.vscode', '.vs', '.eclipse', '.settings', '.project',
    '.classpath', '.metadata', '.fleet', '.sublime-*',

    # OS-specific
    '.DS_Store', '__MACOSX', 'Thumbs.db', 'desktop.ini',

    # Temporary files
    'tmp', 'temp', 'cache', '.cache', '.tmp'
}

DEFAULT_EXCLUDED_FILES = {
    # OS and editor metadata
    '.DS_Store', 'Thumbs.db', 'desktop.ini', '.directory',

    # Python bytecode and cache
    '*.pyc', '*.pyo', '*.pyd', '.python-version', '.coverage.*',

    # Compiled binaries and libraries
    '*.so', '*.dll', '*.dylib', '*.o', '*.obj', '*.exe', '*.lib',
    '*.a', '*.la', '*.lo', '*.class', '*.jar', '*.war', '*.ear',

    # Package management
    'package-lock.json', 'yarn.lock', 'Cargo.lock', 'Gemfile.lock',
    'poetry.lock', 'composer.lock', 'Pipfile.lock', 'pnpm-lock.yaml',

    # Configuration files
    '.env', '.env.*', '*.config', '*.conf', '*.cfg', '*.ini',

    # Log files
    '*.log', '*.logs', 'npm-debug.log*', 'yarn-debug.log*',
    'yarn-error.log*', 'lerna-debug.log*',

    # Backup and temporary files
    '*~', '*.bak', '*.swp', '*.swo', '*.tmp', '*.temp',
    '*.orig', '*.rej', '*.old', '*.new',

    # Generated files
    '*.min.*', '*.bundle.*', '*.map', '*.generated.*',
    '*.pb.go', '*_pb2.py', '*.g.cs', '*.g.dart',

    # Documentation
    '*.md', '*.rst', '*.txt', 'LICENSE*', 'README*', 'CHANGELOG*',
    'CONTRIBUTING*', 'AUTHORS*', 'NOTICE*', 'PATENTS*',

    # Media and binary files
    '*.jpg', '*.jpeg', '*.png', '*.gif', '*.ico', '*.svg',
    '*.pdf', '*.zip', '*.tar', '*.gz', '*.rar', '*.7z',

    # Database files
    '*.db', '*.sqlite', '*.sqlite3', '*.mdb'
}

# Constants for file processing
FILE_SIZE_LIMIT = 20 * 1024 * 1024  # 20MB
TIMEOUT_SECONDS = 5  # seconds
MAX_REPO_SIZE = 1 * 1024 * 1024 * 1024  # 1GB
IS_WINDOWS = platform.system() == 'Windows'
PARSE_TIMEOUT = 30
GRAMMAR_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "build")

# Logging configuration
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

# Generate log filename based on current date/time
LOG_FILENAME = LOG_DIR / f"codelyzer_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

# Debug flag - can be toggled via environment variable
DEBUG = os.environ.get("CODELYZER_DEBUG", "").lower() in ("true", "1", "yes")