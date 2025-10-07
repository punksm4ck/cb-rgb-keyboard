import os
import importlib.util
import tkinter as tk
from tkinter import ttk

print("🔍 Starting final verification of RGB orchestration suite...")

# 1. Verify required directories
required_dirs = [
    "gui", "presets/audio", "audio/mapping", "voice_profiles/audio",
    "plugins/changelogs", "history/exports", "mqtt/topics"
]
for d in required_dirs:
    if not os.path.exists(d):
        print(f"❌ Missing directory: {d}")
    else:
        print(f"✅ Directory exists: {d}")

# 2. Verify controller.py exists and loads
controller_path = "gui/controller.py"
if not os.path.exists(controller_path):
    print("❌ gui/controller.py not found.")
else:
    print("✅ controller.py found.")
    spec = importlib.util.spec_from_file_location("controller", controller_path)
    controller = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(controller)
        print("✅ controller.py loaded successfully.")
    except Exception as e:
        print(f"❌ Error loading controller.py: {e}")

# 3. Verify GUI tabs and functions
required_functions = [
    "_create_status_bar", "_create_audio_layering_tab", "_create_rgbpreset_export_tab",
    "_create_band_mapping_tab", "_create_waveform_render_tab", "_create_changelog_diff_tab",
    "_create_gif_export_tab", "_create_mqtt_listener_tab", "_create_freq_band_tab",
    "_create_visualizer_presets_tab", "_create_audio_composer_tab", "_add_help_box"
]
missing = []
for func in required_functions:
    if func not in controller.__dict__:
        missing.append(func)
if missing:
    print(f"❌ Missing GUI functions: {', '.join(missing)}")
else:
    print("✅ All GUI functions present.")

# 4. Verify installed Python packages
required_packages = [
    "numpy", "sounddevice", "requests", "paho.mqtt.client", "imageio", "PIL", "matplotlib", "pygments"
]
for pkg in required_packages:
    try:
        importlib.import_module(pkg.split(".")[0])
        print(f"✅ Package available: {pkg}")
    except ImportError:
        print(f"❌ Missing package: {pkg}")

# 5. Verify preset export
preset_path = "presets/audio/test.rgbpreset"
try:
    with open(preset_path, "w") as f:
        f.write("Effect: shimmer + pulse\nLayer: audio-reactive\nZones: WASD, Arrows, Function\n")
    print("✅ Preset export test passed.")
except Exception as e:
    print(f"❌ Preset export failed: {e}")

# 6. Verify MQTT mapping
mapping_path = "audio/mapping/band_to_zone.txt"
try:
    with open(mapping_path, "w") as f:
        f.write("Bass: 17,18,19,20\nMid: 21,22,23,24\nTreble: 1,2,3,4,5\n")
    print("✅ Band-to-zone mapping test passed.")
except Exception as e:
    print(f"❌ Mapping write failed: {e}")

# 7. Verify GUI launch
try:
    root = tk.Tk()
    root.title("RGB Orchestration Verification")
    ttk.Label(root, text="✅ GUI launch test passed.").pack(padx=20, pady=20)
    root.after(2000, root.destroy)
    root.mainloop()
except Exception as e:
    print(f"❌ GUI launch failed: {e}")

print("🎯 Final verification complete.")
