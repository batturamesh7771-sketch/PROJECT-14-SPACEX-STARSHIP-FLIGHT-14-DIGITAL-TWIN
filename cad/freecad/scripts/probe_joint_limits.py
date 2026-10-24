import sys
import FreeCAD as App
import Part

print("=" * 60)
print("PROBING JOINT CREATION & LIMITS")
print("=" * 60)

import JointObject

doc = App.newDocument("JointTest")
asy = doc.addObject("Assembly::AssemblyObject", "Assembly")
jg = asy.newObject("Assembly::JointGroup", "Joints")

# Create a revolute joint
jnt = jg.newObject("App::FeaturePython", "FlapRevoluteJoint")
JointObject.Joint(jnt, 1) # 1 = Revolute
doc.recompute()

print("Joint created:", jnt.Label, "Type:", jnt.JointType)
print("Joint properties:")
for p in jnt.PropertiesList:
    if "Angle" in p or "Limit" in p or "Ref" in p or "Distance" in p:
        print(f"  {p}: {getattr(jnt, p)}")

# Check setting angle limits
jnt.EnableAngleMin = True
jnt.EnableAngleMax = True
jnt.AngleMin = -30.0
jnt.AngleMax = 60.0
print(f"Angle limits set: Min={jnt.AngleMin}, Max={jnt.AngleMax}, Enabled=({jnt.EnableAngleMin}, {jnt.EnableAngleMax})")

# Create a ball joint (type 4)
jnt_ball = jg.newObject("App::FeaturePython", "EngineGimbalBallJoint")
JointObject.Joint(jnt_ball, 4) # 4 = Ball
doc.recompute()
print("Ball Joint created:", jnt_ball.Label, "Type:", jnt_ball.JointType)

App.closeDocument("JointTest")
print("=" * 60)
print("JOINT PROBE COMPLETED SUCCESSFULLY")
print("=" * 60)
