import os
import json

# Directory structure
folders = [
    "effects",
    "effects/engine",
    "plugins",
    "themes",
    "presets",
    "logs",
    "tests"
]

# Core files to scaffold
files = {
    "effects/engine/__init__.py": "",
    "effects/engine/base.py": '''
class BaseEffect:
    def __init__(self, controller):
        self.controller = controller
        self.running = False

    def start(self):
        self.running = True

    def stop(self):
        self.running = False

    def update(self):
        pass
''',
    "effects/engine/ripple.py": '''
from .base import BaseEffect

class RippleEffect(BaseEffect):
    def start(self):
        super().start()
        # Trigger ripple from key index
        def ripple_from(index):
            for radius in range(5):
                if not self.running:
                    break
                affected = self.controller.get_keys_in_radius(index, radius)
                for key in affected:
                    self.controller.hardware.set_keys(key, [0x00FFFF])
                self.controller.root.after(100, lambda: self.controller.clear_keys(affected))
        self.controller.bind_keypress(ripple_from)
''',
    "plugins/sample_plugin.py": '''
def register_effect():
    return {
        "name": "PluginPulse",
        "type": "pulse",
        "color": "#FF00FF",
        "steps": 8,
        "delay": 80
    }

def run(controller):
    # Custom plugin logic
    controller.hardware.clear_all(0xFF00FF)
''',
    "themes/dark.json": json.dumps({
        "background": "#1a1a1a",
        "foreground": "#ffffff",
        "accent": "#00ffff"
    }, indent=4),
    "presets/cyberpulse.rgbpreset": json.dumps({
        "name": "CyberPulse",
        "type": "chain",
        "effects": [
            {"type": "pulse", "color": "#00FFFF", "steps": 10},
            {"type": "gradient", "color": "#FF00FF"}
        ],
        "reactive": {
            "keypress": "flash",
            "idle": "dim"
        }
    }, indent=4),
    "tests/test_engine.py": '''
def test_effect_start():
    from effects.engine.base import BaseEffect
    e = BaseEffect(None)
    e.start()
    assert e.running

def test_effect_stop():
    from effects.engine.base import BaseEffect
    e = BaseEffect(None)
    e.start()
    e.stop()
    assert not e.running
''',
    "logs/.gitkeep": ""
}

# Create folders
for folder in folders:
    os.makedirs(folder, exist_ok=True)

# Create files
for path, content in files.items():
    with open(path, "w") as f:
        f.write(content)

print("✅ RGB platform scaffolded:")
for folder in folders:
    print(f"📁 {folder}")
for path in files:
    print(f"📄 {path}")
