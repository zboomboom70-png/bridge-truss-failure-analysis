# Bridge Truss Progressive Failure Analysis

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![ParaView](https://img.shields.io/badge/ParaView-5.10+-green.svg)](https://www.paraview.org/)
[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org/)

**Author:** Stacey Blakeney, Forensic Mechanical Engineer  
**Application:** Forensic Mechanical Failure & Fracture Analysis  
**Last Updated:** December 2025

---

## Overview

This portfolio provides a complete forensic investigation workflow for analyzing **progressive structural failure** in a bridge truss component using ParaView. The time-series FEA dataset simulates fatigue crack initiation, propagation, and catastrophic fracture under overload conditions.

### Key Features

- ⏱️ **12-Timestep Time Series** showing complete failure sequence
- 🔍 **Warp By Vector** for micro-crack visualization (100× amplification)
- 📍 **Temporal Particles to Pathlines** for debris trajectory tracking
- 📋 **Annotate Selection** with yield exceedance node identification
- 🐍 **Automated Python scripts** for forensic analysis

---

## Repository Structure

```
stacey-blakeney-bridge-truss-failure-analysis/
│
├── time-series-data/
│   ├── generate_truss_failure.py      # Time series generator
│   ├── bridge_truss_failure.pvd       # Structure PVD file
│   ├── debris_pathlines.pvd           # Debris PVD file
│   ├── truss_failure_XXXX.vtk         # 12 structure timesteps
│   └── debris_particles_XXXX.vtk      # 12 particle timesteps
│
├── scripts/
│   └── forensic_failure_analysis.py   # Automated analysis
│
├── documentation/
│   └── SOP_Forensic_Failure_Analysis.md
│
├── README.md
└── LICENSE
```

---

## Quick Start

### 1. Load Time Series

```bash
paraview time-series-data/bridge_truss_failure.pvd
```

### 2. Apply Warp By Vector (100×)

```
Filters > Warp By Vector
- Vectors: Displacement
- Scale Factor: 100
```

### 3. Track Debris Pathlines

```
# Load debris data
File > Open > debris_pathlines.pvd

# Apply pathlines
Filters > Temporal > Temporal Particles To Pathlines
```

### 4. Find Yield Exceedance

```
Filters > Threshold
- Scalars: yield_ratio
- Lower: 1.0
- Upper: 100
```

### 5. Run Automated Analysis

```bash
pvpython scripts/forensic_failure_analysis.py
```

---

## Dataset Specifications

### Geometry: Warren Truss Section

| Parameter | Value |
|-----------|-------|
| Truss Length | 200 mm |
| Truss Height | 80 mm |
| Member Width | 12 mm |
| Grid Resolution | 60 × 30 × 50 |
| Total Nodes | 90,000 |

### Material: Structural Steel A36

| Property | Value | Standard |
|----------|-------|----------|
| Yield Strength | 250 MPa | ASTM A36 |
| Ultimate Strength | 400 MPa | ASTM A36 |
| Young's Modulus | 200 GPa | - |
| Fracture Toughness | 50 MPa√m | - |

### Loading Scenario

| Parameter | Value |
|-----------|-------|
| Design Capacity | 150 kN |
| Overload Factor | 2.8× |
| Peak Load | **420 kN** |
| Failure Time | 2.2 seconds |

---

## Scalar Fields

| Array Name | Description | Units |
|------------|-------------|-------|
| `member_type` | 1=Bottom chord, 2=Top chord, 3=Diagonal, 4=Weld | - |
| `von_mises_stress` | von Mises equivalent stress | MPa |
| `yield_ratio` | σ_vm / σ_yield (>1 = yielded) | - |
| `plastic_strain` | Accumulated plastic strain | % |
| `triaxiality` | σ_h / σ_vm (constraint factor) | - |
| `crack_damage` | Crack zone indicator (0-1) | - |
| `sigma_xx` | Axial stress component | MPa |
| `Displacement` | Deformation vector | mm |

---

## Failure Timeline

```
t = 0.0 s   ─── Initial loading (30% capacity)
    │
    │       Pre-existing fatigue crack at bottom chord
    │
t = 0.4 s   ─── Load increasing, crack stable
    │
t = 0.8 s   ─── Yield begins at crack tip
    │
t = 1.2 s   ─── Plastic zone spreading
    │
    │       ⚠ Debris ejection begins
    │
t = 1.6 s   ─── Rapid crack growth
    │
t = 2.0 s   ─── Unstable fracture propagation
    │
t = 2.2 s   ─── CATASTROPHIC FAILURE
```

---

## ParaView Workflow Summary

### Workflow 1: Warp By Vector

**Purpose:** Amplify deformations to visualize micro-cracks

| Scale | Use Case |
|-------|----------|
| 10× | Overall deflection |
| 50× | Strain localization |
| **100×** | Micro-crack visualization |
| 200× | Crack tip detail |

### Workflow 2: Temporal Particles to Pathlines

**Purpose:** Track debris trajectories from fracture surface

- Debris appears after t > 1.2 s
- Color by `Velocity` magnitude
- High velocity indicates brittle fracture

### Workflow 3: Annotate Selection

**Purpose:** Document yield exceedance with node precision

1. Threshold by `yield_ratio > 1.0`
2. Open Selection Display Inspector
3. Label critical nodes
4. Record timestep, location, stress value

---

## Forensic Investigation Output

The analysis script generates:

1. **Yield Exceedance Report**
   - First yield timestep
   - Critical node location
   - Overstress ratio

2. **Crack Growth Timeline**
   - Damage zone progression
   - Plastic zone extent

3. **Debris Analysis**
   - Number of fragments
   - Ejection velocities
   - Trajectory patterns

---

## Applications

This workflow applies to forensic investigation of:

- Bridge structural failures
- Building collapse analysis
- Industrial equipment fracture
- Transportation accidents
- Pressure vessel rupture
- Weld failure investigation

---

## Requirements

- ParaView 5.10+
- Python 3.8+

---

## References

1. Anderson, T.L. (2017). Fracture Mechanics: Fundamentals and Applications
2. Paris, P.C. & Erdogan, F. (1963). J. Basic Engineering
3. ASTM E1820, E399: Fracture Testing Standards

---

## License

This project is licensed under the MIT License - see [LICENSE](LICENSE) for details.

---

## Contact

**Stacey Blakeney**  
Forensic Mechanical Engineer  
Structural Failure Analysis & Fracture Mechanics

---

*Part of the Forensic Mechanical Failure Analysis Portfolio*
