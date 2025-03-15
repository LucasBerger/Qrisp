import os
import json
from typing import Dict, List, Optional, Any, Set
from base_qrisp_circuits import QrispCircuit
from qrisp import QuantumCircuit, QuantumVariable, QuantumSession
from qrisp.circuit.instruction import Instruction
from qrisp.circuit.transpiler import transpile
from qrisp.config import setup_logging, activate_zx_optimization, deactivate_zx_optimization
from qrisp.misc.utility import t_depth_indicator, cnot_depth_indicator
import logging
import time
import argparse
from mqt import qcec
from tempfile import NamedTemporaryFile
import sys
from multiprocessing import Process, Queue, Lock, Value
from multiprocessing.synchronize import Lock as LockType
from multiprocessing.sharedctypes import Value as SharedValueType
from queue import Empty
from qrisp_circuits.ghz_state import GHZCircuit
from qrisp_circuits.sat_solver import SATCircuit
from qrisp_circuits.tsp import SAMPLE_6CITY_MATRIX, TSPCircuit, SAMPLE_3CITY_MATRIX, SAMPLE_4CITY_MATRIX, cmt1_0, cmt1_1, cmt1_2, cmt1_3, cmt1_4, cmt1_5, cmt1_6, cmt1_7, cmt1_8, cmt1_9, cmt1_10, cmt1_11, cmt1_12, cmt1_13, cmt1_14, cmt1_15, cmt1_16, cmt1_17, cmt1_18, cmt2_lower_cap_0, cmt2_lower_cap_1, cmt2_lower_cap_2, cmt2_lower_cap_3, cmt2_lower_cap_4, cmt2_lower_cap_5, cmt2_lower_cap_6, cmt2_lower_cap_7, cmt2_lower_cap_8, cmt2_lower_cap_9, cmt2_lower_cap_10, cmt2_lower_cap_11, cmt2_lower_cap_12, cmt2_lower_cap_13, cmt2_lower_cap_14, cmt2_lower_cap_15, cmt2_lower_cap_16, cmt2_lower_cap_17, cmt2_lower_cap_18, cmt2_lower_cap_19, cmt2_lower_cap_20, cmt2_lower_cap_21, cmt2_lower_cap_22
from qrisp_circuits.qubo_circuit import QUBOCircuit

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
            circuits[specific_file[:-5]] = qc
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
                    circuits[filename[:-5]] = qc
                except Exception as e:
                    logger.error(f"Failed to load {filename}: {str(e)}")
    
    return circuits

