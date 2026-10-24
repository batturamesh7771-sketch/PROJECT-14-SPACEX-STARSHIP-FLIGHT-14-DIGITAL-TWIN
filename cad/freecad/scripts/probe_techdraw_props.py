import sys
import os
import FreeCAD as App
import Part
import TechDraw

print("TechDraw methods:", [m for m in dir(TechDraw) if not m.startswith("_")])

doc = App.newDocument("TDProbe")
box = doc.addObject("Part::Box", "Box")
page = doc.addObject("TechDraw::DrawPage", "Page")
template = doc.addObject("TechDraw::DrawSVGTemplate", "Template")
template.Template = "E:/Program Files/FreeCAD 1.1/data/Mod/TechDraw/Templates/ISO/A2_Landscape_ISO7200TD.svg"
page.Template = template
doc.recompute()

print("Page properties:", [p for p in page.PropertiesList if not p.startswith("_")])
if hasattr(page, "PageResult"):
    print("PageResult length:", len(page.PageResult))
    print("PageResult start:", page.PageResult[:200])

App.closeDocument("TDProbe")
