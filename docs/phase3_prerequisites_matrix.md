# Starship Flight 14 Digital Engineering Laboratory
## Phase 3 — Prerequisites Matrix & Scientific Toolchain Audit

**Document ID:** `DOC-P3-PREREQ-001`  
**Revision:** `1.0.0`  
**Date:** `2026-10-25`  
**Author:** Simulation Architect & Software Integration Lead  

---

### 1. Scientific Computing Prerequisites Status

| Prerequisite Component | Exact Path / Binary | Detected Version | Primary Purpose | Verification Smoke Test Result | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Scientific Python** | `E:\Program Files\FreeCAD 1.1\bin\python.exe` | 3.11.9 (64-bit) | Scientific solver host | Smoke test executed; verified stdlib & site-packages. | **VERIFIED AND WORKING** |
| **NumPy** | Inside FreeCAD Python site-packages | 1.26.4 | Vector ODE state arrays | State matrix multiplication & norm tests passed. | **VERIFIED AND WORKING** |
| **SciPy Integrate** | `scipy.integrate.solve_ivp` | 1.16.3 | Adaptive RK45/DOP853 | Verified import; event handling functional. | **VERIFIED AND WORKING** |
| **Matplotlib** | `matplotlib.pyplot` | 3.10.8 | Telemetry visualization | Headless `Agg` backend generated 6-panel PNG plot. | **VERIFIED AND WORKING** |
| **Pandas** | `pandas` | 2.3.3 | Data manipulation | CSV dataframe operations verified. | **VERIFIED AND WORKING** |
| **PyYAML** | `yaml` | 6.0.3 | Parameter registry loader | `data/propulsion/parameters.yaml` parsed cleanly. | **VERIFIED AND WORKING** |
| **NASA GMAT** | `E:\NASA\GMAT-R2026a\bin\GmatConsole.exe` | R2026a | Independent orbital validation | Executed `GmatConsole.exe`; verified DE405 core initialization. | **VERIFIED AND WORKING** |
| **Unittest Framework** | Python Standard Library | Built-in | Test runner & assertions | 28 automated test assertions pass in 7.597s. | **VERIFIED AND WORKING** |

---

### 2. Execution Protocol & Fallback Architecture

To ensure cross-platform compatibility and eliminate single-point dependency failures:
1. **Primary High-Fidelity Integrator**:
   `src/integration/scipy_solver.py` provides adaptive Dormand-Prince (RK45) integration with discrete event detection.
2. **Deterministic Embedded Fallback**:
   `src/numerics/rk4_solver.py` provides pure NumPy classical Runge-Kutta 4th-order fixed-step integration for environments without SciPy installed.
3. **CSV Export Interface**:
   Standard library `csv.DictWriter` is utilized in `ascent_3dof.py` to ensure export capability across all Python interpreters without requiring third-party libraries.
