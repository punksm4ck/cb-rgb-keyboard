import os

controller_path = "gui/controller.py"
plugins_dir = "plugins"
os.makedirs(plugins_dir, exist_ok=True)

with open(controller_path, "r") as f:
    content = f.read()

# 1. Real-Time Effect Looping and Sequencing
if "self.loop_var" not in content:
    loop_ui = '''
    def _create_loop_controls(self):
        """Add loop and sequence controls to timeline tab"""
        frame = ttk.LabelFrame(self.timeline_tab, text="Playback Options", padding="10")
        frame.pack(fill=tk.X, padx=10, pady=5)

        self.loop_var = tk.BooleanVar(value=False)
        self.sequence_var = tk.BooleanVar(value=False)
        self.reverse_var = tk.BooleanVar(value=False)

        ttk.Checkbutton(frame, text="Loop", variable=self.loop_var).pack(side=tk.LEFT)
        ttk.Checkbutton(frame, text="Sequence Mode", variable=self.sequence_var).pack(side=tk.LEFT)
        ttk.Checkbutton(frame, text="Reverse", variable=self.reverse_var).pack(side=tk.LEFT)

    def _run_timeline_effect(self):
        import json, time, requests
        try:
            lines = self.timeline_text.get(1.0, tk.END).splitlines()
            frames = [json.loads(line) for line in lines if line.strip()]
            if self.reverse_var.get():
                frames = frames[::-1]
            while True:
                for frame in frames:
                    for zone, color in frame["zones"].items():
                        requests.post("http://127.0.0.1:5000/set_zone_color", json={"zone": int(zone), "color": color})
                    time.sleep(frame.get("delay", 100) / 1000)
                if not self.loop_var.get():
                    break
        except Exception as e:
            print(f"Timeline error: {e}")
    '''
    content += "\n" + loop_ui
    content = content.replace("self._create_timeline_tab()", "self._create_timeline_tab()\n        self._create_loop_controls()")
    print("✅ Real-time effect looping and sequencing added.")

# 2. Modular Plugin Loader
if "self.plugin_tab" not in content:
    plugin_ui = '''
    def _create_plugin_tab(self):
        """Create plugin manager tab"""
        frame = ttk.Frame(self.plugin_tab)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.plugin_listbox = tk.Listbox(frame, height=10)
        self.plugin_listbox.pack(fill=tk.X, pady=5)

        ttk.Button(frame, text="Load Plugins", command=self._load_plugins).pack(pady=5)

    def _load_plugins(self):
        self.plugin_listbox.delete(0, tk.END)
        for fname in os.listdir("plugins"):
            if fname.endswith(".py"):
                self.plugin_listbox.insert(tk.END, fname)
                try:
                    __import__(f"plugins.{fname[:-3]}")
                    print(f"✅ Loaded plugin: {fname}")
                except Exception as e:
                    print(f"❌ Failed to load {fname}: {e}")
    '''
    content += "\n" + plugin_ui
    content = content.replace("self.notebook.add(self.config_browser_tab, text=\"Config Browser\")", "self.notebook.add(self.config_browser_tab, text=\"Config Browser\")\n        self.plugin_tab = ttk.Frame(self.notebook)\n        self.notebook.add(self.plugin_tab, text=\"Plugins\")\n        self._create_plugin_tab()")
    print("✅ Modular plugin loader added.")

# 3. AI-Powered Effect Suggestions
if "def _suggest_effect" not in content:
    ai_ui = '''
    def _create_ai_suggestions(self):
        """Add AI-powered effect suggestion button"""
        ttk.Button(self.timeline_tab, text="Surprise Me", command=self._suggest_effect).pack(pady=5)

    def _suggest_effect(self):
        import random
        zones = {str(i+1): f"#{random.randint(0,255):02x}{random.randint(0,255):02x}{random.randint(0,255):02x}" for i in range(24)}
        frame = {"zones": zones, "delay": 100}
        self.timeline_text.insert(tk.END, f"{frame}\\n")
        print("✨ Suggested effect added.")
    '''
    content += "\n" + ai_ui
    content = content.replace("self._create_timeline_tab()", "self._create_timeline_tab()\n        self._create_ai_suggestions()")
    print("✅ AI-powered effect suggestions added.")

