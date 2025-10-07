import os

controller_path = "gui/controller.py"
api_path = "api/server.py"
preset_dir = "presets"
os.makedirs(preset_dir, exist_ok=True)

# 1. Inject Zone Editor Tab
with open(controller_path, "r") as f:
    gui_code = f.read()

if "self.zone_editor_tab" not in gui_code:
    gui_code = gui_code.replace(
        "self.notebook.add(self.api_test_tab, text=\"API Tester\")",
        "self.notebook.add(self.api_test_tab, text=\"API Tester\")\n        self.zone_editor_tab = ttk.Frame(self.notebook)\n        self.notebook.add(self.zone_editor_tab, text=\"Zone Editor\")\n        self._create_zone_editor_tab()"
    )

    zone_editor_method = '''
    def _create_zone_editor_tab(self):
        """Create 24-zone editor tab"""
        frame = ttk.Frame(self.zone_editor_tab)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.zone_buttons = []
        self.zone_colors = ["#000000"] * 24

        grid = ttk.Frame(frame)
        grid.pack()

        for i in range(24):
            btn = tk.Button(grid, text=f"Z{i+1}", width=6, bg="#000000", fg="white",
                            command=lambda idx=i: self._edit_zone_color(idx))
            btn.grid(row=i//8, column=i%8, padx=4, pady=4)
            self.zone_buttons.append(btn)

        apply_button = ttk.Button(frame, text="Apply Colors", command=self._apply_zone_colors)
        apply_button.pack(pady=10)

    def _edit_zone_color(self, idx):
        from tkinter.colorchooser import askcolor
        color = askcolor()[1]
        if color:
            self.zone_colors[idx] = color
            self.zone_buttons[idx].config(bg=color)

    def _apply_zone_colors(self):
        import requests
        for i, color in enumerate(self.zone_colors):
            try:
                requests.post("http://127.0.0.1:5000/set_zone_color", json={"zone": i+1, "color": color})
            except Exception as e:
                print(f"Zone {i+1} failed: {e}")
    '''
    gui_code += "\n" + zone_editor_method
    print("✅ Zone Editor tab added.")

# 2. Add API endpoints for zone control
with open(api_path, "r") as f:
    api_code = f.read()

if "/set_zone_color" not in api_code:
    zone_api = '''
@app.route("/set_zone_color", methods=["POST"])
def set_zone_color():
    data = request.json
    zone = data.get("zone")
    color = data.get("color")
    try:
        from plugins.ectool_wrapper import set_zone_color
        set_zone_color(zone, color)
        return jsonify({"status": "ok", "zone": zone, "color": color})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    '''
    api_code += "\n" + zone_api
    print("✅ API endpoint /set_zone_color added.")

# 3. Generate ectool wrapper for 24-zone control
ectool_path = "plugins/ectool_wrapper.py"
if not os.path.exists(ectool_path):
    with open(ectool_path, "w") as f:
        f.write('''
import subprocess

def set_zone_color(zone, hex_color):
    """Send ectool command to set color for a zone"""
    r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (1, 3, 5))
    cmd = f"ectool led setzone {zone} {r} {g} {b}"
    subprocess.run(cmd.split(), check=True)
''')
    print("✅ plugins/ectool_wrapper.py created.")

# 4. Add Preset Manager Tab
if "self.preset_tab" not in gui_code:
    gui_code = gui_code.replace(
        "self.notebook.add(self.zone_editor_tab, text=\"Zone Editor\")",
        "self.notebook.add(self.zone_editor_tab, text=\"Zone Editor\")\n        self.preset_tab = ttk.Frame(self.notebook)\n        self.notebook.add(self.preset_tab, text=\"Presets\")\n        self._create_preset_tab()"
    )

    preset_method = '''
    def _create_preset_tab(self):
        """Create preset manager tab"""
        frame = ttk.Frame(self.preset_tab)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.preset_listbox = tk.Listbox(frame, height=10)
        self.preset_listbox.pack(fill=tk.X, pady=5)

        load_button = ttk.Button(frame, text="Load Preset", command=self._load_selected_preset)
        load_button.pack(pady=5)

        self._refresh_preset_list()

    def _refresh_preset_list(self):
        self.preset_listbox.delete(0, tk.END)
        for fname in os.listdir("presets"):
            if fname.endswith(".rgbpreset24"):
                self.preset_listbox.insert(tk.END, fname)

    def _load_selected_preset(self):
        import json, requests
        selection = self.preset_listbox.curselection()
        if not selection:
            return
        fname = self.preset_listbox.get(selection[0])
        with open(os.path.join("presets", fname)) as f:
            preset = json.load(f)
        for zone, color in preset.get("zones", {}).items():
            requests.post("http://127.0.0.1:5000/set_zone_color", json={"zone": int(zone), "color": color})
    '''
    gui_code += "\n" + preset_method
    print("✅ Preset Manager tab added.")

with open(controller_path, "w") as f:
    f.write(gui_code)

with open(api_path, "w") as f:
    f.write(api_code)
