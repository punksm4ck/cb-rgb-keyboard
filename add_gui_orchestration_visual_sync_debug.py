import os

controller_path = "gui/controller.py"
os.makedirs("avatars", exist_ok=True)

with open(controller_path, "r") as f:
    content = f.read()

# 1. MQTT Topic Mapping to Specific Zone Groups
if "def _start_mqtt_group_listener" not in content:
    mqtt_group_sync = '''
def _create_mqtt_group_tab(self):
    self.mqtt_group_tab = ttk.Frame(self.notebook)
    self.notebook.add(self.mqtt_group_tab, text="MQTT Groups")

    ttk.Label(self.mqtt_group_tab, text="Broker").pack()
    self.mqtt_group_broker_var = tk.StringVar(value="localhost")
    ttk.Entry(self.mqtt_group_tab, textvariable=self.mqtt_group_broker_var).pack()

    self.topic_zone_map = {
        "rgb/wasd": [1, 2, 3, 4],
        "rgb/numpad": [17, 18, 19, 20],
        "rgb/function": [5, 6, 7, 8]
    }

    ttk.Button(self.mqtt_group_tab, text="Start Group Listener", command=self._start_mqtt_group_listener).pack(pady=5)

def _start_mqtt_group_listener(self):
    try:
        import paho.mqtt.client as mqtt
        def on_message(client, userdata, msg):
            import json, requests
            topic = msg.topic
            zones = self.topic_zone_map.get(topic, [])
            color = msg.payload.decode()
            for z in zones:
                requests.post("http://127.0.0.1:5000/set_zone_color", json={"zone": z, "color": color})
            print(f"🔄 Synced {color} to zones {zones} via topic {topic}")

        client = mqtt.Client()
        client.on_message = on_message
        client.connect(self.mqtt_group_broker_var.get(), 1883, 60)
        for topic in self.topic_zone_map:
            client.subscribe(topic)
        client.loop_start()
        print("✅ MQTT group listener started.")
    except Exception as e:
        print(f"❌ MQTT group listener failed: {e}")
'''
    content += "\n" + mqtt_group_sync
    print("✅ MQTT topic mapping to specific zone groups added.")

# 2. Avatar Cropping and Preview
if "def _upload_avatar" not in content:
    avatar_crop_ui = '''
def _upload_avatar(self):
    from tkinter.filedialog import askopenfilename
    from PIL import Image, ImageTk
    path = askopenfilename(filetypes=[("PNG Images", "*.png")])
    if path:
        user = self.login_user_var.get()
        dest = f"avatars/{user}.png"
        img = Image.open(path).resize((64, 64)).crop((0, 0, 64, 64))
        img.save(dest)
        self.avatar_preview = ImageTk.PhotoImage(img)
        preview_label = tk.Label(self.login_tab, image=self.avatar_preview)
        preview_label.pack()
        print(f"🖼️ Cropped and previewed avatar for {user}")
'''
    content += "\n" + avatar_crop_ui
    print("✅ Avatar cropping and preview added.")

# 3. ESL Debugger with Breakpoint Toggles and Variable Watch GUI
if "def _create_debugger_tab" not in content:
    debugger_ui = '''
def _create_debugger_tab(self):
    self.debugger_tab = ttk.Frame(self.notebook)
    self.notebook.add(self.debugger_tab, text="Debugger")

    ttk.Label(self.debugger_tab, text="Script").pack()
    self.debug_text = tk.Text(self.debugger_tab, height=10)
    self.debug_text.pack(fill=tk.X)

    ttk.Label(self.debugger_tab, text="Breakpoints (line numbers)").pack()
    self.breakpoint_var = tk.StringVar()
    ttk.Entry(self.debugger_tab, textvariable=self.breakpoint_var).pack()

    ttk.Button(self.debugger_tab, text="Run with Breakpoints", command=self._run_debugger).pack(pady=5)

    ttk.Label(self.debugger_tab, text="Variable Watch").pack()
    self.watch_text = tk.Text(self.debugger_tab, height=10)
    self.watch_text.pack(fill=tk.BOTH, expand=True)

def _run_debugger(self):
    import time
    lines = self.debug_text.get(1.0, tk.END).splitlines()
    breakpoints = [int(x.strip()) for x in self.breakpoint_var.get().split(",") if x.strip().isdigit()]
    local_vars = {}
    self.watch_text.delete(1.0, tk.END)
    for i, line in enumerate(lines):
        try:
            exec(line, {"requests": __import__("requests")}, local_vars)
            if (i+1) in breakpoints:
                self.watch_text.insert(tk.END, f"⛔ Breakpoint at line {i+1}: {line}\\n")
                for k, v in local_vars.items():
                    self.watch_text.insert(tk.END, f"  {k} = {v}\\n")
                time.sleep(1)
        except Exception as e:
            self.watch_text.insert(tk.END, f"❌ Error at line {i+1}: {e}\\n")
            break
'''
    content += "\n" + debugger_ui
    print("✅ ESL debugger with breakpoint toggles and variable watch GUI added.")

# Inject tab creation calls
content = content.replace("self._create_status_bar()", """self._create_status_bar()
        self._create_mqtt_group_tab()
        self._create_debugger_tab()""")

with open(controller_path, "w") as f:
    f.write(content)

print("✅ All visual sync and debugging features fully integrated.")