def get_qrisp_circuits() -> Dict[str, QrispCircuit]:
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
        SATCircuit("./benchmark/sat_instances/simple_wishlist.dimacs", "simple_wishlist"),
        SATCircuit("./benchmark/sat_instances/5vars_5clauses.dimacs", "5vars_5clauses"),
        SATCircuit("./benchmark/sat_instances/3vars_20clauses.dimacs", "3vars_20clauses"),
        SATCircuit("./benchmark/sat_instances/5vars_15clauses.dimacs", "5vars_15clauses"),
        SATCircuit("./benchmark/sat_instances/affiliate_inventory_tracking.dimacs", "affiliate_inventory_tracking"),
        SATCircuit("./benchmark/sat_instances/car.dimacs", "car"),
        SATCircuit("./benchmark/sat_instances/catalog_categories.dimacs", "catalog_categories"),
        SATCircuit("./benchmark/sat_instances/catalog_search.dimacs", "catalog_search"),
        SATCircuit("./benchmark/sat_instances/checkout_type.dimacs", "checkout_type"),
        SATCircuit("./benchmark/sat_instances/complex_catalog.dimacs", "complex_catalog"),
        SATCircuit("./benchmark/sat_instances/cs_service.dimacs", "cs_service"),
        SATCircuit("./benchmark/sat_instances/fulfillment_electronic.dimacs", "fulfillment_electronic"),
        SATCircuit("./benchmark/sat_instances/fulfillment.dimacs", "fulfillment"),
        SATCircuit("./benchmark/sat_instances/home_page.dimacs", "home_page"),
        SATCircuit("./benchmark/sat_instances/registration_enforcement.dimacs", "registration_enforcement"),
        SATCircuit("./benchmark/sat_instances/registration_tracking.dimacs", "registration_tracking"),
        SATCircuit("./benchmark/sat_instances/targeting.dimacs", "targeting"),
        SATCircuit("./benchmark/sat_instances/tracking.dimacs", "tracking"),
        SATCircuit("./benchmark/sat_instances/visited_pages.dimacs", "visited_pages"),
        SATCircuit("./benchmark/sat_instances/wishlist_save.dimacs", "wishlist_save"),
        *[QUBOCircuit("./benchmark/qubo_instances/CMT1_0.lp", "cmt1_0", depth=d, after_iterations = iters) for d in range(1, 6, 2) for iters in range(0, 51, 25)],
        *[QUBOCircuit("./benchmark/qubo_instances/CMT1_1.lp", "cmt1_1", depth=d, after_iterations = iters) for d in range(1, 6, 2) for iters in range(0, 51, 25)],
        *[QUBOCircuit("./benchmark/qubo_instances/CMT1_2.lp", "cmt1_2", depth=d, after_iterations = iters) for d in range(1, 6, 2) for iters in range(0, 51, 25)],
        *[QUBOCircuit("./benchmark/qubo_instances/CMT1_3.lp", "cmt1_3", depth=d, after_iterations = iters) for d in range(1, 6, 2) for iters in range(0, 51, 25)],
        *[QUBOCircuit("./benchmark/qubo_instances/CMT1_4.lp", "cmt1_4", depth=d, after_iterations = iters) for d in range(1, 6, 2) for iters in range(0, 51, 25)],
        *[QUBOCircuit("./benchmark/qubo_instances/CMT1_5.lp", "cmt1_5", depth=d, after_iterations = iters) for d in range(1, 6, 2) for iters in range(0, 51, 25)],
        *[QUBOCircuit("./benchmark/qubo_instances/CMT1_6.lp", "cmt1_6", depth=d, after_iterations = iters) for d in range(1, 6, 2) for iters in range(0, 51, 25)],
        *[QUBOCircuit("./benchmark/qubo_instances/CMT1_7.lp", "cmt1_7", depth=d, after_iterations = iters) for d in range(1, 6, 2) for iters in range(0, 51, 25)],
        *[QUBOCircuit("./benchmark/qubo_instances/CMT1_8.lp", "cmt1_8", depth=d, after_iterations = iters) for d in range(1, 6, 2) for iters in range(0, 51, 25)],
        *[QUBOCircuit("./benchmark/qubo_instances/CMT1_9.lp", "cmt1_9", depth=d, after_iterations = iters) for d in range(1, 6, 2) for iters in range(0, 51, 25)],
        *[QUBOCircuit("./benchmark/qubo_instances/CMT1_10.lp", "cmt1_10", depth=d, after_iterations = iters) for d in range(1, 6, 2) for iters in range(0, 51, 25)],
        *[QUBOCircuit("./benchmark/qubo_instances/CMT1_11.lp", "cmt1_11", depth=d, after_iterations = iters) for d in range(1, 6, 2) for iters in range(0, 51, 25)],
        *[QUBOCircuit("./benchmark/qubo_instances/CMT1_12.lp", "cmt1_12", depth=d, after_iterations = iters) for d in range(1, 6, 2) for iters in range(0, 51, 25)],
        *[QUBOCircuit("./benchmark/qubo_instances/CMT1_13.lp", "cmt1_13", depth=d, after_iterations = iters) for d in range(1, 6, 2) for iters in range(0, 51, 25)],
        *[QUBOCircuit("./benchmark/qubo_instances/CMT1_14.lp", "cmt1_14", depth=d, after_iterations = iters) for d in range(1, 6, 2) for iters in range(0, 51, 25)],
        *[QUBOCircuit("./benchmark/qubo_instances/CMT1_15.lp", "cmt1_15", depth=d, after_iterations = iters) for d in range(1, 6, 2) for iters in range(0, 51, 25)],
        *[QUBOCircuit("./benchmark/qubo_instances/CMT1_16.lp", "cmt1_16", depth=d, after_iterations = iters) for d in range(1, 6, 2) for iters in range(0, 51, 25)],
        *[QUBOCircuit("./benchmark/qubo_instances/CMT1_17.lp", "cmt1_17", depth=d, after_iterations = iters) for d in range(1, 6, 2) for iters in range(0, 51, 25)],
        *[QUBOCircuit("./benchmark/qubo_instances/CMT1_18.lp", "cmt1_18", depth=d, after_iterations = iters) for d in range(1, 6, 2) for iters in range(0, 51, 25)],
        TSPCircuit(3, SAMPLE_3CITY_MATRIX, 0.4, "small_3city"),
        TSPCircuit(4, SAMPLE_4CITY_MATRIX, 0.4, "medium_4city"),
        TSPCircuit(6, SAMPLE_6CITY_MATRIX, 0.4, "large_6city"),
        TSPCircuit(4, cmt1_0, 0.6, "cmt1_0"),
        TSPCircuit(5, cmt1_1, 0.6, "cmt1_1"), 
        TSPCircuit(2, cmt1_2, 0.6, "cmt1_2"),
        TSPCircuit(3, cmt1_3, 0.6, "cmt1_3"),
        TSPCircuit(3, cmt1_4, 0.6, "cmt1_4"),
        TSPCircuit(5, cmt1_5, 0.6, "cmt1_5"),
        TSPCircuit(2, cmt1_6, 0.6, "cmt1_6"),
        TSPCircuit(3, cmt1_7, 0.6, "cmt1_7"),
        TSPCircuit(3, cmt1_8, 0.6, "cmt1_8"),
        TSPCircuit(4, cmt1_9, 0.6, "cmt1_9"),
        TSPCircuit(4, cmt1_10, 0.6, "cmt1_10"),
        TSPCircuit(4, cmt1_11, 0.6, "cmt1_11"),
        TSPCircuit(4, cmt1_12, 0.6, "cmt1_12"),
        TSPCircuit(4, cmt1_13, 0.6, "cmt1_13"),
        TSPCircuit(4, cmt1_14, 0.6, "cmt1_14"),
        TSPCircuit(3, cmt1_15, 0.6, "cmt1_15"),
        TSPCircuit(5, cmt1_16, 0.6, "cmt1_16"),
        TSPCircuit(4, cmt1_17, 0.6, "cmt1_17"),
        TSPCircuit(3, cmt1_18, 0.6, "cmt1_18"),
        TSPCircuit(4, cmt2_lower_cap_0, 0.6, "cmt2_lower_cap_0"),
        TSPCircuit(5, cmt2_lower_cap_1, 0.6, "cmt2_lower_cap_1"),
        TSPCircuit(5, cmt2_lower_cap_2, 0.6, "cmt2_lower_cap_2"),
        TSPCircuit(5, cmt2_lower_cap_3, 0.6, "cmt2_lower_cap_3"),
        TSPCircuit(5, cmt2_lower_cap_4, 0.6, "cmt2_lower_cap_4"),
        TSPCircuit(5, cmt2_lower_cap_5, 0.6, "cmt2_lower_cap_5"),
        TSPCircuit(4, cmt2_lower_cap_6, 0.6, "cmt2_lower_cap_6"),
        TSPCircuit(4, cmt2_lower_cap_7, 0.6, "cmt2_lower_cap_7"),
        TSPCircuit(4, cmt2_lower_cap_8, 0.6, "cmt2_lower_cap_8"),
        TSPCircuit(3, cmt2_lower_cap_9, 0.6, "cmt2_lower_cap_9"),
        TSPCircuit(6, cmt2_lower_cap_10, 0.6, "cmt2_lower_cap_10"),
        TSPCircuit(4, cmt2_lower_cap_11, 0.6, "cmt2_lower_cap_11"),
        TSPCircuit(5, cmt2_lower_cap_12, 0.6, "cmt2_lower_cap_12"),
        TSPCircuit(5, cmt2_lower_cap_13, 0.6, "cmt2_lower_cap_13"),
        TSPCircuit(3, cmt2_lower_cap_14, 0.6, "cmt2_lower_cap_14"),
        TSPCircuit(4, cmt2_lower_cap_15, 0.6, "cmt2_lower_cap_15"),
        TSPCircuit(5, cmt2_lower_cap_16, 0.6, "cmt2_lower_cap_16"),
        TSPCircuit(4, cmt2_lower_cap_17, 0.6, "cmt2_lower_cap_17"),
        TSPCircuit(5, cmt2_lower_cap_18, 0.6, "cmt2_lower_cap_18"),
        TSPCircuit(4, cmt2_lower_cap_19, 0.6, "cmt2_lower_cap_19"),
        TSPCircuit(4, cmt2_lower_cap_20, 0.6, "cmt2_lower_cap_20"),
        TSPCircuit(2, cmt2_lower_cap_21, 0.6, "cmt2_lower_cap_21"),
        TSPCircuit(3, cmt2_lower_cap_22, 0.6, "cmt2_lower_cap_22"),
    ]
    
    return {circuit.name(): circuit for circuit in qrisp_circuits_array}

