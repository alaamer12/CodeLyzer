"""
CodeLyzer - A comprehensive code analysis tool
"""

# Version
__version__ = "0.1.0"

try:
    from codelyzer.ast_analyzers import initialize_analyzers
    # Initialize tree-sitter parsers if available
    initialize_analyzers()
except ImportError:
    print("Warning: tree-sitter not available. Run: python -m codelyzer.setup_tree_sitter")
except Exception as e:
    print(f"Warning: Failed to initialize analyzers - {str(e)}")
