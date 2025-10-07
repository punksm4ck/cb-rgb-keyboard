import os
import json

controller_path = "gui/controller.py"
plugin_loader_path = "plugins/loader.py"
api_path = "api/server.py"
test_runner_path = "tests/run_tests.py"

# 1. Create plugin loader
plugin_loader_code = '''
import os
import importlib

def load_plugins():
    plugins = []
    plugin_dir = "plugins"
    for fname in os.listdir(plugin_dir):
        if fname.endswith(".py") and fname != "loader.py":
            mod_name = fname[:-3]
            try:
                mod = importlib.import_module(f"plugins.{mod_name}")
                if hasattr(mod, "register_effect"):
                    plugins.append(mod.register_effect())
            except Exception as e:
                print(f"Plugin load failed: {mod_name} → {e}")
    return plugins
'''
os.makedirs("plugins", exist_ok=True)
with open(plugin_loader_path, "w") as f:
    f.write(plugin_loader_code)
print("✅ Plugin loader created.")

# 2. Inject plugin loader into controller.py
with open(controller_path, "r") as f:
    content = f.read()

if "from plugins.loader import load_plugins" not in content:
    content = content.replace("import json", "import json\nfrom plugins.loader import load_plugins")

if "def initialize_gui" in content and "self.plugin_effects" not in content:
    content = content.replace("self._load_saved_settings()", "self._load_saved_settings()\n        self.plugin_effects = load_plugins()")

    plugin_gui_code = '''
        # Plugin effects
        plugin_frame = ttk.LabelFrame(self.effects_tab, text="Plugin Effects", padding="10")
        plugin_frame.pack(fill=tk.X, padx=5, pady=5)

        self.plugin_var = tk.StringVar()
        self.plugin_combo = ttk.Combobox(
            plugin_frame,
            textvariable=self.plugin_var,
            values=[p["name"] for p in self.plugin_effects],
            state="readonly",
            width=20
        )
        self.plugin_combo.pack(side=tk.LEFT, padx=(5, 10))

        run_plugin_button = ttk.Button(
            plugin_frame,
            text="Run Plugin",
            command=self.run_selected_plugin
        )
        run_plugin_button.pack(side=tk.LEFT, padx=5)
    '''
    content = content.replace("# Effect parameters", plugin_gui_code + "\n\n        # Effect parameters")

    plugin_run_code = '''
    def run_selected_plugin(self):
        """Run selected plugin effect"""
        selected = self.plugin_var.get()
        for plugin in self.plugin_effects:
            if plugin["name"] == selected:
                if "run" in plugin:
                    plugin["run"](self)
                else:
                    self.hardware.clear_all(0x00FF00)
                break
    '''
    content += "\n" + plugin_run_code
    print("✅ Plugin GUI and runner injected.")

# 3. Create REST API scaffold
api_code = '''
from flask import Flask, request, jsonify
app = Flask(__name__)

@app.route("/run_effect", methods=["POST"])
def run_effect():
    data = request.json
    effect = data.get("effect")
    # TODO: wire to controller
    return jsonify({"status": "triggered", "effect": effect})

@app.route("/status", methods=["GET"])
def status():
    return jsonify({"status": "running", "fps": 30})

if __name__ == "__main__":
    app.run(port=5050)
'''
os.makedirs("api", exist_ok=True)
with open(api_path, "w") as f:
    f.write(api_code)
print("✅ REST API scaffold created.")

# 4. Create test runner
test_runner_code = '''
import unittest
import sys
import os

sys.path.insert(0, os.path.abspath("tests"))

def run_all_tests():
    loader = unittest.TestLoader()
    suite = loader.discover("tests")
    runner = unittest.TextTestRunner()
    runner.run(suite)

if __name__ == "__main__":
    run_all_tests()
'''
with open(test_runner_path, "w") as f:
    f.write(test_runner_code)
print("✅ Test runner created.")

# 5. Save controller.py
with open(controller_path, "w") as f:
    f.write(content)
print("✅ controller.py updated.")