def print_metrics(qc: QuantumCircuit, name: str) -> None:
    """Print basic metrics about a quantum circuit to a JSON file."""
    logger = logging.getLogger('benchmark')
    logger.info(f"Printing metrics for circuit: {name}")
    
    # Create quantum session and variables
    qs = QuantumSession()
    num_qubits = qc.num_qubits()
    qv = QuantumVariable(num_qubits, qs=qs)
    
    # Convert circuit to gate and apply it
    logger.info("Converting circuit to gate and applying...")
    
    clbits = qc.clbits
    for clbit in clbits:
        for op in qc.data:
            op: Instruction = op
            if len(op.clbits) > 0 and op.clbits.index(clbit) != -1:
                continue
            
        qc.clbits = [clbit for clbit in qc.clbits if clbit != clbit]
    
    gate = qc.to_gate()
    qs.append(gate, qv)
    
    transpiled_qc = transpile(qc)
    
    # Calculate basic metrics
    metrics = {
        "name": name,
        "num_qubits": qs.num_qubits(),
        "circuit_depth": transpiled_qc.depth(),
        "operation_counts": qs.count_ops(),
        "transpiled_operation_counts": transpiled_qc.count_ops()
    }
    
    # Create the metrics directory if it doesn't exist
    metrics_dir = os.path.join("benchmark", "circuit_metrics")
    os.makedirs(metrics_dir, exist_ok=True)
    
    # Save metrics to file
    output_file = os.path.join(metrics_dir, f"{name}_metrics.json")
    with open(output_file, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    logger.info(f"Metrics saved to {output_file}")

def run_circuit(qc: QuantumCircuit, name: str) -> Dict[str, Any]:
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
    
    clbits = qc.clbits
    for clbit in clbits:
        for op in qc.data:
            op: Instruction = op
            if len(op.clbits) > 0 and op.clbits.index(clbit) != -1:
                continue
            
        qc.clbits = [clbit for clbit in qc.clbits if clbit != clbit]
    
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

def save_circuit_result(result: Dict[str, Any], circuit_name: str) -> None:
    """Save benchmark result for a single circuit to its own JSON file."""
    # Create the results directory if it doesn't exist
    results_dir = os.path.join("benchmark", "benchmark_results")
    os.makedirs(results_dir, exist_ok=True)
    
    # Create a safe filename from the circuit name
    safe_name = "".join(c if c.isalnum() or c in ('-', '_') else '_' for c in circuit_name)
    output_file = os.path.join(results_dir, f"{safe_name}.json")
    
    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2)

