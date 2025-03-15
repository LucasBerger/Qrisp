# Qrisp ZX-Calculus Compiler Benchmark Visualization

This directory contains scripts to visualize and analyze the results of benchmarking the ZX-calculus enhanced compiler in Qrisp against the standard Qrisp compiler and no-compiler approaches.

## Overview

The benchmark data consists of 270+ JSON files in the `../../results_01/` directory, each representing a different quantum circuit. The circuits are categorized into:

- SAT problems (files starting with "SAT_")
- TSP problems solved using Grover's algorithm (files starting with "TSP_")
- TSP problems transformed into QUBO and solved using QAOA (files starting with "QUBO_")
- GHZ circuits (files starting with "GHZ-")
- Standard benchmark circuits (remaining files)

The metrics analyzed include:
- T-count/T-depth reduction
- CNOT-count reduction
- CNOT-depth reduction
- Optimization time
- Circuit size (number of qubits)

## Scripts

### 1. `fix_json_files.py`

This script fixes potential issues with the JSON files to ensure they can be properly loaded.

```bash
python fix_json_files.py
```

### 2. `load_data.py`

This script provides functions to load and process the benchmark data from the JSON files.

```python
from load_data import load_benchmark_data

# Load all benchmark data
df = load_benchmark_data()

# Get statistics by category
from load_data import get_category_statistics
category_stats = get_category_statistics(df)

# Get statistics by circuit size
from load_data import get_size_binned_statistics
size_stats = get_size_binned_statistics(df)
```

### 3. `generate_diagrams.py`

This script generates a comprehensive set of diagrams for analyzing the benchmark results.

```bash
python generate_diagrams.py
```

The generated diagrams include:
- Improvement by circuit category
- Improvement by circuit size
- Optimization time vs. improvement
- Circuit size vs. improvement
- Comparative boxplots
- Top circuits for each metric
- Correlation heatmap

### 4. `paper_diagrams.py`

This script generates publication-quality diagrams specifically designed for academic papers.

```bash
python paper_diagrams.py
```

The generated diagrams include:
- T-depth reduction by category (with error bars)
- CNOT metrics comparison
- Optimization time vs. circuit size
- T-depth reduction distribution
- Improvement radar chart
- Case studies for SAT and TSP problems

### 5. `run_all.py`

This script runs all the visualization steps in sequence.

```bash
python run_all.py
```

## Requirements

- Python 3.6+
- pandas
- numpy
- matplotlib
- seaborn

## Installation

```bash
pip install pandas numpy matplotlib seaborn
```

## Usage

1. First, fix any potential issues with the JSON files:
   ```bash
   python fix_json_files.py
   ```

2. Generate comprehensive diagrams:
   ```bash
   python generate_diagrams.py
   ```

3. Generate publication-quality diagrams for your paper:
   ```bash
   python paper_diagrams.py
   ```

4. Or run all steps at once:
   ```bash
   python run_all.py
   ```

## Output

- General diagrams are saved in the `output/` directory
- Publication-quality diagrams are saved in the `paper_output/` directory
- Both PNG and PDF formats are provided for each diagram

## Example Diagram Descriptions

1. **T-Depth Reduction by Circuit Category**: Compares the T-depth reduction achieved by the standard Qrisp compiler and the ZX-enhanced compiler across different circuit categories.

2. **CNOT Metrics Comparison**: Scatter plot showing the relationship between CNOT-depth reduction and CNOT-count reduction, with points colored by circuit size.

3. **Optimization Time vs. Circuit Size**: Shows how the ZX optimization time scales with the number of qubits in the circuit.

4. **Case Studies**: Detailed analysis of specific circuit types (SAT, TSP) showing the improvements achieved by the ZX-enhanced compiler. 