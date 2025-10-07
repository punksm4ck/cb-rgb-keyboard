
import subprocess

def set_zone_color(zone, hex_color):
    """Send ectool command to set color for a zone"""
    r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (1, 3, 5))
    cmd = f"ectool led setzone {zone} {r} {g} {b}"
    subprocess.run(cmd.split(), check=True)
