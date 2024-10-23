import subprocess
import sys

def install_requirements():
    """Install required packages."""
    result = subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "-r", "requirements.txt"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode != 0:
        print("Failed to install requirements", file=sys.stderr)
        print(result.stderr.decode(), file=sys.stderr)
        raise Exception("Failed to install requirements")
    
if __name__ == "__main__":
    install_requirements()