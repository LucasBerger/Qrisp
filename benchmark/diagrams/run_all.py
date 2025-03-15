#!/usr/bin/env python3
"""
Main script to run all the visualization steps in sequence.
"""

import os
import time
import subprocess
import sys

def run_script(script_name, description):
    """Run a Python script and print its output."""
    print(f"\n{'=' * 80}")
    print(f"Running {script_name}: {description}")
    print(f"{'=' * 80}\n")
    
    start_time = time.time()
    
    try:
        result = subprocess.run([sys.executable, script_name], 
                               stdout=subprocess.PIPE, 
                               stderr=subprocess.PIPE,
                               text=True,
                               check=True)
        
        print(result.stdout)
        
        if result.stderr:
            print("Errors/Warnings:")
            print(result.stderr)
        
        elapsed_time = time.time() - start_time
        print(f"\nCompleted in {elapsed_time:.2f} seconds.")
        return True
    
    except subprocess.CalledProcessError as e:
        print(f"Error running {script_name}:")
        print(e.stdout)
        print(e.stderr)
        elapsed_time = time.time() - start_time
        print(f"\nFailed after {elapsed_time:.2f} seconds.")
        return False

def main():
    """Run all visualization scripts in sequence."""
    print("\nQrisp ZX-Calculus Compiler Benchmark Visualization")
    print("=" * 80)
    
    # Create output directories
    os.makedirs("output", exist_ok=True)
    os.makedirs("paper_output", exist_ok=True)
    
    # Step 1: Fix JSON files
    if not run_script("fix_json_files.py", "Fix potential issues with JSON files"):
        print("Failed to fix JSON files. Exiting.")
        return
    
    # Step 2: Generate comprehensive diagrams
    if not run_script("generate_diagrams.py", "Generate comprehensive diagrams"):
        print("Failed to generate comprehensive diagrams. Continuing anyway...")
    
    # Step 3: Generate publication-quality diagrams
    if not run_script("paper_diagrams.py", "Generate publication-quality diagrams"):
        print("Failed to generate publication-quality diagrams. Continuing anyway...")
    
    print("\nAll visualization steps completed!")
    print("\nOutput files:")
    print("  - General diagrams: ./output/")
    print("  - Publication diagrams: ./paper_output/")

if __name__ == "__main__":
    main() 