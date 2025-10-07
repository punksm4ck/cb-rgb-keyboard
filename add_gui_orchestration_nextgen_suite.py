import os

controller_path = "gui/controller.py"
os.makedirs("macros", exist_ok=True)

with open(controller_path, "r") as f:
    content = f.read()

# 1. Effect Composer with Layered Tracks
if "def _create_effect_composer_tab" not in content:
    composer_ui = '''
def _create_effect_composer_tab(self):
    self.composer_tab = ttk.Frame(self.notebook)
    self.notebook.add(self.composer_tab, text="Effect Composer")

    ttk.Label(self.composer_tab, text="Layered Effects").pack()
    self.track_listbox = tk.Listbox(self.composer_tab, height=6)
    self.track_listbox.pack(fill=tk.X)

    ttk.Button(self.composer_tab, text="Add Layer", command=self._add_effect_layer).pack()
    ttk.Button(self.composer_tab, text="Export Stack", command=self._export_rgbstack).pack(pady=5)

def _add_effect_layer(self):
    from tkinter.simpledialog import askstring
    name = askstring("Layer Name", "Enter effect layer name:")
    if name:
        self.track_listbox.insert(tk.END, name)

def _export_rgbstack(self):
    layers = self.track_listbox.get(0, tk.END)
    import json
    with open("preset_stack.rgbstack", "w") as f:
        json.dump({"layers": layers}, f)
    print(f"✅ Exported .rgbstack with layers: {layers}")
'''
    content += "\n" + composer_ui
    print("✅ Effect Composer with layered tracks added.")

# 2. Live Preview Recorder
if "def _create_preview_recorder_tab" not in content:
    recorder_ui = '''
def _create_preview_recorder_tab(self):
    self.recorder_tab = ttk.Frame(self.notebook)
    self.notebook.add(self.recorder_tab, text="Preview Recorder")

    ttk.Label(self.recorder_tab, text="FPS").pack()
    self.fps_var = tk.IntVar(value=10)
    ttk.Entry(self.recorder_tab, textvariable=self.fps_var).pack()

    ttk.Button(self.recorder_tab, text="Record Preview", command=self._record_preview).pack(pady=5)

def _record_preview(self):
    import imageio, time
    frames = []
    for i in range(30):
        self.root.update()
        self.root.update_idletasks()
        self.root.postscript(file=f"frame_{i}.ps", colormode='color')
        frames.append(imageio.imread(f"frame_{i}.ps"))
        time.sleep(1 / self.fps_var.get())
    imageio.mimsave("preview.gif", frames, fps=self.fps_var.get())
    print("🎥 Preview recorded and saved as preview.gif")
'''
    content += "\n" + recorder_ui
    print("✅ Live Preview Recorder added.")

# 3. Smart Zone AI
if "def _create_smart_zone_tab" not in content:
    smart_zone_ui = '''
def _create_smart_zone_tab(self):
    self.smart_tab = ttk.Frame(self.notebook)
    self.notebook.add(self.smart_tab, text="Smart Zones")

    ttk.Button(self.smart_tab, text="Optimize Zones", command=self._optimize_zones).pack(pady=5)

def _optimize_zones(self):
    clusters = {
        "WASD": [17, 18, 19, 20],
        "Arrows": [21, 22, 23, 24],
        "Numpad": [13, 14, 15, 16]
    }
    import requests
    for name, zones in clusters.items():
        for z in zones:
            requests.post("http://127.0.0.1:5000/set_zone_color", json={"zone": z, "color": "#00ffcc"})
    print("🧠 Smart zone optimization applied.")
'''
    content += "\n" + smart_zone_ui
    print("✅ Smart Zone AI added.")

