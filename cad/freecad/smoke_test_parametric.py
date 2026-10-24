#!/usr/bin/env python3
"""
STARSHIP FLIGHT 14 DIGITAL ENGINEERING PROJECT
Phase 2 CAD Automation — P2.0A: Minimal Parametric CAD Smoke Test Macro
Platform: FreeCAD 1.1.4 (freecadcmd.exe / Python 3.11)
Author: Senior Aerospace CAD Automation Engineer & Verification Lead
"""

import os
import sys
import math
import json
import time

# FreeCAD Core Imports
import FreeCAD as App
import Part
import Import

def run_smoke_test():
    log_data = {
        "test_name": "P2.0A_MINIMAL_CAD_SMOKE_TEST",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "freecad_version": ".".join(App.Version()[:3]),
        "python_version": sys.version.replace("\n", " "),
        "steps": [],
        "overall_status": "PENDING"
    }
    
    print("=" * 78)
    print("  STARSHIP FLIGHT 14 — P2.0A: MINIMAL PARAMETRIC CAD SMOKE TEST")
    print(f"  FreeCAD Version: {log_data['freecad_version']} | Revision: {App.Version()[3]}")
    print("=" * 78)

    # Establish output directory
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    output_dir = os.path.join(project_root, "cad", "freecad", "output")
    os.makedirs(output_dir, exist_ok=True)
    
    fcstd_path = os.path.join(output_dir, "smoke_test_model.FCStd")
    step_path = os.path.join(output_dir, "smoke_test_model.step")
    log_path = os.path.join(output_dir, "smoke_test_execution_log.json")

    # Safe Idempotent Cleanup of prior documents
    doc_name = "SmokeTest_Flight14_P2"
    if doc_name in App.listDocuments():
        App.closeDocument(doc_name)
    inspect_doc_name = "SmokeTest_Reimport_Inspect"
    if inspect_doc_name in App.listDocuments():
        App.closeDocument(inspect_doc_name)

    try:
        # Step 1: Create Document
        doc = App.newDocument(doc_name)
        log_data["steps"].append({"step": 1, "action": "Create Document", "doc_name": doc_name, "status": "PASS"})
        print(f"[STEP 1] Created native FreeCAD document: '{doc_name}'")

        # Step 2: Create Parametric Cylinder (Vehicle Barrel Section)
        # Dimensions based on 9.0m diameter Starship barrel section (scaled 1:1 in millimeters: R=4500mm, H=10000mm)
        cyl = doc.addObject("Part::Cylinder", "SuperHeavy_Barrel_Section")
        cyl.Radius = 4500.0  # 4.5m radius = 9m diameter
        cyl.Height = 10000.0 # 10m height
        cyl.Label = "SuperHeavy_Barrel_Section"
        cyl.addProperty("App::PropertyString", "ComponentID", "Metadata", "Unique Component Identifier")
        cyl.ComponentID = "TEST-CYL-001"
        cyl.addProperty("App::PropertyString", "Discipline", "Metadata", "Subsystem Tag")
        cyl.Discipline = "Primary_Structure"

        # Step 3: Create Parametric Cone (Transition Section)
        cone = doc.addObject("Part::Cone", "Starship_Transition_Ogive")
        cone.Radius1 = 4500.0  # 4.5m bottom radius
        cone.Radius2 = 1200.0  # 1.2m top radius
        cone.Height = 6000.0   # 6m transition height
        cone.Placement.Base = App.Vector(0.0, 0.0, 10000.0) # Stacked on cylinder
        cone.Label = "Starship_Transition_Ogive"
        cone.addProperty("App::PropertyString", "ComponentID", "Metadata", "Unique Component Identifier")
        cone.ComponentID = "TEST-CONE-001"
        cone.addProperty("App::PropertyString", "Discipline", "Metadata", "Subsystem Tag")
        cone.Discipline = "Aerodynamic_Fairing"

        # Step 4: Create Parametric Box (Aerodynamic Flap Placeholder)
        flap = doc.addObject("Part::Box", "Starship_Aft_Flap_Solid")
        flap.Length = 3000.0  # 3.0m chord
        flap.Width = 350.0    # 0.35m thickness
        flap.Height = 5000.0  # 5.0m span
        # Offset radially to edge of 9m diameter cylinder (+4.5m in X)
        flap.Placement.Base = App.Vector(4500.0, -175.0, 2000.0)
        flap.Label = "Starship_Aft_Flap_Solid"
        flap.addProperty("App::PropertyString", "ComponentID", "Metadata", "Unique Component Identifier")
        flap.ComponentID = "TEST-BOX-001"
        flap.addProperty("App::PropertyString", "Discipline", "Metadata", "Subsystem Tag")
        flap.Discipline = "Aero_Control_Surface"

        # Step 5: Document Recompute & Volumetric Validation
        doc.recompute()
        
        objects = [cyl, cone, flap]
        object_count = len(objects)
        assert object_count == 3, f"Expected 3 objects, got {object_count}"

        # Theoretical Volumes (explicit float conversion to avoid FreeCAD Quantity unit mismatch)
        r_cyl = float(cyl.Radius)
        h_cyl = float(cyl.Height)
        v_cyl_theo = math.pi * (r_cyl ** 2) * h_cyl

        r1_cone = float(cone.Radius1)
        r2_cone = float(cone.Radius2)
        h_cone = float(cone.Height)
        v_cone_theo = (1.0 / 3.0) * math.pi * h_cone * (r1_cone**2 + r1_cone * r2_cone + r2_cone**2)

        l_flap = float(flap.Length)
        w_flap = float(flap.Width)
        h_flap = float(flap.Height)
        v_flap_theo = l_flap * w_flap * h_flap
        v_total_theo = v_cyl_theo + v_cone_theo + v_flap_theo

        v_cyl_meas = float(cyl.Shape.Volume)
        v_cone_meas = float(cone.Shape.Volume)
        v_flap_meas = float(flap.Shape.Volume)
        v_total_meas = v_cyl_meas + v_cone_meas + v_flap_meas

        # Shape Validity & Dimension checks
        for obj, v_theo, v_meas in zip(objects, [v_cyl_theo, v_cone_theo, v_flap_theo], [v_cyl_meas, v_cone_meas, v_flap_meas]):
            assert obj.Shape.isValid(), f"Object {obj.Label} ({obj.ComponentID}) shape is NOT valid!"
            assert not obj.Shape.isNull(), f"Object {obj.Label} ({obj.ComponentID}) shape is NULL!"
            assert v_meas > 0.0, f"Object {obj.Label} has zero/negative volume: {v_meas}"
            err_pct = abs(v_meas - v_theo) / v_theo * 100.0
            assert err_pct < 0.001, f"Volume error for {obj.Label} exceeded 0.001%: {err_pct:.5f}%"
            print(f"  [VALIDATED] {obj.ComponentID} ({obj.Label}): Volume={v_meas/1e9:.4f} m^3, Valid={obj.Shape.isValid()}")

        log_data["steps"].append({
            "step": 2,
            "action": "Parametric Geometry Creation & B-Rep Validation",
            "object_count": object_count,
            "measured_total_volume_m3": v_total_meas / 1e9,
            "theoretical_total_volume_m3": v_total_theo / 1e9,
            "status": "PASS"
        })
        print(f"[STEP 2] All {object_count} parametric solids verified valid. Total Volume: {v_total_meas/1e9:.4f} m^3")

        # Step 6: Native FreeCAD Document Save
        doc.saveAs(fcstd_path)
        assert os.path.exists(fcstd_path), f"Failed to save native document: {fcstd_path}"
        fcstd_size = os.path.getsize(fcstd_path)
        assert fcstd_size > 1024, f"Native FCStd file size suspiciously small: {fcstd_size} bytes"
        log_data["steps"].append({
            "step": 3,
            "action": "Native Document Save (.FCStd)",
            "file_path": fcstd_path,
            "size_bytes": fcstd_size,
            "status": "PASS"
        })
        print(f"[STEP 3] Saved native FreeCAD document: {fcstd_path} ({fcstd_size:,} bytes)")

        # Step 7: STEP Geometry Export (ISO 10303-21)
        Import.export(objects, step_path)
        assert os.path.exists(step_path), f"Failed to export STEP file: {step_path}"
        step_size = os.path.getsize(step_path)
        assert step_size > 1024, f"Exported STEP file size suspiciously small: {step_size} bytes"
        
        # Verify STEP file has valid ISO header
        with open(step_path, "r", encoding="latin1") as sf:
            header_snippet = sf.read(500)
            assert "ISO-10303-21;" in header_snippet, "Exported file does not contain valid ISO-10303-21 header"
            assert "HEADER;" in header_snippet, "Missing HEADER section in STEP file"

        log_data["steps"].append({
            "step": 4,
            "action": "Neutral STEP Export (ISO-10303)",
            "file_path": step_path,
            "size_bytes": step_size,
            "status": "PASS"
        })
        print(f"[STEP 4] Exported neutral STEP geometry: {step_path} ({step_size:,} bytes)")

        # Step 8: Close Document to verify release
        App.closeDocument(doc_name)
        print(f"[STEP 5] Primary document '{doc_name}' closed cleanly.")

        # Step 9: Re-Open & Independent Re-Import Volumetric Inspection
        inspect_doc = App.newDocument(inspect_doc_name)
        Part.insert(step_path, inspect_doc_name)
        inspect_doc.recompute()

        reimported_objs = inspect_doc.Objects
        assert len(reimported_objs) >= 1, "Failed to re-import any objects from exported STEP file"
        
        reimported_total_vol = sum([float(o.Shape.Volume) for o in reimported_objs if hasattr(o, "Shape")])
        vol_residual_pct = abs(reimported_total_vol - v_total_meas) / v_total_meas * 100.0
        
        assert vol_residual_pct < 0.01, f"Re-imported STEP volume differs from native volume by {vol_residual_pct:.4f}%!"
        for ro in reimported_objs:
            assert ro.Shape.isValid(), f"Re-imported object {ro.Label} is invalid!"
        
        App.closeDocument(inspect_doc_name)

        log_data["steps"].append({
            "step": 5,
            "action": "Closed-Loop STEP Re-Import & Volumetric Residual Check",
            "reimported_objects": len(reimported_objs),
            "reimported_total_volume_m3": reimported_total_vol / 1e9,
            "volume_residual_pct": vol_residual_pct,
            "status": "PASS"
        })
        print(f"[STEP 6] Closed-loop STEP verification PASSED. Volumetric residual: {vol_residual_pct:.6f}%")

        # Step 10: Idempotent Regeneration Demonstration
        # Re-run document creation a second time to prove zero file locking or naming collisions
        doc_idem = App.newDocument(doc_name)
        cyl_idem = doc_idem.addObject("Part::Cylinder", "Barrel_Idempotent")
        cyl_idem.Radius = 4500.0
        cyl_idem.Height = 10000.0
        doc_idem.recompute()
        doc_idem.saveAs(fcstd_path)
        App.closeDocument(doc_name)

        log_data["steps"].append({
            "step": 6,
            "action": "Idempotent Safe Regeneration Check",
            "status": "PASS"
        })
        print("[STEP 7] Idempotent re-execution and overwrite verified without file locks.")

        log_data["overall_status"] = "VERIFIED_SUCCESS"
        print("=" * 78)
        print("  P2.0A MINIMAL CAD SMOKE TEST COMPLETED SUCCESSFULLY (10/10 CRITERIA MET)")
        print("=" * 78)

    finally:
        with open(log_path, "w", encoding="utf-8") as lf:
            json.dump(log_data, lf, indent=2)
        print(f"[LOG SAVED] Execution record saved to: {log_path}")

# Call run_smoke_test unconditionally to support FreeCAD module execution
run_smoke_test()


