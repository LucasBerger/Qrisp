import os
import json

def get_json_files(directory):
    """Get all JSON files in a directory."""
    json_files = []
    for filename in os.listdir(directory):
        if filename.endswith('.json'):
            json_files.append(filename)
    return json_files

def main():
    """Find missing files between results_01 and circuit_metrics directories."""
    results_dir = "../results_01"
    metrics_dir = "../circuit_metrics"
    
    # Get JSON files from both directories
    results_files = set(get_json_files(results_dir))
    metrics_files = set(get_json_files(metrics_dir))
    
    # Get base names (without extension)
    results_base_names = {os.path.splitext(f)[0] for f in results_files}
    metrics_base_names = {os.path.splitext(f)[0] for f in metrics_files}
    
    # Check if metrics files are just results files with "_metrics" appended
    metrics_without_suffix = {name.replace("_metrics", "") for name in metrics_base_names}
    
    # Find truly missing files
    missing_in_metrics = results_base_names - metrics_without_suffix
    
    # Print results
    print(f"Total JSON files in results_01: {len(results_files)}")
    print(f"Total JSON files in circuit_metrics: {len(metrics_files)}")
    
    # Check if all metrics files follow the pattern
    if metrics_without_suffix == results_base_names:
        print("\nAll files in circuit_metrics follow the pattern: [results_file]_metrics.json")
    else:
        print("\nNot all files follow the expected pattern.")
        
        print(f"\nNumber of truly missing files: {len(missing_in_metrics)}")
        if missing_in_metrics:
            print("\nMissing files (not in circuit_metrics even with suffix):")
            for name in sorted(missing_in_metrics):
                print(f"- {name}")
        
        # Check for files in circuit_metrics that don't correspond to results files
        extra_in_metrics = metrics_without_suffix - results_base_names
        if extra_in_metrics:
            print("\nFiles in circuit_metrics that don't correspond to results files:")
            for name in sorted(extra_in_metrics):
                print(f"- {name}")
    
    # Count files that are in results_01 but don't have corresponding metrics files
    missing_count = 0
    for result_file in results_base_names:
        if f"{result_file}_metrics" not in metrics_base_names:
            missing_count += 1
    
    print(f"\nNumber of files in results_01 without corresponding metrics files: {missing_count}")
    
    # Count files that are in circuit_metrics but don't have corresponding results files
    extra_count = 0
    for metric_file in metrics_base_names:
        base_name = metric_file.replace("_metrics", "")
        if base_name not in results_base_names:
            extra_count += 1
    
    print(f"Number of files in circuit_metrics without corresponding results files: {extra_count}")

if __name__ == "__main__":
    main() 