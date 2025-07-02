#!/usr/bin/env python3

import sys
import os
import subprocess
from pathlib import Path
from datetime import datetime

def main():
    """Entry point: Validate input, check dependencies, run scan, and handle results."""
    if len(sys.argv) < 2:
        print("[!] Error: Please provide a domain to scan")
        print("Usage: python3 subfinder.py example.com")
        
        sys.exit(1)
    
    domain = sys.argv[1]

    #os.environ["PDCP_API_KEY"] = "" # TODO: remove this after testing       

    if not check_subfinder_installed():
        print("[!] Error: subfinder is not installed or not in PATH")
        print("Please install subfinder first: https://subfinder.projectdiscovery.io/subfinder/get-started/")
        sys.exit(1)
    
    activate_venv()
    
    print(f"[*] Starting subfinder domain scan for: {domain}")
    exit_code = run_subfinder_scan_and_save(domain)
    
    if exit_code == 0:
        print("[+] Scan completed successfully")
    else:
        print("[!] Scan completed with errors or warnings")
    
    sys.exit(exit_code)

def check_subfinder_installed():
    """Return True if subfinder is installed and available in PATH."""
    try:
        result = subprocess.run(
            ["/go/bin/subfinder", "-version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=5
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False

def activate_venv():
    """Detect and note if a virtual environment exists."""
    venv_path = Path("venv")
    if venv_path.exists() and venv_path.is_dir():
        print("[*] Virtual environment found")
        venv_python = venv_path / "bin" / "python3"
        if venv_python.exists():
            print("[*] Using virtual environment Python")
        else:
            print("[*] Virtual environment found but Python not detected")

def run_subfinder_scan_and_save(domain):
    """Run subfinder scan and save results to a timestamped file."""
    try:
        scan_output = run_subfinder_scan(domain)
        if scan_output is None:
            print("[!] subfinder scan failed or returned no output")
            return 1
        
        output_dir = "outputs"
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")[:-3]
        filename = f"{timestamp}-scan.txt"
        filepath = os.path.join(output_dir, filename)

        with open(filepath, "w") as f:
            f.write(scan_output)
        print(f"[*] Scan results saved as {filepath}")
        return 0

    except Exception as e:
        print(f"[!] Error running scan: {e}", file=sys.stderr)
        return 1

def run_subfinder_scan(domain):
    """Run subfinder scan on the given domain and return its output as a string, or None on error."""
    command = [
        "/go/bin/subfinder",
        "-d", domain,
        "-silent"
    ]
    print(f"[*] Executing: {' '.join(command)}")
    try:
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=300,
            check=False
        )
        if result.returncode == -9:
            print("[!] Warning: subfinder process was killed by SIGKILL (likely due to memory/resource limits)")
            if result.stdout.strip():
                return result.stdout
            return None
        if result.returncode != 0:
            print(f"[!] subfinder exited with code {result.returncode}")
            if result.stderr:
                print("subfinder error output:")
                print(result.stderr)
            return result.stdout if result.stdout.strip() else None
        return result.stdout
    except subprocess.TimeoutExpired:
        print("[!] subfinder scan timed out")
        return None
    except FileNotFoundError:
        print("[!] Error: subfinder command not found. Please ensure subfinder is installed and in PATH")
        return None
    except Exception as e:
        print(f"[!] Unexpected error running subfinder: {e}")
        return None

if __name__ == "__main__":
    main() 