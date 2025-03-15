import os
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from load_data import load_benchmark_data, get_category_statistics, categorize_circuit
from matplotlib.ticker import PercentFormatter

# Set style for plots
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_context("paper", font_scale=1.5)
COLORS = sns.color_palette("viridis", 3)
OUTPUT_DIR = "paper_output"

def ensure_output_dir():
    """Ensure the output directory exists."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)

def plot_t_depth_reduction_by_category(df: pd.DataFrame):
    """
    Create a publication-quality plot of T-depth reduction by circuit category.
    
    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame containing all benchmark data
    """
    # Get category statistics
    category_stats = df.groupby('category').agg({
        'transpiled_t_depth_reduction': ['mean', 'std', 'count'],
        'zx_t_depth_reduction': ['mean', 'std', 'count']
    })
    
    # Flatten the multi-index columns
    category_stats.columns = ['_'.join(col).strip() for col in category_stats.columns.values]
    
    # Create figure
    plt.figure(figsize=(10, 6))
    
    # Prepare data for plotting
    categories = category_stats.index
    x = np.arange(len(categories))
    width = 0.35
    
    # Calculate error bars (95% confidence interval)
    transpiled_err = 1.96 * category_stats['transpiled_t_depth_reduction_std'] / np.sqrt(category_stats['transpiled_t_depth_reduction_count'])
    zx_err = 1.96 * category_stats['zx_t_depth_reduction_std'] / np.sqrt(category_stats['zx_t_depth_reduction_count'])
    
    # Plot bars with error bars
    plt.bar(x - width/2, category_stats['transpiled_t_depth_reduction_mean'], width, 
            yerr=transpiled_err, label='Standard Transpiler', color=COLORS[0], alpha=0.7,
            capsize=5, error_kw={'elinewidth': 1.5, 'capthick': 1.5})
    plt.bar(x + width/2, category_stats['zx_t_depth_reduction_mean'], width, 
            yerr=zx_err, label='ZX-Enhanced', color=COLORS[2], alpha=0.7,
            capsize=5, error_kw={'elinewidth': 1.5, 'capthick': 1.5})
    
    # Add labels and title
    plt.xlabel('Circuit Category')
    plt.ylabel('T-Depth Reduction (%)')
    plt.title('T-Depth Reduction by Circuit Category')
    plt.xticks(x, categories, rotation=45, ha='right')
    plt.legend()
    
    # Add grid
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    
    # Format y-axis as percentage
    plt.gca().yaxis.set_major_formatter(PercentFormatter(1.0))
    
    # Add value labels on top of bars
    for i, v in enumerate(category_stats['transpiled_t_depth_reduction_mean']):
        plt.text(i - width/2, v + 0.02, f"{v:.1%}", ha='center', va='bottom', fontsize=9)
    
    for i, v in enumerate(category_stats['zx_t_depth_reduction_mean']):
        plt.text(i + width/2, v + 0.02, f"{v:.1%}", ha='center', va='bottom', fontsize=9)
    
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 't_depth_reduction_by_category.png'), dpi=300, bbox_inches='tight')
    plt.savefig(os.path.join(OUTPUT_DIR, 't_depth_reduction_by_category.pdf'), bbox_inches='tight')
    plt.close()

def plot_cnot_metrics_comparison(df: pd.DataFrame):
    """
    Create a publication-quality plot comparing CNOT-depth and CNOT-count reductions.
    
    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame containing all benchmark data
    """
    # Create figure
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # Plot scatter points
    scatter = ax.scatter(df['zx_cnot_depth_reduction'], df['zx_cnot_count_reduction'], 
                         c=df['num_qubits'], cmap='viridis', alpha=0.7, s=100,
                         edgecolor='k', linewidth=0.5)
    
    # Add colorbar
    cbar = plt.colorbar(scatter)
    cbar.set_label('Number of Qubits')
    
    # Add labels for different categories
    for category in df['category'].unique():
        category_df = df[df['category'] == category]
        centroid_x = category_df['zx_cnot_depth_reduction'].mean()
        centroid_y = category_df['zx_cnot_count_reduction'].mean()
        ax.annotate(category, (centroid_x, centroid_y), 
                    fontsize=12, fontweight='bold',
                    bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="gray", alpha=0.8))
    
    # Add reference lines
    ax.axhline(y=0, color='gray', linestyle='--', alpha=0.5)
    ax.axvline(x=0, color='gray', linestyle='--', alpha=0.5)
    
    # Add labels and title
    ax.set_xlabel('CNOT-Depth Reduction (%)')
    ax.set_ylabel('CNOT-Count Reduction (%)')
    ax.set_title('ZX-Enhanced Compiler: CNOT-Depth vs. CNOT-Count Reduction')
    
    # Format axes as percentage
    ax.xaxis.set_major_formatter(PercentFormatter(1.0))
    ax.yaxis.set_major_formatter(PercentFormatter(1.0))
    
    # Add grid
    ax.grid(linestyle='--', alpha=0.7)
    
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'cnot_metrics_comparison.png'), dpi=300, bbox_inches='tight')
    plt.savefig(os.path.join(OUTPUT_DIR, 'cnot_metrics_comparison.pdf'), bbox_inches='tight')
    plt.close()

def plot_optimization_time_vs_circuit_size(df: pd.DataFrame):
    """
    Create a publication-quality plot of optimization time vs. circuit size.
    
    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame containing all benchmark data
    """
    # Create figure
    plt.figure(figsize=(10, 6))
    
    # Plot scatter points with regression line
    sns.regplot(x='num_qubits', y='zx_optimization_time', data=df, 
                scatter_kws={'alpha': 0.7, 's': 100, 'edgecolor': 'k', 'linewidth': 0.5},
                line_kws={'color': 'red'})
    
    # Add labels for different categories
    for category in df['category'].unique():
        category_df = df[df['category'] == category]
        centroid_x = category_df['num_qubits'].mean()
        centroid_y = category_df['zx_optimization_time'].mean()
        plt.annotate(category, (centroid_x, centroid_y), 
                     fontsize=12, fontweight='bold',
                     bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="gray", alpha=0.8))
    
    # Add labels and title
    plt.xlabel('Number of Qubits')
    plt.ylabel('ZX Optimization Time (s)')
    plt.title('ZX Optimization Time vs. Circuit Size')
    
    # Use logarithmic scale for y-axis
    plt.yscale('log')
    
    # Add grid
    plt.grid(linestyle='--', alpha=0.7)
    
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'optimization_time_vs_circuit_size.png'), dpi=300, bbox_inches='tight')
    plt.savefig(os.path.join(OUTPUT_DIR, 'optimization_time_vs_circuit_size.pdf'), bbox_inches='tight')
    plt.close()

def plot_t_depth_reduction_distribution(df: pd.DataFrame):
    """
    Create a publication-quality plot of T-depth reduction distribution.
    
    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame containing all benchmark data
    """
    # Create figure
    plt.figure(figsize=(12, 6))
    
    # Prepare data for plotting
    data = pd.melt(df, id_vars=['name', 'category'], 
                  value_vars=['transpiled_t_depth_reduction', 'zx_t_depth_reduction'],
                  var_name='compiler', value_name='reduction')
    data['compiler'] = data['compiler'].map({
        'transpiled_t_depth_reduction': 'Standard Transpiler',
        'zx_t_depth_reduction': 'ZX-Enhanced'
    })
    
    # Plot violin plots
    sns.violinplot(x='category', y='reduction', hue='compiler', data=data, 
                   palette=[COLORS[0], COLORS[2]], alpha=0.7, inner='quartile',
                   split=True, cut=0)
    
    # Add labels and title
    plt.xlabel('Circuit Category')
    plt.ylabel('T-Depth Reduction')
    plt.title('Distribution of T-Depth Reduction by Circuit Category')
    
    # Format y-axis as percentage
    plt.gca().yaxis.set_major_formatter(PercentFormatter(1.0))
    
    # Rotate x-axis labels for better readability
    plt.xticks(rotation=45, ha='right')
    
    # Add grid
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 't_depth_reduction_distribution.png'), dpi=300, bbox_inches='tight')
    plt.savefig(os.path.join(OUTPUT_DIR, 't_depth_reduction_distribution.pdf'), bbox_inches='tight')
    plt.close()

def plot_improvement_radar_chart(df: pd.DataFrame):
    """
    Create a radar chart comparing the improvements across different metrics.
    
    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame containing all benchmark data
    """
    # Get category statistics
    category_stats = df.groupby('category').agg({
        'transpiled_t_depth_reduction': 'mean',
        'transpiled_cnot_depth_reduction': 'mean',
        'transpiled_cnot_count_reduction': 'mean',
        'zx_t_depth_reduction': 'mean',
        'zx_cnot_depth_reduction': 'mean',
        'zx_cnot_count_reduction': 'mean'
    })
    
    # Prepare data for radar chart
    categories = category_stats.index
    metrics = ['T-Depth Reduction', 'CNOT-Depth Reduction', 'CNOT-Count Reduction']
    
    # Create figure
    fig = plt.figure(figsize=(12, 10))
    
    # Number of variables
    N = len(metrics)
    
    # Create a radar chart with as many axes as there are metrics
    angles = np.linspace(0, 2*np.pi, N, endpoint=False).tolist()
    angles += angles[:1]  # Close the loop
    
    # Create subplots for each category
    n_rows = (len(categories) + 1) // 2
    n_cols = 2
    
    for i, category in enumerate(categories):
        ax = fig.add_subplot(n_rows, n_cols, i+1, polar=True)
        
        # Get data for this category
        transpiled_values = [
            category_stats.loc[category, 'transpiled_t_depth_reduction'],
            category_stats.loc[category, 'transpiled_cnot_depth_reduction'],
            category_stats.loc[category, 'transpiled_cnot_count_reduction']
        ]
        transpiled_values += transpiled_values[:1]  # Close the loop
        
        zx_values = [
            category_stats.loc[category, 'zx_t_depth_reduction'],
            category_stats.loc[category, 'zx_cnot_depth_reduction'],
            category_stats.loc[category, 'zx_cnot_count_reduction']
        ]
        zx_values += zx_values[:1]  # Close the loop
        
        # Plot data
        ax.plot(angles, transpiled_values, 'o-', linewidth=2, label='Standard Transpiler', color=COLORS[0], alpha=0.7)
        ax.fill(angles, transpiled_values, color=COLORS[0], alpha=0.1)
        
        ax.plot(angles, zx_values, 'o-', linewidth=2, label='ZX-Enhanced', color=COLORS[2], alpha=0.7)
        ax.fill(angles, zx_values, color=COLORS[2], alpha=0.1)
        
        # Set labels
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(metrics)
        
        # Set title
        ax.set_title(category, size=14, y=1.1)
        
        # Add legend
        ax.legend(loc='upper right', bbox_to_anchor=(0.1, 0.1))
    
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'improvement_radar_chart.png'), dpi=300, bbox_inches='tight')
    plt.savefig(os.path.join(OUTPUT_DIR, 'improvement_radar_chart.pdf'), bbox_inches='tight')
    plt.close()

def plot_case_study_sat(df: pd.DataFrame):
    """
    Create a case study visualization for SAT problems.
    
    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame containing all benchmark data
    """
    # Filter for SAT problems
    sat_df = df[df['category'] == 'SAT'].copy()
    
    if len(sat_df) == 0:
        print("No SAT problems found in the data.")
        return
    
    # Create figure with 2 subplots
    fig, axes = plt.subplots(1, 2, figsize=(15, 6))
    
    # Plot T-depth before and after optimization
    sat_df['non_transpiled_t_depth_normalized'] = sat_df['non_transpiled_t_depth'] / sat_df['num_qubits']
    sat_df['zx_t_depth_normalized'] = sat_df['zx_t_depth'] / sat_df['num_qubits']
    
    # Sort by non-transpiled T-depth
    sat_df = sat_df.sort_values('non_transpiled_t_depth_normalized', ascending=False)
    
    # Plot normalized T-depth
    x = np.arange(len(sat_df))
    axes[0].bar(x, sat_df['non_transpiled_t_depth_normalized'], color=COLORS[0], alpha=0.7, label='Original')
    axes[0].bar(x, sat_df['zx_t_depth_normalized'], color=COLORS[2], alpha=0.7, label='ZX-Enhanced')
    
    axes[0].set_title('T-Depth per Qubit in SAT Problems')
    axes[0].set_xlabel('SAT Problem')
    axes[0].set_ylabel('T-Depth / Number of Qubits')
    axes[0].set_xticks(x)
    axes[0].set_xticklabels(sat_df['name'], rotation=45, ha='right')
    axes[0].legend()
    
    # Plot improvement percentages
    axes[1].bar(x, sat_df['zx_t_depth_reduction'], color=COLORS[2], alpha=0.7)
    
    axes[1].set_title('T-Depth Reduction in SAT Problems')
    axes[1].set_xlabel('SAT Problem')
    axes[1].set_ylabel('Reduction Percentage')
    axes[1].set_xticks(x)
    axes[1].set_xticklabels(sat_df['name'], rotation=45, ha='right')
    
    # Format y-axis as percentage
    axes[1].yaxis.set_major_formatter(PercentFormatter(1.0))
    
    # Add value labels on top of bars
    for i, v in enumerate(sat_df['zx_t_depth_reduction']):
        axes[1].text(i, v + 0.02, f"{v:.1%}", ha='center', va='bottom', fontsize=9)
    
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'case_study_sat.png'), dpi=300, bbox_inches='tight')
    plt.savefig(os.path.join(OUTPUT_DIR, 'case_study_sat.pdf'), bbox_inches='tight')
    plt.close()

def plot_case_study_tsp(df: pd.DataFrame):
    """
    Create a case study visualization for TSP problems.
    
    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame containing all benchmark data
    """
    # Filter for TSP problems (both Grover and QAOA)
    tsp_df = df[(df['category'] == 'TSP-Grover') | (df['category'] == 'TSP-QAOA')].copy()
    
    if len(tsp_df) == 0:
        print("No TSP problems found in the data.")
        return
    
    # Create figure with 2 subplots
    fig, axes = plt.subplots(1, 2, figsize=(15, 6))
    
    # Group by category and calculate mean improvements
    tsp_stats = tsp_df.groupby('category').agg({
        'transpiled_t_depth_reduction': 'mean',
        'transpiled_cnot_depth_reduction': 'mean',
        'transpiled_cnot_count_reduction': 'mean',
        'zx_t_depth_reduction': 'mean',
        'zx_cnot_depth_reduction': 'mean',
        'zx_cnot_count_reduction': 'mean',
        'num_qubits': 'mean'
    })
    
    # Plot T-depth reduction comparison
    x = np.arange(len(tsp_stats.index))
    width = 0.35
    
    axes[0].bar(x - width/2, tsp_stats['transpiled_t_depth_reduction'], width, 
                label='Standard Transpiler', color=COLORS[0], alpha=0.7)
    axes[0].bar(x + width/2, tsp_stats['zx_t_depth_reduction'], width, 
                label='ZX-Enhanced', color=COLORS[2], alpha=0.7)
    
    axes[0].set_title('T-Depth Reduction in TSP Problems')
    axes[0].set_xlabel('TSP Solution Approach')
    axes[0].set_ylabel('Reduction Percentage')
    axes[0].set_xticks(x)
    axes[0].set_xticklabels(tsp_stats.index)
    axes[0].legend()
    
    # Format y-axis as percentage
    axes[0].yaxis.set_major_formatter(PercentFormatter(1.0))
    
    # Plot CNOT metrics comparison
    metrics = ['CNOT-Depth', 'CNOT-Count']
    x = np.arange(len(metrics))
    
    for i, category in enumerate(tsp_stats.index):
        axes[1].bar(x - width/2 + i*width/len(tsp_stats), 
                    [tsp_stats.loc[category, 'zx_cnot_depth_reduction'], 
                     tsp_stats.loc[category, 'zx_cnot_count_reduction']], 
                    width/len(tsp_stats), label=category, alpha=0.7)
    
    axes[1].set_title('ZX-Enhanced CNOT Metrics in TSP Problems')
    axes[1].set_xlabel('Metric')
    axes[1].set_ylabel('Reduction Percentage')
    axes[1].set_xticks(x)
    axes[1].set_xticklabels(metrics)
    axes[1].legend()
    
    # Format y-axis as percentage
    axes[1].yaxis.set_major_formatter(PercentFormatter(1.0))
    
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'case_study_tsp.png'), dpi=300, bbox_inches='tight')
    plt.savefig(os.path.join(OUTPUT_DIR, 'case_study_tsp.pdf'), bbox_inches='tight')
    plt.close()

def main():
    """Main function to generate all paper diagrams."""
    # Ensure output directory exists
    ensure_output_dir()
    
    # Load data
    print("Loading benchmark data...")
    df = load_benchmark_data()
    print(f"Loaded {len(df)} circuits.")
    
    # Generate diagrams
    print("Generating paper diagrams...")
    
    print("1. Plotting T-depth reduction by category...")
    plot_t_depth_reduction_by_category(df)
    
    print("2. Plotting CNOT metrics comparison...")
    plot_cnot_metrics_comparison(df)
    
    print("3. Plotting optimization time vs. circuit size...")
    plot_optimization_time_vs_circuit_size(df)
    
    print("4. Plotting T-depth reduction distribution...")
    plot_t_depth_reduction_distribution(df)
    
    print("5. Plotting improvement radar chart...")
    plot_improvement_radar_chart(df)
    
    print("6. Plotting case study for SAT problems...")
    plot_case_study_sat(df)
    
    print("7. Plotting case study for TSP problems...")
    plot_case_study_tsp(df)
    
    print("All paper diagrams generated successfully!")

if __name__ == "__main__":
    main() 