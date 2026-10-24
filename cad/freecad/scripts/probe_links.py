import sys
import FreeCAD as App
import Part

print("=" * 60)
print("PROBING APPLINK & SUBASSEMBLY LINKING")
print("=" * 60)

doc1 = App.newDocument("SubPartDoc")
cyl = doc1.addObject("Part::Cylinder", "EngineCylinder")
cyl.Radius = 650.0
cyl.Height = 2800.0
doc1.recompute()

doc_main = App.newDocument("MainAssemblyDoc")
asy = doc_main.addObject("Assembly::AssemblyObject", "Assembly")

# Test App::Link
link1 = asy.newObject("App::Link", "EngineLink_01")
link1.LinkedObject = cyl
link1.Placement = App.Placement(App.Vector(1000, 0, 0), App.Rotation(App.Vector(0, 0, 1), 0))

# Test App::LinkElement or second link
link2 = asy.newObject("App::Link", "EngineLink_02")
link2.LinkedObject = cyl
link2.Placement = App.Placement(App.Vector(-1000, 0, 0), App.Rotation(App.Vector(0, 0, 1), 0))

doc_main.recompute()

print("Main assembly objects count:", len(doc_main.Objects))
print("Link 1 LinkedObject:", link1.LinkedObject.Label if link1.LinkedObject else None)
print("Link 1 Shape valid:", link1.Shape.isValid())
print("Link 2 Shape valid:", link2.Shape.isValid())

App.closeDocument("SubPartDoc")
App.closeDocument("MainAssemblyDoc")
print("=" * 60)
print("LINK PROBE PASSED")
print("=" * 60)