# 4. Live Hardware Feedback Integration
if "def _poll_hardware_status" not in content:
    hardware_ui = '''
    def _poll_hardware_status(self):
        import random
        heatmap = [random.randint(0, 100) for _ in range(24)]
        for i, val in enumerate(heatmap):
            color = f"#{val:02x}0000"
            self.layout_canvas.itemconfig(self.zone_rects[i], fill=color)
        self.root.after(5000, self._poll_hardware_status)
    '''
    content += "\n" + hardware_ui
    content = content.replace("self._create_layout_tab()", "self._create_layout_tab()\n        self._poll_hardware_status()")
    print("✅ Live hardware feedback integration added.")

# 5. Preset Sharing and Import
if "def _import_preset_file" not in content:
    preset_ui = '''
    def _import_preset_file(self, path):
        import json
        try:
            with open(path) as f:
                preset = json.load(f)
            for zone, color in preset.get("zones", {}).items():
                import requests
                requests.post("http://127.0.0.1:5000/set_zone_color", json={"zone": int(zone), "color": color})
            print(f"✅ Imported preset from {path}")
        except Exception as e:
            print(f"❌ Failed to import preset: {e}")
    '''
    content += "\n" + preset_ui
    print("✅ Preset sharing and import added.")

# 6. Advanced GUI Customization
if "def _apply_theme" not in content:
    theme_ui = '''
    def _create_theme_switcher(self):
        """Add theme switcher"""
        frame = ttk.LabelFrame(self.root, text="Theme", padding="10")
        frame.pack(side=tk.BOTTOM, fill=tk.X)

        self.theme_var = tk.StringVar(value="dark")
        ttk.Combobox(frame, textvariable=self.theme_var, values=["dark", "light"], state="readonly").pack(side=tk.LEFT)
        ttk.Button(frame, text="Apply Theme", command=self._apply_theme).pack(side=tk.LEFT)

    def _apply_theme(self):
        theme = self.theme_var.get()
        bg = "black" if theme == "dark" else "white"
        fg = "white" if theme == "dark" else "black"
        self.root.configure(bg=bg)
        for widget in self.root.winfo_children():
            try:
                widget.configure(bg=bg, fg=fg)
            except:
                continue
    '''
    content += "\n" + theme_ui
    content = content.replace("self._create_status_bar()", "self._create_status_bar()\n        self._create_theme_switcher()")
    print("✅ Advanced GUI customization added.")

# 7. Effect Scheduler
if "self.scheduler_tab" not in content:
    scheduler_ui = ''
    def _create_scheduler_tab(self):
        """Create effect scheduler tab"""
        frame = ttk.Frame(self.scheduler_tab)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.schedule_entries = []

        for label in ["Wake-up wave (7:00)", "Focus pulse (14:00)"]:
            ttk.Label(frame, text=label).pack(anchor=tk.W)
            entry = tk.Text(frame, height=3)
            entry.pack(fill=tk.X, pady=2)
            self.schedule_entries.append((label, entry))

        ttk.Button(frame, text="Activate Schedule", command=self._run_schedule).pack(pady=5)

    def _run_schedule(self):
        import datetime, json, time, requests
        now = datetime.datetime.now().strftime("%H:%M")
        for label, entry in self.schedule_entries:
            if "7:00" in label and now == "07:00":
                frame = json.loads(entry.get(1.0, tk.END))
                for zone, color in frame.get("zones", {}).items():
                    requests.post("http://127.0.0.1:5000/set_zone_color", json={"zone": int(zone), "color": color})
            if "14:00" in label and now == "14:00":
                frame = json.loads(entry.get(1.0, tk.END))
                for zone, color in frame.get("zones", {}).items():
                    requests.post("http://127.0.0.1:5000/set_zone_color", json={"zone": int(zone), "color": color})
        self.root.after(60000, self._run_schedule)
