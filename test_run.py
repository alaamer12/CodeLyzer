import subprocess
import sys
import os


def run_analysis():
    command = [
        "python", "codelyzer/cli.py", "analyze",
        r"E:\Projects\Languages\Python\WorkingOnIt\CodeLyzer",
        "--format", "html"
    ]

    # Configure environment with UTF-8 encoding
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"

    try:
        # Use shell=True on Windows to ensure proper encoding handling
        use_shell = sys.platform == "win32"

        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",  # Explicitly set UTF-8 encoding
            errors="replace",  # Replace characters that can't be decoded
            env=env,
            shell=use_shell
        )

        # Read output in real-time
        for line in process.stdout:
            print(line, end='', flush=True)  # Add flush to ensure immediate output

        process.wait()

        if process.returncode != 0:
            print(f"\nProcess exited with code {process.returncode}")

    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    run_analysis()
