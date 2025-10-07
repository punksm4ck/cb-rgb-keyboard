import os

controller_path = "gui/controller.py"
main_path = "__main__.py"

# 1. Inject GUI status indicator
with open(controller_path, "r") as f:
    content = f.read()

if "self.flask_status_label" not in content:
    # Add label to header
    header_patch = '''
        # Flask server status
        self.flask_status_label = ttk.Label(
            header_frame,
            text="API: Unknown",
            font=('Arial', 9)
        )
        self.flask_status_label.pack(side=tk.RIGHT, padx=(10, 0))
    '''
    content = content.replace("# Update hardware status", header_patch + "\n        # Update hardware status")

    # Add update method
    update_method = '''
    def _update_flask_status(self):
        import requests
        try:
            r = requests.get("http://127.0.0.1:5000/status", timeout=1)
            if r.status_code == 200:
                self.flask_status_label.config(text="API: ✓ Online")
            else:
                self.flask_status_label.config(text="API: ⚠ Error")
        except:
            self.flask_status_label.config(text="API: ✗ Offline")
    '''
    content += "\n" + update_method

    # Call it from update loop
    content = content.replace("# Update hardware status", "# Update hardware status\n                self._update_flask_status()")

    with open(controller_path, "w") as f:
        f.write(content)
    print("✅ GUI Flask status indicator added.")

# 2. Add toggle to settings tab
with open(controller_path, "r") as f:
    content = f.read()

if "self.api_autostart_var" not in content:
    toggle_code = '''
        self.api_autostart_var = tk.BooleanVar(value=self.settings.get('api_autostart', True))
        api_check = ttk.Checkbutton(
            startup_frame,
            text="Auto-start API server",
            variable=self.api_autostart_var,
            command=self.on_startup_option_changed
        )
        api_check.pack(side=tk.LEFT, padx=(20, 0))
    '''
    content = content.replace("# Startup options", "# Startup options\n" + toggle_code)

    # Update settings handler
    if "api_autostart" not in content:
        update_patch = '''
        self.settings.update({
            'restore_on_startup': self.restore_on_startup_var.get(),
            'minimize_to_tray': self.minimize_to_tray_var.get(),
            'api_autostart': self.api_autostart_var.get()
        })
        '''
        content = content.replace("def on_startup_option_changed(self):", "def on_startup_option_changed(self):\n" + update_patch)

    with open(controller_path, "w") as f:
        f.write(content)
    print("✅ Settings toggle for API auto-start added.")

# 3. Add retry logic to __main__.py
with open(main_path, "r") as f:
    lines = f.readlines()

patched = False
for i, line in enumerate(lines):
    if "start_flask_server()" in line:
        lines[i] = "        self._start_flask_with_retry()\n"
        patched = True

if "def _start_flask_with_retry" not in "".join(lines):
    retry_block = '''
    def _start_flask_with_retry(self, max_attempts=3):
        import subprocess, time
        if not self.settings.get("api_autostart", True):
            self.logger.info("API auto-start disabled.")
            return
        for attempt in range(1, max_attempts + 1):
            try:
                subprocess.Popen(["flask", "--app", "api/server.py", "run"])
                self.logger.info(f"Flask server started on attempt {attempt}")
                return
            except Exception as e:
                self.logger.warning(f"Flask start failed (attempt {attempt}): {e}")
                time.sleep(2)
        self.logger.error("Flask server failed to start after retries.")
    '''
    # Insert before run_gui_mode
    for i, line in enumerate(lines):
        if "def run_gui_mode" in line:
            lines.insert(i, retry_block + "\n")
            break

if patched:
    with open(main_path, "w") as f:
        f.writelines(lines)
    print("✅ Retry logic and toggle-aware Flask launcher added to __main__.py.")
else:
    print("⚠️ No patch applied to __main__.py. Pattern not found.")
