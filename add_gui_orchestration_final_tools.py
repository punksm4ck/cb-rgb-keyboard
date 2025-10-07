import os

controller_path = "gui/controller.py"

with open(controller_path, "r") as f:
    content = f.read()

# 1. Config Browser with Metadata Filters
if "self.config_browser_tab" not in content:
    content = content.replace(
        "self.notebook.add(self.diagnostics_tab, text=\"Diagnostics\")",
        "self.notebook.add(self.diagnostics_tab, text=\"Diagnostics\")\n        self.config_browser_tab = ttk.Frame(self.notebook)\n        self.notebook.add(self.config_browser_tab, text=\"Config Browser\")\n        self._create_config_browser_tab()"
    )

    browser_method = '''
    def _create_config_browser_tab(self):
        """Create config browser with metadata filters"""
        frame = ttk.Frame(self.config_browser_tab)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.config_filter_var = tk.StringVar(value="ALL")
        ttk.Label(frame, text="Filter by Type:").pack(anchor=tk.W)
        ttk.Combobox(frame, textvariable=self.config_filter_var, values=["ALL", "timeline", "groups"], state="readonly").pack(anchor=tk.W)
        ttk.Button(frame, text="Refresh", command=self._refresh_config_list).pack(pady=5)

        self.config_listbox = tk.Listbox(frame, height=10)
        self.config_listbox.pack(fill=tk.X, pady=5)

        self.config_metadata_text = tk.Text(frame, height=10)
        self.config_metadata_text.pack(fill=tk.BOTH, expand=True)

        self._refresh_config_list()

    def _refresh_config_list(self):
        self.config_listbox.delete(0, tk.END)
        filter_type = self.config_filter_var.get()
        for fname in os.listdir("."):
            if fname.endswith(".json") and "_config_" in fname:
                with open(fname) as f:
                    import json
                    try:
                        data = json.load(f)
                        if filter_type == "ALL" or data.get("metadata", {}).get("type") == filter_type:
                            self.config_listbox.insert(tk.END, fname)
                    except:
                        continue
        self.config_listbox.bind("<<ListboxSelect>>", self._show_config_metadata)

    def _show_config_metadata(self, event):
        selection = self.config_listbox.curselection()
        if not selection:
            return
        fname = self.config_listbox.get(selection[0])
        with open(fname) as f:
            import json
            data = json.load(f)
        meta = data.get("metadata", {})
        self.config_metadata_text.delete(1.0, tk.END)
        for k, v in meta.items():
            self.config_metadata_text.insert(tk.END, f"{k}: {v}\\n")
    '''
    content += "\n" + browser_method
    print("✅ Config browser with metadata filters added.")

# 2. Timeline Easing Functions
if "def _ease" not in content:
    easing_logic = '''
    def _ease(self, t, mode="linear"):
        if mode == "ease-in":
            return t * t
        elif mode == "ease-out":
            return t * (2 - t)
        elif mode == "ease-in-out":
            return 3 * t * t - 2 * t * t * t
        return t

    def _interpolate_keyframes(self, start, end, steps, easing="linear"):
        from colours import interpolate_rgb
        interpolated = []
        for i in range(steps):
            t = self._ease(i / steps, easing)
            frame = {"zones": {}, "delay": 100}
            for z in start["zones"]:
                c1 = start["zones"][z]
                c2 = end["zones"].get(z, c1)
                frame["zones"][z] = interpolate_rgb(c1, c2, t)
            interpolated.append(frame)
        return interpolated

    def _run_timeline_effect(self):
        import json, time, requests
        try:
            lines = self.timeline_text.get(1.0, tk.END).splitlines()
            frames = [json.loads(line) for line in lines if line.strip()]
            easing = "ease-in-out"
            for i in range(len(frames) - 1):
                steps = self._interpolate_keyframes(frames[i], frames[i+1], 5, easing)
                for frame in steps:
                    for zone, color in frame["zones"].items():
                        requests.post("http://127.0.0.1:5000/set_zone_color", json={"zone": int(zone), "color": color})
                    time.sleep(frame.get("delay", 100) / 1000)
        except Exception as e:
            print(f"Timeline error: {e}")
    '''
    content += "\n" + easing_logic
    print("✅ Timeline easing functions added.")

# 3. Export Diagnostics Chart as Image or CSV
if "def _export_diagnostics_chart" not in content:
    export_chart_logic = '''
    def _export_diagnostics_chart(self):
        try:
            self.diagnostics_chart.figure.savefig("diagnostics_chart.png")
            print("✅ Chart exported to diagnostics_chart.png")
        except Exception as e:
            print(f"Export failed: {e}")

    def _export_diagnostics_csv(self):
        try:
            import csv
            with open("diagnostics_data.csv", "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["Frame", "FPS", "Latency"])
                for i, (fps, lat) in enumerate(zip(self.diagnostics_data["fps"], self.diagnostics_data["latency"])):
                    writer.writerow([i+1, fps, lat])
            print("✅ Diagnostics exported to diagnostics_data.csv")
        except Exception as e:
            print(f"Export failed: {e}")
    '''
    content += "\n" + export_chart_logic

    content = content.replace("self.diagnostics_chart.get_tk_widget().pack(padx=10, pady=10)", '''self.diagnostics_chart.get_tk_widget().pack(padx=10, pady=10)
        ttk.Button(self.diagnostics_tab, text="Export Chart", command=self._export_diagnostics_chart).pack(pady=2)
        ttk.Button(self.diagnostics_tab, text="Export CSV", command=self._export_diagnostics_csv).pack(pady=2)''')
    print("✅ Export diagnostics chart as image and CSV added.")

with open(controller_path, "w") as f:
    f.write(content)
