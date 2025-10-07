import os

controller_path = "gui/controller.py"

with open(controller_path, "r") as f:
    content = f.read()

# 1. Config Tagging and Search
if "self.config_tag_var" not in content:
    tagging_ui = '''
    def _create_config_browser_tagging(self):
        """Add tagging and search to config browser"""
        ttk.Label(self.config_browser_tab, text="Search Tag:").pack(anchor=tk.W)
        self.config_tag_var = tk.StringVar()
        ttk.Entry(self.config_browser_tab, textvariable=self.config_tag_var, width=30).pack(anchor=tk.W, pady=2)
        ttk.Button(self.config_browser_tab, text="Search by Tag", command=self._search_config_by_tag).pack(pady=5)

    def _search_config_by_tag(self):
        tag = self.config_tag_var.get().lower()
        self.config_listbox.delete(0, tk.END)
        for fname in os.listdir("."):
            if fname.endswith(".json") and "_config_" in fname:
                with open(fname) as f:
                    import json
                    try:
                        data = json.load(f)
                        tags = data.get("metadata", {}).get("tags", [])
                        if any(tag in t.lower() for t in tags):
                            self.config_listbox.insert(tk.END, fname)
                    except:
                        continue
    '''
    content += "\n" + tagging_ui
    content = content.replace("self._create_config_browser_tab()", "self._create_config_browser_tab()\n        self._create_config_browser_tagging()")
    print("✅ Config tagging and search added.")

# 2. Custom Easing Curves
if "def _custom_ease" not in content:
    easing_ui = '''
    def _custom_ease(self, t, curve="linear"):
        import math
        if curve == "ease-in":
            return t * t
        elif curve == "ease-out":
            return t * (2 - t)
        elif curve == "ease-in-out":
            return 3 * t * t - 2 * t * t * t
        elif curve == "bounce":
            return abs(math.sin(6.28 * t) * (1 - t))
        elif curve == "elastic":
            return math.sin(13 * t) * math.pow(2, 10 * (t - 1))
        return t

    def _interpolate_keyframes(self, start, end, steps, curve="linear"):
        from colours import interpolate_rgb
        interpolated = []
        for i in range(steps):
            t = self._custom_ease(i / steps, curve)
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
            curve = "bounce"
            for i in range(len(frames) - 1):
                steps = self._interpolate_keyframes(frames[i], frames[i+1], 5, curve)
                for frame in steps:
                    for zone, color in frame["zones"].items():
                        requests.post("http://127.0.0.1:5000/set_zone_color", json={"zone": int(zone), "color": color})
                    time.sleep(frame.get("delay", 100) / 1000)
        except Exception as e:
            print(f"Timeline error: {e}")
    '''
    content += "\n" + easing_ui
    print("✅ Custom easing curves added.")

# 3. Diagnostics Export Scheduler / Auto-Save
if "def _auto_export_diagnostics" not in content:
    auto_export_logic = '''
    def _auto_export_diagnostics(self):
        import csv, datetime
        try:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            with open(f"diagnostics_{timestamp}.csv", "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["Frame", "FPS", "Latency"])
                for i, (fps, lat) in enumerate(zip(self.diagnostics_data["fps"], self.diagnostics_data["latency"])):
                    writer.writerow([i+1, fps, lat])
            print(f"✅ Auto-saved diagnostics to diagnostics_{timestamp}.csv")
        except Exception as e:
            print(f"Auto-export failed: {e}")
        self.root.after(60000, self._auto_export_diagnostics)
    '''
    content += "\n" + auto_export_logic
    content = content.replace("self._update_diagnostics_metrics()", "self._update_diagnostics_metrics()\n        self._auto_export_diagnostics()")
    print("✅ Diagnostics export scheduler and auto-save added.")

with open(controller_path, "w") as f:
    f.write(content)
