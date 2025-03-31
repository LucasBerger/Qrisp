import os
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from load_data import load_benchmark_data, get_category_statistics, categorize_circuit
from matplotlib.ticker import PercentFormatter, ScalarFormatter
import matplotlib.gridspec as gridspec
import json

# Set style for plots
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_context("paper", font_scale=1.5)
COLORS = sns.color_palette("viridis", 3)
OUTPUT_DIR = "comparison_output"

def ensure_output_dir():
    """Ensure the output directory exists."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)

def plot_absolute_metrics_comparison(df: pd.DataFrame):
    """
    Create a plot comparing absolute metrics (T-depth, CNOT-depth, CNOT-count) 
    between non-transpiled, normal Qrisp compiler, and ZX-enhanced compiler.
    
    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame containing all benchmark data
    """
    # Calculate mean values for each metric across all circuits
    metrics = {
        'T-Depth': {
            'Non-Transpiled': df['non_transpiled_t_depth'].mean(),
            'Normal Qrisp': df['transpiled_t_depth'].mean(),
            'ZX-Enhanced': df['zx_t_depth'].mean()
        },
        'CNOT-Depth': {
            'Non-Transpiled': df['non_transpiled_cnot_depth'].mean(),
            'Normal Qrisp': df['transpiled_cnot_depth'].mean(),
            'ZX-Enhanced': df['zx_cnot_depth'].mean()
        },
        'CNOT-Count': {
            'Non-Transpiled': df['non_transpiled_cnot_count'].mean(),
            'Normal Qrisp': df['transpiled_cnot_count'].mean(),
            'ZX-Enhanced': df['zx_cnot_count'].mean()
        }
    }
    
    # Create figure with 3 subplots
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    
    # Plot each metric
    for i, (metric, values) in enumerate(metrics.items()):
        compilers = list(values.keys())
        metric_values = list(values.values())
        
        # Create bar plot
        bars = axes[i].bar(compilers, metric_values, color=[COLORS[0], COLORS[1], COLORS[2]], alpha=0.7)
        
        # Add value labels on top of bars
        for bar in bars:
            height = bar.get_height()
            axes[i].text(bar.get_x() + bar.get_width()/2., height + 0.1*height,
                        f'{int(height)}', ha='center', va='bottom', fontsize=10)
        
        # Set title and labels
        axes[i].set_title(f'Average {metric}')
        axes[i].set_ylabel('Count')
        
        # Use log scale for better visualization
        axes[i].set_yscale('log')
        
        # Format y-axis with actual numbers instead of scientific notation
        axes[i].yaxis.set_major_formatter(ScalarFormatter())
        
        # Set x-ticks and then set the labels with rotation
        axes[i].set_xticks(range(len(compilers)))
        axes[i].set_xticklabels(compilers, rotation=45, ha='right')
    
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'absolute_metrics_comparison.png'), dpi=300, bbox_inches='tight')
    plt.savefig(os.path.join(OUTPUT_DIR, 'absolute_metrics_comparison.pdf'), bbox_inches='tight')
    plt.close()

def plot_relative_improvement_by_category(df: pd.DataFrame):
    """
    Create a plot showing the relative improvement of ZX-enhanced compiler over normal Qrisp compiler
    for each category.
    
    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame containing all benchmark data
    """
    # Calculate relative improvement for each circuit
    df['relative_t_depth_improvement'] = df['zx_over_normal_t_depth_reduction']
    df['relative_cnot_depth_improvement'] = df['zx_over_normal_cnot_depth_reduction']
    df['relative_cnot_count_improvement'] = df['zx_over_normal_cnot_count_reduction']
    
    # Group by category and calculate mean relative improvement
    category_stats = df.groupby('category').agg({
        'relative_t_depth_improvement': 'mean',
        'relative_cnot_depth_improvement': 'mean',
        'relative_cnot_count_improvement': 'mean'
    })
    
    # Reorder the categories
    category_order = ['Standard', 'SAT', 'TSP-Grover', 'TSP-QAOA']
    category_stats = category_stats.reindex(category_order)
    
    # Create figure with 3 subplots
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    
    # Plot relative improvement for each metric
    metrics = ['relative_t_depth_improvement', 'relative_cnot_depth_improvement', 'relative_cnot_count_improvement']
    titles = ['T-Depth', 'CNOT-Depth', 'CNOT-Count']
    
    for i, (metric, title) in enumerate(zip(metrics, titles)):
        # Create bar plot
        bars = axes[i].bar(category_stats.index, category_stats[metric], color=COLORS[2], alpha=0.7)
        
        # Add value labels on top of bars
        for bar in bars:
            height = bar.get_height()
            if height >= 0:
                va = 'bottom'
                y_pos = height + 0.01
            else:
                va = 'top'
                y_pos = height - 0.01
            axes[i].text(bar.get_x() + bar.get_width()/2., y_pos,
                        f'{height:.1%}', ha='center', va=va, fontsize=10)
        
        # Set title and labels
        axes[i].set_title(f'ZX vs. Normal: {title} Improvement')
        axes[i].set_ylabel('Relative Improvement')
        
        # Format y-axis as percentage
        axes[i].yaxis.set_major_formatter(PercentFormatter(1.0))
        
        # Add reference line at y=0
        axes[i].axhline(y=0, color='gray', linestyle='--', alpha=0.5)
        
        # Set x-ticks and then set the labels with rotation
        axes[i].set_xticks(range(len(category_stats.index)))
        axes[i].set_xticklabels(category_stats.index, rotation=45, ha='right')
    
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'relative_improvement_by_category.png'), dpi=300, bbox_inches='tight')
    plt.savefig(os.path.join(OUTPUT_DIR, 'relative_improvement_by_category.pdf'), bbox_inches='tight')
    plt.close()

def plot_category_specific_metrics(df: pd.DataFrame, category: str):
    """
    Create detailed plots for a specific category.
    
    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame containing all benchmark data
    category : str
        Category to analyze
    """
    # Filter data for the specified category
    category_df = df[df['category'] == category].copy()
    
    if len(category_df) == 0:
        print(f"No circuits found for category: {category}")
        return
    
    # Sort by circuit name for consistency
    category_df = category_df.sort_values('name')
    
    # Create figure with 3 subplots
    fig = plt.figure(figsize=(15, 10))
    gs = gridspec.GridSpec(2, 2, height_ratios=[1, 1.5])
    
    # 1. Plot average metrics for this category
    ax1 = fig.add_subplot(gs[0, 0])
    
    # Calculate mean values for each metric
    metrics = {
        'T-Depth': [
            category_df['non_transpiled_t_depth'].mean(),
            category_df['transpiled_t_depth'].mean(),
            category_df['zx_t_depth'].mean()
        ],
        'CNOT-Depth': [
            category_df['non_transpiled_cnot_depth'].mean(),
            category_df['transpiled_cnot_depth'].mean(),
            category_df['zx_cnot_depth'].mean()
        ],
        'CNOT-Count': [
            category_df['non_transpiled_cnot_count'].mean(),
            category_df['transpiled_cnot_count'].mean(),
            category_df['zx_cnot_count'].mean()
        ]
    }
    
    # Create a grouped bar plot
    x = np.arange(len(metrics))
    width = 0.25
    
    ax1.bar(x - width, [metrics[m][0] for m in metrics], width, label='Non-Transpiled', color=COLORS[0], alpha=0.7)
    ax1.bar(x, [metrics[m][1] for m in metrics], width, label='Normal Qrisp', color=COLORS[1], alpha=0.7)
    ax1.bar(x + width, [metrics[m][2] for m in metrics], width, label='ZX-Enhanced', color=COLORS[2], alpha=0.7)
    
    ax1.set_yscale('log')
    ax1.set_ylabel('Count (log scale)')
    ax1.set_xticks(x)
    ax1.set_xticklabels(list(metrics.keys()))
    ax1.set_title(f'Average Metrics for {category} Circuits')
    ax1.legend()
    
    # 2. Plot average reduction percentages
    ax2 = fig.add_subplot(gs[0, 1])
    
    # Calculate mean reduction percentages
    reductions = {
        'T-Depth': [
            category_df['transpiled_t_depth_reduction'].mean(),
            category_df['zx_t_depth_reduction'].mean()
        ],
        'CNOT-Depth': [
            category_df['transpiled_cnot_depth_reduction'].mean(),
            category_df['zx_cnot_depth_reduction'].mean()
        ],
        'CNOT-Count': [
            category_df['transpiled_cnot_count_reduction'].mean(),
            category_df['zx_cnot_count_reduction'].mean()
        ]
    }
    
    # Create a grouped bar plot
    x = np.arange(len(reductions))
    width = 0.35
    
    ax2.bar(x - width/2, [reductions[m][0] for m in reductions], width, label='Normal Qrisp', color=COLORS[1], alpha=0.7)
    ax2.bar(x + width/2, [reductions[m][1] for m in reductions], width, label='ZX-Enhanced', color=COLORS[2], alpha=0.7)
    
    ax2.yaxis.set_major_formatter(PercentFormatter(1.0))
    ax2.set_ylabel('Reduction Percentage')
    ax2.set_xticks(x)
    ax2.set_xticklabels(list(reductions.keys()))
    ax2.set_title(f'Average Reduction for {category} Circuits')
    ax2.legend()
    
    # 3. Plot circuit-specific comparison
    ax3 = fig.add_subplot(gs[1, :])
    
    # Limit to top 10 circuits by name length if there are too many
    if len(category_df) > 10:
        if category == 'Standard':
            # Group by first 4 letters and take first circuit from each group
            # First remove GHZ circuits
            filtered_df = category_df[~category_df['name'].str.startswith('GHZ')]
            
            # Group by first 4 letters and get bucket sizes
            groups = filtered_df.groupby(filtered_df['name'].str[:4])
            bucket_sizes = groups.size()
            
            # For each group, get the middle circuit
            middle_circuits = []
            for name_prefix, group in groups:
                sorted_group = group.sort_values('name')
                middle_idx = len(sorted_group) // 2
                middle_circuit = sorted_group.iloc[middle_idx].copy()
                middle_circuit['bucket_size'] = bucket_sizes[name_prefix]
                middle_circuits.append(middle_circuit)
                
            # Convert to DataFrame, sort by bucket size descending, and take top 10
            category_df = pd.DataFrame(middle_circuits).sort_values(
                by='bucket_size', ascending=False
            ).head(10)
        else:
            # Group by number of qubits
            groups = category_df.groupby('num_qubits')
            
            # Get all circuits in interleaved order
            interleaved_circuits = []
            max_per_group = max(len(group) for _, group in groups)
            
            for i in range(max_per_group):
                for _, group in groups:
                    if i < len(group):
                        interleaved_circuits.append(group.iloc[i])
                        
            # Convert to DataFrame and take top 10
            category_df = pd.DataFrame(interleaved_circuits).head(10)
    
    # Prepare data for plotting
    circuit_names = category_df['name'].tolist()
    x = np.arange(len(circuit_names))
    width = 0.3
    
    # Plot reduction percentages
    ax3.bar(x - width, category_df['zx_over_normal_t_depth_reduction'], width, label='T-Depth Reduction', color=COLORS[0], alpha=0.7)
    ax3.bar(x, category_df['zx_over_normal_cnot_depth_reduction'], width, label='CNOT-Depth Reduction', color=COLORS[2], alpha=0.7)
    
    ax3.set_ylabel('Reduction Percentage')
    ax3.set_xticks(x)
    ax3.set_xticklabels(circuit_names, rotation=45, ha='right')
    ax3.set_title(f'Circuit-Specific Comparison for {category}')
    ax3.yaxis.set_major_formatter(PercentFormatter(1.0))
    ax3.legend()
    
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, f'category_{category.lower()}.png'), dpi=300, bbox_inches='tight')
    plt.savefig(os.path.join(OUTPUT_DIR, f'category_{category.lower()}.pdf'), bbox_inches='tight')
    plt.close()

def plot_optimization_time_analysis(df: pd.DataFrame):
    """
    Create plots analyzing the optimization time of the ZX-enhanced compiler.
    
    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame containing all benchmark data
    """
    # Create figure with 2 subplots
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))
    
    # Load total gate counts from circuit metrics files
    metrics_dir = "../circuit_metrics"
    total_gates_dict = {}
    
    # Iterate through metrics files to get total gate counts
    for filename in os.listdir(metrics_dir):
        if not filename.endswith('.json'):
            continue
            
        # Extract circuit name from filename (remove _metrics.json)
        circuit_name = filename.replace('_metrics.json', '')
        
        try:
            with open(os.path.join(metrics_dir, filename), 'r') as f:
                metrics = json.load(f)
                
            # Calculate total gates from transpiled operation counts
            if 'transpiled_operation_counts' in metrics:
                total_gates = sum(metrics['transpiled_operation_counts'].values())
                total_gates_dict[circuit_name] = total_gates
        except Exception as e:
            print(f"Error processing {filename}: {e}")
    
    # Add total gates to the dataframe
    df['total_gates'] = df['name'].map(total_gates_dict)
    
    # If some circuits don't have metrics files, use CNOT count as fallback
    missing_total_gates = df['total_gates'].isna()
    if missing_total_gates.any():
        missing_circuits = df.loc[missing_total_gates, 'name'].tolist()
        print(f"Warning: {missing_total_gates.sum()} circuits don't have metrics files: {missing_circuits}. Using CNOT count as fallback.")
        df.loc[missing_total_gates, 'total_gates'] = df.loc[missing_total_gates, 'non_transpiled_cnot_count']
    
    # 1. Plot optimization time vs. qubit count by category
    sns.scatterplot(x='num_qubits', y='zx_optimization_time', 
                    hue='category', size='total_gates',
                    sizes=(20, 200), alpha=0.7, data=df, ax=axes[0])
    
    # Add regression line for qubit count
    x1 = df['num_qubits']
    y = df['zx_optimization_time']
    z1 = np.polyfit(x1, np.log(y), 1)
    p1 = np.poly1d(z1)
    axes[0].plot(x1, np.exp(p1(x1)), "r--", alpha=0.7)
    
    axes[0].set_yscale('log')
    axes[0].set_xlabel('Number of Qubits')
    axes[0].set_ylabel('ZX Optimization Time (s)')
    axes[0].set_title('Optimization Time vs. Circuit Size (Qubits)')
    
    # Update legend label for first subplot
    legend1 = axes[0].get_legend()
    handles1 = legend1.legend_handles
    labels1 = [t.get_text() for t in legend1.get_texts()]
    labels1 = ['Category' if l == 'category' else 'Total Gates' if l == 'total_gates' else l for l in labels1]
    axes[0].legend(handles1, labels1)
    
    # 2. Plot optimization time vs. total gate count by category
    sns.scatterplot(x='total_gates', y='zx_optimization_time', 
                    hue='category', size='num_qubits',
                    sizes=(20, 200), alpha=0.7, data=df, ax=axes[1])
    
    # Add regression line for gate count
    x2 = df['total_gates']
    z2 = np.polyfit(np.log(x2), np.log(y), 1)
    p2 = np.poly1d(z2)
    # Use logarithmically spaced points for smoother curve on log scale
    x2_range = np.logspace(np.log10(x2.min()), np.log10(x2.max()), 100)
    axes[1].plot(x2_range, np.exp(p2(np.log(x2_range))), "r--", alpha=0.7)
    
    axes[1].set_xscale('log')
    axes[1].set_yscale('log')
    axes[1].set_xlabel('Total Gate Count')
    axes[1].set_ylabel('ZX Optimization Time (s)')
    axes[1].set_title('Optimization Time vs. Circuit Complexity (Gates)')
    
    # Update legend label for second subplot
    legend2 = axes[1].get_legend()
    handles2 = legend2.legend_handles
    labels2 = [t.get_text() for t in legend2.get_texts()]
    labels2 = ['Category' if l == 'category' else 'Number of Qubits' if l == 'num_qubits' else l for l in labels2]
    axes[1].legend(handles2, labels2)
    
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'optimization_time_analysis.png'), dpi=300, bbox_inches='tight')
    plt.savefig(os.path.join(OUTPUT_DIR, 'optimization_time_analysis.pdf'), bbox_inches='tight')
    plt.close()

def plot_circuit_complexity_vs_improvement(df: pd.DataFrame):
    """
    Create plots analyzing how circuit complexity affects improvement.
    
    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame containing all benchmark data
    """
    # Create figure with 2 subplots
    fig, axes = plt.subplots(1, 2, figsize=(15, 6))
    
    # 1. Plot CNOT count vs. T-depth reduction
    sns.scatterplot(x='non_transpiled_cnot_count', y='zx_t_depth_reduction', 
                    hue='category', size='num_qubits',
                    sizes=(20, 200), alpha=0.7, data=df, ax=axes[0])
    
    axes[0].set_xscale('log')
    axes[0].set_xlabel('Original CNOT Count (log scale)')
    axes[0].set_ylabel('T-Depth Reduction')
    axes[0].yaxis.set_major_formatter(PercentFormatter(1.0))
    axes[0].set_title('Circuit Complexity vs. T-Depth Reduction')
    
    # 2. Plot T-depth vs. CNOT count reduction
    sns.scatterplot(x='non_transpiled_t_depth', y='zx_cnot_count_reduction', 
                    hue='category', size='num_qubits',
                    sizes=(20, 200), alpha=0.7, data=df, ax=axes[1])
    
    axes[1].set_xscale('log')
    axes[1].set_xlabel('Original T-Depth (log scale)')
    axes[1].set_ylabel('CNOT Count Reduction')
    axes[1].yaxis.set_major_formatter(PercentFormatter(1.0))
    axes[1].set_title('Circuit Complexity vs. CNOT Count Reduction')
    
    # Remove legend from the second subplot
    axes[1].get_legend().remove()
    
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'circuit_complexity_vs_improvement.png'), dpi=300, bbox_inches='tight')
    plt.savefig(os.path.join(OUTPUT_DIR, 'circuit_complexity_vs_improvement.pdf'), bbox_inches='tight')
    plt.close()

def plot_improvement_distribution(df: pd.DataFrame):
    """
    Create plots showing the distribution of improvements.
    
    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame containing all benchmark data
    """
    # Create figure with 3 subplots
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    
    # 1. Plot T-depth reduction distribution
    sns.kdeplot(data=df, x='transpiled_t_depth_reduction', label='Normal Qrisp', ax=axes[0], color=COLORS[1], fill=True, alpha=0.3)
    sns.kdeplot(data=df, x='zx_t_depth_reduction', label='ZX-Enhanced', ax=axes[0], color=COLORS[2], fill=True, alpha=0.3)
    
    axes[0].set_xlabel('T-Depth Reduction')
    axes[0].set_ylabel('Density')
    axes[0].set_title('T-Depth Reduction Distribution')
    axes[0].xaxis.set_major_formatter(PercentFormatter(1.0))
    
    # 2. Plot CNOT-depth reduction distribution
    sns.kdeplot(data=df, x='transpiled_cnot_depth_reduction', label='Normal Qrisp', ax=axes[1], color=COLORS[1], fill=True, alpha=0.3)
    sns.kdeplot(data=df, x='zx_cnot_depth_reduction', label='ZX-Enhanced', ax=axes[1], color=COLORS[2], fill=True, alpha=0.3)
    
    axes[1].set_xlabel('CNOT-Depth Reduction')
    axes[1].set_ylabel('Density')
    axes[1].set_title('CNOT-Depth Reduction Distribution')
    axes[1].xaxis.set_major_formatter(PercentFormatter(1.0))
    
    # 3. Plot CNOT-count reduction distribution
    sns.kdeplot(data=df, x='transpiled_cnot_count_reduction', label='Normal Qrisp', ax=axes[2], color=COLORS[1], fill=True, alpha=0.3)
    sns.kdeplot(data=df, x='zx_cnot_count_reduction', label='ZX-Enhanced', ax=axes[2], color=COLORS[2], fill=True, alpha=0.3)
    
    axes[2].set_xlabel('CNOT-Count Reduction')
    axes[2].set_ylabel('Density')
    axes[2].set_title('CNOT-Count Reduction Distribution')
    axes[2].xaxis.set_major_formatter(PercentFormatter(1.0))
    
    # Remove legend from the second and third subplots if they exist
    for i in [1, 2]:
        legend = axes[i].get_legend()
        if legend is not None:
            legend.remove()
    
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'improvement_distribution.png'), dpi=300, bbox_inches='tight')
    plt.savefig(os.path.join(OUTPUT_DIR, 'improvement_distribution.pdf'), bbox_inches='tight')
    plt.close()

def main():
    """Main function to generate all comparison diagrams."""
    # Ensure output directory exists
    ensure_output_dir()
    
    # Load data
    print("Loading benchmark data...")
    df = load_benchmark_data()
    print(f"Loaded {len(df)} circuits.")
    
    # Generate diagrams
    print("Generating comparison diagrams...")
    
    print("1. Plotting absolute metrics comparison...")
    plot_absolute_metrics_comparison(df)
    
    print("2. Plotting relative improvement by category...")
    plot_relative_improvement_by_category(df)
    
    print("3. Plotting category-specific metrics...")
    for category in ['Standard', 'SAT', 'TSP-Grover', 'TSP-QAOA']:
        print(f"   - {category}...")
        plot_category_specific_metrics(df, category)
    
    print("4. Plotting optimization time analysis...")
    plot_optimization_time_analysis(df)
    
    print("5. Plotting circuit complexity vs. improvement...")
    plot_circuit_complexity_vs_improvement(df)
    
    print("6. Plotting improvement distribution...")
    plot_improvement_distribution(df)
    
    print("All comparison diagrams generated successfully!")

if __name__ == "__main__":
    main() 