import os
import json
from typing import Dict, List, Optional, Any
from qrisp import QuantumCircuit, QuantumVariable, QuantumSession
from qrisp.config import setup_logging, activate_zx_optimization, deactivate_zx_optimization
from qrisp.misc.utility import t_depth_indicator, cnot_depth_indicator
import logging
import time
import argparse

def load_qasm_circuits(directory: str, specific_file: Optional[str] = None) -> Dict[str, QuantumCircuit]:
    """
    Load QASM files from the specified directory.
    
    Parameters
    ----------
    directory : str
        Directory containing QASM files
    specific_file : str, optional
        If provided, only load this specific QASM file
        
    Returns
    -------
    Dict[str, QuantumCircuit]
        Dictionary mapping filenames to quantum circuits
    """
    circuits: Dict[str, QuantumCircuit] = {}
    
    if specific_file:
        # Load only the specified file
        if not specific_file.endswith('.qasm'):
            specific_file += '.qasm'
        path = os.path.join(directory, specific_file)
        if not os.path.exists(path):
            raise FileNotFoundError(f"QASM file not found: {path}")
        try:
            qc = QuantumCircuit.from_qasm_file(path)
            circuits[specific_file] = qc
        except Exception as e:
            logging.error(f"Failed to load {specific_file}: {str(e)}")
            raise
    else:
        # Load all QASM files in directory
        for filename in os.listdir(directory):
            if filename.endswith('.qasm'):
                path = os.path.join(directory, filename)
                try:
                    qc = QuantumCircuit.from_qasm_file(path)
                    circuits[filename] = qc
                except Exception as e:
                    logging.error(f"Failed to load {filename}: {str(e)}")
    
    return circuits

