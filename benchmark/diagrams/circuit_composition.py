import os
import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from collections import defaultdict, Counter
from typing import Dict, List, Tuple, Any
import re

# Set style for plots
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_context("paper", font_scale=1.5)

# Define distinct color palettes for different visualizations
GATE_COLORS = plt.cm.tab10(np.linspace(0, 1, 10))[:4]  # Colors for T, CNOT, H, and Rest gates
CATEGORY_COLORS = np.vstack([
    plt.cm.tab10(np.linspace(0, 1, 10)),
    plt.cm.Set1(np.linspace(0, 1, 9)),
    plt.cm.Dark2(np.linspace(0, 1, 8))
])  # Colors for different categories

OUTPUT_DIR = "circuit_composition"

def ensure_output_dir():
    """Ensure the output directory exists."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)

def load_circuit_metrics(metrics_dir: str = "../circuit_metrics") -> pd.DataFrame:
    """
    Load all circuit metrics from JSON files in the metrics directory.
    
    Parameters:
    -----------
    metrics_dir : str
        Directory containing the circuit metrics JSON files
        
    Returns:
    --------
    pd.DataFrame
        DataFrame containing all circuit metrics
    """
    data = []
    
    for filename in os.listdir(metrics_dir):
        if not filename.endswith('.json'):
            continue
            
        filepath = os.path.join(metrics_dir, filename)
        
        try:
            with open(filepath, 'r') as f:
                metrics = json.load(f)
                
            # Extract basic information
            circuit_info = {
                'name': metrics['name'],
                'category': categorize_circuit(metrics['name']),
                'num_qubits': metrics['num_qubits'],
                'circuit_depth': metrics['circuit_depth'],
            }
            
            # Extract gate counts
            if 'transpiled_operation_counts' in metrics:
                gate_counts = metrics['transpiled_operation_counts']
                
                # Categorize gates
                t_gates = 0
                cnot_gates = 0
                h_gates = 0
                rest_gates = 0
                rest_gate_types = {}
                
                for gate_type, count in gate_counts.items():
                    if gate_type in ['t', 't_dg', 'rz', 'ry', 'rx', 'u1', 'p']:
                        t_gates += count
                    elif gate_type in ['cx', 'cz', 'cy']:
                        cnot_gates += count
                    elif gate_type in ['h']:
                        h_gates += count
                    else:
                        rest_gates += count
                        rest_gate_types[gate_type] = count
                
                circuit_info.update({
                    't_gates': t_gates,
                    'cnot_gates': cnot_gates,
                    'h_gates': h_gates,
                    'rest_gates': rest_gates,
                    'rest_gate_types': rest_gate_types,
                    'total_gates': sum(gate_counts.values()),
                    'gate_types': gate_counts
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
    elif name.startswith("GHZ-"):
        return "GHZ"
    else:
        return "Standard"

def plot_gate_composition_by_category(df: pd.DataFrame):
    """
    Create pie charts showing the gate composition for each circuit category.
    
    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame containing all circuit metrics
    """
    # Filter out GHZ circuits
    filtered_df = df[df['category'] != 'GHZ'].copy()
    
    # Group by category and calculate mean gate counts
    category_stats = filtered_df.groupby('category').agg({
        't_gates': 'sum',
        'cnot_gates': 'sum',
        'h_gates': 'sum',
        'rest_gates': 'sum',
        'total_gates': 'sum',
        'name': 'count'
    }).rename(columns={'name': 'count'})
    
    # Create a figure with subplots for each category
    categories = category_stats.index
    num_categories = len(categories)
    num_cols = 2
    num_rows = (num_categories + num_cols - 1) // num_cols  # Ceiling division
    
    fig, axes = plt.subplots(num_rows, num_cols, figsize=(10, 5*num_rows))
    
    # Convert axes to 1D array for easier indexing
    axes = axes.flatten() if num_categories > 1 else [axes]
    
    # Plot pie chart for each category
    for i, category in enumerate(categories):
        # Prepare data for pie chart
        gate_counts = [
            category_stats.loc[category, 't_gates'],
            category_stats.loc[category, 'cnot_gates'],
            category_stats.loc[category, 'h_gates'],
            category_stats.loc[category, 'rest_gates']
        ]
        
        # Calculate percentages
        total = sum(gate_counts)
        percentages = [count/total*100 for count in gate_counts]
        
        # Create labels with counts and percentages
        labels = [
            f'T-Gates: ({percentages[0]:.1f}%)',
            f'CNOT-Gates: ({percentages[1]:.1f}%)',
            f'H-Gates: ({percentages[2]:.1f}%)',
            f'Rest: ({percentages[3]:.1f}%)'
        ]
        
        # Plot pie chart with distinct colors
        axes[i].pie(gate_counts, labels=None, autopct='%1.1f%%', startangle=90, colors=GATE_COLORS)
        axes[i].set_title(f'{category} Circuits\n(Total Gates: {total:,})')
        
        # Add legend
        axes[i].legend(labels, loc='center left', bbox_to_anchor=(1, 0.5))
    
    # Hide empty subplots
    for i in range(num_categories, len(axes)):
        axes[i].set_visible(False)
    
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'gate_composition_by_category.png'), dpi=300, bbox_inches='tight')
    plt.savefig(os.path.join(OUTPUT_DIR, 'gate_composition_by_category.pdf'), bbox_inches='tight')
    plt.close()

def plot_gate_composition_overall(df: pd.DataFrame):
    """
    Create a pie chart showing the overall gate composition across all circuits.
    
    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame containing all circuit metrics
    """
    # Filter out GHZ circuits
    filtered_df = df[df['category'] != 'GHZ'].copy()
    
    # Calculate total gate counts
    total_t_gates = filtered_df['t_gates'].sum()
    total_cnot_gates = filtered_df['cnot_gates'].sum()
    total_h_gates = filtered_df['h_gates'].sum()
    total_rest_gates = filtered_df['rest_gates'].sum()
    total_gates = filtered_df['total_gates'].sum()
    
    # Prepare data for pie chart
    gate_counts = [total_t_gates, total_cnot_gates, total_h_gates, total_rest_gates]
    
    # Calculate percentages
    percentages = [count/total_gates*100 for count in gate_counts]
    
    # Create labels with counts and percentages
    labels = [
        f'T-Gates: {total_t_gates:,} ({percentages[0]:.1f}%)',
        f'CNOT-Gates: {total_cnot_gates:,} ({percentages[1]:.1f}%)',
        f'H-Gates: {total_h_gates:,} ({percentages[2]:.1f}%)',
        f'Rest: {total_rest_gates:,} ({percentages[3]:.1f}%)'
    ]
    
    # Create figure
    plt.figure(figsize=(10, 8))
    
    # Plot pie chart with distinct colors
    plt.pie(gate_counts, labels=None, autopct='%1.1f%%', startangle=90, colors=GATE_COLORS)
    plt.title(f'Overall Gate Composition (Excluding GHZ Circuits)\n(Total Gates: {total_gates:,})')
    
    # Add legend
    plt.legend(labels, loc='center left', bbox_to_anchor=(1, 0.5))
    
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'gate_composition_overall.png'), dpi=300, bbox_inches='tight')
    plt.savefig(os.path.join(OUTPUT_DIR, 'gate_composition_overall.pdf'), bbox_inches='tight')
    plt.close()

def plot_rest_gate_composition(df: pd.DataFrame):
    """
    Create a pie chart showing the composition of the "Rest" gate category.
    
    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame containing all circuit metrics
    """
    # Filter out GHZ circuits
    filtered_df = df[df['category'] != 'GHZ'].copy()
    
    # Collect all rest gate types and counts
    rest_gate_counts = defaultdict(int)
    
    for _, row in filtered_df.iterrows():
        if isinstance(row['rest_gate_types'], dict):
            for gate_type, count in row['rest_gate_types'].items():
                rest_gate_counts[gate_type] += count
    
    # Sort by count (descending)
    sorted_rest_gates = sorted(rest_gate_counts.items(), key=lambda x: x[1], reverse=True)
    
    # Prepare data for pie chart
    gate_types = [gate for gate, _ in sorted_rest_gates]
    gate_counts = [count for _, count in sorted_rest_gates]
    
    # Calculate total
    total_rest_gates = sum(gate_counts)
    
    # Calculate percentages
    percentages = [count/total_rest_gates*100 for count in gate_counts]
    
    # Create labels with counts and percentages
    labels = [f'{gate}: {count:,} ({percentage:.1f}%)' 
              for gate, count, percentage in zip(gate_types, gate_counts, percentages)]
    
    # Create figure
    plt.figure(figsize=(12, 10))
    
    # Create a colormap with distinct colors for rest gates
    num_rest_gates = len(gate_types)
    rest_colors = plt.cm.tab20(np.linspace(0, 1, 20))
    if num_rest_gates > 20:
        rest_colors = np.vstack([rest_colors, plt.cm.tab20b(np.linspace(0, 1, 20))])
    if num_rest_gates > 40:
        rest_colors = np.vstack([rest_colors, plt.cm.tab20c(np.linspace(0, 1, 20))])
    rest_colors = rest_colors[:num_rest_gates]
    
    # Plot pie chart with distinct colors
    plt.pie(gate_counts, labels=None, autopct='%1.1f%%', startangle=90, colors=rest_colors)
    plt.title(f'Rest Gate Composition (Excluding GHZ Circuits)\n(Total Rest Gates: {total_rest_gates:,})')
    
    # Add legend
    plt.legend(labels, loc='center left', bbox_to_anchor=(1, 0.5))
    
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'rest_gate_composition.png'), dpi=300, bbox_inches='tight')
    plt.savefig(os.path.join(OUTPUT_DIR, 'rest_gate_composition.pdf'), bbox_inches='tight')
    plt.close()

def plot_gate_density(df: pd.DataFrame):
    """
    Create a scatter plot showing the gate density (gates per qubit) for each circuit.
    
    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame containing all circuit metrics
    """
    # Calculate gate density
    df['gate_density'] = df['total_gates'] / df['num_qubits']
    
    # Create figure
    plt.figure(figsize=(12, 8))
    
    # Plot scatter points
    sns.scatterplot(x='num_qubits', y='gate_density', hue='category', 
                    size='circuit_depth', sizes=(50, 500), alpha=0.7, data=df)
    
    # Add labels and title
    plt.xlabel('Number of Qubits')
    plt.ylabel('Gate Density (Gates per Qubit)')
    plt.title('Gate Density vs. Circuit Size')
    
    # Add grid
    plt.grid(linestyle='--', alpha=0.7)
    
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'gate_density.png'), dpi=300, bbox_inches='tight')
    plt.savefig(os.path.join(OUTPUT_DIR, 'gate_density.pdf'), bbox_inches='tight')
    plt.close()

def plot_cnot_t_ratio(df: pd.DataFrame):
    """
    Create a scatter plot showing the CNOT to T-gate ratio for each circuit.
    
    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame containing all circuit metrics
    """
    # Filter out GHZ circuits
    filtered_df = df[df['category'] != 'GHZ'].copy()
    
    # Calculate CNOT to T-gate ratio
    # Add a small epsilon to avoid division by zero
    filtered_df['cnot_t_ratio'] = filtered_df['cnot_gates'] / (filtered_df['t_gates'] + 1e-10)
    
    # Create figure
    plt.figure(figsize=(12, 8))
    
    # Get unique categories for color mapping
    categories = filtered_df['category'].unique()
    category_colors = {cat: CATEGORY_COLORS[i % len(CATEGORY_COLORS)] for i, cat in enumerate(categories)}
    
    # Plot scatter points with distinct colors
    for category in categories:
        cat_data = filtered_df[filtered_df['category'] == category]
        plt.scatter(cat_data['num_qubits'], cat_data['cnot_t_ratio'], 
                   s=np.log(cat_data['circuit_depth'])/np.log(1.5)*5, alpha=0.7,
                   label=category, color=category_colors[category])
    # Add labels and title
    plt.xlabel('Number of Qubits')
    plt.ylabel('CNOT to T-gate Ratio')
    plt.title('CNOT to T-gate Ratio vs. Circuit Size (Excluding GHZ Circuits)')
    
    # Add grid
    plt.grid(linestyle='--', alpha=0.7)
    
    # Use logarithmic scale for y-axis if the ratios vary widely
    if filtered_df['cnot_t_ratio'].max() / (filtered_df['cnot_t_ratio'].min() + 1e-10) > 100:
        plt.yscale('log')
    
    # Add legend
    plt.legend(title='Category')
    
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'cnot_t_ratio.png'), dpi=300, bbox_inches='tight')
    plt.savefig(os.path.join(OUTPUT_DIR, 'cnot_t_ratio.pdf'), bbox_inches='tight')
    plt.close()

def plot_gate_type_distribution(df: pd.DataFrame):
    """
    Create a heatmap showing the distribution of gate types across circuit categories.
    
    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame containing all circuit metrics
    """
    # Collect all gate types
    all_gate_types = set()
    for _, row in df.iterrows():
        if isinstance(row['gate_types'], dict):
            all_gate_types.update(row['gate_types'].keys())
    
    # Create a matrix of gate type counts by category
    gate_type_matrix = {}
    
    for category in df['category'].unique():
        category_df = df[df['category'] == category]
        gate_counts = defaultdict(int)
        
        for _, row in category_df.iterrows():
            if isinstance(row['gate_types'], dict):
                for gate_type, count in row['gate_types'].items():
                    gate_counts[gate_type] += count
        
        gate_type_matrix[category] = gate_counts
    
    # Convert to DataFrame
    gate_type_df = pd.DataFrame(gate_type_matrix).fillna(0)
    
    # Calculate percentages within each category
    for category in gate_type_df.columns:
        total = gate_type_df[category].sum()
        gate_type_df[category] = gate_type_df[category] / total * 100
    
    # Sort by overall frequency
    gate_type_df['total'] = gate_type_df.sum(axis=1)
    gate_type_df = gate_type_df.sort_values('total', ascending=False)
    gate_type_df = gate_type_df.drop('total', axis=1)
    
    # Create figure
    plt.figure(figsize=(12, max(8, len(gate_type_df) * 0.4)))
    
    # Plot heatmap
    sns.heatmap(gate_type_df, annot=True, fmt='.1f', cmap='viridis', 
                cbar_kws={'label': 'Percentage of Gates (%)'})
    
    # Add labels and title
    plt.xlabel('Circuit Category')
    plt.ylabel('Gate Type')
    plt.title('Gate Type Distribution by Circuit Category')
    
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'gate_type_distribution.png'), dpi=300, bbox_inches='tight')
    plt.savefig(os.path.join(OUTPUT_DIR, 'gate_type_distribution.pdf'), bbox_inches='tight')
    plt.close()

def plot_qubit_size_distribution(df: pd.DataFrame):
    """
    Create a stacked bar chart showing the distribution of circuit sizes (number of qubits),
    grouped into buckets of size 5.
    
    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame containing all circuit metrics
    """
    # Create a copy of the dataframe to avoid modifying the original
    plot_df = df.copy()
    
    # Create qubit size buckets (0-4, 5-9, 10-14, etc.)
    plot_df['qubit_bucket'] = (plot_df['num_qubits'] // 5) * 5
    
    # Count circuits by qubit bucket and category
    qubit_counts = plot_df.groupby(['qubit_bucket', 'category']).size().reset_index(name='count')
    
    # Create a pivot table for easier stacked bar plotting
    pivot_df = qubit_counts.pivot(index='qubit_bucket', columns='category', values='count').fillna(0)
    
    # Sort the index to ensure buckets are in ascending order
    pivot_df = pivot_df.sort_index()
    
    # Create figure
    plt.figure(figsize=(14, 8))
    
    # Create a colormap with more distinct colors
    # Using a combination of tab10, Set1, and Dark2 for better distinction
    categories = pivot_df.columns
    colors = plt.cm.tab10(np.linspace(0, 1, 10))
    colors = np.vstack([colors, plt.cm.Set1(np.linspace(0, 1, 9))])
    colors = np.vstack([colors, plt.cm.Dark2(np.linspace(0, 1, 8))])
    colors = colors[:len(categories)]
    
    # Create the stacked bar chart with wider bars (width=3)
    bottom = np.zeros(len(pivot_df.index))
    bars = {}
    bar_width = 3
    
    for i, category in enumerate(categories):
        values = pivot_df[category].values
        bars[category] = plt.bar(pivot_df.index, values, width=bar_width, bottom=bottom, 
                                 label=category, color=colors[i], alpha=0.8)
        bottom += values
    
    # Add labels and title
    plt.xlabel('Number of Qubits (Bucketed)')
    plt.ylabel('Number of Circuits')
    plt.title('Distribution of Circuit Sizes by Category (Stacked)')
    
    # Set x-ticks with bucket ranges
    bucket_labels = [f'{b}-{b+4}' for b in pivot_df.index]
    plt.xticks(pivot_df.index, bucket_labels)
    
    # Add grid lines for better readability
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    
    # Add legend
    plt.legend(title='Category', loc='upper right')
    
    # Add value labels on top of the stacked bars for total counts
    for i, bucket in enumerate(pivot_df.index):
        total = sum(pivot_df.loc[bucket])
        if total > 0:
            plt.text(bucket, total + 0.5, f'{int(total)}', 
                    ha='center', va='bottom', fontsize=10, fontweight='bold')
    
    # Add value labels for each segment if large enough
    for category in categories:
        for bar in bars[category]:
            height = bar.get_height()
            if height > 3:  # Only add labels for segments with enough height
                plt.text(bar.get_x() + bar.get_width()/2., 
                        bar.get_y() + height/2,
                        f'{int(height)}', 
                        ha='center', va='center', 
                        fontsize=9, color='white', fontweight='bold')
    
    # Adjust x-axis limits to give some padding around the bars
    plt.xlim(min(pivot_df.index) - 2, max(pivot_df.index) + 2)
    
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'qubit_size_distribution.png'), dpi=300, bbox_inches='tight')
    plt.savefig(os.path.join(OUTPUT_DIR, 'qubit_size_distribution.pdf'), bbox_inches='tight')
    plt.close()
    
def plot_total_gate_distribution(df: pd.DataFrame):
    """
    Create a stacked bar chart showing the distribution of circuit sizes (total number of gates),
    grouped into logarithmic buckets.
    
    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame containing all circuit metrics
    """
    # Create a copy of the dataframe to avoid modifying the original
    plot_df = df.copy()
    
    # Create logarithmic gate size buckets (1-10, 11-100, 101-1000, etc.)
    plot_df['gate_bucket'] = np.power(10, np.floor(np.log10(plot_df['total_gates'])))
    
    # Count circuits by gate bucket and category
    gate_counts = plot_df.groupby(['gate_bucket', 'category']).size().reset_index(name='count')
    
    # Create a pivot table for easier stacked bar plotting
    pivot_df = gate_counts.pivot(index='gate_bucket', columns='category', values='count').fillna(0)
    
    # Sort the index to ensure buckets are in ascending order
    pivot_df = pivot_df.sort_index()
    
    # Create figure
    plt.figure(figsize=(14, 8))
    
    # Create a colormap with more distinct colors
    # Using a combination of tab10, Set1, and Dark2 for better distinction
    categories = pivot_df.columns
    colors = plt.cm.tab10(np.linspace(0, 1, 10))
    colors = np.vstack([colors, plt.cm.Set1(np.linspace(0, 1, 9))])
    colors = np.vstack([colors, plt.cm.Dark2(np.linspace(0, 1, 8))])
    colors = colors[:len(categories)]
    
    # Create the stacked bar chart with wider bars (width=0.3)
    bottom = np.zeros(len(pivot_df.index))
    bars = {}
    bar_width = 0.3
    
    for i, category in enumerate(categories):
        values = pivot_df[category].values
        bars[category] = plt.bar(range(len(pivot_df.index)), values, width=bar_width, bottom=bottom, 
                                 label=category, color=colors[i], alpha=0.8)
        bottom += values
    
    # Add labels and title
    plt.xlabel('Total Number of Gates (Log Scale)')
    plt.ylabel('Number of Circuits')
    plt.title('Distribution of Circuit Sizes by Category (Stacked)')
    
    # Set x-ticks with bucket ranges
    bucket_labels = [f'{int(b)}-{int(b*10-1)}' for b in pivot_df.index]
    plt.xticks(range(len(pivot_df.index)), bucket_labels, rotation=45)
    
    # Add grid lines for better readability
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    
    # Add legend
    plt.legend(title='Category', loc='upper right')
    
    # Add value labels on top of the stacked bars for total counts
    for i, bucket in enumerate(pivot_df.index):
        total = sum(pivot_df.loc[bucket])
        if total > 0:
            plt.text(i, total + 0.5, f'{int(total)}', 
                    ha='center', va='bottom', fontsize=10, fontweight='bold')
    
    # Add value labels for each segment if large enough
    for category in categories:
        for bar in bars[category]:
            height = bar.get_height()
            if height > 3:  # Only add labels for segments with enough height
                plt.text(bar.get_x() + bar.get_width()/2., 
                        bar.get_y() + height/2,
                        f'{int(height)}', 
                        ha='center', va='center', 
                        fontsize=9, color='white', fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'gate_size_distribution.png'), dpi=300, bbox_inches='tight')
    plt.savefig(os.path.join(OUTPUT_DIR, 'gate_size_distribution.pdf'), bbox_inches='tight')
    plt.close()

def generate_rest_gates_report(df: pd.DataFrame):
    """
    Generate a report of all the gates in the "Rest" category.
    
    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame containing all circuit metrics
    """
    # Filter out GHZ circuits
    filtered_df = df[df['category'] != 'GHZ'].copy()
    
    # Collect all rest gate types and counts
    rest_gate_counts = defaultdict(int)
    
    for _, row in filtered_df.iterrows():
        if isinstance(row['rest_gate_types'], dict):
            for gate_type, count in row['rest_gate_types'].items():
                rest_gate_counts[gate_type] += count
    
    # Sort by count (descending)
    sorted_rest_gates = sorted(rest_gate_counts.items(), key=lambda x: x[1], reverse=True)
    
    # Generate report
    report = "# Rest Gates Report (Excluding GHZ Circuits)\n\n"
    report += "This report lists all the gates that were categorized as 'Rest' gates.\n\n"
    report += "## Overall Counts\n\n"
    report += "| Gate Type | Count | Percentage |\n"
    report += "|-----------|-------|------------|\n"
    
    total_rest_gates = sum(count for _, count in sorted_rest_gates)
    
    for gate_type, count in sorted_rest_gates:
        percentage = count / total_rest_gates * 100
        report += f"| {gate_type} | {count:,} | {percentage:.2f}% |\n"
    
    report += f"\nTotal Rest Gates: {total_rest_gates:,}\n\n"
    
    # Add section for gates by category
    report += "## Gates by Category\n\n"
    
    for category in filtered_df['category'].unique():
        report += f"### {category} Circuits\n\n"
        report += "| Gate Type | Count | Percentage |\n"
        report += "|-----------|-------|------------|\n"
        
        category_df = filtered_df[filtered_df['category'] == category]
        category_rest_gates = defaultdict(int)
        
        for _, row in category_df.iterrows():
            if isinstance(row['rest_gate_types'], dict):
                for gate_type, count in row['rest_gate_types'].items():
                    category_rest_gates[gate_type] += count
        
        category_total = sum(category_rest_gates.values())
        
        if category_total > 0:
            sorted_category_gates = sorted(category_rest_gates.items(), key=lambda x: x[1], reverse=True)
            
            for gate_type, count in sorted_category_gates:
                percentage = count / category_total * 100
                report += f"| {gate_type} | {count:,} | {percentage:.2f}% |\n"
            
            report += f"\nTotal Rest Gates in {category} Circuits: {category_total:,}\n\n"
        else:
            report += "No rest gates in this category.\n\n"
    
    # Write report to file
    with open(os.path.join(OUTPUT_DIR, 'rest_gates_report.md'), 'w') as f:
        f.write(report)

def main():
    """Main function to generate all circuit composition visualizations."""
    # Ensure output directory exists
    ensure_output_dir()
    
    # Load data
    print("Loading circuit metrics...")
    df = load_circuit_metrics()
    print(f"Loaded {len(df)} circuits.")
    
    # Generate visualizations
    print("Generating circuit composition visualizations...")
    
    print("1. Plotting gate composition by category...")
    plot_gate_composition_by_category(df)
    
    print("2. Plotting overall gate composition...")
    plot_gate_composition_overall(df)
    
    print("3. Plotting rest gate composition...")
    plot_rest_gate_composition(df)
    
    print("4. Plotting gate density...")
    plot_gate_density(df)
    
    print("5. Plotting CNOT to T-gate ratio...")
    plot_cnot_t_ratio(df)
    
    print("6. Plotting gate type distribution...")
    plot_gate_type_distribution(df)
    
    print("7. Generating rest gates report...")
    generate_rest_gates_report(df)
    
    print("8. Plotting qubit size distribution...")
    plot_qubit_size_distribution(df)
    
    print("9. Plotting gate size distribution...")
    plot_total_gate_distribution(df)
    
    print("All circuit composition visualizations generated successfully!")

if __name__ == "__main__":
    main() 