import os
import json
from typing import Dict, List, Optional, Any
from qrisp import QuantumCircuit, QuantumVariable, QuantumSession
from qrisp.config import setup_logging, activate_zx_optimization, deactivate_zx_optimization
from qrisp.misc.utility import t_depth_indicator, cnot_depth_indicator
import logging
import time
import argparse
from mqt import qcec
from tempfile import NamedTemporaryFile
import sys
from qrisp_circuits.ghz_state import GHZCircuit
from qrisp_circuits.sat_solver import SATCircuit, sample_dimacs_3vars_20clauses, sample_dimacs_5vars_5clauses, sample_dimacs_5vars_15clauses

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
    logger = logging.getLogger('benchmark')
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
            logger.error(f"Failed to load {specific_file}: {str(e)}")
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
                    logger.error(f"Failed to load {filename}: {str(e)}")
    
    return circuits

def get_qrisp_circuits() -> Dict[str, QuantumCircuit]:
    """
    Get predefined Qrisp circuits for benchmarking.
    
    Returns
    -------
    Dict[str, QuantumCircuit]
        Dictionary mapping circuit names to quantum circuits
    """
    
        
    qrisp_circuits_array = [
        GHZCircuit(3),
        GHZCircuit(10),
        SATCircuit(sample_dimacs_3vars_20clauses, "medium_3var"),
        SATCircuit(sample_dimacs_5vars_5clauses, "small_5var"),
        SATCircuit(sample_dimacs_5vars_15clauses, "medium_5var")
    ]
    
    return {circuit.name(): circuit.create_session() for circuit in qrisp_circuits_array}

def load_circuits(specific_circuit: Optional[str] = None) -> Dict[str, QuantumCircuit]:
    """
    Load both QASM files and Qrisp circuits for benchmarking.
    
    Parameters
    ----------
    specific_circuit : str, optional
        If provided, only load this specific circuit. Can be either:
        - A QASM filename (with or without .qasm extension)
        - A Qrisp circuit name (e.g. 'GHZ-3', 'GHZ-10')
        
    Returns
    -------
    Dict[str, QuantumCircuit]
        Dictionary mapping circuit names to quantum circuits
    """
    logger = logging.getLogger('benchmark')
    circuits: Dict[str, QuantumCircuit] = {}
    
    if specific_circuit:
        # First try to load as a Qrisp circuit
        qrisp_circuits = get_qrisp_circuits()
        if specific_circuit in qrisp_circuits:
            logger.info(f"Loading specific Qrisp circuit: {specific_circuit}")
            return {specific_circuit: qrisp_circuits[specific_circuit]}
        
        # If not a Qrisp circuit, try to load as QASM file
        logger.info(f"Loading specific QASM circuit: {specific_circuit}")
        qasm_circuits = load_qasm_circuits(os.path.join("benchmark", "circuits"), specific_circuit)
        return qasm_circuits
    
    # If no specific circuit requested, load all circuits
    # Load QASM circuits
    qasm_circuits = load_qasm_circuits(os.path.join("benchmark", "circuits"), None)
    circuits.update(qasm_circuits)
    
    # Load Qrisp circuits
    logger.info("Loading Qrisp circuits...")
    qrisp_circuits = get_qrisp_circuits()
    circuits.update(qrisp_circuits)
    logger.info(f"Loaded {len(qrisp_circuits)} Qrisp circuits")
    
    return circuits

