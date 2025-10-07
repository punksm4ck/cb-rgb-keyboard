#!/usr/bin/env python3
import os
import shutil

print("📦 Organizing patch scripts into 'patches' folder...")

# Define project root and patches folder
project_root = os.getcwd()
patches_folder = os.path.join(project_root, "patches")
os.makedirs(patches_folder, exist_ok=True)

# Define known patch scripts used today
patch_scripts = [
    "add_gui_orchestration_audio_layering_rgbpreset_mapping.py",
    "add_gui_orchestration_waveform_diff_gif_mqtt.py",
    "add_gui_orchestration_audio_presets_composer.py",
    "add_gui_orchestration_help_sections.py",
    "add_gui_orchestration_voice_plugins_sync_undo.py",
    "add_gui_orchestration_voice_plugins_mqtt_undo.py",
    "add_gui_orchestration_waveform_diff_mqtt_export.py",
    "add_gui_orchestration_collab_stream_remix.py",
    "add_gui_orchestration_sync_plugins_voice_undo.py",
    "inject_gui_features.py",
    "install_dependencies.py",
    "finalize_rgb_orchestration_setup.py",
    "verify_final_setup.py",
    "setup_rgb_virtualenv.sh",
    "install_rgb_orchestration_dependencies.sh"
]

# Move each script if it exists
moved = []
for script in patch_scripts:
    src = os.path.join(project_root, script)
    dst = os.path.join(patches_folder, script)
    if os.path.exists(src):
        shutil.move(src, dst)
        moved.append(script)

# Report results
if moved:
    print(f"✅ Moved {len(moved)} patch scripts to 'patches' folder:")
    for m in moved:
        print(f"   - {m}")
else:
    print("⚠️ No patch scripts found to move.")

print("🎯 Patch organization complete.")
