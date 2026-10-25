# Starship Flight 14 Digital Engineering Lab — Environment & Reproducibility Matrix

**Document ID:** `DOC-AUDIT-ENV-001`  
**Classification:** Runtime Environment & Toolchain Specification  

---

## 1. Dual-Interpreter Architecture Rationale

The development workstation features two primary Python interpreters:
1. **Python 3.14.5 (`python`):** System runtime. Lacks compiled C-extensions for SciPy/Matplotlib in this installation, but possesses pure NumPy 2.5.3, PyYAML 6.0.3, and standard library tools (`unittest`, `csv`, `math`, `sqlite3`).
2. **FreeCAD Python 3.11.14 (`E:\Program Files\FreeCAD 1.1\bin\python.exe`):** Conda-forge runtime bundled with FreeCAD 1.1. Contains SciPy 1.16.3, Matplotlib 3.10.8, pandas 2.3.3, NumPy 1.26.4, PyYAML 6.0.3, and the native `FreeCAD` API.

### Reproducibility Command Protocols:
- **Fast Unit Test Execution (114 tests):**
  ```powershell
  python -m unittest discover tests
  ```
  *Measured Runtime:* ~33.4 seconds (114 tests passing).
- **Full Scientific / CAD / Plotting Execution (with SciPy & Matplotlib):**
  ```powershell
  & "E:\Program Files\FreeCAD 1.1\bin\python.exe" -m unittest discover tests
  ```
  *Measured Runtime:* ~45.5 seconds (114 tests passing).
- **Publication Figures Generation (Figures 1–10):**
  ```powershell
  & "E:\Program Files\FreeCAD 1.1\bin\python.exe" src/generate_phase6_plots.py
  ```
- **Independent Orbital Verification via NASA GMAT:**
  ```powershell
  & "E:\NASA\GMAT-R2026a\bin\GmatConsole.exe" -r src/orbit/gmat_phase5_verification.script
  ```

---

## 2. Environment Verification Matrix

| Tool / Dependency | Expected Path | Verified Version | Tested Functionality | Status |
| :--- | :--- | :--- | :--- | :---: |
| **System Python** | `C:\Users\user\AppData\Local\Python\pythoncore-3.14-64\python.exe` | 3.14.5 | Unittest, NumPy RK4, YAML loading | **OPERATIONAL** |
| **NumPy (Sys)** | Standard site-packages | 2.5.3 | Array math, vector calculus | **OPERATIONAL** |
| **FreeCAD Python**| `E:\Program Files\FreeCAD 1.1\bin\python.exe` | 3.11.14 | SciPy DOP853, Matplotlib plotting | **OPERATIONAL** |
| **SciPy** | FreeCAD site-packages | 1.16.3 | Adaptive integration (`solve_ivp`) | **OPERATIONAL** |
| **Matplotlib** | FreeCAD site-packages | 3.10.8 | Publication 300 DPI plot generation | **OPERATIONAL** |
| **pandas** | FreeCAD site-packages | 2.3.3 | DataFrame analysis | **OPERATIONAL** |
| **FreeCAD API** | `FreeCAD`, `Part`, `Assembly` | 1.1.4 | B-Rep solid creation, assemblies | **OPERATIONAL** |
| **NASA GMAT** | `E:\NASA\GMAT-R2026a\bin\GmatConsole.exe` | Build Mar 26 2026 | Orbital propagation, J2 perturbation | **OPERATIONAL** |
| **SQLite3 Engine**| Python standard library | 3.45.1 | 100,065-record BOM spatial queries | **OPERATIONAL** |