def benchmark_circuit(qc: QuantumCircuit, name: str) -> Dict[str, Any]:
    """Run benchmarks on a single circuit."""
    logger = logging.getLogger('benchmark')
    logger.info(f"Starting benchmark for circuit: {name}")
    logger.info(f"Circuit size: {qc.num_qubits()} qubits")
    
    # Create quantum session and variables
    qs = QuantumSession()
    num_qubits = qc.num_qubits()
    qv = QuantumVariable(num_qubits, qs=qs)
    
    # Convert circuit to gate and apply it
    logger.info("Converting circuit to gate and applying...")
    gate = qc.to_gate()
    qs.append(gate, qv)
    
    # Skip measurements for large circuits
    should_measure = num_qubits < 30
    if not should_measure:
        logger.info(f"Skipping measurements due to large circuit size ({num_qubits} qubits)")
    
    # Calculate non-transpiled depths
    logger.info("Calculating metrics for non-transpiled circuit...")
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
        logger.info("Measuring non-transpiled circuit probabilities...")
        results["non_transpiled"]["probabilities"] = qv.get_measurement(compile=False)
    
    # Calculate transpiled depths (without ZX)
    logger.info("Transpiling circuit (without ZX optimization)...")
    transpiled_qs = qs.compile(
        compile_mcm=True,
        workspace=0
    )
    logger.info("Calculating metrics for transpiled circuit...")
    
    results["transpiled"] = {
        "t_depth": transpiled_qs.depth(depth_indicator=lambda op: t_depth_indicator(op, epsilon=2**-10), transpile=False),
        "cnot_depth": transpiled_qs.depth(depth_indicator=cnot_depth_indicator, transpile=False),
        "cnot_count": transpiled_qs.cnot_count(),
        "num_qubits": transpiled_qs.num_qubits(),
        "operation_counts": transpiled_qs.count_ops()
    }
    
    if should_measure:
        logger.info("Measuring transpiled circuit probabilities...")
        results["transpiled"]["probabilities"] = qv.get_measurement(precompiled_qc=transpiled_qs)
    
    # Compile with ZX optimization enabled
    logger.info("Starting ZX optimization...")
    start_time = time.time()
    activate_zx_optimization()
    optimized_qs = qs.compile(
        compile_mcm=False,
        workspace=0
    )
    deactivate_zx_optimization()  # Reset to default state
    optimization_time = time.time() - start_time
    logger.info(f"ZX optimization completed in {optimization_time:.3f} seconds")
    logger.info("Calculating metrics for ZX-optimized circuit...")
    
    results["zx_optimized"] = {
        "t_depth": optimized_qs.depth(depth_indicator=lambda op: t_depth_indicator(op, epsilon=2**-10), transpile=False),
        "cnot_depth": optimized_qs.depth(depth_indicator=cnot_depth_indicator, transpile=False),
        "cnot_count": optimized_qs.cnot_count(),
        "num_qubits": optimized_qs.num_qubits(),
        "operation_counts": optimized_qs.count_ops(),
        "optimization_time": optimization_time
    }
    
    if should_measure:
        logger.info("Measuring ZX-optimized circuit probabilities...")
        results["zx_optimized"]["probabilities"] = qv.get_measurement(precompiled_qc=optimized_qs)
    
    # Perform equivalence checking using MQT QCEC
    logger.info("Starting equivalence checking with MQT QCEC...")
    results["equivalence_checking"] = {}
    
    # Create temporary QASM files for each circuit version
    with NamedTemporaryFile(mode='w', suffix='.qasm') as original_file, \
         NamedTemporaryFile(mode='w', suffix='.qasm') as transpiled_file, \
         NamedTemporaryFile(mode='w', suffix='.qasm') as zx_file:
        
        # Save circuits to temporary files
        logger.info("Saving circuits to temporary QASM files...")
        qasm_saved = False
        try:
            qs.qasm(filename=original_file.name)
            transpiled_qs.qasm(filename=transpiled_file.name) 
            optimized_qs.qasm(filename=zx_file.name)
            qasm_saved = True
        except:
            logger.error("Failed to save circuits as QASM")
            results["equivalence_checking"]["transpiled"] = {
                "equivalent": "unknown",
                "time": 0
            }
            results["equivalence_checking"]["zx_optimized"] = {
                "equivalent": "unknown", 
                "time": 0
            }
            
        if qasm_saved:
            # Check equivalence between original and transpiled
            logger.info("Checking equivalence between original and transpiled circuits...")
            try:
                verifier = qcec.verify(original_file.name, transpiled_file.name)
                results["equivalence_checking"]["transpiled"] = {
                    "equivalent": verifier.equivalence.name,
                    "time": verifier.check_time
                }
                logger.info(f"Transpiled circuit equivalence result: {verifier.equivalence.name} (in {verifier.check_time:.3f}s)")
            except Exception as e:
                logger.error(f"Error checking transpiled circuit equivalence: {str(e)}")
                results["equivalence_checking"]["transpiled"] = {
                    "error": str(e)
                }
            
            # Check equivalence between original and ZX-optimized
            logger.info("Checking equivalence between original and ZX-optimized circuits...")
            try:
                verifier = qcec.verify(original_file.name, zx_file.name)
                results["equivalence_checking"]["zx_optimized"] = {
                    "equivalent": verifier.equivalence.name,
                    "time": verifier.check_time,
                }
                logger.info(f"ZX-optimized circuit equivalence result: {verifier.equivalence.name} (in {verifier.check_time:.3f}s)")
            except Exception as e:
                logger.error(f"Error checking ZX-optimized circuit equivalence: {str(e)}")
                results["equivalence_checking"]["zx_optimized"] = {
                    "error": str(e)
                }
    
    # Calculate improvements
    logger.info("Calculating improvement metrics...")
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
        logger.info("Comparing probability distributions...")
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
            logger.warning("Found differences in probability distributions")
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
    
    logger.info(f"Benchmark completed for circuit: {name}")
    return results

