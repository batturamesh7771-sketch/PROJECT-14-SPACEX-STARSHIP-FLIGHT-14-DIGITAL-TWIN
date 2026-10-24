import sys
import FreeCAD as App
import Part

print("=" * 60)
print("PROBING FREECAD 1.1 ASSEMBLY & TECHDRAW API")
print("=" * 60)

doc = App.newDocument("ProbeDoc")

# Test AssemblyObject
try:
    asy = doc.addObject("Assembly::AssemblyObject", "Assembly")
    print("[SUCCESS] AssemblyObject created:", asy.TypeId)
    print("AssemblyObject properties:", [p for p in asy.PropertiesList if not p.startswith("_")])
except Exception as e:
    print("[FAIL] AssemblyObject:", e)

# Test JointGroup & JointObject
try:
    jg = doc.addObject("Assembly::JointGroup", "Joints")
    print("[SUCCESS] JointGroup created:", jg.TypeId)
except Exception as e:
    print("[FAIL] JointGroup:", e)

try:
    jt = doc.addObject("Assembly::JointObject", "TestJoint")
    print("[SUCCESS] JointObject created:", jt.TypeId)
    print("JointObject properties:", [p for p in jt.PropertiesList if not p.startswith("_")])
except Exception as e:
    print("[FAIL] JointObject:", e)

# Test BomObject
try:
    bom = doc.addObject("Assembly::BomObject", "BOM")
    print("[SUCCESS] BomObject created:", bom.TypeId)
    print("BomObject properties:", [p for p in bom.PropertiesList if not p.startswith("_")])
except Exception as e:
    print("[FAIL] BomObject:", e)

# Test TechDraw
try:
    import TechDraw
    page = doc.addObject("TechDraw::DrawPage", "Page")
    template = doc.addObject("TechDraw::DrawSVGTemplate", "Template")
    # check default templates in FreeCAD install
    template_path = "E:/Program Files/FreeCAD 1.1/data/Mod/TechDraw/Templates/A2_Landscape_ISO7200TD.svg"
    import os
    if os.path.exists(template_path):
        template.Template = template_path
        page.Template = template
        print(f"[SUCCESS] TechDraw DrawPage created with ISO template: {template_path}")
    else:
        print("[INFO] TechDraw template path not found at standard path, checking Mod/TechDraw/Templates")
        templates_dir = "E:/Program Files/FreeCAD 1.1/data/Mod/TechDraw/Templates"
        if os.path.exists(templates_dir):
            print("Templates found:", os.listdir(templates_dir)[:5])
except Exception as e:
    print("[FAIL] TechDraw:", e)

App.closeDocument("ProbeDoc")
print("=" * 60)
