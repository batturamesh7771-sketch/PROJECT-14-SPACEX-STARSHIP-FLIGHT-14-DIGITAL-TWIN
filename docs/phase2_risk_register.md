# Starship Flight 14 Digital Engineering Project
## Phase 2: FreeCAD CAD Automation Risk Register & Mitigations

**Document ID:** `DOC-P2-RISK-001`  
**Revision:** `1.0.0`  
**Date:** `2026-10-24`  
**Author:** Senior Aerospace CAD Automation Engineer & Systems Architect  
**Classification:** Phase 2 Risk Management Baseline  

---

### 1. Risk Evaluation Framework

Phase 2 risks are evaluated using standard probability ($P \in [1, 5]$) and impact ($I \in [1, 5]$) criteria.

$$\text{Risk Score} = P \times I$$

---

### 2. Phase 2 Specific Engineering Risks

| Risk ID | Category | Description | P | I | Score | Proactive Engineering Mitigation Strategy | Fallback / Contingency | Residual Status |
| :--- | :--- | :--- | :---: | :---: | :---: | :--- | :--- | :--- |
| **CAD-RSK-01** | **Memory Exhaustion** | Modeling 100,000 individually detailed parametric features in a single document exhausts the 7.92 GB RAM. | 5 | 5 | **25** | Implement Multi-Resolution Assembly Architecture. Use `App::Link` and lightweight visual instances for repeating components (tiles, fasteners). | Cap native parametric solid count to primary structures; use BOM metadata for fastener counts. | **MITIGATED** |
| **CAD-RSK-02** | **Topological Naming** | Parametric dimensional changes in driver spreadsheet cause downstream face/edge renumbering (TNP), breaking sketches. | 4 | 4 | **16** | FreeCAD 1.1 includes the integrated Topological Naming Problem (TNP) algorithm. Bind all features to master skeleton Datum planes and coordinate axes rather than generated B-Rep faces. | Never attach sketches directly to generated fillets or chamfers; always reference master Datums. | **CONTROLLED** |
| **CAD-RSK-03** | **API Incompatibility**| Using deprecated Assembly4 / A2plus scripts or syntax from FreeCAD 0.20 causing runtime crashes in FreeCAD 1.1.4. | 4 | 4 | **16** | Strictly use the native FreeCAD 1.1 `Assembly::AssemblyObject` and `JointObject.py` API verified directly from FreeCAD's internal `AssemblyTests/TestCore.py`. | Audit all imports against native `E:\Program Files\FreeCAD 1.1\Mod\Assembly\`. | **MITIGATED** |
| **CAD-RSK-04** | **Headless CLI Limits**| Certain GUI-dependent methods (`FreeCADGui`, `ImportGui`, interactive task dialogs) fail in headless `freecadcmd.exe`. | 4 | 3 | **12** | Ensure all automation scripts operate exclusively on pure `FreeCAD` (`App`) document objects and `Import.export()`, completely bypassing `FreeCADGui`. | Implement headless conditionals: `if FreeCAD.GuiUp: ...`. | **MITIGATED** |
| **CAD-RSK-05** | **Solver Divergence** | Conflicting or redundant kinematic assembly joint constraints cause the Assembly solver to lock up or report singular Jacobian. | 3 | 4 | **12** | Enforce minimal kinematic constraint formulation: 1 Grounded joint on master frame, followed by exact single-DOF revolute joints for flaps and gimbal mounts. | Validate assembly degrees of freedom ($DOF$) analytically before triggering `assembly.solve()`. | **CONTROLLED** |
| **CAD-RSK-06** | **STEP File Bloat** | Exporting 100,000 individual solids into a single STEP file creates a multi-gigabyte text file that crashes downstream CFD/FEA meshing. | 4 | 4 | **16** | Export hierarchical, modular STEP files (`booster_aero.step`, `ship_aero.step`) containing only outer mold line (OML) surfaces for downstream CFD. | Exclude internal components, brackets, and fastener arrays from CFD/FEA geometry handoffs. | **MITIGATED** |
| **CAD-RSK-07** | **File Access Locks**| Windows file locking prevents overwriting active `.FCStd` or `.step` files during iterative macro execution. | 3 | 3 | **9** | Ensure automation scripts explicitly call `FreeCAD.closeDocument(doc.Name)` and use unique timestamped or staged file paths. | Pre-check write permissions and file lock handles before saving. | **MITIGATED** |
| **CAD-RSK-08** | **Drafting Slowdown** | TechDraw associative projection on massive assemblies takes excessive time or hangs on hidden line removal (HLR). | 3 | 3 | **9** | Generate 2D dimensioned drawings on simplified modular subassembly skeletons rather than dense fastener assemblies. | Use coarse HLR precision settings for large assemblies. | **CONTROLLED** |

---

### 3. Residual Risk Profile

With the Multi-Resolution Assembly Architecture, strict Datum-based sketching, and native FreeCAD 1.1 Assembly API adoption, **all high-severity risks are effectively mitigated**.