def worker_process(circuit_queue: Queue, log_lock: LockType, active_workers: SharedValueType) -> None:
    """Worker process that benchmarks circuits from the queue."""
    # Set up logging with a lock to prevent output interleaving
    formatter = logging.Formatter('%(asctime)s - %(processName)s - %(levelname)s - %(message)s')
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    
    logger = logging.getLogger('benchmark')
    logger.handlers = []  # Remove any existing handlers
    logger.addHandler(console_handler)
    logger.setLevel(logging.INFO)
    
    # Configure qrisp logger similarly
    qrisp_logger = logging.getLogger('qrisp')
    qrisp_logger.handlers = []
    qrisp_logger.addHandler(console_handler)
    qrisp_logger.setLevel(logging.INFO)
    
    while True:
        try:
            # Try to get a circuit name and type from the queue
            circuit_info = circuit_queue.get(timeout=1)
            if circuit_info is None:  # Sentinel value
                break
                
            circuit_name, is_qasm = circuit_info
        except Empty:
            # If queue is empty, exit the process
            break
            
        try:
            with log_lock:
                logger.info(f"Starting benchmark for circuit: {circuit_name}")
            
            # Create the circuit within the worker process
            if is_qasm:
                # Load QASM circuit
                circuits = load_qasm_circuits(os.path.join("benchmark", "circuits"), circuit_name)
                circuit = circuits[circuit_name]
            else:
                # Load Qrisp circuit
                qrisp_circuits = get_qrisp_circuits()
                circuit = qrisp_circuits[circuit_name].create_session()
            
            # Run benchmark for this circuit
            result = run_circuit(circuit, circuit_name)
            
            # Save individual result
            save_circuit_result(result, circuit_name)
            
            with log_lock:
                logger.info(f"Completed benchmark for {circuit_name}")
                logger.info("Transpiler improvements:")
                logger.info(f"  T-depth reduction: {result['improvements']['transpiled']['t_depth_reduction']:.2f}%")
                logger.info(f"  CNOT-depth reduction: {result['improvements']['transpiled']['cnot_depth_reduction']:.2f}%")
                logger.info(f"  CNOT-count reduction: {result['improvements']['transpiled']['cnot_count_reduction']:.2f}%")
                logger.info("ZX-optimization improvements:")
                logger.info(f"  T-depth reduction: {result['improvements']['zx']['t_depth_reduction']:.2f}%")
                logger.info(f"  CNOT-depth reduction: {result['improvements']['zx']['cnot_depth_reduction']:.2f}%")
                logger.info(f"  CNOT-count reduction: {result['improvements']['zx']['cnot_count_reduction']:.2f}%")
        except Exception as e:
            with log_lock:
                logger.error(f"Failed to benchmark {circuit_name}: {str(e)}")
                logger.exception("Detailed error information:")
    
    with active_workers.get_lock():
        active_workers.value -= 1

