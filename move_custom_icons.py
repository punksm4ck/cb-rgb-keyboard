import shutil
import os

source_splash = "/home/tsann/Pictures/Icons/rgb_controller_splash.png"
source_tray = "/home/tsann/Pictures/Icons/rgb_controller_icon.png"
target_dir = "assets"

os.makedirs(target_dir, exist_ok=True)

try:
    shutil.copy(source_splash, os.path.join(target_dir, "rgb_controller_splash.png"))
    print("✅ Moved splash icon to assets/")
except Exception as e:
    print(f"❌ Failed to move splash icon: {e}")

try:
    shutil.copy(source_tray, os.path.join(target_dir, "rgb_controller_icon.png"))
    print("✅ Moved tray icon to assets/")
except Exception as e:
    print(f"❌ Failed to move tray icon: {e}")
