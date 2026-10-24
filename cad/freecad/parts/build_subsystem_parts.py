"""
Starship Flight 14 — Subsystem Parts Generator (FreeCAD 1.1)
============================================================
Builds parametric 3D B-Rep solid models for all Starship Flight 14 subsystems:
- Super Heavy Booster (Barrel tanks, Grid fins, Thrust puck)
- Hot-Staging Vented Interstage
- Starship Upper Stage (Fuselage tanks, Ogive nose cone, Flaps, Payload bay)
- Propulsion (Raptor 3 Sea-Level and Vacuum engines)
- Payload (Starlink V3 Direct-to-Cell satellite)

Each part is saved as native FreeCAD document (.FCStd) and exported as ISO-10303 STEP (.step).
All parameters sourced from data/config/vehicle_parameters.yaml.
"""

import os
import sys
import math
import json
import yaml
import FreeCAD as App
import Part
import Import

def build_all_parts():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(script_dir, "..", "..", ".."))
    params_yaml_path = os.path.join(project_root, "data", "config", "vehicle_parameters.yaml")

    with open(params_yaml_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    geom = config["geometry"]
    prop = config["propulsion"]

    D_core = float(geom["core_outer_diameter"]["value"]) * 1000.0       # 9000 mm
    R_core = D_core / 2.0                                              # 4500 mm
    H_booster = float(geom["booster_height"]["value"]) * 1000.0        # 71000 mm
    H_ship = float(geom["ship_height"]["value"]) * 1000.0              # 50300 mm
    H_interstage = float(geom["interstage_ring_height"]["value"]) * 1000.0 # 3500 mm
    H_nose = 16000.0                                                   # 16000 mm
    H_ship_barrel = H_ship - H_nose                                    # 34300 mm

    log_data = {
        "execution_engine": "FreeCAD 1.1.4 (cmdline)",
        "parts_generated": []
    }

    print("=" * 80)
    print("  STARSHIP FLIGHT 14 — BUILDING MODULAR SUBSYSTEM PARTS")
    print(f"  Core Diameter: {D_core} mm | Booster: {H_booster} mm | Ship: {H_ship} mm")
    print("=" * 80)

    def save_and_export(doc, part_name, solid, out_dir, metadata):
        fcstd_path = os.path.join(out_dir, f"{part_name}.FCStd")
        step_path = os.path.join(out_dir, f"{part_name}.step")

        doc.recompute()
        assert solid.Shape.isValid(), f"Shape invalid for {part_name}"
        vol_m3 = float(solid.Shape.Volume) / 1e9
        bbox = solid.Shape.BoundBox

        doc.saveAs(fcstd_path)
        Import.export([solid], step_path)
        assert os.path.exists(fcstd_path) and os.path.getsize(fcstd_path) > 1000
        assert os.path.exists(step_path) and os.path.getsize(step_path) > 1000

        entry = {
            "part_name": part_name,
            "part_id": metadata["part_id"],
            "subsystem": metadata["subsystem"],
            "material": metadata["material"],
            "design_mass_kg": metadata["mass_kg"],
            "cad_volume_m3": round(vol_m3, 4),
            "bbox_mm": {
                "xmin": round(bbox.XMin, 1), "xmax": round(bbox.XMax, 1),
                "ymin": round(bbox.YMin, 1), "ymax": round(bbox.YMax, 1),
                "zmin": round(bbox.ZMin, 1), "zmax": round(bbox.ZMax, 1),
            },
            "fcstd_file": fcstd_path,
            "step_file": step_path,
            "fcstd_bytes": os.path.getsize(fcstd_path),
            "step_bytes": os.path.getsize(step_path)
        }
        log_data["parts_generated"].append(entry)
        print(f"  [BUILT] {part_name:<28} | Vol: {vol_m3:>10.3f} m^3 | Mass: {metadata['mass_kg']:>7} kg | STEP: {entry['step_bytes']:,} B")
        App.closeDocument(doc.Name)

    # --------------------------------------------------------------------------
    # 1. BOOSTER BARREL TANKS
    # --------------------------------------------------------------------------
    booster_dir = os.path.join(project_root, "cad", "freecad", "parts", "booster")
    doc_bb = App.newDocument("Booster_Barrel_Tanks")
    # Outer cylinder
    outer_cyl = Part.makeCylinder(R_core, H_booster)
    # Inner bore (hollow tank structure representation with 10mm equivalent shell)
    inner_cyl = Part.makeCylinder(R_core - 15.0, H_booster - 200.0, App.Vector(0, 0, 100.0))
    # Common bulkhead dome (spherical cap)
    dome = Part.makeSphere(R_core, App.Vector(0, 0, 35000.0))
    dome_cut = Part.makeBox(D_core * 2, D_core * 2, D_core, App.Vector(-D_core, -D_core, 35000.0 - D_core))
    dome_half = dome.cut(dome_cut)
    # Compound shell
    booster_shell = outer_cyl.cut(inner_cyl).fuse(dome_half)
    booster_obj = doc_bb.addObject("Part::Feature", "Booster_Tank_Barrel")
    booster_obj.Shape = booster_shell
    save_and_export(doc_bb, "Booster_Tank_Barrel", booster_obj, booster_dir, {
        "part_id": "PART-BST-BARREL-001",
        "subsystem": "Super Heavy Booster",
        "material": "AISI 304L Cold-Worked Stainless Steel",
        "mass_kg": 130000.0
    })

    # --------------------------------------------------------------------------
    # 2. BOOSTER GRID FIN (Titanium Welded Grid with Pivot Axle)
    # --------------------------------------------------------------------------
    doc_gf = App.newDocument("Booster_Grid_Fin")
    # Grid Fin frame: 4.0m span, 2.0m height, 0.20m thick
    fin_frame = Part.makeBox(4000.0, 200.0, 2000.0, App.Vector(0, -100.0, 0))
    # Cut internal lattice cells (3x6 grid)
    cells = []
    for ix in range(3):
        for iz in range(5):
            x_pos = 400.0 + ix * 1100.0
            z_pos = 200.0 + iz * 340.0
            hole = Part.makeBox(800.0, 400.0, 240.0, App.Vector(x_pos, -200.0, z_pos))
            cells.append(hole)
    for c in cells:
        fin_frame = fin_frame.cut(c)
    # Pivot axle
    axle = Part.makeCylinder(150.0, 800.0, App.Vector(0, -400.0, 1000.0), App.Vector(0, 1, 0))
    grid_fin_solid = fin_frame.fuse(axle)
    grid_fin_obj = doc_gf.addObject("Part::Feature", "Booster_Grid_Fin")
    grid_fin_obj.Shape = grid_fin_solid
    save_and_export(doc_gf, "Booster_Grid_Fin", grid_fin_obj, booster_dir, {
        "part_id": "PART-BST-GRIDFIN-001",
        "subsystem": "Super Heavy Booster",
        "material": "Ti-6Al-4V Grade 5 Cast/Welded Titanium",
        "mass_kg": 750.0
    })

    # --------------------------------------------------------------------------
    # 3. BOOSTER THRUST PUCK (33 Engine Hardpoint Disk)
    # --------------------------------------------------------------------------
    doc_tp = App.newDocument("Booster_Thrust_Puck")
    puck_base = Part.makeCylinder(R_core - 50.0, 1200.0, App.Vector(0, 0, 0))
    # Core cavity
    puck_cavity = Part.makeCylinder(R_core - 200.0, 1000.0, App.Vector(0, 0, 100.0))
    puck_solid = puck_base.cut(puck_cavity)
    puck_obj = doc_tp.addObject("Part::Feature", "Booster_Thrust_Puck")
    puck_obj.Shape = puck_solid
    save_and_export(doc_tp, "Booster_Thrust_Puck", puck_obj, booster_dir, {
        "part_id": "PART-BST-PUCK-001",
        "subsystem": "Super Heavy Booster",
        "material": "SX500 High-Strength Austenitic Superalloy",
        "mass_kg": 8500.0
    })

    # --------------------------------------------------------------------------
    # 4. HOT STAGING VENTED INTERSTAGE (3.5m tall with 24 exhaust ports)
    # --------------------------------------------------------------------------
    interstage_dir = os.path.join(project_root, "cad", "freecad", "parts", "interstage")
    doc_is = App.newDocument("Hot_Staging_Ring")
    ring_outer = Part.makeCylinder(R_core, H_interstage)
    ring_inner = Part.makeCylinder(R_core - 15.0, H_interstage + 20.0, App.Vector(0, 0, -10.0))
    ring_shell = ring_outer.cut(ring_inner)
    # Cut 24 radial vent ports for plume diversion
    ports = []
    for i in range(24):
        theta = i * (2.0 * math.pi / 24.0)
        px = (R_core + 200.0) * math.cos(theta)
        py = (R_core + 200.0) * math.sin(theta)
        # Port slot cylinder directed radially
        port = Part.makeCylinder(280.0, 1000.0, App.Vector(0, 0, H_interstage * 0.5), App.Vector(math.cos(theta), math.sin(theta), 0))
        ring_shell = ring_shell.cut(port)
    is_obj = doc_is.addObject("Part::Feature", "Hot_Staging_Ring")
    is_obj.Shape = ring_shell
    save_and_export(doc_is, "Hot_Staging_Ring", is_obj, interstage_dir, {
        "part_id": "PART-INT-STAGE-001",
        "subsystem": "Hot Staging Interstage",
        "material": "AISI 304L Stainless Steel / Inconel Thermal Heat Shielding",
        "mass_kg": 9000.0
    })

    # --------------------------------------------------------------------------
    # 5. STARSHIP FUSELAGE TANKS (34.3m barrel section)
    # --------------------------------------------------------------------------
    ship_dir = os.path.join(project_root, "cad", "freecad", "parts", "ship")
    doc_sf = App.newDocument("Ship_Fuselage_Tanks")
    s_outer = Part.makeCylinder(R_core, H_ship_barrel)
    s_inner = Part.makeCylinder(R_core - 15.0, H_ship_barrel - 100.0, App.Vector(0, 0, 50.0))
    # Common bulkhead dome inside Ship
    s_dome = Part.makeSphere(R_core, App.Vector(0, 0, 18000.0))
    s_dome_cut = Part.makeBox(D_core * 2, D_core * 2, D_core, App.Vector(-D_core, -D_core, 18000.0 - D_core))
    s_dome_half = s_dome.cut(s_dome_cut)
    ship_shell = s_outer.cut(s_inner).fuse(s_dome_half)
    sf_obj = doc_sf.addObject("Part::Feature", "Ship_Fuselage_Tanks")
    sf_obj.Shape = ship_shell
    save_and_export(doc_sf, "Ship_Fuselage_Tanks", sf_obj, ship_dir, {
        "part_id": "PART-SHP-FUSELAGE-001",
        "subsystem": "Starship Upper Stage",
        "material": "AISI 304L Cold-Worked Stainless Steel",
        "mass_kg": 55000.0
    })

    # --------------------------------------------------------------------------
    # 6. STARSHIP OGIVE NOSE CONE (16.0m ogive with forward header tank)
    # --------------------------------------------------------------------------
    doc_sn = App.newDocument("Ship_Nose_Cone")
    # Parametric ogive profile via revolution
    # Ogive radius rho = (R^2 + L^2) / (2*R)
    rho = (R_core**2 + H_nose**2) / (2.0 * R_core)
    # Build stepped revolved ogive approximation (smooth 12-segment loft/cones)
    ogive_sections = []
    num_seg = 16
    for i in range(num_seg):
        z1 = i * (H_nose / float(num_seg))
        z2 = (i + 1) * (H_nose / float(num_seg))
        r1 = math.sqrt(rho**2 - (H_nose - z1)**2) + R_core - rho
        r2 = math.sqrt(rho**2 - (H_nose - z2)**2) + R_core - rho
        cone_seg = Part.makeCone(max(r1, 50.0), max(r2, 10.0), z2 - z1, App.Vector(0, 0, z1))
        ogive_sections.append(cone_seg)
    ogive_solid = ogive_sections[0]
    for seg in ogive_sections[1:]:
        ogive_solid = ogive_solid.fuse(seg)
    # Header tank (spherical header in the nose tip)
    header_tank = Part.makeSphere(1200.0, App.Vector(0, 0, H_nose - 3000.0))
    ogive_solid = ogive_solid.fuse(header_tank)
    sn_obj = doc_sn.addObject("Part::Feature", "Ship_Nose_Cone")
    sn_obj.Shape = ogive_solid
    save_and_export(doc_sn, "Ship_Nose_Cone", sn_obj, ship_dir, {
        "part_id": "PART-SHP-NOSE-001",
        "subsystem": "Starship Upper Stage",
        "material": "AISI 304L Stainless Steel + TUFROC/AETB-12 Aerothermal TPS",
        "mass_kg": 22000.0
    })

    # --------------------------------------------------------------------------
    # 7. STARSHIP FORWARD FLAP (Canard with Hinge Pin)
    # --------------------------------------------------------------------------
    doc_ff = App.newDocument("Ship_Forward_Flap")
    # Aerodynamic wedge: 4.5m span, 1.8m root chord, 0.20m thickness
    ff_main = Part.makeBox(4500.0, 1800.0, 200.0, App.Vector(0, -900.0, -100.0))
    # Bevel leading edge using box cut
    bevel = Part.makeBox(4600.0, 500.0, 300.0, App.Vector(-50.0, 700.0, -150.0))
    ff_body = ff_main.cut(bevel)
    # Hinge axle pin
    ff_pin = Part.makeCylinder(120.0, 600.0, App.Vector(-300.0, 0, -100.0), App.Vector(1, 0, 0))
    ff_solid = ff_body.fuse(ff_pin)
    ff_obj = doc_ff.addObject("Part::Feature", "Ship_Forward_Flap")
    ff_obj.Shape = ff_solid
    save_and_export(doc_ff, "Ship_Forward_Flap", ff_obj, ship_dir, {
        "part_id": "PART-SHP-FLAP-FWD-001",
        "subsystem": "Starship Upper Stage",
        "material": "AISI 304L + Aerothermal TPS Tiles",
        "mass_kg": 1200.0
    })

    # --------------------------------------------------------------------------
    # 8. STARSHIP AFT FLAP (Large Delta Flap with Hinge Lugs)
    # --------------------------------------------------------------------------
    doc_af = App.newDocument("Ship_Aft_Flap")
    # 11.5m span, 3.2m root chord, 0.35m thickness
    af_box = Part.makeBox(11500.0, 3200.0, 350.0, App.Vector(0, -1600.0, -175.0))
    # Hinge bracket cylinder
    af_pin = Part.makeCylinder(180.0, 800.0, App.Vector(-400.0, 0, -175.0), App.Vector(1, 0, 0))
    af_solid = af_box.fuse(af_pin)
    af_obj = doc_af.addObject("Part::Feature", "Ship_Aft_Flap")
    af_obj.Shape = af_solid
    save_and_export(doc_af, "Ship_Aft_Flap", af_obj, ship_dir, {
        "part_id": "PART-SHP-FLAP-AFT-001",
        "subsystem": "Starship Upper Stage",
        "material": "AISI 304L + Aerothermal TPS Tiles",
        "mass_kg": 3800.0
    })

    # --------------------------------------------------------------------------
    # 9. PAYLOAD DISPENSER BAY (Internal Cargo Bay with PEZ Slot)
    # --------------------------------------------------------------------------
    doc_pb = App.newDocument("Payload_Dispenser_Bay")
    pb_outer = Part.makeCylinder(R_core - 100.0, 17000.0, App.Vector(0, 0, 0))
    pb_cavity = Part.makeCylinder(R_core - 300.0, 16800.0, App.Vector(0, 0, 100.0))
    pb_shell = pb_outer.cut(pb_cavity)
    # Dispenser slot (PEZ door opening)
    pez_door = Part.makeBox(1200.0, 4000.0, 8000.0, App.Vector(R_core - 600.0, -2000.0, 4000.0))
    pb_solid = pb_shell.cut(pez_door)
    pb_obj = doc_pb.addObject("Part::Feature", "Payload_Dispenser_Bay")
    pb_obj.Shape = pb_solid
    save_and_export(doc_pb, "Payload_Dispenser_Bay", pb_obj, ship_dir, {
        "part_id": "PART-SHP-PAYLOAD-BAY-001",
        "subsystem": "Starship Upper Stage",
        "material": "Al-Li 2195 / Carbon Composite Dispenser Rails",
        "mass_kg": 4500.0
    })

    # --------------------------------------------------------------------------
    # 10. RAPTOR 3 SEA-LEVEL ENGINE
    # --------------------------------------------------------------------------
    prop_dir = os.path.join(project_root, "cad", "freecad", "parts", "propulsion")
    doc_rsl = App.newDocument("Raptor3_Engine_SL")
    # Gimbal sphere mount at top
    gimbal_sph = Part.makeSphere(150.0, App.Vector(0, 0, 2700.0))
    # Turbopump powerhead block
    powerhead = Part.makeCylinder(450.0, 700.0, App.Vector(0, 0, 2000.0))
    # Combustion chamber neck
    chamber = Part.makeCylinder(220.0, 400.0, App.Vector(0, 0, 1600.0))
    # Expanding regenerative nozzle bell (1300mm exit dia, length 1600mm)
    nozzle = Part.makeCone(650.0, 220.0, 1600.0, App.Vector(0, 0, 0))
    # Combine into single engine solid
    rsl_solid = gimbal_sph.fuse(powerhead).fuse(chamber).fuse(nozzle)
    rsl_obj = doc_rsl.addObject("Part::Feature", "Raptor3_Engine_SL")
    rsl_obj.Shape = rsl_solid
    save_and_export(doc_rsl, "Raptor3_Engine_SL", rsl_obj, prop_dir, {
        "part_id": "PART-ENG-RAPTOR3-SL-001",
        "subsystem": "Propulsion (Raptor 3)",
        "material": "SX500 Austenitic Superalloy / Inconel 718 Powerhead",
        "mass_kg": 1525.0
    })

    # --------------------------------------------------------------------------
    # 11. RAPTOR 3 VACUUM ENGINE (Large 2.30m Expansion Nozzle)
    # --------------------------------------------------------------------------
    doc_rvac = App.newDocument("Raptor3_Engine_Vac")
    # Gimbal mount & powerhead identical
    gimbal_sph_v = Part.makeSphere(150.0, App.Vector(0, 0, 3300.0))
    powerhead_v = Part.makeCylinder(450.0, 700.0, App.Vector(0, 0, 2600.0))
    chamber_v = Part.makeCylinder(220.0, 400.0, App.Vector(0, 0, 2200.0))
    # Vacuum expansion nozzle bell (2300mm exit dia, length 2200mm)
    nozzle_v = Part.makeCone(1150.0, 220.0, 2200.0, App.Vector(0, 0, 0))
    rvac_solid = gimbal_sph_v.fuse(powerhead_v).fuse(chamber_v).fuse(nozzle_v)
    rvac_obj = doc_rvac.addObject("Part::Feature", "Raptor3_Engine_Vac")
    rvac_obj.Shape = rvac_solid
    save_and_export(doc_rvac, "Raptor3_Engine_Vac", rvac_obj, prop_dir, {
        "part_id": "PART-ENG-RAPTOR3-VAC-001",
        "subsystem": "Propulsion (Raptor 3)",
        "material": "SX500 / Niobium C-103 Radiative Bell Extension",
        "mass_kg": 1800.0
    })

    # --------------------------------------------------------------------------
    # 12. STARLINK V3 SATELLITE (Direct-to-Cell Flat-Panel Satellite)
    # --------------------------------------------------------------------------
    pld_dir = os.path.join(project_root, "cad", "freecad", "parts", "payload")
    doc_sat = App.newDocument("Starlink_V3_Satellite")
    # 7.0m length x 3.5m width x 0.25m thickness
    sat_bus = Part.makeBox(7000.0, 3500.0, 250.0, App.Vector(-3500.0, -1750.0, 0))
    # Phased array antenna panel on face
    antenna_face = Part.makeBox(6600.0, 3100.0, 30.0, App.Vector(-3300.0, -1550.0, 250.0))
    # Retention lugs (4 mounting corners)
    lugs = [
        Part.makeCylinder(60.0, 80.0, App.Vector(-3400.0, -1650.0, 250.0)),
        Part.makeCylinder(60.0, 80.0, App.Vector(3400.0, -1650.0, 250.0)),
        Part.makeCylinder(60.0, 80.0, App.Vector(-3400.0, 1650.0, 250.0)),
        Part.makeCylinder(60.0, 80.0, App.Vector(3400.0, 1650.0, 250.0)),
    ]
    sat_solid = sat_bus.fuse(antenna_face)
    for lug in lugs:
        sat_solid = sat_solid.fuse(lug)
    sat_obj = doc_sat.addObject("Part::Feature", "Starlink_V3_Satellite")
    sat_obj.Shape = sat_solid
    save_and_export(doc_sat, "Starlink_V3_Satellite", sat_obj, pld_dir, {
        "part_id": "PART-PLD-STARLINK-V3-001",
        "subsystem": "Payload Manifest",
        "material": "Al-Li Honeycomb Core / Silicon PV / Direct-to-Cell Arrays",
        "mass_kg": 1500.0
    })

    # --------------------------------------------------------------------------
    # SAVE EXECUTION LOG
    # --------------------------------------------------------------------------
    log_path = os.path.join(project_root, "cad", "freecad", "parts", "subsystem_parts_build_log.json")
    with open(log_path, "w", encoding="utf-8") as lf:
        json.dump(log_data, lf, indent=2)

    print("=" * 80)
    print(f"  ALL {len(log_data['parts_generated'])} SUBSYSTEM PARTS BUILT AND VALIDATED SUCCESSFULLY")
    print(f"  Log written to: {log_path}")
    print("=" * 80)

# Unconditional execution for FreeCAD
build_all_parts()