def get_existing_results() -> Set[str]:
    """Get set of circuit names that have already been benchmarked."""
    results_dir = os.path.join("benchmark", "benchmark_results")
    if not os.path.exists(results_dir):
        return set()
    
    # Get all json files and extract their circuit names
    existing_results = set()
    for filename in os.listdir(results_dir):
        if filename.endswith('.json'):
            # Remove .json extension to get original circuit name
            circuit_name = filename[:-5]  # Remove .json
            existing_results.add(circuit_name)
            
    print(f"Existing results: {existing_results}")
    
    return existing_results

def run_benchmarks(specific_circuit: Optional[str] = None, num_threads: int = 1, skip_existing: bool = False) -> None:
    """
    Run benchmarks on quantum circuits using multiple processes.
    
    Parameters
    ----------
    specific_circuit : str, optional
        If provided, only benchmark this specific circuit
    num_threads : int, optional
        Number of parallel processes to use for benchmarking (default: 1)
    skip_existing : bool, optional
        If True, skip circuits that have already been benchmarked (default: False)
    """
    # Set up logging
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    
    logger = logging.getLogger('benchmark')
    if not logger.handlers:
        logger.addHandler(console_handler)
    logger.setLevel(logging.INFO)
    
    logger.info(f"Starting benchmark run with {num_threads} threads")
    
    # Get list of available circuits without actually creating them
    qasm_circuits = set()
    qrisp_circuits = set()
    
    # Get QASM circuit names
    circuits_dir = os.path.join("benchmark", "circuits")
    if os.path.exists(circuits_dir):
        for filename in os.listdir(circuits_dir):
            if filename.endswith('.qasm'):
                qasm_circuits.add(filename[:-5])
    
    # Get Qrisp circuit names
    temp_qrisp_circuits = get_qrisp_circuits()
    qrisp_circuits = set(temp_qrisp_circuits.keys())
    del temp_qrisp_circuits  # Free memory
    
    if specific_circuit:
        if specific_circuit in qasm_circuits:
            circuit_infos = [(specific_circuit, True)]
        elif specific_circuit in qrisp_circuits:
            circuit_infos = [(specific_circuit, False)]
        else:
            logger.error(f"Circuit {specific_circuit} not found")
            return
    else:
        circuit_infos = [(name, True) for name in qasm_circuits] + [(name, False) for name in qrisp_circuits]
    
    if not circuit_infos:
        logger.error("No circuits found for benchmarking")
        return
    
    logger.info(f"Found {len(circuit_infos)} circuits to process")
    
    # Get existing results if skip_existing is True
    existing_results = get_existing_results() if skip_existing else set()
    
    # Create the results directory
    os.makedirs(os.path.join("benchmark", "benchmark_results"), exist_ok=True)
    
    # Create a queue and fill it with circuit information
    circuit_queue = Queue()
    skipped_count = 0
    circuits_to_process = 0
    
    for name, is_qasm in circuit_infos:
        if skip_existing and name in existing_results:
            skipped_count += 1
            logger.info(f"Skipping already benchmarked circuit: {name}")
            continue
            
        circuit_queue.put((name, is_qasm))
        circuits_to_process += 1
    
    # Add sentinel values to signal workers to exit
    for _ in range(num_threads):
        circuit_queue.put(None)
    
    if skip_existing:
        logger.info(f"Skipped {skipped_count} already benchmarked circuits")
        logger.info(f"Remaining circuits to benchmark: {circuits_to_process}")
    
    if circuits_to_process == 0:
        logger.info("No circuits to benchmark - all have been processed already")
        # Still print the summary of existing results
        print_benchmark_summary()
        return
    
    # Create shared objects for process coordination
    log_lock = Lock()
    active_workers = Value('i', num_threads)
    
    # Start worker processes
    processes = []
    for _ in range(num_threads):
        p = Process(target=worker_process, args=(circuit_queue, log_lock, active_workers))
        p.start()
        processes.append(p)
    
    # Wait for all processes to complete
    for p in processes:
        p.join()
    
    logger.info("All benchmarks completed")
    
    # Print summary of results
    print_benchmark_summary()

