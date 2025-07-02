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
        print("Usage: python3 chaos.py example.com")
        sys.exit(1)
    
    domain = sys.argv[1]

    #os.environ["PDCP_API_KEY"] = "" # TODO: remove this after testing       

    if not check_chaos_installed():
        print("[!] Error: chaos is not installed or not in PATH")
        print("Please install chaos first: https://chaos.projectdiscovery.io/chaos/get-started/")
        sys.exit(1)
    
    activate_venv()
    
    print(f"[*] Starting chaos domain scan for: {domain}")
    exit_code = run_chaos_scan_and_save(domain)
    
    if exit_code == 0:
        print("[+] Scan completed successfully")
    else:
        print("[!] Scan completed with errors or warnings")
    
    sys.exit(exit_code)

def check_chaos_installed():
    """Return True if chaos is installed and available in PATH."""
    try:
        result = subprocess.run(
            ["/go/bin/chaos", "-version"],
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

def run_chaos_scan_and_save(domain):
    """Run chaos scan and save results to a timestamped file."""
    try:
        scan_output = run_chaos_scan(domain)
        if scan_output is None:
            print("[!] chaos scan failed or returned no output")
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

def run_chaos_scan(domain):
    """Run chaos scan on the given domain and return its output as a string, or None on error."""
    command = [
        "/go/bin/chaos",
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
            print("[!] Warning: chaos process was killed by SIGKILL (likely due to memory/resource limits)")
            if result.stdout.strip():
                return result.stdout
            return None
        if result.returncode != 0:
            print(f"[!] chaos exited with code {result.returncode}")
            if result.stderr:
                print("chaos error output:")
                print(result.stderr)
            return result.stdout if result.stdout.strip() else None
        return result.stdout
    except subprocess.TimeoutExpired:
        print("[!] chaos scan timed out")
        return None
    except FileNotFoundError:
        print("[!] Error: chaos command not found. Please ensure chaos is installed and in PATH")
        return None
    except Exception as e:
        print(f"[!] Unexpected error running chaos: {e}")
        return None

if __name__ == "__main__":
    main() 