import os

controller_path = "gui/controller.py"

with open(controller_path, "r") as f:
    content = f.read()

# 1. Tag Manager with Autocomplete
if "self.tag_autocomplete" not in content:
    tag_manager_ui = '''
    def _create_tag_manager(self):
        """Create tag manager with autocomplete"""
        ttk.Label(self.config_browser_tab, text="Add Tag:").pack(anchor=tk.W)
        self.new_tag_var = tk.StringVar()
        self.tag_autocomplete = ttk.Combobox(self.config_browser_tab, textvariable=self.new_tag_var, values=[], width=30)
        self.tag_autocomplete.pack(anchor=tk.W, pady=2)
        ttk.Button(self.config_browser_tab, text="Attach Tag to Selected", command=self._attach_tag_to_config).pack(pady=5)

    def _attach_tag_to_config(self):
        selection = self.config_listbox.curselection()
        if not selection:
            return
        fname = self.config_listbox.get(selection[0])
        tag = self.new_tag_var.get()
        if not tag:
            return
        try:
            import json
            with open(fname, "r") as f:
                data = json.load(f)
            tags = data.get("metadata", {}).get("tags", [])
            if tag not in tags:
                tags.append(tag)
            data["metadata"]["tags"] = tags
            with open(fname, "w") as f:
                json.dump(data, f, indent=2)
            self._update_tag_autocomplete()
            print(f"✅ Tag '{tag}' attached to {fname}")
        except Exception as e:
            print(f"Tagging failed: {e}")

    def _update_tag_autocomplete(self):
        tags = set()
        for fname in os.listdir("."):
            if fname.endswith(".json") and "_config_" in fname:
                try:
                    import json
                    with open(fname) as f:
                        data = json.load(f)
                    tags.update(data.get("metadata", {}).get("tags", []))
                except:
                    continue
        self.tag_autocomplete["values"] = sorted(tags)
    '''
    content += "\n" + tag_manager_ui
    content = content.replace("self._create_config_browser_tab()", "self._create_config_browser_tab()\n        self._create_tag_manager()\n        self._update_tag_autocomplete()")
    print("✅ Tag manager with autocomplete added.")

# 2. Easing Curve Visualizer
if "def _show_easing_curve" not in content:
    easing_visualizer = '''
    def _show_easing_curve(self, curve="ease-in-out"):
        import matplotlib.pyplot as plt
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

        fig, ax = plt.subplots(figsize=(4, 2))
        x = [i / 100 for i in range(101)]
        y = [self._custom_ease(t, curve) for t in x]
        ax.plot(x, y, label=curve, color="lime")
        ax.set_title(f"Easing: {curve}")
        ax.set_ylim(0, 1)
        ax.legend()

        canvas = FigureCanvasTkAgg(fig, master=self.timeline_tab)
        canvas.get_tk_widget().pack(pady=5)
        canvas.draw()
    '''
    content += "\n" + easing_visualizer
    content = content.replace("self._create_timeline_tab()", "self._create_timeline_tab()\n        self._show_easing_curve(\"ease-in-out\")")
    print("✅ Easing curve visualizer added.")

# 3. Export Scheduler with Interval Control and Toggle
if "self.export_interval_var" not in content:
    scheduler_ui = '''
    def _create_export_scheduler(self):
        """Create export scheduler controls"""
        frame = ttk.LabelFrame(self.diagnostics_tab, text="Auto Export Settings", padding="10")
        frame.pack(fill=tk.X, padx=10, pady=10)

        self.export_enabled_var = tk.BooleanVar(value=True)
        self.export_interval_var = tk.IntVar(value=60)

        ttk.Checkbutton(frame, text="Enable Auto Export", variable=self.export_enabled_var).pack(anchor=tk.W)
        ttk.Label(frame, text="Interval (seconds):").pack(anchor=tk.W)
        ttk.Entry(frame, textvariable=self.export_interval_var, width=10).pack(anchor=tk.W)

        self.root.after(5000, self._scheduled_export_loop)

    def _scheduled_export_loop(self):
        if self.export_enabled_var.get():
            self._auto_export_diagnostics()
        interval = max(10, self.export_interval_var.get()) * 1000
        self.root.after(interval, self._scheduled_export_loop)
    '''
    content += "\n" + scheduler_ui
    content = content.replace("self._create_diagnostics_tab()", "self._create_diagnostics_tab()\n        self._create_export_scheduler()")
    print("✅ Export scheduler with interval control and toggle added.")

with open(controller_path, "w") as f:
    f.write(content)
