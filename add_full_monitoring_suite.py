import os

controller_path = "gui/controller.py"

with open(controller_path, "r") as f:
    content = f.read()

# 1. Add Log Viewer Tab
if "self.log_tab" not in content:
    content = content.replace(
        "self.notebook.add(self.api_tab, text=\"API Control\")",
        "self.notebook.add(self.api_tab, text=\"API Control\")\n        self.log_tab = ttk.Frame(self.notebook)\n        self.notebook.add(self.log_tab, text=\"Logs\")\n        self._create_log_tab()"
    )

    log_tab_method = '''
    def _create_log_tab(self):
        """Create log viewer tab"""
        frame = ttk.Frame(self.log_tab)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.log_text = tk.Text(frame, wrap=tk.NONE, height=20)
        self.log_text.pack(fill=tk.BOTH, expand=True)

        refresh_button = ttk.Button(frame, text="Refresh Logs", command=self._load_logs)
        refresh_button.pack(pady=5)

    def _load_logs(self):
        try:
            from gui.core.constants import LOG_DIR, APP_NAME
            log_file = LOG_DIR / f"{APP_NAME.lower().replace(' ', '_')}.log"
            with open(log_file, "r") as f:
                self.log_text.delete(1.0, tk.END)
                self.log_text.insert(tk.END, f.read())
        except Exception as e:
            self.log_text.delete(1.0, tk.END)
            self.log_text.insert(tk.END, f"Error loading logs: {e}")
    '''
    content += "\n" + log_tab_method
    print("✅ Log viewer tab added.")

# 2. Add GUI API Tester Tab
if "self.api_test_tab" not in content:
    content = content.replace(
        "self.notebook.add(self.log_tab, text=\"Logs\")",
        "self.notebook.add(self.log_tab, text=\"Logs\")\n        self.api_test_tab = ttk.Frame(self.notebook)\n        self.notebook.add(self.api_test_tab, text=\"API Tester\")\n        self._create_api_test_tab()"
    )

    api_test_method = '''
    def _create_api_test_tab(self):
        """Create API tester tab"""
        frame = ttk.Frame(self.api_test_tab)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        ttk.Label(frame, text="Endpoint:").pack(anchor=tk.W)
        self.api_endpoint_var = tk.StringVar(value="/status")
        ttk.Entry(frame, textvariable=self.api_endpoint_var, width=40).pack(anchor=tk.W, pady=5)

        ttk.Label(frame, text="Payload (JSON):").pack(anchor=tk.W)
        self.api_payload_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.api_payload_var, width=40).pack(anchor=tk.W, pady=5)

        send_button = ttk.Button(frame, text="Send Request", command=self._send_api_test)
        send_button.pack(pady=5)

        self.api_test_result = tk.Text(frame, height=10)
        self.api_test_result.pack(fill=tk.BOTH, expand=True)

    def _send_api_test(self):
        import requests
        endpoint = self.api_endpoint_var.get()
        payload = self.api_payload_var.get()
        try:
            url = f"http://127.0.0.1:5000{endpoint}"
            if payload:
                r = requests.post(url, json=eval(payload))
            else:
                r = requests.get(url)
            self.api_test_result.delete(1.0, tk.END)
            self.api_test_result.insert(tk.END, f"Status: {r.status_code}\\nResponse:\\n{r.text}")
        except Exception as e:
            self.api_test_result.delete(1.0, tk.END)
            self.api_test_result.insert(tk.END, f"Error: {e}")
    '''
    content += "\n" + api_test_method
    print("✅ GUI API tester tab added.")

# 3. Add System Tray Flask Status Indicator
if "self.tray_flask_status" not in content:
    tray_patch = '''
        self.tray_flask_status = tk.StringVar(value="API: Unknown")
        self.root.after(3000, self._update_flask_tray_status)
    '''
    content = content.replace("self._create_status_bar()", "self._create_status_bar()\n        " + tray_patch)

    tray_method = '''
    def _update_flask_tray_status(self):
        import requests
        try:
            r = requests.get("http://127.0.0.1:5000/status", timeout=1)
            if r.status_code == 200:
                self.tray_flask_status.set("API: ✓ Online")
            else:
                self.tray_flask_status.set("API: ⚠ Error")
        except:
            self.tray_flask_status.set("API: ✗ Offline")
        self.root.after(5000, self._update_flask_tray_status)
    '''
    content += "\n" + tray_method
    print("✅ System tray Flask status indicator added.")

with open(controller_path, "w") as f:
    f.write(content)
