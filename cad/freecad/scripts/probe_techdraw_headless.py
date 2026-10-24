import sys
import os
import FreeCAD as App
import Part
import TechDraw

print("=" * 60)
print("PROBING TECHDRAW HEADLESS GENERATION & EXPORT")
print("=" * 60)

test_dir = os.path.abspath("cad/freecad/output/techdraw_test")
os.makedirs(test_dir, exist_ok=True)
svg_out = os.path.join(test_dir, "test_drawing.svg")

doc = App.newDocument("TechDrawTest")

# Create a test 3D part
box = doc.addObject("Part::Box", "TestBox")
box.Length = 1000.0
box.Width = 500.0
box.Height = 2000.0
doc.recompute()

# Create TechDraw Page
page = doc.addObject("TechDraw::DrawPage", "Page")
template = doc.addObject("TechDraw::DrawSVGTemplate", "Template")

template_path = "E:/Program Files/FreeCAD 1.1/data/Mod/TechDraw/Templates/ISO/A2_Landscape_ISO7200TD.svg"
if not os.path.exists(template_path):
    template_path = "E:/Program Files/FreeCAD 1.1/data/Mod/TechDraw/Templates/Default_Template_A4_Landscape.svg"

template.Template = template_path
page.Template = template
doc.recompute()

# Add Part View
view = doc.addObject("TechDraw::DrawViewPart", "BoxFrontView")
view.Source = [box]
view.Direction = App.Vector(0, -1, 0) # Front view (looking in +Y)
view.X = 200.0
view.Y = 150.0
view.Scale = 0.1
page.addView(view)
doc.recompute()

print(f"TechDraw Page created: {page.Label}")
print(f"View added: {view.Label}, Scale={view.Scale}")

# Export Page to SVG
TechDraw.writeSVGPage(page, svg_out)
assert os.path.exists(svg_out), f"Failed to export {svg_out}"
print(f"Exported SVG: {svg_out} ({os.path.getsize(svg_out):,} bytes)")

App.closeDocument("TechDrawTest")
print("=" * 60)
print("TECHDRAW HEADLESS PROBE PASSED 100%")
print("=" * 60)
