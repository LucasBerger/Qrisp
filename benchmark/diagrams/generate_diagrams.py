import os
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from load_data import load_benchmark_data, get_category_statistics, get_size_binned_statistics

# Set style for plots
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_context("paper", font_scale=1.5)
COLORS = sns.color_palette("viridis", 3)
OUTPUT_DIR = "output"

def ensure_output_dir():
    """Ensure the output directory exists."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)

def plot_improvement_by_category(df: pd.DataFrame):
    """
    Plot improvement metrics by circuit category.
    
    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame containing all benchmark data
    """
    # Get category statistics
    category_stats = get_category_statistics(df)
    
    # Prepare data for plotting
    categories = category_stats.index
    
    # Create figure with 3 subplots
    fig, axes = plt.subplots(1, 3, figsize=(18, 6), sharey=True)
    
    # Plot T-depth reduction
    axes[0].bar(categories, category_stats['transpiled_t_depth_reduction'], color=COLORS[0], alpha=0.7, label='Standard Transpiler')
    axes[0].bar(categories, category_stats['zx_t_depth_reduction'], color=COLORS[2], alpha=0.7, label='ZX-Enhanced')
    axes[0].set_title('T-Depth Reduction (%)')
    axes[0].set_ylabel('Reduction Percentage')
    axes[0].set_ylim(bottom=-0.5)  # Allow for negative values (as decimal)
    
    # Format y-axis as percentage
    from matplotlib.ticker import PercentFormatter
    axes[0].yaxis.set_major_formatter(PercentFormatter(1.0))
    
    # Plot CNOT-depth reduction
    axes[1].bar(categories, category_stats['transpiled_cnot_depth_reduction'], color=COLORS[0], alpha=0.7, label='Standard Transpiler')
    axes[1].bar(categories, category_stats['zx_cnot_depth_reduction'], color=COLORS[2], alpha=0.7, label='ZX-Enhanced')
    axes[1].set_title('CNOT-Depth Reduction (%)')
    axes[1].yaxis.set_major_formatter(PercentFormatter(1.0))
    
    # Plot CNOT-count reduction
    axes[2].bar(categories, category_stats['transpiled_cnot_count_reduction'], color=COLORS[0], alpha=0.7, label='Standard Transpiler')
    axes[2].bar(categories, category_stats['zx_cnot_count_reduction'], color=COLORS[2], alpha=0.7, label='ZX-Enhanced')
    axes[2].set_title('CNOT-Count Reduction (%)')
    axes[2].yaxis.set_major_formatter(PercentFormatter(1.0))
    
    # Add legend to the first subplot
    axes[0].legend(loc='upper right')
    
    # Rotate x-axis labels for better readability
    for ax in axes:
        ax.set_xticks(range(len(categories)))
        ax.set_xticklabels(categories, rotation=45, ha='right')
    
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'improvement_by_category.png'), dpi=300, bbox_inches='tight')
    plt.savefig(os.path.join(OUTPUT_DIR, 'improvement_by_category.pdf'), bbox_inches='tight')
    plt.close()

def plot_improvement_by_size(df: pd.DataFrame):
    """
    Plot improvement metrics by circuit size (number of qubits).
    
    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame containing all benchmark data
    """
    # Get size-binned statistics
    size_stats = get_size_binned_statistics(df)
    
    # Create figure with 3 subplots
    fig, axes = plt.subplots(1, 3, figsize=(18, 6), sharey=True)
    
    # Convert index to strings for plotting
    size_labels = size_stats.index.astype(str)
    
    # Plot T-depth reduction
    axes[0].bar(range(len(size_labels)), size_stats['transpiled_t_depth_reduction'], color=COLORS[0], alpha=0.7, label='Standard Transpiler')
    axes[0].bar(range(len(size_labels)), size_stats['zx_t_depth_reduction'], color=COLORS[2], alpha=0.7, label='ZX-Enhanced')
    axes[0].set_title('T-Depth Reduction by Circuit Size')
    axes[0].set_ylabel('Reduction Percentage')
    axes[0].set_ylim(bottom=-0.5)  # Allow for negative values (as decimal)
    
    # Format y-axis as percentage
    from matplotlib.ticker import PercentFormatter
    axes[0].yaxis.set_major_formatter(PercentFormatter(1.0))
    
    # Plot CNOT-depth reduction
    axes[1].bar(range(len(size_labels)), size_stats['transpiled_cnot_depth_reduction'], color=COLORS[0], alpha=0.7, label='Standard Transpiler')
    axes[1].bar(range(len(size_labels)), size_stats['zx_cnot_depth_reduction'], color=COLORS[2], alpha=0.7, label='ZX-Enhanced')
    axes[1].set_title('CNOT-Depth Reduction by Circuit Size')
    axes[1].yaxis.set_major_formatter(PercentFormatter(1.0))
    
    # Plot CNOT-count reduction
    axes[2].bar(range(len(size_labels)), size_stats['transpiled_cnot_count_reduction'], color=COLORS[0], alpha=0.7, label='Standard Transpiler')
    axes[2].bar(range(len(size_labels)), size_stats['zx_cnot_count_reduction'], color=COLORS[2], alpha=0.7, label='ZX-Enhanced')
    axes[2].set_title('CNOT-Count Reduction by Circuit Size')
    axes[2].yaxis.set_major_formatter(PercentFormatter(1.0))
    
    # Add legend to the first subplot
    axes[0].legend(loc='upper right')
    
    # Rotate x-axis labels for better readability
    for ax in axes:
        ax.set_xticks(range(len(size_labels)))
        ax.set_xticklabels(size_labels, rotation=45, ha='right')
        ax.set_xlabel('Number of Qubits')
    
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'improvement_by_size.png'), dpi=300, bbox_inches='tight')
    plt.savefig(os.path.join(OUTPUT_DIR, 'improvement_by_size.pdf'), bbox_inches='tight')
    plt.close()

def plot_optimization_time_vs_improvement(df: pd.DataFrame):
    """
    Plot optimization time vs. improvement metrics.
    
    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame containing all benchmark data
    """
    # Create figure with 3 subplots
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    
    # Plot optimization time vs. T-depth reduction
    sns.scatterplot(x='zx_optimization_time', y='zx_t_depth_reduction', 
                    hue='category', size='num_qubits', sizes=(20, 200),
                    data=df, ax=axes[0], alpha=0.7)
    axes[0].set_title('ZX Optimization Time vs. T-Depth Reduction')
    axes[0].set_xlabel('Optimization Time (s)')
    axes[0].set_ylabel('T-Depth Reduction')
    axes[0].set_xscale('log')
    
    # Format y-axis as percentage
    from matplotlib.ticker import PercentFormatter
    axes[0].yaxis.set_major_formatter(PercentFormatter(1.0))
    
    # Plot optimization time vs. CNOT-depth reduction
    sns.scatterplot(x='zx_optimization_time', y='zx_cnot_depth_reduction', 
                    hue='category', size='num_qubits', sizes=(20, 200),
                    data=df, ax=axes[1], alpha=0.7)
    axes[1].set_title('ZX Optimization Time vs. CNOT-Depth Reduction')
    axes[1].set_xlabel('Optimization Time (s)')
    axes[1].set_ylabel('CNOT-Depth Reduction')
    axes[1].set_xscale('log')
    axes[1].yaxis.set_major_formatter(PercentFormatter(1.0))
    
    # Plot optimization time vs. CNOT-count reduction
    sns.scatterplot(x='zx_optimization_time', y='zx_cnot_count_reduction', 
                    hue='category', size='num_qubits', sizes=(20, 200),
                    data=df, ax=axes[2], alpha=0.7)
    axes[2].set_title('ZX Optimization Time vs. CNOT-Count Reduction')
    axes[2].set_xlabel('Optimization Time (s)')
    axes[2].set_ylabel('CNOT-Count Reduction')
    axes[2].set_xscale('log')
    axes[2].yaxis.set_major_formatter(PercentFormatter(1.0))
    
    # Remove legend from the second and third subplots
    axes[1].get_legend().remove()
    axes[2].get_legend().remove()
    
    # Adjust legend position for the first subplot
    axes[0].legend(loc='upper left', bbox_to_anchor=(0, -0.15), ncol=3)
    
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'optimization_time_vs_improvement.png'), dpi=300, bbox_inches='tight')
    plt.savefig(os.path.join(OUTPUT_DIR, 'optimization_time_vs_improvement.pdf'), bbox_inches='tight')
    plt.close()

def plot_circuit_size_vs_improvement(df: pd.DataFrame):
    """
    Plot circuit size vs. improvement metrics.
    
    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame containing all benchmark data
    """
    # Create figure with 3 subplots
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    
    # Plot circuit size vs. T-depth reduction
    sns.scatterplot(x='num_qubits', y='zx_t_depth_reduction', 
                    hue='category', data=df, ax=axes[0], alpha=0.7)
    axes[0].set_title('Circuit Size vs. T-Depth Reduction')
    axes[0].set_xlabel('Number of Qubits')
    axes[0].set_ylabel('T-Depth Reduction')
    
    # Format y-axis as percentage
    from matplotlib.ticker import PercentFormatter
    axes[0].yaxis.set_major_formatter(PercentFormatter(1.0))
    
    # Plot circuit size vs. CNOT-depth reduction
    sns.scatterplot(x='num_qubits', y='zx_cnot_depth_reduction', 
                    hue='category', data=df, ax=axes[1], alpha=0.7)
    axes[1].set_title('Circuit Size vs. CNOT-Depth Reduction')
    axes[1].set_xlabel('Number of Qubits')
    axes[1].set_ylabel('CNOT-Depth Reduction')
    axes[1].yaxis.set_major_formatter(PercentFormatter(1.0))
    
    # Plot circuit size vs. CNOT-count reduction
    sns.scatterplot(x='num_qubits', y='zx_cnot_count_reduction', 
                    hue='category', data=df, ax=axes[2], alpha=0.7)
    axes[2].set_title('Circuit Size vs. CNOT-Count Reduction')
    axes[2].set_xlabel('Number of Qubits')
    axes[2].set_ylabel('CNOT-Count Reduction')
    axes[2].yaxis.set_major_formatter(PercentFormatter(1.0))
    
    # Remove legend from the second and third subplots
    axes[1].get_legend().remove()
    axes[2].get_legend().remove()
    
    # Adjust legend position for the first subplot
    axes[0].legend(loc='upper left', bbox_to_anchor=(0, -0.15), ncol=3)
    
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'circuit_size_vs_improvement.png'), dpi=300, bbox_inches='tight')
    plt.savefig(os.path.join(OUTPUT_DIR, 'circuit_size_vs_improvement.pdf'), bbox_inches='tight')
    plt.close()

def plot_comparative_boxplots(df: pd.DataFrame):
    """
    Plot boxplots comparing the distributions of improvement metrics.
    
    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame containing all benchmark data
    """
    # Create figure with 3 subplots
    fig, axes = plt.subplots(1, 3, figsize=(18, 6), sharey=True)
    
    # Prepare data for boxplots
    t_depth_data = pd.melt(df, id_vars=['name', 'category'], 
                           value_vars=['transpiled_t_depth_reduction', 'zx_t_depth_reduction'],
                           var_name='compiler', value_name='reduction')
    t_depth_data['compiler'] = t_depth_data['compiler'].map({
        'transpiled_t_depth_reduction': 'Standard',
        'zx_t_depth_reduction': 'ZX-Enhanced'
    })
    
    cnot_depth_data = pd.melt(df, id_vars=['name', 'category'], 
                             value_vars=['transpiled_cnot_depth_reduction', 'zx_cnot_depth_reduction'],
                             var_name='compiler', value_name='reduction')
    cnot_depth_data['compiler'] = cnot_depth_data['compiler'].map({
        'transpiled_cnot_depth_reduction': 'Standard',
        'zx_cnot_depth_reduction': 'ZX-Enhanced'
    })
    
    cnot_count_data = pd.melt(df, id_vars=['name', 'category'], 
                             value_vars=['transpiled_cnot_count_reduction', 'zx_cnot_count_reduction'],
                             var_name='compiler', value_name='reduction')
    cnot_count_data['compiler'] = cnot_count_data['compiler'].map({
        'transpiled_cnot_count_reduction': 'Standard',
        'zx_cnot_count_reduction': 'ZX-Enhanced'
    })
    
    # Plot boxplots
    sns.boxplot(x='category', y='reduction', hue='compiler', data=t_depth_data, ax=axes[0])
    axes[0].set_title('T-Depth Reduction Distribution')
    axes[0].set_xlabel('')
    axes[0].set_ylabel('Reduction Percentage')
    
    # Format y-axis as percentage
    from matplotlib.ticker import PercentFormatter
    axes[0].yaxis.set_major_formatter(PercentFormatter(1.0))
    
    sns.boxplot(x='category', y='reduction', hue='compiler', data=cnot_depth_data, ax=axes[1])
    axes[1].set_title('CNOT-Depth Reduction Distribution')
    axes[1].set_xlabel('')
    axes[1].set_ylabel('')
    axes[1].yaxis.set_major_formatter(PercentFormatter(1.0))
    
    sns.boxplot(x='category', y='reduction', hue='compiler', data=cnot_count_data, ax=axes[2])
    axes[2].set_title('CNOT-Count Reduction Distribution')
    axes[2].set_xlabel('')
    axes[2].set_ylabel('')
    axes[2].yaxis.set_major_formatter(PercentFormatter(1.0))
    
    # Remove legend from the second and third subplots
    axes[1].get_legend().remove()
    axes[2].get_legend().remove()
    
    # Rotate x-axis labels for better readability
    for ax in axes:
        # Get the current tick positions and labels
        positions = ax.get_xticks()
        labels = [item.get_text() for item in ax.get_xticklabels()]
        
        # Set the ticks and labels explicitly
        ax.set_xticks(positions)
        ax.set_xticklabels(labels, rotation=45, ha='right')
    
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'comparative_boxplots.png'), dpi=300, bbox_inches='tight')
    plt.savefig(os.path.join(OUTPUT_DIR, 'comparative_boxplots.pdf'), bbox_inches='tight')
    plt.close()

def plot_top_circuits(df: pd.DataFrame, metric: str, top_n: int = 5):
    """
    Plot top N and bottom N circuits with the highest/lowest improvement for a given metric.
    
    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame containing all benchmark data
    metric : str
        Metric to sort by ('t_depth', 'cnot_depth', or 'cnot_count')
    top_n : int
        Number of top/bottom circuits to show
    """
    # Sort by the specified metric
    if metric == 't_depth':
        sorted_df = df.sort_values(by='zx_over_normal_t_depth_reduction', ascending=False)
        metric_name = 'T-Depth'
        zx_over_normal_col = 'zx_over_normal_t_depth_reduction'
    elif metric == 'cnot_depth':
        sorted_df = df.sort_values(by='zx_over_normal_cnot_depth_reduction', ascending=False)
        metric_name = 'CNOT-Depth'
        zx_over_normal_col = 'zx_over_normal_cnot_depth_reduction'
    elif metric == 'cnot_count':
        sorted_df = df.sort_values(by='zx_over_normal_cnot_count_reduction', ascending=False)
        metric_name = 'CNOT-Count'
        zx_over_normal_col = 'zx_over_normal_cnot_count_reduction'
    else:
        raise ValueError(f"Unknown metric: {metric}")
    
    # Get top and bottom N circuits
    top_df = sorted_df.head(top_n)
    bottom_df = sorted_df.tail(top_n)
    
    # Create figure
    plt.figure(figsize=(15, 8))
    
    # Plot top N
    x_top = np.arange(len(top_df))
    width = 0.5
    
    plt.bar(x_top, top_df[zx_over_normal_col], width, color=COLORS[2], alpha=0.7)
    
    # Add gap with "..."
    gap = 1
    x_bottom = np.arange(len(top_df) + gap, len(top_df) + gap + len(bottom_df))
    
    plt.bar(x_bottom, bottom_df[zx_over_normal_col], width, color=COLORS[2], alpha=0.7)
    
    plt.xlabel('Circuit')
    plt.ylabel('Additional Reduction over Standard Transpiler')
    plt.title(f'Top and Bottom {top_n} Circuits by {metric_name} Reduction')
    
    # Set x-ticks and labels
    all_x = np.concatenate([x_top, x_bottom])
    all_names = list(top_df['name']) + list(bottom_df['name'])
    plt.xticks(all_x, all_names, rotation=45, ha='right')
    
    # Add "..." text between top and bottom groups
    plt.text(len(top_df) - 0.5, 0, '...', ha='center', va='center')
    # Format y-axis as percentage
    from matplotlib.ticker import PercentFormatter
    plt.gca().yaxis.set_major_formatter(PercentFormatter(1.0))
    
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, f'top_circuits_{metric}.png'), dpi=300, bbox_inches='tight')
    plt.savefig(os.path.join(OUTPUT_DIR, f'top_circuits_{metric}.pdf'), bbox_inches='tight')
    plt.close()

def plot_correlation_heatmap(df: pd.DataFrame):
    """
    Plot correlation heatmap between different metrics.
    
    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame containing all benchmark data
    """
    # Select columns for correlation
    cols = [
        'num_qubits',
        'non_transpiled_t_depth',
        'non_transpiled_cnot_depth',
        'non_transpiled_cnot_count',
        'transpiled_t_depth_reduction',
        'transpiled_cnot_depth_reduction',
        'transpiled_cnot_count_reduction',
        'zx_t_depth_reduction',
        'zx_cnot_depth_reduction',
        'zx_cnot_count_reduction',
        'zx_optimization_time'
    ]
    
    # Calculate correlation matrix
    corr = df[cols].corr()
    
    # Create figure
    plt.figure(figsize=(12, 10))
    
    # Plot heatmap
    sns.heatmap(corr, annot=True, cmap='coolwarm', fmt='.2f', linewidths=0.5)
    
    plt.title('Correlation Between Circuit Metrics')
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'correlation_heatmap.png'), dpi=300, bbox_inches='tight')
    plt.savefig(os.path.join(OUTPUT_DIR, 'correlation_heatmap.pdf'), bbox_inches='tight')
    plt.close()

def main():
    """Main function to generate all diagrams."""
    # Ensure output directory exists
    ensure_output_dir()
    
    # Load data
    print("Loading benchmark data...")
    df = load_benchmark_data()
    print(f"Loaded {len(df)} circuits.")
    
    # Generate diagrams
    print("Generating diagrams...")
    
    print("1. Plotting improvement by category...")
    plot_improvement_by_category(df)
    
    print("2. Plotting improvement by circuit size...")
    plot_improvement_by_size(df)
    
    print("3. Plotting optimization time vs. improvement...")
    plot_optimization_time_vs_improvement(df)
    
    print("4. Plotting circuit size vs. improvement...")
    plot_circuit_size_vs_improvement(df)
    
    print("5. Plotting comparative boxplots...")
    plot_comparative_boxplots(df)
    
    print("6. Plotting top circuits for T-depth reduction...")
    plot_top_circuits(df, 't_depth')
    
    print("7. Plotting top circuits for CNOT-depth reduction...")
    plot_top_circuits(df, 'cnot_depth')
    
    print("8. Plotting top circuits for CNOT-count reduction...")
    plot_top_circuits(df, 'cnot_count')
    
    print("9. Plotting correlation heatmap...")
    plot_correlation_heatmap(df)
    
    print("All diagrams generated successfully!")

if __name__ == "__main__":
    main() 