def benchmark_circuit(qc: QuantumCircuit, name: str) -> Dict[str, Any]:
    """Run benchmarks on a single circuit."""
    # Create quantum session and variables
    qs = QuantumSession()
    num_qubits = qc.num_qubits()
    qv = QuantumVariable(num_qubits, qs=qs)
    
    # Convert circuit to gate and apply it
    gate = qc.to_gate()
    qs.append(gate, qv)
    
    # Skip measurements for large circuits
    should_measure = num_qubits < 30
    
    # Calculate non-transpiled depths
    results: Dict[str, Any] = {
        "name": name,
        "non_transpiled": {
            "t_depth": qs.depth(depth_indicator=lambda op: t_depth_indicator(op, epsilon=2**-10), transpile=False),
            "cnot_depth": qs.depth(depth_indicator=cnot_depth_indicator, transpile=False),
            "cnot_count": qs.cnot_count(),
            "num_qubits": qs.num_qubits(),
            "operation_counts": qs.count_ops()
        }
    }
    
    if should_measure:
        results["non_transpiled"]["probabilities"] = qv.get_measurement(compile=False)
    
    # Calculate transpiled depths (without ZX)
    transpiled_qs = qs.compile(
        compile_mcm=True,
        workspace=0
    )
    
    results["transpiled"] = {
        "t_depth": transpiled_qs.depth(depth_indicator=lambda op: t_depth_indicator(op, epsilon=2**-10), transpile=False),
        "cnot_depth": transpiled_qs.depth(depth_indicator=cnot_depth_indicator, transpile=False),
        "cnot_count": transpiled_qs.cnot_count(),
        "num_qubits": transpiled_qs.num_qubits(),
        "operation_counts": transpiled_qs.count_ops()
    }
    
    if should_measure:
        results["transpiled"]["probabilities"] = qv.get_measurement(precompiled_qc=transpiled_qs)
    
    # Compile with ZX optimization enabled
    start_time = time.time()
    activate_zx_optimization()
    optimized_qs = qs.compile(
        compile_mcm=False,
        workspace=0
    )
    deactivate_zx_optimization()  # Reset to default state
    optimization_time = time.time() - start_time
    
    results["zx_optimized"] = {
        "t_depth": optimized_qs.depth(depth_indicator=lambda op: t_depth_indicator(op, epsilon=2**-10), transpile=False),
        "cnot_depth": optimized_qs.depth(depth_indicator=cnot_depth_indicator, transpile=False),
        "cnot_count": optimized_qs.cnot_count(),
        "num_qubits": optimized_qs.num_qubits(),
        "operation_counts": optimized_qs.count_ops(),
        "optimization_time": optimization_time
    }
    
    if should_measure:
        results["zx_optimized"]["probabilities"] = qv.get_measurement(precompiled_qc=optimized_qs)
    
    # Calculate improvements
    results["improvements"] = {
        "transpiled": {
            "t_depth_reduction": (results["non_transpiled"]["t_depth"] - results["transpiled"]["t_depth"]) / results["non_transpiled"]["t_depth"] * 100 if results["non_transpiled"]["t_depth"] > 0 else 0,
            "cnot_depth_reduction": (results["non_transpiled"]["cnot_depth"] - results["transpiled"]["cnot_depth"]) / results["non_transpiled"]["cnot_depth"] * 100 if results["non_transpiled"]["cnot_depth"] > 0 else 0,
            "cnot_count_reduction": (results["non_transpiled"]["cnot_count"] - results["transpiled"]["cnot_count"]) / results["non_transpiled"]["cnot_count"] * 100 if results["non_transpiled"]["cnot_count"] > 0 else 0
        },
        "zx": {
            "t_depth_reduction": (results["non_transpiled"]["t_depth"] - results["zx_optimized"]["t_depth"]) / results["non_transpiled"]["t_depth"] * 100 if results["non_transpiled"]["t_depth"] > 0 else 0,
            "cnot_depth_reduction": (results["non_transpiled"]["cnot_depth"] - results["zx_optimized"]["cnot_depth"]) / results["non_transpiled"]["cnot_depth"] * 100 if results["non_transpiled"]["cnot_depth"] > 0 else 0,
            "cnot_count_reduction": (results["non_transpiled"]["cnot_count"] - results["zx_optimized"]["cnot_count"]) / results["non_transpiled"]["cnot_count"] * 100 if results["non_transpiled"]["cnot_count"] > 0 else 0
        }
    }
    
    # Check if probabilities match across all versions only if measurements were taken
    if should_measure:
        def normalize_probs(probs: Dict[str, int]) -> Dict[str, float]:
            return {str(k): float(v)/100000 for k, v in probs.items()}
        
        prob_original = normalize_probs(results["non_transpiled"]["probabilities"])
        prob_transpiled = normalize_probs(results["transpiled"]["probabilities"])
        prob_zx = normalize_probs(results["zx_optimized"]["probabilities"])
        
        results["probability_matches"] = {
            "transpiled_matches_original": prob_original == prob_transpiled,
            "zx_matches_original": prob_original == prob_zx
        }
        
        if not all(results["probability_matches"].values()):
            results["probability_differences"] = {
                "transpiled": {
                    "in_original_only": list(set(prob_original.keys()) - set(prob_transpiled.keys())),
                    "in_transpiled_only": list(set(prob_transpiled.keys()) - set(prob_original.keys())),
                    "value_differences": {
                        k: (prob_original.get(k), prob_transpiled.get(k))
                        for k in set(prob_original.keys()) & set(prob_transpiled.keys())
                        if abs(prob_original[k] - prob_transpiled[k]) > 1e-2
                    }
                },
                "zx": {
                    "in_original_only": list(set(prob_original.keys()) - set(prob_zx.keys())),
                    "in_zx_only": list(set(prob_zx.keys()) - set(prob_original.keys())),
                    "value_differences": {
                        k: (prob_original.get(k), prob_zx.get(k))
                        for k in set(prob_original.keys()) & set(prob_zx.keys())
                        if abs(prob_original[k] - prob_zx[k]) > 1e-2
                    }
                }
            }
    else:
        results["probability_matches"] = {
            "transpiled_matches_original": None,
            "zx_matches_original": None,
            "skipped_due_to_size": True
        }
    
    return results

