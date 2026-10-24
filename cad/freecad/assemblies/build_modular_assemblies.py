"""
Starship Flight 14 — Modular Assembly Architecture (FreeCAD 1.1)
================================================================
Constructs the hierarchical engineering assemblies using native FreeCAD 1.1
Assembly workbench (Assembly::AssemblyObject and App::Link instances):

1. Assembly_Booster_Stage1.FCStd
   - Booster tank barrel (9m x 71m)
   - Booster thrust puck
   - 4x Titanium grid fins (spaced 90 deg at Z = 67m)
   - 33x Raptor 3 engines (1 center, 2 inner, 10 mid, 20 outer ring)

2. Assembly_Starship_Stage2.FCStd
   - Ship fuselage tanks (9m x 34.3m)
   - Ship ogive nose cone (16m)
   - Payload dispenser bay with PEZ slot
   - 2x Forward canard flaps (Z = 45m local)
   - 2x Aft aerodynamic delta flaps (Z = 3m local)
   - 6x Raptor 3 engines (3 center SL + 3 outer vacuum)

3. Assembly_Flight14_FullStack.FCStd
   - Stage 1 Booster Assembly (Z = 0)
   - Hot-Staging Vented Interstage (Z = 71m)
   - Stage 2 Starship Assembly (Z = 74.5m)
   - 26x Starlink V3 direct-to-cell satellites stacked in payload bay

Exports native .FCStd documents and neutral ISO-10303 STEP assemblies.
"""

import os
import sys
import math
import json
import FreeCAD as App
import Part
import Import

