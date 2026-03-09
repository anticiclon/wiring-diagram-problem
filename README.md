# Wiring Diagram Problem

Source code and instances accompanying the paper:

> **Optimal Embedding of Wiring Diagrams in Constrained Three-Dimensional Spaces**  
> V. Blanco, G. González, J. Puerto  
> *Manuscript under review. This entry will be updated upon publication.*

## Overview

This repository contains the Python implementation of the optimization framework described in the paper, along with the synthetic instances used in the computational experiments (Section 5).

The **Wiring Diagram Problem (WDP)** consists of embedding a hierarchical, tree-structured interconnection scheme into a constrained three-dimensional design domain, minimizing total cable/pipeline length while satisfying safety separation, obstacle avoidance, and constructibility constraints. The approach combines a Hanan-grid-based spatial discretization with a Mixed-Integer Linear Programming (MILP) model solved via Gurobi.

## Requirements

- Python ≥ 3.8
- [Gurobi](https://www.gurobi.com/) ≥ 9.5 with a valid licence (academic licences are available free of charge)
- [gurobipy](https://pypi.org/project/gurobipy/)
- [networkx](https://networkx.org/)
- [matplotlib](https://matplotlib.org/)

Install the Python dependencies with:

```bash
pip install gurobipy networkx matplotlib
```

## Repository structure

| File | Description |
|---|---|
| `main.py` | Entry point. Selects a scenario and calls the solver and visualizer. |
| `codeModel.py` | MILP formulation and Gurobi solver (includes lazy constraint callbacks for safety separation). |
| `auxiliar.py` | I/O utilities: reads scenario files and helper functions. |
| `scenario_generator.py` | Generates synthetic instances as described in Section 5. |
| `drawing.py` | 3D visualisation of solutions using matplotlib. |
| `scenarios.zip` | All synthetic instances used in the computational experiments (Table 1). |

## Usage

### Running an existing scenario

1. Unzip `scenarios.zip` into a `scenarios/` folder in the repository root.
2. Open `main.py` and set the desired scenario name and solver parameters:

```python
nameScenario      = "col1ram3nod10caj1lad5ver1"  # scenario identifier
security_distance = 5      # minimum safety distance Δ
gap               = 0      # optimality gap tolerance (0 = proven optimal)
timelimit         = 3600   # time limit in seconds
```

3. Run:

```bash
python main.py
```

### Scenario naming convention

Scenario filenames encode the instance parameters:

```
col<#c>ram<#b>nod<#n>caj<#boxes>lad<box_side>ver<seed>
```

For example, `col2ram3nod10caj1lad5ver2` corresponds to 2 pipelines, 3 branches per pipeline, 10 nodes per branch, 1 admissible box per intermediate node, box side length 5, random seed 2.

### Generating new instances

```python
import scenario_generator as generator
generator.generate(...)   # see function signature for parameters
```

## Computational environment

Experiments reported in the paper were run on an Intel Core i7-1165G7 (2.80 GHz, 4 cores), 16 GB RAM, Windows 11, using **Gurobi 9.5.0** with a time limit of 3600 s and optimality gap set to 0%.

## Industrial case study

The data for the naval cabin case study (Section 6) cannot be shared due to a confidentiality agreement with the industrial partner, Ghenova.

## Licence

This code is released for academic and research purposes. If you use it, please cite the paper above.

## Acknowledgements

This work was supported by grants PID2020-114594GB-C21, PID2022-139219OB-I00, PID2024-156594NB-C21, and RED2022-134149-T funded by MICIU/AEI; FEDER+Junta de Andalucía projects C-EXP-139-UGR23 and AT 21_00032; SOL2024-31596 and SOL2024-31708 funded by US; the IMAG–María de Maeztu grant CEX2020-001105-M; and the IMUS–María de Maeztu grant CEX2024-001517-M.
