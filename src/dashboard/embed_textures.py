import base64
import os

base_dir = os.path.dirname(__file__)
tex_dir = os.path.join(base_dir, "static", "assets", "textures")

def read_b64(filename):
    p = os.path.join(tex_dir, filename)
    with open(p, "rb") as f:
        return base64.b64encode(f.read()).decode("ascii")

clouds_b64 = read_b64("globeprev-clouds-on-DOpaHC5m-r2.jpg")
night_b64 = read_b64("globeprev-night-on-BUXG0tvC-r2.jpg")
sat_b64 = read_b64("mappreview-satellite-n3glFQWc-r2.jpg")

out_path = os.path.join(tex_dir, "earth_textures_embedded.js")
with open(out_path, "w", encoding="utf-8") as f:
    f.write("// High-Resolution Photorealistic Earth Textures (Offline Base64 Embedded)\n")
    f.write("// Starship Flight 14 Digital Engineering Lab\n")
    f.write("window.EMBEDDED_TEXTURES = {\n")
    f.write(f'  earthDay: "data:image/jpeg;base64,{clouds_b64}",\n')
    f.write(f'  earthNight: "data:image/jpeg;base64,{night_b64}",\n')
    f.write(f'  satelliteMap: "data:image/jpeg;base64,{sat_b64}"\n')
    f.write("};\n")

print(f"Successfully generated {out_path} ({os.path.getsize(out_path)} bytes)")
