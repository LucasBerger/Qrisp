#!/usr/bin/env python3
"""
Main script to run all the visualization steps in sequence.
"""

import os
import time
import subprocess
import sys

def run_script(script_name, description):
    """Run a Python script and measure execution time."""
    print(f"\n{'='*80}")
    print(f"Running {description}...")
    print(f"{'='*80}")
    
    start_time = time.time()
    
    try:
        subprocess.run([sys.executable, script_name], check=True)
        end_time = time.time()
        print(f"\n{description} completed in {end_time - start_time:.2f} seconds.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\nError running {description}: {e}")
        return False

def main():
    """Run all scripts for benchmark visualization."""
    print("\n" + "="*80)
    print("Qrisp ZX-Calculus Compiler Benchmark Visualization")
    print("="*80 + "\n")
    
    # Run fix_json_files.py
    if not run_script("fix_json_files.py", "JSON file fixing"):
        print("Error fixing JSON files. Exiting.")
        return
    
    # Run generate_diagrams.py
    if not run_script("generate_diagrams.py", "general diagram generation"):
        print("Error generating diagrams. Exiting.")
        return
    
    # Run paper_diagrams.py
    if not run_script("paper_diagrams.py", "paper diagram generation"):
        print("Error generating paper diagrams. Exiting.")
        return
    
    # Run comparison_diagrams.py
    if not run_script("comparison_diagrams.py", "comparison diagram generation"):
        print("Error generating comparison diagrams. Exiting.")
        return
    
    print("\n" + "="*80)
    print("All visualization tasks completed successfully!")
    print("="*80 + "\n")
    
    # Print output directories
    print("Output directories:")
    print("- General diagrams: ./output/")
    print("- Paper diagrams: ./paper_output/")
    print("- Comparison diagrams: ./comparison_output/")

if __name__ == "__main__":
    main() 