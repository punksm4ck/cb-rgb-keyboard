import os

# 1. Extend API with new endpoints
api_path = "api/server.py"
with open(api_path, "r") as f:
    api_code = f.read()

if "/list_presets" not in api_code:
    new_endpoints = '''
@app.route("/list_presets", methods=["GET"])
def list_presets():
    try:
        presets = []
        for fname in os.listdir("presets"):
            if fname.endswith(".rgbpreset"):
                with open(os.path.join("presets", fname)) as f:
                    data = json.load(f)
                    presets.append(data["name"])
        return jsonify({"presets": presets})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/run_plugin", methods=["POST"])
def run_plugin():
    plugin_name = request.json.get("plugin")
    from plugins.loader import load_plugins
    plugins = load_plugins()
    for plugin in plugins:
        if plugin["name"] == plugin_name:
            if "run" in plugin:
                plugin["run"](None)
                return jsonify({"status": "executed", "plugin": plugin_name})
    return jsonify({"error": "Plugin not found"}), 404
'''
    api_code += "\n" + new_endpoints
    with open(api_path, "w") as f:
        f.write(api_code)
    print("✅ API endpoints /list_presets and /run_plugin added.")

# 2. Inject GUI tab for API interaction
controller_path = "gui/controller.py"
with open(controller_path, "r") as f:
    gui_code = f.read()

if "self.api_tab" not in gui_code:
    # Add tab
    gui_code = gui_code.replace("self.notebook.add(self.settings_tab, text=\"Settings\")",
                                "self.notebook.add(self.settings_tab, text=\"Settings\")\n        self.api_tab = ttk.Frame(self.notebook)\n        self.notebook.add(self.api_tab, text=\"API Control\")")

    # Add method
    api_gui_method = '''
    def _create_api_tab(self):
        """Create API control tab"""
        frame = ttk.LabelFrame(self.api_tab, text="API Interaction", padding="10")
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        ttk.Label(frame, text="Run Plugin via API:").pack(anchor=tk.W)
        self.api_plugin_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.api_plugin_var, width=30).pack(anchor=tk.W, pady=5)

        run_button = ttk.Button(frame, text="Send", command=self._send_plugin_api)
        run_button.pack(pady=5)

        self.api_response_label = ttk.Label(frame, text="Response: --")
        self.api_response_label.pack(anchor=tk.W, pady=5)
    '''

    gui_code += "\n" + api_gui_method

    # Add sender method
    sender_method = '''
    def _send_plugin_api(self):
        import requests
        plugin = self.api_plugin_var.get()
        try:
            r = requests.post("http://127.0.0.1:5000/run_plugin", json={"plugin": plugin})
            self.api_response_label.config(text=f"Response: {r.json()}")
        except Exception as e:
            self.api_response_label.config(text=f"Error: {e}")
    '''

    gui_code += "\n" + sender_method

    # Call method
    gui_code = gui_code.replace("self._create_status_bar()", "self._create_status_bar()\n        self._create_api_tab()")

    with open(controller_path, "w") as f:
        f.write(gui_code)
    print("✅ GUI tab for API interaction added.")

# 3. Auto-start Flask server when launching GUI
main_path = "__main__.py"
if os.path.exists(main_path):
    with open(main_path, "r") as f:
        main_code = f.read()

    if "start_flask_server()" not in main_code:
        flask_launcher = '''
import subprocess

def start_flask_server():
    try:
        subprocess.Popen(["flask", "--app", "api/server.py", "run"])
    except Exception as e:
        print(f"Failed to start Flask server: {e}")
'''

        main_code = flask_launcher + "\n" + main_code
        main_code = main_code.replace("controller.initialize_gui()", "start_flask_server()\n    controller.initialize_gui()")

        with open(main_path, "w") as f:
            f.write(main_code)
        print("✅ Flask server auto-start added to __main__.py.")
else:
    print("⚠️ __main__.py not found. Skipped auto-start injection.")