def print_benchmark_summary(specific_circuit: Optional[str] = None) -> None:
    """Print a summary of all benchmark results found in the results directory."""
    logger = logging.getLogger('benchmark')
    logger.info("\nGenerating benchmark summary")
    results_dir = os.path.join("benchmark", "benchmark_results")
    print("\nBenchmark Summary:")
    print("-----------------")
    
    if not os.path.exists(results_dir):
        print("No benchmark results found.")
        return
    
    for filename in sorted(os.listdir(results_dir)):
        if not filename.endswith('.json'):
            continue
        
        if specific_circuit and specific_circuit != filename[:-5]:
            continue
            
        with open(os.path.join(results_dir, filename), 'r') as f:
            result = json.load(f)
            
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

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Benchmark quantum circuits with and without ZX optimization')
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Run command
    run_parser = subparsers.add_parser('run', help='Run full benchmarking')
    run_parser.add_argument('--circuit', '-c', type=str, help='Specific QASM file to benchmark (without .qasm extension)')
    run_parser.add_argument('--threads', '-t', type=int, default=1, help='Number of parallel processes to use for benchmarking')
    run_parser.add_argument('--skip-existing', '-s', action='store_true', help='Skip circuits that have already been benchmarked')
    
    # Print metrics command
    metrics_parser = subparsers.add_parser('print_metrics', help='Print basic circuit metrics')
    metrics_parser.add_argument('--circuit', '-c', type=str, required=True, help='Circuit to analyze')
    
    args = parser.parse_args()
    
    if args.command == 'run':
        run_benchmarks(args.circuit, args.threads, args.skip_existing)
    elif args.command == 'print_metrics':
        # Set up logging
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        
        logger = logging.getLogger('benchmark')
        if not logger.handlers:
            logger.addHandler(console_handler)
        logger.setLevel(logging.INFO)
        
        # Load the circuit
        if args.circuit:
            # Try loading as QASM first
            try:
                circuits = load_qasm_circuits(os.path.join("benchmark", "circuits"), args.circuit)
                circuit = circuits[args.circuit]
            except (FileNotFoundError, KeyError):
                # If not found as QASM, try as Qrisp circuit
                qrisp_circuits = get_qrisp_circuits()
                if args.circuit not in qrisp_circuits:
                    logger.error(f"Circuit {args.circuit} not found")
                    sys.exit(1)
                circuit = qrisp_circuits[args.circuit].create_session()
            
            print_metrics(circuit, args.circuit)
        else:
            logger.error("Circuit name must be provided when using print_metrics command")
            sys.exit(1)
    else:
        parser.print_help()
        sys.exit(1)
