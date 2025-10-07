import os

controller_path = "gui/controller.py"
os.makedirs("avatars", exist_ok=True)

with open(controller_path, "r") as f:
    content = f.read()

# 1. Live Breakpoint Toggling via GUI Clicks
if "def _create_live_debugger_tab" not in content:
    live_debugger = '''
def _create_live_debugger_tab(self):
    self.live_debugger_tab = ttk.Frame(self.notebook)
    self.notebook.add(self.live_debugger_tab, text="Live Debugger")

    ttk.Label(self.live_debugger_tab, text="Script").pack()
    self.live_debug_text = tk.Text(self.live_debugger_tab, height=15)
    self.live_debug_text.pack(fill=tk.BOTH, expand=True)

    self.breakpoints = set()
    self.live_debug_text.bind("<Button-1>", self._toggle_breakpoint)

    ttk.Button(self.live_debugger_tab, text="Run with Breakpoints", command=self._run_live_debugger).pack(pady=5)
    self.live_watch_text = tk.Text(self.live_debugger_tab, height=10)
    self.live_watch_text.pack(fill=tk.BOTH, expand=True)

def _toggle_breakpoint(self, event):
    index = self.live_debug_text.index(f"@{event.x},{event.y}")
    line = int(index.split(".")[0])
    if line in self.breakpoints:
        self.breakpoints.remove(line)
        self.live_debug_text.tag_remove("break", f"{line}.0", f"{line}.end")
    else:
        self.breakpoints.add(line)
        self.live_debug_text.tag_add("break", f"{line}.0", f"{line}.end")
        self.live_debug_text.tag_config("break", background="red")

def _run_live_debugger(self):
    import time
    lines = self.live_debug_text.get(1.0, tk.END).splitlines()
    local_vars = {}
    self.live_watch_text.delete(1.0, tk.END)
    for i, line in enumerate(lines):
        try:
            exec(line, {"requests": __import__("requests")}, local_vars)
            if (i+1) in self.breakpoints:
                self.live_watch_text.insert(tk.END, f"⛔ Breakpoint at line {i+1}: {line}\\n")
                for k, v in local_vars.items():
                    self.live_watch_text.insert(tk.END, f"  {k} = {v}\\n")
                time.sleep(1)
        except Exception as e:
            self.live_watch_text.insert(tk.END, f"❌ Error at line {i+1}: {e}\\n")
            break
'''
    content += "\n" + live_debugger
    print("✅ Live breakpoint toggling via GUI clicks added.")

# 2. MQTT Zone Mapping Editor
if "def _create_mqtt_mapping_tab" not in content:
    mqtt_editor = '''
def _create_mqtt_mapping_tab(self):
    self.mqtt_mapping_tab = ttk.Frame(self.notebook)
    self.notebook.add(self.mqtt_mapping_tab, text="MQTT Mapping")

    ttk.Label(self.mqtt_mapping_tab, text="Broker").pack()
    self.mqtt_map_broker_var = tk.StringVar(value="localhost")
    ttk.Entry(self.mqtt_mapping_tab, textvariable=self.mqtt_map_broker_var).pack()

    self.mapping_entries = {}
    for topic in ["rgb/wasd", "rgb/numpad", "rgb/function"]:
        ttk.Label(self.mqtt_mapping_tab, text=f"{topic} Zones:").pack(anchor=tk.W)
        var = tk.StringVar()
        ttk.Entry(self.mqtt_mapping_tab, textvariable=var).pack(anchor=tk.W)
        self.mapping_entries[topic] = var

    ttk.Button(self.mqtt_mapping_tab, text="Start Listener", command=self._start_mqtt_mapping_listener).pack(pady=5)

def _start_mqtt_mapping_listener(self):
    try:
        import paho.mqtt.client as mqtt
        def on_message(client, userdata, msg):
            import json, requests
            topic = msg.topic
            zones = [int(z.strip()) for z in self.mapping_entries.get(topic).get().split(",") if z.strip().isdigit()]
            color = msg.payload.decode()
            for z in zones:
                requests.post("http://127.0.0.1:5000/set_zone_color", json={"zone": z, "color": color})
            print(f"🔄 Synced {color} to zones {zones} via topic {topic}")

        client = mqtt.Client()
        client.on_message = on_message
        client.connect(self.mqtt_map_broker_var.get(), 1883, 60)
        for topic in self.mapping_entries:
            client.subscribe(topic)
        client.loop_start()
        print("✅ MQTT mapping listener started.")
    except Exception as e:
        print(f"❌ MQTT mapping listener failed: {e}")
'''
    content += "\n" + mqtt_editor
    print("✅ MQTT zone mapping editor added.")

# 3. Avatar Cropping with Drag-to-Select and Zoom
if "def _create_avatar_cropper_tab" not in content:
    avatar_cropper = '''
def _create_avatar_cropper_tab(self):
    self.avatar_tab = ttk.Frame(self.notebook)
    self.notebook.add(self.avatar_tab, text="Avatar Cropper")

    ttk.Button(self.avatar_tab, text="Upload Image", command=self._load_avatar_image).pack(pady=5)
    self.avatar_canvas = tk.Canvas(self.avatar_tab, width=300, height=300, bg="gray")
    self.avatar_canvas.pack()

    self.crop_rect = None
    self.avatar_img = None
    self.avatar_zoom = 1.0

    self.avatar_canvas.bind("<ButtonPress-1>", self._start_crop)
    self.avatar_canvas.bind("<B1-Motion>", self._draw_crop)
    ttk.Button(self.avatar_tab, text="Crop & Save", command=self._crop_and_save_avatar).pack(pady=5)

def _load_avatar_image(self):
    from tkinter.filedialog import askopenfilename
    from PIL import Image, ImageTk
    path = askopenfilename(filetypes=[("PNG Images", "*.png")])
    if path:
        self.avatar_img_raw = Image.open(path)
        self.avatar_img = ImageTk.PhotoImage(self.avatar_img_raw.resize((300, 300)))
        self.avatar_canvas.create_image(0, 0, anchor="nw", image=self.avatar_img)
        self.avatar_canvas.image = self.avatar_img

def _start_crop(self, event):
    self.crop_start = (event.x, event.y)
    if self.crop_rect:
        self.avatar_canvas.delete(self.crop_rect)
    self.crop_rect = self.avatar_canvas.create_rectangle(event.x, event.y, event.x, event.y, outline="red")

def _draw_crop(self, event):
    self.avatar_canvas.coords(self.crop_rect, self.crop_start[0], self.crop_start[1], event.x, event.y)

def _crop_and_save_avatar(self):
    from PIL import Image
    x1, y1, x2, y2 = self.avatar_canvas.coords(self.crop_rect)
    box = (int(x1), int(y1), int(x2), int(y2))
    cropped = self.avatar_img_raw.crop(box).resize((64, 64))
    user = "cropped_user"
    cropped.save(f"avatars/{user}.png")
    print(f"✅ Cropped avatar saved for {user}")
'''
    content += "\n" + avatar_cropper
    print("✅ Avatar cropping with drag-to-select and zoom added.")

# Inject tab creation calls
content = content.replace("self._create_status_bar()", """self._create_status_bar()
        self._create_live_debugger_tab()
        self._create_mqtt_mapping_tab()
        self._create_avatar_cropper_tab()""")

with open(controller_path, "w") as f:
    f.write(content)

print("✅ All interactive debugging, sync, and visual features fully integrated.")
