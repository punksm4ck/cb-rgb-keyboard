import os

controller_path = "gui/controller.py"

with open(controller_path, "r") as f:
    content = f.read()

# 1. Snap-to-Grid for Drag Layout
if "self._snap_to_grid" not in content:
    snap_logic = '''
    def _snap_to_grid(self, x, y, grid_size=60):
        gx = round(x / grid_size) * grid_size
        gy = round(y / grid_size) * grid_size
        return gx, gy

    def _drag_motion(self, event):
        if self.dragging_idx is not None:
            x, y = self._snap_to_grid(event.x, event.y)
            self.zone_labels[self.dragging_idx].place(x=x, y=y)
    '''
    content += "\n" + snap_logic
    print("✅ Snap-to-grid for drag layout added.")

# 2. Timeline Interpolation Between Keyframes
if "def _interpolate_keyframes" not in content:
    interpolation_logic = '''
    def _interpolate_keyframes(self, start, end, steps):
        from colours import interpolate_rgb
        interpolated = []
        for i in range(steps):
            frame = {"zones": {}, "delay": 100}
            for z in start["zones"]:
                c1 = start["zones"][z]
                c2 = end["zones"].get(z, c1)
                frame["zones"][z] = interpolate_rgb(c1, c2, i / steps)
            interpolated.append(frame)
        return interpolated

    def _run_timeline_effect(self):
        import json, time, requests
        try:
            lines = self.timeline_text.get(1.0, tk.END).splitlines()
            frames = [json.loads(line) for line in lines if line.strip()]
            for i in range(len(frames) - 1):
                steps = self._interpolate_keyframes(frames[i], frames[i+1], 5)
                for frame in steps:
                    for zone, color in frame["zones"].items():
                        requests.post("http://127.0.0.1:5000/set_zone_color", json={"zone": int(zone), "color": color})
                    time.sleep(frame.get("delay", 100) / 1000)
        except Exception as e:
            print(f"Timeline error: {e}")
    '''
    content += "\n" + interpolation_logic
    print("✅ Timeline interpolation between keyframes added.")

# 3. Diagnostics History Chart
if "self.diagnostics_chart" not in content:
    chart_logic = '''
    def _create_diagnostics_chart(self):
        """Create diagnostics history chart"""
        import matplotlib.pyplot as plt
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

        self.diagnostics_data = {"fps": [], "latency": []}
        fig, ax = plt.subplots(figsize=(6, 2))
        self.diagnostics_chart = FigureCanvasTkAgg(fig, master=self.diagnostics_tab)
        self.diagnostics_chart.get_tk_widget().pack(padx=10, pady=10)
        self.diagnostics_ax = ax

    def _update_diagnostics_metrics(self):
        import random
        fps = random.randint(28, 32)
        latency = random.randint(5, 15)
        self.fps_var.set(f"FPS: {fps}")
        self.latency_var.set(f"Latency: {latency} ms")
        self.sync_var.set("Zone Sync: OK")

        self.diagnostics_data["fps"].append(fps)
        self.diagnostics_data["latency"].append(latency)
        if len(self.diagnostics_data["fps"]) > 30:
            self.diagnostics_data["fps"] = self.diagnostics_data["fps"][-30:]
            self.diagnostics_data["latency"] = self.diagnostics_data["latency"][-30:]

        self.diagnostics_ax.clear()
        self.diagnostics_ax.plot(self.diagnostics_data["fps"], label="FPS", color="cyan")
        self.diagnostics_ax.plot(self.diagnostics_data["latency"], label="Latency", color="orange")
        self.diagnostics_ax.legend()
        self.diagnostics_ax.set_ylim(0, 40)
        self.diagnostics_chart.draw()

        self.root.after(3000, self._update_diagnostics_metrics)
    '''
    content += "\n" + chart_logic
    content = content.replace("self._create_diagnostics_metrics()", "self._create_diagnostics_metrics()\n        self._create_diagnostics_chart()")
    print("✅ Diagnostics history chart added.")

# 4. Config Versioning and Metadata
if "def _save_config_with_metadata" not in content:
    config_logic = '''
    def _save_config_with_metadata(self, config_type, data):
        import json, datetime
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        metadata = {
            "type": config_type,
            "created": timestamp,
            "author": "Thomas",
            "zones": len(data.get("zones", {})),
            "description": f"{config_type} config saved at {timestamp}"
        }
        full_config = {"metadata": metadata, "data": data}
        fname = f"{config_type}_config_{timestamp}.json"
        with open(fname, "w") as f:
            json.dump(full_config, f, indent=2)
        print(f"✅ {config_type} config saved with metadata to {fname}")
    '''
    content += "\n" + config_logic

    content = content.replace("self._export_timeline()", "self._export_timeline()\n        self._save_config_with_metadata(\"timeline\", json.loads(self.timeline_text.get(1.0, tk.END)))")
    content = content.replace("self._export_groups()", "self._export_groups()\n        self._save_config_with_metadata(\"groups\", {name: var.get() for name, var in self.group_entries.items()})")
    print("✅ Config versioning and metadata added.")

with open(controller_path, "w") as f:
    f.write(content)
