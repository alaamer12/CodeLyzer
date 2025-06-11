"""
Test script for tree-sitter based code analyzers
"""
import os
import sys
from rich.table import Table
from rich.console import Console

# Add the parent directory to sys.path if needed
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from codelyzer.ast_analyzers import PythonASTAnalyzer, JavaScriptASTAnalyzer, initialize_analyzers
from codelyzer.console import console

def test_python_analyzer(file_path: str = None):
    """Test the Python analyzer on a file"""
    if not file_path:
        # Create a temporary Python file if none is provided
        file_path = "temp_test.py"
        with open(file_path, "w") as f:
            f.write("""
# This is a comment
import os
import sys
from typing import List, Dict, Optional

class TestClass:
    \"\"\"This is a docstring\"\"\"
    
    def __init__(self, value: int = 0):
        self.value = value
    
    def calculate(self, x: int, y: int) -> int:
        \"\"\"Calculate a value based on inputs\"\"\"
        if x > 0:
            return x + y
        elif y > 0:
            return y
        else:
            return self.value

def main(args: List[str]) -> int:
    test = TestClass(10)
    
    result = 0
    for arg in args:
        try:
            value = int(arg)
            if value > 0:
                result += test.calculate(value, 5)
        except ValueError:
            print(f"Invalid argument: {arg}")
    
    return result

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
""")
    
    analyzer = PythonASTAnalyzer()
    metrics = analyzer.analyze_file(file_path)
    
    if file_path == "temp_test.py":
        os.remove(file_path)
    
    return metrics

def test_js_analyzer(file_path: str = None):
    """Test the JavaScript analyzer on a file"""
    if not file_path:
        # Create a temporary JavaScript file if none is provided
        file_path = "temp_test.js"
        with open(file_path, "w") as f:
            f.write("""
// This is a comment
import React from 'react';
import { useState, useEffect } from 'react';

/**
 * This is a JSDoc comment
 */
class TestComponent extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            count: 0
        };
    }
    
    handleClick() {
        this.setState(prevState => ({
            count: prevState.count + 1
        }));
    }
    
    render() {
        return (
            <div>
                <h1>Counter: {this.state.count}</h1>
                <button onClick={() => this.handleClick()}>Increment</button>
            </div>
        );
    }
}

// Function component
function FunctionalCounter() {
    const [count, setCount] = useState(0);
    
    useEffect(() => {
        document.title = `Count: ${count}`;
    }, [count]);
    
    const handleIncrement = () => {
        setCount(prevCount => prevCount + 1);
    };
    
    return (
        <div>
            <h2>Functional Counter: {count}</h2>
            <button onClick={handleIncrement}>Increment</button>
        </div>
    );
}

export { TestComponent, FunctionalCounter };
""")
    
    analyzer = JavaScriptASTAnalyzer()
    metrics = analyzer.analyze_file(file_path)
    
    if file_path == "temp_test.js":
        os.remove(file_path)
    
    return metrics

def display_metrics(metrics, title="File Metrics"):
    """Display metrics in a nice table"""
    table = Table(title=title)
    
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("File", os.path.basename(metrics.base.file_path))
    table.add_row("Language", metrics.base.language)
    table.add_row("Lines of Code", str(metrics.base.loc))
    table.add_row("SLOC", str(metrics.base.sloc))
    table.add_row("Blank Lines", str(metrics.base.blanks))
    table.add_row("Comment Lines", str(metrics.base.comments))
    table.add_row("Classes", str(metrics.base.classes))
    table.add_row("Functions", str(metrics.base.functions))
    table.add_row("Imports", str(metrics.base.imports))
    table.add_row("Complexity Score", str(metrics.base.complexity_score))
    
    console.print(table)


def main():
    """Run tests for both analyzers"""
    # Initialize the tree-sitter parsers
    initialize_analyzers()
    
    console.print("\n[bold blue]Testing Python Analyzer[/bold blue]")
    python_metrics = test_python_analyzer()
    display_metrics(python_metrics, "Python Metrics")
    
    console.print("\n[bold blue]Testing JavaScript Analyzer[/bold blue]")
    js_metrics = test_js_analyzer()
    display_metrics(js_metrics, "JavaScript Metrics")


if __name__ == "__main__":
    main() 