
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
