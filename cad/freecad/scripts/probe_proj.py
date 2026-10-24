import TechDraw
import Part
import FreeCAD as App

b = Part.makeBox(10, 10, 10)
s = TechDraw.projectToSVG(b, App.Vector(0, -1, 0))
print("SVG len:", len(s))
d = TechDraw.projectToDXF(b, App.Vector(0, -1, 0))
print("DXF len:", len(d))
