import os

controller_path = "gui/controller.py"

with open(controller_path, "r") as f:
    content = f.read()

# 1. Visual Layout Tab
if "self.layout_tab" not in content:
    content = content.replace(
        "self.notebook.add(self.preset_tab, text=\"Presets\")",
        "self.notebook.add(self.preset_tab, text=\"Presets\")\n        self.layout_tab = ttk.Frame(self.notebook)\n        self.notebook.add(self.layout_tab, text=\"Keyboard Layout\")\n        self._create_layout_tab()"
    )

    layout_method = '''
    def _create_layout_tab(self):
        """Create visual layout tab matching physical keyboard"""
        canvas = tk.Canvas(self.layout_tab, width=800, height=300, bg="black")
        canvas.pack(padx=10, pady=10)

        self.zone_rects = []
        self.zone_colors = ["#000000"] * 24

        for i in range(24):
            x = 30 + (i % 12) * 60
            y = 30 + (i // 12) * 100
            rect = canvas.create_rectangle(x, y, x+50, y+50, fill="#000000", outline="white")
            canvas.tag_bind(rect, "<Button-1>", lambda e, idx=i: self._edit_zone_color(idx))
            self.zone_rects.append(rect)

        self.layout_canvas = canvas
    '''
    content += "\n" + layout_method
    print("✅ Visual layout tab added.")

# 2. Timeline-Based Effect Designer
if "self.timeline_tab" not in content:
    content = content.replace(
        "self.notebook.add(self.layout_tab, text=\"Keyboard Layout\")",
        "self.notebook.add(self.layout_tab, text=\"Keyboard Layout\")\n        self.timeline_tab = ttk.Frame(self.notebook)\n        self.notebook.add(self.timeline_tab, text=\"Effect Designer\")\n        self._create_timeline_tab()"
    )

    timeline_method = '''
    def _create_timeline_tab(self):
        """Create timeline-based effect designer"""
        frame = ttk.Frame(self.timeline_tab)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        ttk.Label(frame, text="Effect Timeline (ms):").pack(anchor=tk.W)
        self.timeline_text = tk.Text(frame, height=10)
        self.timeline_text.pack(fill=tk.BOTH, expand=True)

        run_button = ttk.Button(frame, text="Run Timeline", command=self._run_timeline_effect)
        run_button.pack(pady=5)

    def _run_timeline_effect(self):
        import json, time, requests
        try:
            lines = self.timeline_text.get(1.0, tk.END).splitlines()
            for line in lines:
                if not line.strip():
                    continue
                entry = json.loads(line)
                for zone, color in entry["zones"].items():
                    requests.post("http://127.0.0.1:5000/set_zone_color", json={"zone": int(zone), "color": color})
                time.sleep(entry.get("delay", 100) / 1000)
        except Exception as e:
            print(f"Timeline error: {e}")
    '''
    content += "\n" + timeline_method
    print("✅ Timeline-based effect designer added.")

# 3. Zone Grouping and Batch Scripting
if "self.group_tab" not in content:
    content = content.replace(
        "self.notebook.add(self.timeline_tab, text=\"Effect Designer\")",
        "self.notebook.add(self.timeline_tab, text=\"Effect Designer\")\n        self.group_tab = ttk.Frame(self.notebook)\n        self.notebook.add(self.group_tab, text=\"Zone Groups\")\n        self._create_group_tab()"
    )

    group_method = '''
    def _create_group_tab(self):
        """Create zone grouping and batch scripting tab"""
        frame = ttk.Frame(self.group_tab)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.group_entries = {}
        for name in ["WASD", "FunctionRow", "Numpad", "LeftSide", "RightSide"]:
            ttk.Label(frame, text=f"{name} Zones:").pack(anchor=tk.W)
            var = tk.StringVar()
            ttk.Entry(frame, textvariable=var, width=30).pack(anchor=tk.W, pady=2)
            self.group_entries[name] = var

        ttk.Label(frame, text="Color:").pack(anchor=tk.W)
        self.group_color_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.group_color_var, width=10).pack(anchor=tk.W, pady=2)

        apply_button = ttk.Button(frame, text="Apply to Groups", command=self._apply_group_colors)
        apply_button.pack(pady=5)

    def _apply_group_colors(self):
        import requests
        color = self.group_color_var.get()
        for name, var in self.group_entries.items():
            zones = var.get().split(",")
            for z in zones:
                try:
                    zone = int(z.strip())
                    requests.post("http://127.0.0.1:5000/set_zone_color", json={"zone": zone, "color": color})
                except:
                    continue
    '''
    content += "\n" + group_method
    print("✅ Zone grouping and batch scripting tab added.")

# 4. Live Preview and Diagnostics Tab
if "self.diagnostics_tab" not in content:
    content = content.replace(
        "self.notebook.add(self.group_tab, text=\"Zone Groups\")",
        "self.notebook.add(self.group_tab, text=\"Zone Groups\")\n        self.diagnostics_tab = ttk.Frame(self.notebook)\n        self.notebook.add(self.diagnostics_tab, text=\"Diagnostics\")\n        self._create_diagnostics_tab()"
    )

    diagnostics_method = '''
    def _create_diagnostics_tab(self):
        """Create diagnostics tab with live preview"""
        frame = ttk.Frame(self.diagnostics_tab)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.diagnostics_text = tk.Text(frame, height=15)
        self.diagnostics_text.pack(fill=tk.BOTH, expand=True)

        self.root.after(3000, self._update_diagnostics)

    def _update_diagnostics(self):
        import requests
        try:
            r = requests.get("http://127.0.0.1:5000/status")
            self.diagnostics_text.delete(1.0, tk.END)
            self.diagnostics_text.insert(tk.END, f"Status: {r.json()}")
        except Exception as e:
            self.diagnostics_text.delete(1.0, tk.END)
            self.diagnostics_text.insert(tk.END, f"Error: {e}")
        self.root.after(3000, self._update_diagnostics)
    '''
    content += "\n" + diagnostics_method
    print("✅ Live preview and diagnostics tab added.")

with open(controller_path, "w") as f:
    f.write(content)
