import sys
import FreeCAD as App

print("=" * 60)
print("PROBING FREECAD 1.1 ASSEMBLY JOINT API")
print("=" * 60)

import Assembly
print("Assembly module attributes:", [a for a in dir(Assembly) if not a.startswith("_")])

# Check Assembly python scripts/classes
import inspect
for name, obj in inspect.getmembers(Assembly):
    if inspect.isclass(obj) or inspect.isfunction(obj):
        print(f"  {name}: {type(obj)}")

# Let's check JointGroup methods
doc = App.newDocument("JointProbe")
jg = doc.addObject("Assembly::JointGroup", "Joints")
print("JointGroup methods/props:", [p for p in dir(jg) if not p.startswith("_")])

App.closeDocument("JointProbe")
print("=" * 60)