def run_benchmarks(specific_circuit: Optional[str] = None) -> None:
    """
    Run benchmarks on quantum circuits.
    
    Parameters
    ----------
    specific_circuit : str, optional
        If provided, only benchmark this specific circuit. Can be either:
        - A QASM filename (with or without .qasm extension)
        - A Qrisp circuit name (e.g. 'GHZ-3', 'GHZ-10')
    """
    # Set up logging with a more detailed format
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    
    # Configure both the qrisp logger and our benchmark logger
    qrisp_logger = logging.getLogger('qrisp')
    if not qrisp_logger.handlers:
        qrisp_logger.addHandler(console_handler)
    qrisp_logger.setLevel(logging.INFO)
    
    # Configure our benchmark logger
    logger = logging.getLogger('benchmark')
    if not logger.handlers:
        logger.addHandler(console_handler)
    logger.setLevel(logging.INFO)
    
    logger.info("Starting benchmark run")
    if specific_circuit:
        logger.info(f"Benchmarking specific circuit: {specific_circuit}")
    else:
        logger.info("Benchmarking all circuits")
    
    # Load circuits
    logger.info("Loading circuits")
    try:
        circuits = load_circuits(specific_circuit)
    except FileNotFoundError as e:
        logger.error(str(e))
        return
    
    if not circuits:
        logger.error("No circuits loaded for benchmarking")
        return
    
    logger.info(f"Successfully loaded {len(circuits)} circuits")
    
    # Run benchmarks
    results: List[Dict[str, Any]] = []
    total_circuits = len(circuits)
    for idx, (name, circuit) in enumerate(circuits.items(), 1):
        logger.info(f"Processing circuit {idx}/{total_circuits}: {name}")
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
            logger.exception("Detailed error information:")
    
    # Save results
    output_file = os.path.join("benchmark", "results.json")
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    logger.info(f"Saving results to {output_file}")
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info("Results saved successfully")
    
    # Print summary
    logger.info("\nGenerating benchmark summary")
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
        print("\nEquivalence Checking Results:")
        print("  Transpiled vs Original:")
        if "error" in result["equivalence_checking"]["transpiled"]:
            print(f"    Error: {result['equivalence_checking']['transpiled']['error']}")
        else:
            print(f"    Equivalent: {result['equivalence_checking']['transpiled']['equivalent']}")
            print(f"    Time: {result['equivalence_checking']['transpiled']['time']:.3f}s")
        print("  ZX-optimized vs Original:")
        if "error" in result["equivalence_checking"]["zx_optimized"]:
            print(f"    Error: {result['equivalence_checking']['zx_optimized']['error']}")
        else:
            print(f"    Equivalent: {result['equivalence_checking']['zx_optimized']['equivalent']}")
            print(f"    Time: {result['equivalence_checking']['zx_optimized']['time']:.3f}s")
        print(f"\nProbability distributions match:")
        print(f"  Transpiled vs Original: {result['probability_matches']['transpiled_matches_original']}")
        print(f"  ZX vs Original: {result['probability_matches']['zx_matches_original']}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Benchmark quantum circuits with and without ZX optimization')
    parser.add_argument('--circuit', '-c', type=str, help='Specific QASM file to benchmark (without .qasm extension)')
    args = parser.parse_args()
    
    run_benchmarks(args.circuit)
