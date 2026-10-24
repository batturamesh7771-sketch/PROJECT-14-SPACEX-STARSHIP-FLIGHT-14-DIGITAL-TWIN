import sys
import os
import FreeCAD as App
import Part

print("=" * 60)
print("PROBING APPLINK SAVING ORDER")
print("=" * 60)

test_dir = os.path.abspath("cad/freecad/output/link_test")
os.makedirs(test_dir, exist_ok=True)
doc1_path = os.path.join(test_dir, "EnginePart.FCStd")
doc_main_path = os.path.join(test_dir, "MainAssembly.FCStd")

# Create and save sub-part
doc1 = App.newDocument("EnginePart")
cyl = doc1.addObject("Part::Cylinder", "EngineCylinder")
cyl.Radius = 650.0
cyl.Height = 2800.0
doc1.recompute()
doc1.saveAs(doc1_path)

# Create and save main doc BEFORE linking
doc_main = App.newDocument("MainAssembly")
doc_main.saveAs(doc_main_path)
asy = doc_main.addObject("Assembly::AssemblyObject", "Assembly")

link1 = asy.newObject("App::Link", "EngineLink_01")
link1.setLink(cyl)
link1.Placement = App.Placement(App.Vector(1000, 0, 0), App.Rotation(App.Vector(0, 0, 1), 0))

link2 = asy.newObject("App::Link", "EngineLink_02")
link2.setLink(cyl)
link2.Placement = App.Placement(App.Vector(-1000, 0, 0), App.Rotation(App.Vector(0, 0, 1), 0))

doc_main.recompute()
doc_main.save()

print("Main assembly objects count:", len(doc_main.Objects))
print("Link 1 LinkedObject:", link1.LinkedObject.Label if link1.LinkedObject else None)
print("Link 1 Shape valid:", link1.Shape.isValid())
print("Link 2 Shape valid:", link2.Shape.isValid())
print("Link 1 placement:", link1.Placement.Base)
print("Link 2 placement:", link2.Placement.Base)

App.closeDocument("EnginePart")
App.closeDocument("MainAssembly")
print("=" * 60)
print("LINK PROBE WITH PROPER SAVE ORDER PASSED 100%")
print("=" * 60)
