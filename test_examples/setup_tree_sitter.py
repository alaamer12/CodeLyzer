"""
Setup script for tree-sitter language parsers
This script installs tree-sitter and ensures that the required language parsers are built
"""
import os
import sys
import subprocess
import shutil
from pathlib import Path
from rich.console import Console

console = Console()

# Define paths
ROOT_DIR = Path(__file__).parent.parent.absolute()
BUILD_DIR = ROOT_DIR / "build"
LIBS_DIR = ROOT_DIR / "libs"

# Required languages
LANGUAGES = {
    "python": "https://github.com/tree-sitter/tree-sitter-python",
    "javascript": "https://github.com/tree-sitter/tree-sitter-javascript"
}


def check_pip():
    """Check if pip is installed"""
    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "--version"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return True
    except subprocess.CalledProcessError:
        return False


def install_tree_sitter():
    """Install the tree-sitter Python package"""
    console.print("[bold blue]Installing tree-sitter...[/bold blue]")
    
    # Check if pip is available
    if not check_pip():
        console.print("[bold red]Error: pip is not available. Please install pip first.[/bold red]")
        return False
    
    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "tree-sitter"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        console.print("[green]Successfully installed tree-sitter[/green]")
        return True
    except subprocess.CalledProcessError:
        console.print("[bold red]Error installing tree-sitter. Please install it manually:[/bold red]")
        console.print("pip install tree-sitter")
        return False


def check_tree_sitter():
    """Check if tree-sitter is installed"""
    try:
        import tree_sitter
        return True
    except ImportError:
        return False


def check_git():
    """Check if git is installed"""
    try:
        subprocess.check_call(
            ["git", "--version"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def clone_language_repos():
    """Clone language repositories"""
    console.print("[bold blue]Cloning language repositories...[/bold blue]")
    
    # Check if git is available
    if not check_git():
        console.print("[bold red]Error: git is not available. Please install git first.[/bold red]")
        return False
    
    # Create libs directory if it doesn't exist
    if not LIBS_DIR.exists():
        LIBS_DIR.mkdir(parents=True)
    
    # Clone each language repo
    for lang, repo in LANGUAGES.items():
        lang_dir = LIBS_DIR / f"tree-sitter-{lang}"
        
        # Skip if already cloned
        if lang_dir.exists():
            console.print(f"[yellow]Repository for {lang} already exists, skipping...[/yellow]")
            continue
        
        try:
            console.print(f"Cloning {lang} repository...")
            subprocess.check_call(
                ["git", "clone", repo, str(lang_dir)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            console.print(f"[green]Successfully cloned {lang} repository[/green]")
        except subprocess.CalledProcessError:
            console.print(f"[bold red]Error cloning {lang} repository[/bold red]")
            return False
    
    return True


def build_language_parsers():
    """Build language parsers using tree-sitter"""
    console.print("[bold blue]Building language parsers...[/bold blue]")
    
    try:
        import tree_sitter
        from tree_sitter import Language
    except ImportError:
        console.print("[bold red]Error: tree-sitter is not installed.[/bold red]")
        return False
    
    # Create build directory if it doesn't exist
    if not BUILD_DIR.exists():
        BUILD_DIR.mkdir(parents=True)
    
    # Mapped language grammar file paths
    parser_paths = {}
    for lang in LANGUAGES.keys():
        lang_dir = LIBS_DIR / f"tree-sitter-{lang}"
        parser_paths[lang] = str(lang_dir / "src")

    # Use existing .so files if available
    py_so = BUILD_DIR / "py-lang.so"
    js_so = BUILD_DIR / "js-lang.so"
    
    if py_so.exists() and js_so.exists():
        console.print("[yellow]Language parser libraries already exist. Using existing files.[/yellow]")
        return True
    
    # Build parsers
    try:
        Language.build_library(
            # Output path
            str(BUILD_DIR / "py-lang.so"),
            # Include path for a specific language
            [parser_paths["python"]]
        )
        
        Language.build_library(
            # Output path
            str(BUILD_DIR / "js-lang.so"),
            # Include path for a specific language
            [parser_paths["javascript"]]
        )
        
        console.print("[green]Successfully built language parsers[/green]")
        return True
    except Exception as e:
        console.print(f"[bold red]Error building language parsers: {str(e)}[/bold red]")
        return False


def main():
    """Main entry point"""
    console.print("[bold]Setting up tree-sitter for CodeLyzer[/bold]")
    
    # Check/install tree-sitter
    if not check_tree_sitter():
        if not install_tree_sitter():
            return False
    
    # Clone language repos if needed
    if not clone_language_repos():
        return False
    
    # Build language parsers
    if not build_language_parsers():
        return False
    
    console.print("\n[bold green]Setup complete! The tree-sitter parsers are ready to use.[/bold green]")
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 