def build_all_assemblies():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(script_dir, "..", "..", ".."))

    parts_dir = os.path.join(project_root, "cad", "freecad", "parts")
    asy_dir = os.path.join(project_root, "cad", "freecad", "assemblies")
    os.makedirs(asy_dir, exist_ok=True)

    log_data = {
        "execution_engine": "FreeCAD 1.1.4 (cmdline)",
        "assemblies": []
    }

    print("=" * 80)
    print("  STARSHIP FLIGHT 14 — P2.2: MODULAR ENGINEERING ASSEMBLIES")
    print("=" * 80)

    # --------------------------------------------------------------------------
    # 1. ASSEMBLY: SUPER HEAVY BOOSTER (STAGE 1)
    # --------------------------------------------------------------------------
    booster_asy_path = os.path.join(asy_dir, "Assembly_Booster_Stage1.FCStd")
    booster_step_path = os.path.join(asy_dir, "Assembly_Booster_Stage1.step")

    # Open constituent parts
    doc_barrel = App.openDocument(os.path.join(parts_dir, "booster", "Booster_Tank_Barrel.FCStd"))
    barrel_obj = doc_barrel.getObject("Booster_Tank_Barrel")

    doc_puck = App.openDocument(os.path.join(parts_dir, "booster", "Booster_Thrust_Puck.FCStd"))
    puck_obj = doc_puck.getObject("Booster_Thrust_Puck")

    doc_fin = App.openDocument(os.path.join(parts_dir, "booster", "Booster_Grid_Fin.FCStd"))
    fin_obj = doc_fin.getObject("Booster_Grid_Fin")

    doc_rsl = App.openDocument(os.path.join(parts_dir, "propulsion", "Raptor3_Engine_SL.FCStd"))
    rsl_obj = doc_rsl.getObject("Raptor3_Engine_SL")

    # Create Booster Assembly document
    doc_ba = App.newDocument("Assembly_Booster_Stage1")
    doc_ba.saveAs(booster_asy_path)
    asy_booster = doc_ba.addObject("Assembly::AssemblyObject", "Assembly_Booster_Stage1")

    # 1.1 Add Barrel Link
    l_barrel = asy_booster.newObject("App::Link", "Occurrence_Booster_Barrel")
    l_barrel.setLink(barrel_obj)
    l_barrel.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation())

    # 1.2 Add Thrust Puck Link
    l_puck = asy_booster.newObject("App::Link", "Occurrence_Thrust_Puck")
    l_puck.setLink(puck_obj)
    l_puck.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation())

    # 1.3 Add 4 Grid Fins (at Z = 67,000 mm, R = 4500 mm, angles 0, 90, 180, 270)
    R_core = 4500.0
    Z_gridfin = 67000.0
    fin_angles = [0.0, 90.0, 180.0, 270.0]
    for i, ang in enumerate(fin_angles):
        rad = math.radians(ang)
        fx = R_core * math.cos(rad)
        fy = R_core * math.sin(rad)
        l_fin = asy_booster.newObject("App::Link", f"Occurrence_GridFin_{i+1:02d}")
        l_fin.setLink(fin_obj)
        # Rotate fin radially outward
        rot = App.Rotation(App.Vector(0, 0, 1), ang)
        l_fin.Placement = App.Placement(App.Vector(fx, fy, Z_gridfin), rot)

    # 1.4 Add 33 Raptor 3 Engines
    # Layout: Center (1), Inner ring (2), Middle ring (10), Outer ring (20)
    engine_coords = []
    # 1 center engine
    engine_coords.append((0.0, 0.0, 0.0, "Center_01"))
    # 2 inner ring engines (R = 1200 mm)
    for i, a in enumerate([0.0, 180.0]):
        r_rad = math.radians(a)
        engine_coords.append((1200.0 * math.cos(r_rad), 1200.0 * math.sin(r_rad), a, f"Inner_{i+1:02d}"))
    # 10 middle ring engines (R = 2300 mm)
    for i in range(10):
        a = i * 36.0
        r_rad = math.radians(a)
        engine_coords.append((2300.0 * math.cos(r_rad), 2300.0 * math.sin(r_rad), a, f"Middle_{i+1:02d}"))
    # 20 outer ring engines (R = 3800 mm)
    for i in range(20):
        a = i * 18.0
        r_rad = math.radians(a)
        engine_coords.append((3800.0 * math.cos(r_rad), 3800.0 * math.sin(r_rad), a, f"Outer_{i+1:02d}"))

    Z_engine_mount = -100.0 # Just below puck base
    for x, y, ang, tag in engine_coords:
        l_eng = asy_booster.newObject("App::Link", f"Occurrence_Raptor3_BST_{tag}")
        l_eng.setLink(rsl_obj)
        rot = App.Rotation(App.Vector(0, 0, 1), ang)
        l_eng.Placement = App.Placement(App.Vector(x, y, Z_engine_mount), rot)

    doc_ba.recompute()
    doc_ba.save()

    # Export Booster STEP
    solids_to_export = [l.Shape for l in doc_ba.Objects if hasattr(l, "Shape") and l.Shape.isValid()]
    Part.export(solids_to_export, booster_step_path)

    booster_stats = {
        "assembly_name": "Assembly_Booster_Stage1",
        "file_fcstd": booster_asy_path,
        "file_step": booster_step_path,
        "fcstd_bytes": os.path.getsize(booster_asy_path),
        "step_bytes": os.path.getsize(booster_step_path),
        "total_occurrences": len(engine_coords) + len(fin_angles) + 2,
        "engine_count": len(engine_coords),
        "gridfin_count": len(fin_angles),
    }
    log_data["assemblies"].append(booster_stats)
    print(f"  [ASSEMBLED] Booster Stage 1: {booster_stats['total_occurrences']} occurrences ({booster_stats['engine_count']} engines, {booster_stats['gridfin_count']} grid fins) | STEP: {booster_stats['step_bytes']:,} B")

    # --------------------------------------------------------------------------
    # 2. ASSEMBLY: STARSHIP UPPER STAGE (STAGE 2)
    # --------------------------------------------------------------------------
    ship_asy_path = os.path.join(asy_dir, "Assembly_Starship_Stage2.FCStd")
    ship_step_path = os.path.join(asy_dir, "Assembly_Starship_Stage2.step")

    # Open constituent parts
    doc_sf = App.openDocument(os.path.join(parts_dir, "ship", "Ship_Fuselage_Tanks.FCStd"))
    sf_obj = doc_sf.getObject("Ship_Fuselage_Tanks")

    doc_sn = App.openDocument(os.path.join(parts_dir, "ship", "Ship_Nose_Cone.FCStd"))
    sn_obj = doc_sn.getObject("Ship_Nose_Cone")

    doc_pb = App.openDocument(os.path.join(parts_dir, "ship", "Payload_Dispenser_Bay.FCStd"))
    pb_obj = doc_pb.getObject("Payload_Dispenser_Bay")

    doc_ff = App.openDocument(os.path.join(parts_dir, "ship", "Ship_Forward_Flap.FCStd"))
    ff_obj = doc_ff.getObject("Ship_Forward_Flap")

    doc_af = App.openDocument(os.path.join(parts_dir, "ship", "Ship_Aft_Flap.FCStd"))
    af_obj = doc_af.getObject("Ship_Aft_Flap")

    doc_rvac = App.openDocument(os.path.join(parts_dir, "propulsion", "Raptor3_Engine_Vac.FCStd"))
    rvac_obj = doc_rvac.getObject("Raptor3_Engine_Vac")

    doc_sa = App.newDocument("Assembly_Starship_Stage2")
    doc_sa.saveAs(ship_asy_path)
    asy_ship = doc_sa.addObject("Assembly::AssemblyObject", "Assembly_Starship_Stage2")

    # 2.1 Ship Fuselage Tanks (Z = 0 local)
    l_sf = asy_ship.newObject("App::Link", "Occurrence_Ship_Fuselage")
    l_sf.setLink(sf_obj)
    l_sf.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation())

    # 2.2 Ship Nose Cone (Z = 34,300 mm local)
    l_sn = asy_ship.newObject("App::Link", "Occurrence_Ship_Nose")
    l_sn.setLink(sn_obj)
    l_sn.Placement = App.Placement(App.Vector(0, 0, 34300.0), App.Rotation())

    # 2.3 Payload Dispenser Bay (Z = 17,000 mm local)
    l_pb = asy_ship.newObject("App::Link", "Occurrence_Payload_Bay")
    l_pb.setLink(pb_obj)
    l_pb.Placement = App.Placement(App.Vector(0, 0, 17000.0), App.Rotation())

    # 2.4 Forward Flaps (2x at Z = 45,000 mm local, Port +Y, Starboard -Y)
    Z_ff = 45000.0
    l_ff_p = asy_ship.newObject("App::Link", "Occurrence_Forward_Flap_Port")
    l_ff_p.setLink(ff_obj)
    l_ff_p.Placement = App.Placement(App.Vector(0, R_core, Z_ff), App.Rotation(App.Vector(0, 0, 1), 90.0))

    l_ff_s = asy_ship.newObject("App::Link", "Occurrence_Forward_Flap_Starboard")
    l_ff_s.setLink(ff_obj)
    l_ff_s.Placement = App.Placement(App.Vector(0, -R_core, Z_ff), App.Rotation(App.Vector(0, 0, 1), -90.0))

    # 2.5 Aft Flaps (2x at Z = 3,000 mm local, Port +Y, Starboard -Y)
    Z_af = 3000.0
    l_af_p = asy_ship.newObject("App::Link", "Occurrence_Aft_Flap_Port")
    l_af_p.setLink(af_obj)
    l_af_p.Placement = App.Placement(App.Vector(0, R_core, Z_af), App.Rotation(App.Vector(0, 0, 1), 90.0))

    l_af_s = asy_ship.newObject("App::Link", "Occurrence_Aft_Flap_Starboard")
    l_af_s.setLink(af_obj)
    l_af_s.Placement = App.Placement(App.Vector(0, -R_core, Z_af), App.Rotation(App.Vector(0, 0, 1), -90.0))

    # 2.6 6x Raptor Engines: 3 Center Sea-Level + 3 Outer Vacuum
    # 3 SL center engines at R = 1200 mm (0, 120, 240 deg)
    for i, a in enumerate([0.0, 120.0, 240.0]):
        rad = math.radians(a)
        l_rsl = asy_ship.newObject("App::Link", f"Occurrence_Raptor3_SHP_SL_{i+1:02d}")
        l_rsl.setLink(rsl_obj)
        l_rsl.Placement = App.Placement(App.Vector(1200.0 * math.cos(rad), 1200.0 * math.sin(rad), -100.0), App.Rotation(App.Vector(0, 0, 1), a))

    # 3 Vacuum engines at R = 2700 mm (60, 180, 300 deg)
    for i, a in enumerate([60.0, 180.0, 300.0]):
        rad = math.radians(a)
        l_rvac = asy_ship.newObject("App::Link", f"Occurrence_Raptor3_SHP_VAC_{i+1:02d}")
        l_rvac.setLink(rvac_obj)
        l_rvac.Placement = App.Placement(App.Vector(2700.0 * math.cos(rad), 2700.0 * math.sin(rad), -100.0), App.Rotation(App.Vector(0, 0, 1), a))

    doc_sa.recompute()
    doc_sa.save()

    # Export Ship STEP
    ship_solids = [l.Shape for l in doc_sa.Objects if hasattr(l, "Shape") and l.Shape.isValid()]
    Part.export(ship_solids, ship_step_path)

    ship_stats = {
        "assembly_name": "Assembly_Starship_Stage2",
        "file_fcstd": ship_asy_path,
        "file_step": ship_step_path,
        "fcstd_bytes": os.path.getsize(ship_asy_path),
        "step_bytes": os.path.getsize(ship_step_path),
        "total_occurrences": 3 + 4 + 6,
        "engine_count": 6,
        "flap_count": 4,
    }
    log_data["assemblies"].append(ship_stats)
    print(f"  [ASSEMBLED] Starship Stage 2: {ship_stats['total_occurrences']} occurrences (6 engines, 4 flaps) | STEP: {ship_stats['step_bytes']:,} B")

    # --------------------------------------------------------------------------
    # 3. ASSEMBLY: STARSHIP FLIGHT 14 FULL STACK MASTER
    # --------------------------------------------------------------------------
    full_asy_path = os.path.join(asy_dir, "Assembly_Flight14_FullStack.FCStd")
    full_step_path = os.path.join(asy_dir, "Assembly_Flight14_FullStack.step")

    # Open Interstage & Payload
    doc_is = App.openDocument(os.path.join(parts_dir, "interstage", "Hot_Staging_Ring.FCStd"))
    is_obj = doc_is.getObject("Hot_Staging_Ring")

    doc_sat = App.openDocument(os.path.join(parts_dir, "payload", "Starlink_V3_Satellite.FCStd"))
    sat_obj = doc_sat.getObject("Starlink_V3_Satellite")

    doc_fs = App.newDocument("Assembly_Flight14_FullStack")
    doc_fs.saveAs(full_asy_path)
    asy_fs = doc_fs.addObject("Assembly::AssemblyObject", "Assembly_Flight14_FullStack")

    # 3.1 Link Booster Assembly (Z = 0)
    l_bst_asm = asy_fs.newObject("App::Link", "Subassembly_Booster_Stage1")
    l_bst_asm.setLink(asy_booster)
    l_bst_asm.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation())

    # 3.2 Link Hot Staging Interstage (Z = 71,000 mm)
    l_is = asy_fs.newObject("App::Link", "Occurrence_Hot_Staging_Ring")
    l_is.setLink(is_obj)
    l_is.Placement = App.Placement(App.Vector(0, 0, 71000.0), App.Rotation())

    # 3.3 Link Starship Upper Stage Assembly (Z = 74,500 mm)
    l_shp_asm = asy_fs.newObject("App::Link", "Subassembly_Starship_Stage2")
    l_shp_asm.setLink(asy_ship)
    l_shp_asm.Placement = App.Placement(App.Vector(0, 0, 74500.0), App.Rotation())

    # 3.4 Link 26 Starlink V3 Satellites in Payload Bay (Z = 91,500 mm to 98,000 mm)
    Z_sat_base = 91500.0
    sat_spacing = 250.0 # 250 mm stack pitch
    for i in range(26):
        z_pos = Z_sat_base + i * sat_spacing
        l_sat = asy_fs.newObject("App::Link", f"Occurrence_Starlink_V3_{i+1:02d}")
        l_sat.setLink(sat_obj)
        l_sat.Placement = App.Placement(App.Vector(0, 0, z_pos), App.Rotation())

    doc_fs.recompute()
    doc_fs.save()

    # Export Full Stack STEP
    fs_solids = [l.Shape for l in doc_fs.Objects if hasattr(l, "Shape") and l.Shape.isValid()]
    Part.export(fs_solids, full_step_path)

    fs_stats = {
        "assembly_name": "Assembly_Flight14_FullStack",
        "file_fcstd": full_asy_path,
        "file_step": full_step_path,
        "fcstd_bytes": os.path.getsize(full_asy_path),
        "step_bytes": os.path.getsize(full_step_path),
        "total_top_occurrences": 3 + 26, # Booster + Interstage + Ship + 26 Sats
        "subassemblies_count": 2,
        "payload_count": 26,
    }
    log_data["assemblies"].append(fs_stats)
    print(f"  [ASSEMBLED] Flight 14 Full Stack: {fs_stats['total_top_occurrences']} occurrences (2 subassemblies, 26 satellites) | STEP: {fs_stats['step_bytes']:,} B")

    # Close documents
    for d in [doc_barrel, doc_puck, doc_fin, doc_rsl, doc_sf, doc_sn, doc_pb, doc_ff, doc_af, doc_rvac, doc_is, doc_sat, doc_ba, doc_sa, doc_fs]:
        try:
            App.closeDocument(d.Name)
        except Exception:
            pass

    # Save log
    log_path = os.path.join(asy_dir, "assembly_build_log.json")
    with open(log_path, "w", encoding="utf-8") as lf:
        json.dump(log_data, lf, indent=2)

    print("=" * 80)
    print("  P2.2 MODULAR ENGINEERING ASSEMBLIES COMPLETED SUCCESSFULLY")
    print(f"  Log saved: {log_path}")
    print("=" * 80)

# Run unconditionally
build_all_assemblies()
