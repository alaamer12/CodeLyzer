"""
Test script for tree-sitter initialization.
"""
import os
from tree_sitter import Language, Parser

# Paths to the compiled grammar files
GRAMMAR_PATH = os.path.join(os.path.dirname(__file__), "build")
PY_GRAMMAR_PATH = os.path.join(GRAMMAR_PATH, "py-lang.so")
JS_GRAMMAR_PATH = os.path.join(GRAMMAR_PATH, "js-lang.so")

def test_parser_initialization():
    """Test proper initialization of tree-sitter parsers."""
    try:
        print(f"Python grammar file exists: {os.path.exists(PY_GRAMMAR_PATH)}")
        print(f"JavaScript grammar file exists: {os.path.exists(JS_GRAMMAR_PATH)}")
        
        # Try to initialize the Language objects
        try:
            py_lang = Language(PY_GRAMMAR_PATH)
            print("Successfully initialized Python language")
        except Exception as e:
            print(f"Error initializing Python language: {str(e)}")
        
        try:
            js_lang = Language(JS_GRAMMAR_PATH)
            print("Successfully initialized JavaScript language")
        except Exception as e:
            print(f"Error initializing JavaScript language: {str(e)}")
            
        # If we got this far, try to create a parser
        parser = Parser()
        try:
            parser.language = py_lang
            print("Successfully set parser language to Python")
        except Exception as e:
            print(f"Error setting parser language: {str(e)}")
            
        # Test parsing a simple Python snippet
        try:
            code = bytes("def hello(): print('world')", "utf8")
            tree = parser.parse(code)
            root_node = tree.root_node
            print(f"Parsed Python code. Root node type: {root_node.type}")
        except Exception as e:
            print(f"Error parsing code: {str(e)}")
            
    except Exception as e:
        print(f"Unexpected error: {str(e)}")

if __name__ == "__main__":
    test_parser_initialization() 