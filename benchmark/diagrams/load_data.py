import os
import json
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Any

def load_benchmark_data(results_dir: str = "../results_01") -> pd.DataFrame:
    """
    Load all benchmark data from JSON files in the results directory.
    
    Parameters:
    -----------
    results_dir : str
        Directory containing the benchmark JSON files
        
    Returns:
    --------
    pd.DataFrame
        DataFrame containing all benchmark data
    """
    data = []
    
    for filename in os.listdir(results_dir):
        if not filename.endswith('.json'):
            continue
            
        filepath = os.path.join(results_dir, filename)
        
        try:
            with open(filepath, 'r') as f:
                result = json.load(f)
                
            # Extract basic information
            circuit_info = {
                'name': result['name'],
                'category': categorize_circuit(result['name']),
                'num_qubits': result['non_transpiled']['num_qubits'],
                
                # Non-transpiled metrics
                'non_transpiled_t_depth': result['non_transpiled']['t_depth'],
                'non_transpiled_cnot_depth': result['non_transpiled']['cnot_depth'],
                'non_transpiled_cnot_count': result['non_transpiled']['cnot_count'],
                
                # Transpiled metrics
                'transpiled_t_depth': result['transpiled']['t_depth'],
                'transpiled_cnot_depth': result['transpiled']['cnot_depth'],
                'transpiled_cnot_count': result['transpiled']['cnot_count'],
                
                # ZX-optimized metrics
                'zx_t_depth': result['zx_optimized']['t_depth'],
                'zx_cnot_depth': result['zx_optimized']['cnot_depth'],
                'zx_cnot_count': result['zx_optimized']['cnot_count'],
                
                # Optimization time
                'zx_optimization_time': result['zx_optimized'].get('optimization_time', np.nan),
            }
            
            # Handle improvements as percentages (convert from percentage to decimal)
            # For example, 99.9 (%) becomes 0.999 as a decimal
            circuit_info.update({
                'transpiled_t_depth_reduction': result['improvements']['transpiled']['t_depth_reduction'] / 100,
                'transpiled_cnot_depth_reduction': result['improvements']['transpiled']['cnot_depth_reduction'] / 100,
                'transpiled_cnot_count_reduction': result['improvements']['transpiled']['cnot_count_reduction'] / 100,
                
                'zx_t_depth_reduction': result['improvements']['zx']['t_depth_reduction'] / 100,
                'zx_cnot_depth_reduction': result['improvements']['zx']['cnot_depth_reduction'] / 100,
                'zx_cnot_count_reduction': result['improvements']['zx']['cnot_count_reduction'] / 100,
                
                'zx_over_normal_t_depth_reduction': (circuit_info['transpiled_t_depth'] - circuit_info['zx_t_depth']) / circuit_info['transpiled_t_depth'] if circuit_info['transpiled_t_depth'] > 0 else 0,
                'zx_over_normal_cnot_depth_reduction': (circuit_info['transpiled_cnot_depth'] - circuit_info['zx_cnot_depth']) / circuit_info['transpiled_cnot_depth'] if circuit_info['transpiled_cnot_depth'] > 0 else 0,
                'zx_over_normal_cnot_count_reduction': (circuit_info['transpiled_cnot_count'] - circuit_info['zx_cnot_count']) / circuit_info['transpiled_cnot_count'] if circuit_info['transpiled_cnot_count'] > 0 else 0,
            })
            
            data.append(circuit_info)
        except Exception as e:
            print(f"Error processing {filename}: {e}")
    
    return pd.DataFrame(data)

def categorize_circuit(name: str) -> str:
    """
    Categorize circuit based on its name.
    
    Parameters:
    -----------
    name : str
        Circuit name
        
    Returns:
    --------
    str
        Category of the circuit
    """
    if name.startswith("SAT_"):
        return "SAT"
    elif name.startswith("TSP_"):
        return "TSP-Grover"
    elif name.startswith("QUBO_"):
        return "TSP-QAOA"
    else:
        return "Standard"  # GHZ circuits are now included in Standard

def get_category_statistics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate statistics for each category of circuits.
    
    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame containing all benchmark data
        
    Returns:
    --------
    pd.DataFrame
        DataFrame containing statistics for each category
    """
    # Group by category and calculate mean improvements
    category_stats = df.groupby('category').agg({
        'transpiled_t_depth_reduction': 'mean',
        'transpiled_cnot_depth_reduction': 'mean',
        'transpiled_cnot_count_reduction': 'mean',
        'zx_t_depth_reduction': 'mean',
        'zx_cnot_depth_reduction': 'mean',
        'zx_cnot_count_reduction': 'mean',
        'num_qubits': 'mean',
        'zx_optimization_time': 'mean',
        'name': 'count'
    }).rename(columns={'name': 'count'})
    
    return category_stats

def get_size_binned_statistics(df: pd.DataFrame, bin_edges: List[int] = [0, 10, 20, 30, 50, 100]) -> pd.DataFrame:
    """
    Calculate statistics for circuits binned by number of qubits.
    
    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame containing all benchmark data
    bin_edges : List[int]
        Edges for binning circuits by number of qubits
        
    Returns:
    --------
    pd.DataFrame
        DataFrame containing statistics for each size bin
    """
    # Create size bins
    df['size_bin'] = pd.cut(df['num_qubits'], bins=bin_edges)
    
    # Group by size bin and calculate mean improvements
    size_stats = df.groupby('size_bin').agg({
        'transpiled_t_depth_reduction': 'mean',
        'transpiled_cnot_depth_reduction': 'mean',
        'transpiled_cnot_count_reduction': 'mean',
        'zx_t_depth_reduction': 'mean',
        'zx_cnot_depth_reduction': 'mean',
        'zx_cnot_count_reduction': 'mean',
        'zx_optimization_time': 'mean',
        'name': 'count'
    }).rename(columns={'name': 'count'})
    
    return size_stats

if __name__ == "__main__":
    # Load data
    df = load_benchmark_data()
    
    # Print basic statistics
    print(f"Total circuits: {len(df)}")
    print(f"Categories: {df['category'].value_counts().to_dict()}")
    
    # Calculate and print category statistics
    category_stats = get_category_statistics(df)
    print("\nCategory Statistics:")
    print(category_stats)
    
    # Calculate and print size-binned statistics
    size_stats = get_size_binned_statistics(df)
    print("\nSize-Binned Statistics:")
    print(size_stats) 