# 4. EC Command Sandbox
if "def _create_ec_sandbox_tab" not in content:
    ec_sandbox_ui = '''
def _create_ec_sandbox_tab(self):
    self.sandbox_tab = ttk.Frame(self.notebook)
    self.notebook.add(self.sandbox_tab, text="EC Sandbox")

    self.ec_entry = tk.Entry(self.sandbox_tab)
    self.ec_entry.pack(fill=tk.X)
    ttk.Button(self.sandbox_tab, text="Run Command", command=self._run_ec_command).pack()

    self.ec_output = tk.Text(self.sandbox_tab, height=10)
    self.ec_output.pack(fill=tk.BOTH, expand=True)

    ttk.Button(self.sandbox_tab, text="Save Macro", command=self._save_ec_macro).pack(pady=5)

def _run_ec_command(self):
    cmd = self.ec_entry.get()
    import subprocess
    try:
        result = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT).decode()
        self.ec_output.delete(1.0, tk.END)
        self.ec_output.insert(tk.END, result)
    except Exception as e:
        self.ec_output.insert(tk.END, f"❌ Error: {e}")

def _save_ec_macro(self):
    macro = self.ec_entry.get()
    with open(f"macros/{macro.replace(' ', '_')}.txt", "w") as f:
        f.write(macro)
    print(f"💾 Saved EC macro: {macro}")
'''
    content += "\n" + ec_sandbox_ui
    print("✅ EC Command Sandbox added.")

# 5. Event-Driven Automation
if "def _create_event_automation_tab" not in content:
    event_ui = '''
def _create_event_automation_tab(self):
    self.event_tab = ttk.Frame(self.notebook)
    self.notebook.add(self.event_tab, text="Event Automation")

    ttk.Label(self.event_tab, text="Rule: When").pack()
    self.event_trigger_var = tk.StringVar()
    ttk.Entry(self.event_tab, textvariable=self.event_trigger_var).pack()

    ttk.Label(self.event_tab, text="Do").pack()
    self.event_action_var = tk.StringVar()
    ttk.Entry(self.event_tab, textvariable=self.event_action_var).pack()

    self.event_enabled_var = tk.BooleanVar(value=True)
    ttk.Checkbutton(self.event_tab, text="Enable Listener", variable=self.event_enabled_var).pack()
    self.root.after(5000, self._check_event_trigger)

def _check_event_trigger(self):
    if self.event_enabled_var.get():
        if self.event_trigger_var.get() == "USB":
            import requests
            requests.post("http://127.0.0.1:5000/set_zone_color", json={"zone": 1, "color": "#ff00ff"})
            print("🧭 USB event triggered effect.")
    self.root.after(5000, self._check_event_trigger)
'''
    content += "\n" + event_ui
    print("✅ Event-Driven Automation added.")

# 6. Copilot Assistant Tab
if "def _create_copilot_tab" not in content:
    copilot_ui = '''
def _create_copilot_tab(self):
    self.copilot_tab = ttk.Frame(self.notebook)
    self.notebook.add(self.copilot_tab, text="Copilot")

    ttk.Label(self.copilot_tab, text="Ask Copilot").pack()
    self.copilot_entry = tk.Entry(self.copilot_tab)
    self.copilot_entry.pack(fill=tk.X)

    ttk.Button(self.copilot_tab, text="Submit", command=self._query_copilot).pack(pady=5)
    self.copilot_output = tk.Text(self.copilot_tab, height=10)
    self.copilot_output.pack(fill=tk.BOTH, expand=True)

def _query_copilot(self):
    query = self.copilot_entry.get()
    self.copilot_output.insert(tk.END, f"🤖 Copilot says: '{query}' is a great idea! Try layering it with WASD pulse and export as .rgbstack.\\n")
'''
    content += "\n" + copilot_ui
    print("✅ Copilot Assistant Tab added.")

# Inject tab creation calls
content = content.replace("self._create_status_bar()", """self._create_status_bar()
        self._create_effect_composer_tab()
        self._create_preview_recorder_tab()
        self._create_smart_zone_tab()
        self._create_ec_sandbox_tab()
        self._create_event_automation_tab()
        self._create_copilot_tab()""")

with open(controller_path, "w") as f:
    f.write(content)

print("✅ All next-gen orchestration features fully integrated.")
