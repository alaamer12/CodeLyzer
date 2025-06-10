import subprocess

def run_analysis():
    command = [
        "python", "cli.py", "analyze", 
        r"E:\Projects\Languages\Websites\Vanila\Done\2048",
        "--format", "html"
    ]
    
    try:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        
        # Read output in real-time
        for line in process.stdout:
            print(line, end='')

        process.wait()

        if process.returncode != 0:
            print(f"\nProcess exited with code {process.returncode}")
    
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    run_analysis()
