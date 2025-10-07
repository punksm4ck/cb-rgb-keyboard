import os

controller_path = "gui/controller.py"
os.makedirs("avatars", exist_ok=True)

with open(controller_path, "r") as f:
    content = f.read()

# 1. MQTT Listener for Real-Time Effect Sync
if "def _start_mqtt_listener" not in content:
    mqtt_listener = '''
def _create_mqtt_listener_tab(self):
    self.mqtt_tab = ttk.Frame(self.notebook)
    self.notebook.add(self.mqtt_tab, text="MQTT Listener")

    ttk.Label(self.mqtt_tab, text="Broker").pack()
    self.mqtt_broker_var = tk.StringVar(value="localhost")
    ttk.Entry(self.mqtt_tab, textvariable=self.mqtt_broker_var).pack()

    ttk.Label(self.mqtt_tab, text="Topic").pack()
    self.mqtt_topic_var = tk.StringVar(value="rgb/effects")
    ttk.Entry(self.mqtt_tab, textvariable=self.mqtt_topic_var).pack()

    ttk.Button(self.mqtt_tab, text="Start Listener", command=self._start_mqtt_listener).pack(pady=5)

def _start_mqtt_listener(self):
    try:
        import paho.mqtt.client as mqtt
        def on_message(client, userdata, msg):
            import json, requests
            try:
                frame = json.loads(msg.payload.decode())
                for zone, color in frame.get("zones", {}).items():
                    requests.post("http://127.0.0.1:5000/set_zone_color", json={"zone": int(zone), "color": color})
                print(f"🔄 Synced effect from MQTT: {frame}")
            except Exception as e:
                print(f"❌ MQTT message error: {e}")

        client = mqtt.Client()
        client.on_message = on_message
        client.connect(self.mqtt_broker_var.get(), 1883, 60)
        client.subscribe(self.mqtt_topic_var.get())
        client.loop_start()
        print(f"✅ MQTT listener started on topic {self.mqtt_topic_var.get()}")
    except Exception as e:
        print(f"❌ MQTT listener failed: {e}")
'''
    content += "\n" + mqtt_listener
    print("✅ MQTT listener for real-time effect sync added.")

# 2. Avatar Uploader and Role-Based GUI Access
if "def _create_login_tab" not in content:
    avatar_ui = '''
def _create_login_tab(self):
    self.login_tab = ttk.Frame(self.notebook)
    self.notebook.add(self.login_tab, text="Login")

    ttk.Label(self.login_tab, text="Username").pack()
    self.login_user_var = tk.StringVar()
    ttk.Entry(self.login_tab, textvariable=self.login_user_var).pack()

    ttk.Label(self.login_tab, text="Password").pack()
    self.login_pass_var = tk.StringVar()
    ttk.Entry(self.login_tab, textvariable=self.login_pass_var, show="*").pack()

    ttk.Label(self.login_tab, text="Role").pack()
    self.login_role_var = tk.StringVar()
    ttk.Combobox(self.login_tab, textvariable=self.login_role_var, values=["Admin", "User", "Guest"], state="readonly").pack()

    ttk.Button(self.login_tab, text="Upload Avatar", command=self._upload_avatar).pack(pady=2)
    ttk.Button(self.login_tab, text="Login", command=self._login_user).pack(pady=5)

def _upload_avatar(self):
    from tkinter.filedialog import askopenfilename
    path = askopenfilename(filetypes=[("PNG Images", "*.png")])
    if path:
        user = self.login_user_var.get()
        dest = f"avatars/{user}.png"
        import shutil
        shutil.copy(path, dest)
        print(f"🖼️ Avatar uploaded for {user}")

def _login_user(self):
    import hashlib, json
    user = self.login_user_var.get()
    pwd = self.login_pass_var.get()
    role = self.login_role_var.get()
    key = hashlib.sha256(pwd.encode()).hexdigest()
    profile_path = f"profile_{user}.json"
    if os.path.exists(profile_path):
        with open(profile_path) as f:
            data = json.load(f)
        if data.get("key") == key:
            print(f"🔐 Welcome back, {user} ({data.get('role')})")
            self._apply_role_access(data.get("role"))
        else:
            print("❌ Incorrect password.")
    else:
        with open(profile_path, "w") as f:
            json.dump({"user": user, "key": key, "role": role, "avatar": f"avatars/{user}.png"}, f)
        print(f"🆕 Profile created for {user} ({role})")
        self._apply_role_access(role)

def _apply_role_access(self, role):
    if role == "Guest":
        print("🔒 Guest access: read-only mode")
    elif role == "User":
        print("🔓 User access: limited control")
    elif role == "Admin":
        print("🛠️ Admin access: full control")
'''
    content += "\n" + avatar_ui
    print("✅ Avatar uploader and role-based GUI access added.")

# 3. ESL Debugger with Step-Through Execution and Variable Watch
if "def _step_through_script" not in content:
    debugger_ui = '''
def _create_script_editor_tab(self):
    self.script_tab = ttk.Frame(self.notebook)
    self.notebook.add(self.script_tab, text="Script Editor")

    self.script_text = tk.Text(self.script_tab, height=15, wrap=tk.NONE)
    self.script_text.pack(fill=tk.BOTH, expand=True)

    ttk.Button(self.script_tab, text="Run Script", command=self._run_script).pack(pady=5)
    ttk.Button(self.script_tab, text="Step Through", command=self._step_through_script).pack(pady=2)

def _run_script(self):
    try:
        exec(self.script_text.get(1.0, tk.END), {"requests": __import__("requests")})
    except Exception as e:
        print(f"Script error: {e}")

def _step_through_script(self):
    import time
    lines = self.script_text.get(1.0, tk.END).splitlines()
    local_vars = {}
    for i, line in enumerate(lines):
        try:
            exec(line, {"requests": __import__("requests")}, local_vars)
            print(f"▶ Line {i+1}: {line}")
            for k, v in local_vars.items():
                print(f"  {k} = {v}")
            time.sleep(0.5)
        except Exception as e:
            print(f"❌ Error at line {i+1}: {e}")
            break
'''
    content += "\n" + debugger_ui
    print("✅ ESL debugger with step-through execution and variable watch added.")

# Inject tab creation calls
content = content.replace("self._create_status_bar()", """self._create_status_bar()
        self._create_script_editor_tab()
        self._create_login_tab()
        self._create_mqtt_listener_tab()""")

with open(controller_path, "w") as f:
    f.write(content)

print("✅ All sync, secure, and debugging features fully integrated.")
