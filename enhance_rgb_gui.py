import re

controller_path = "gui/controller.py"

def inject_gui_enhancements():
    with open(controller_path, "r") as f:
        content = f.read()

    # 1. Inject preset dropdown in _create_effect_controls
    if "self.selected_preset_var" not in content:
        dropdown_code = '''
        # Preset selection
        preset_frame = ttk.Frame(effects_frame)
        preset_frame.pack(fill=tk.X, pady=(5, 10))

        ttk.Label(preset_frame, text="Preset:").pack(side=tk.LEFT)

        self.selected_preset_var = tk.StringVar()
        self.preset_combo = ttk.Combobox(
            preset_frame,
            textvariable=self.selected_preset_var,
            values=list(self.load_presets().keys()),
            state="readonly",
            width=20
        )
        self.preset_combo.pack(side=tk.LEFT, padx=(5, 10))

        run_preset_button = ttk.Button(
            preset_frame,
            text="Run Preset",
            command=self.run_selected_preset
        )
        run_preset_button.pack(side=tk.LEFT, padx=5)
        '''

        content = re.sub(r"(# Effect parameters[\s\S]+?params_frame = ttk\.LabelFrame\(effects_frame,.*?\))",
                         dropdown_code + r"\n\1", content)
        print("✅ Injected preset dropdown.")

    # 2. Inject scheduler controls
    if "self.schedule_delay_var" not in content:
        scheduler_code = '''
        # Scheduler
        schedule_frame = ttk.Frame(effects_frame)
        schedule_frame.pack(fill=tk.X, pady=(5, 10))

        ttk.Label(schedule_frame, text="Schedule Effect (seconds):").pack(side=tk.LEFT)
        self.schedule_delay_var = tk.IntVar(value=10)
        ttk.Entry(schedule_frame, textvariable=self.schedule_delay_var, width=10).pack(side=tk.LEFT, padx=(5, 10))

        schedule_button = ttk.Button(
            schedule_frame,
            text="Schedule Start",
            command=self.schedule_effect
        )
        schedule_button.pack(side=tk.LEFT, padx=5)
        '''

        content = re.sub(r"(# Effect parameters[\s\S]+?params_frame = ttk\.LabelFrame\(effects_frame,.*?\))",
                         scheduler_code + r"\n\1", content)
        print("✅ Injected scheduler controls.")

    # 3. Inject preset editor tab
    if "self.presets_tab" not in content:
        tab_code = '''
        self.presets_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.presets_tab, text="Preset Editor")
        '''

        content = re.sub(r"(# Create tabs[\s\S]+?self\.notebook\.add\(self\.settings_tab, text=\"Settings\"\))",
                         r"\1\n" + tab_code, content)
        print("✅ Injected preset editor tab.")

    # 4. Inject _create_preset_editor call
    if "_create_preset_editor()" not in content:
        content = re.sub(r"(# Create GUI sections[\s\S]+?self\._create_status_bar\(\))",
                         r"\1\n        self._create_preset_editor()", content)

    # 5. Inject _create_preset_editor method
    if "def _create_preset_editor" not in content:
        editor_code = '''
    def _create_preset_editor(self):
        """Create visual preset editor"""
        editor_frame = ttk.LabelFrame(self.presets_tab, text="Create New Preset", padding="10")
        editor_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        ttk.Label(editor_frame, text="Preset Name:").pack(anchor=tk.W)
        self.new_preset_name_var = tk.StringVar()
        ttk.Entry(editor_frame, textvariable=self.new_preset_name_var, width=30).pack(anchor=tk.W, pady=5)

        ttk.Label(editor_frame, text="Preset Type:").pack(anchor=tk.W)
        self.new_preset_type_var = tk.StringVar(value="sequence")
        ttk.Combobox(editor_frame, textvariable=self.new_preset_type_var, values=["sequence", "pulse"], state="readonly").pack(anchor=tk.W, pady=5)

        ttk.Label(editor_frame, text="Colors (comma-separated hex):").pack(anchor=tk.W)
        self.new_preset_colors_var = tk.StringVar()
        ttk.Entry(editor_frame, textvariable=self.new_preset_colors_var, width=50).pack(anchor=tk.W, pady=5)

        ttk.Label(editor_frame, text="Delay (ms):").pack(anchor=tk.W)
        self.new_preset_delay_var = tk.IntVar(value=100)
        ttk.Entry(editor_frame, textvariable=self.new_preset_delay_var, width=10).pack(anchor=tk.W, pady=5)

        save_button = ttk.Button(editor_frame, text="Save Preset", command=self.save_new_preset)
        save_button.pack(pady=10)
        '''
        content += "\n" + editor_code
        print("✅ Injected visual preset editor.")

    # 6. Inject save_new_preset method
    if "def save_new_preset" not in content:
        save_code = '''
    def save_new_preset(self):
        """Save new preset to presets.json"""
        name = self.new_preset_name_var.get().strip()
        preset_type = self.new_preset_type_var.get()
        colors = [c.strip() for c in self.new_preset_colors_var.get().split(",") if c.strip()]
        delay = self.new_preset_delay_var.get()

        if not name or not colors:
            messagebox.showerror("Error", "Preset name and colors are required.")
            return

        try:
            with open("presets.json", "r") as f:
                presets = json.load(f)
        except:
            presets = {}

        presets[name] = {
            "type": preset_type,
            "colors": colors,
            "delay": delay
        }

        with open("presets.json", "w") as f:
            json.dump(presets, f, indent=4)

        messagebox.showinfo("Success", f"Preset '{name}' saved.")
        self.preset_combo['values'] = list(presets.keys())
        '''
        content += "\n" + save_code
        print("✅ Injected save_new_preset method.")

    # 7. Inject run_selected_preset method
    if "def run_selected_preset" not in content:
        run_code = '''
    def run_selected_preset(self):
        """Run the selected preset from dropdown"""
        preset_name = self.selected_preset_var.get()
        if preset_name:
            self.run_preset_effect(preset_name)
        '''
        content += "\n" + run_code
        print("✅ Injected run_selected_preset method.")

    # 8. Inject schedule_effect method
    if "def schedule_effect" not in content:
        schedule_code = '''
    def schedule_effect(self):
        """Schedule effect to start after delay"""
        delay = self.schedule_delay_var.get()
        effect_name = self.effect_var.get()
        self.logger.info(f"Scheduling effect '{effect_name}' to start in {delay} seconds.")
        self.root.after(delay * 1000, self.start_effect)
        '''
        content += "\n" + schedule_code
        print("✅ Injected schedule_effect method.")

    with open(controller_path, "w") as f:
        f.write(content)

inject_gui_enhancements()