def run_benchmarks(specific_file: Optional[str] = None) -> None:
    """
    Run benchmarks on quantum circuits.
    
    Parameters
    ----------
    specific_file : str, optional
        If provided, only benchmark this specific QASM file
    """
    # Set up logging
    setup_logging(level=logging.DEBUG)
    logger = logging.getLogger(__name__)
    
    # Load circuits
    circuits_dir = os.path.join("benchmark", "circuits")
    try:
        circuits = load_qasm_circuits(circuits_dir, specific_file)
    except FileNotFoundError as e:
        logger.error(str(e))
        return
    
    if not circuits:
        logger.error("No circuits loaded for benchmarking")
        return
    
    logger.info(f"Loaded {len(circuits)} circuits for benchmarking")
    
    # Run benchmarks
    results: List[Dict[str, Any]] = []
    for name, circuit in circuits.items():
        logger.info(f"Benchmarking circuit: {name}")
        try:
            result = benchmark_circuit(circuit, name)
            results.append(result)
            logger.info(f"Completed benchmark for {name}")
            logger.info("Transpiler improvements:")
            logger.info(f"  T-depth reduction: {result['improvements']['transpiled']['t_depth_reduction']:.2f}%")
            logger.info(f"  CNOT-depth reduction: {result['improvements']['transpiled']['cnot_depth_reduction']:.2f}%")
            logger.info(f"  CNOT-count reduction: {result['improvements']['transpiled']['cnot_count_reduction']:.2f}%")
            logger.info("ZX-optimization improvements:")
            logger.info(f"  T-depth reduction: {result['improvements']['zx']['t_depth_reduction']:.2f}%")
            logger.info(f"  CNOT-depth reduction: {result['improvements']['zx']['cnot_depth_reduction']:.2f}%")
            logger.info(f"  CNOT-count reduction: {result['improvements']['zx']['cnot_count_reduction']:.2f}%")
            logger.info(f"Probability distributions match: {result['probability_matches']}")
        except Exception as e:
            logger.error(f"Failed to benchmark {name}: {str(e)}")
    
    # Save results
    output_file = os.path.join("benchmark", "results.json")
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Results saved to {output_file}")
    
    # Print summary
    print("\nBenchmark Summary:")
    print("-----------------")
    for result in results:
        print(f"\nCircuit: {result['name']}")
        print("\nNon-transpiled metrics:")
        print(f"  T-depth: {result['non_transpiled']['t_depth']}")
        print(f"  CNOT-depth: {result['non_transpiled']['cnot_depth']}")
        print(f"  CNOT-count: {result['non_transpiled']['cnot_count']}")
        print("\nTranspiled metrics:")
        print(f"  T-depth: {result['transpiled']['t_depth']}")
        print(f"  CNOT-depth: {result['transpiled']['cnot_depth']}")
        print(f"  CNOT-count: {result['transpiled']['cnot_count']}")
        print(f"  Improvements:")
        print(f"    T-depth reduction: {result['improvements']['transpiled']['t_depth_reduction']:.2f}%")
        print(f"    CNOT-depth reduction: {result['improvements']['transpiled']['cnot_depth_reduction']:.2f}%")
        print(f"    CNOT-count reduction: {result['improvements']['transpiled']['cnot_count_reduction']:.2f}%")
        print("\nZX-optimized metrics:")
        print(f"  T-depth: {result['zx_optimized']['t_depth']}")
        print(f"  CNOT-depth: {result['zx_optimized']['cnot_depth']}")
        print(f"  CNOT-count: {result['zx_optimized']['cnot_count']}")
        print(f"  Improvements:")
        print(f"    T-depth reduction: {result['improvements']['zx']['t_depth_reduction']:.2f}%")
        print(f"    CNOT-depth reduction: {result['improvements']['zx']['cnot_depth_reduction']:.2f}%")
        print(f"    CNOT-count reduction: {result['improvements']['zx']['cnot_count_reduction']:.2f}%")
        print(f"  Optimization time: {result['zx_optimized']['optimization_time']:.3f}s")
        print(f"\nProbability distributions match:")
        print(f"  Transpiled vs Original: {result['probability_matches']['transpiled_matches_original']}")
        print(f"  ZX vs Original: {result['probability_matches']['zx_matches_original']}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Benchmark quantum circuits with and without ZX optimization')
    parser.add_argument('--circuit', '-c', type=str, help='Specific QASM file to benchmark (without .qasm extension)')
    args = parser.parse_args()
    
    run_benchmarks(args.circuit)
