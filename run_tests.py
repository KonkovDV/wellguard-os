import subprocess, sys
sys.exit(subprocess.call([sys.executable, "-m", "pytest", "-q"]))
