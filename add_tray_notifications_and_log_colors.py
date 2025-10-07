import os

controller_path = "gui/controller.py"

with open(controller_path, "r") as f:
    content = f.read()

# 1. Tray Notifications for Events
if "def _notify_tray" not in content:
    notify_method = '''
    def _notify_tray(self, title, message):
        try:
            from plyer import notification
            notification.notify(
                title=title,
                message=message,
                app_name="RGB Controller",
                timeout=5
            )
        except Exception as e:
            print(f"Tray notification failed: {e}")
    '''
    content += "\n" + notify_method
    content = content.replace("self._create_status_bar()", "self._create_status_bar()\n        self._notify_tray(\"RGB Controller\", \"Application started\")")
    print("✅ Tray notifications for events added.")

# 2. Severity Color-Coding in Logs
if "def _colorize_log_line" not in content:
    colorize_method = '''
    def _colorize_log_line(self, line):
        if " - INFO -" in line:
            return ("#00ccff", line)
        elif " - WARNING -" in line:
            return ("#ffaa00", line)
        elif " - ERROR -" in line:
            return ("#ff4444", line)
        elif " - CRITICAL -" in line:
            return ("#ff0000", line)
        else:
            return ("#cccccc", line)
    '''
    content += "\n" + colorize_method

    if "def _tail_logs" in content:
        content = content.replace(
            'self.log_text.insert(tk.END, "".join(lines[-100:]))',
            'self.log_text.delete(1.0, tk.END)\n            for line in lines[-100:]:\n                color, text = self._colorize_log_line(line)\n                self.log_text.insert(tk.END, text, color)\n                self.log_text.tag_config(color, foreground=color)'
        )
    print("✅ Severity color-coding in logs added.")

# 3. Toggle for Auto-Minimize on Startup
if "self.auto_minimize_var" not in content:
    toggle_ui = '''
        self.auto_minimize_var = tk.BooleanVar(value=self.settings.get("auto_minimize", False))
        auto_minimize_check = ttk.Checkbutton(
            startup_frame,
            text="Auto-minimize on startup",
            variable=self.auto_minimize_var,
            command=self.on_startup_option_changed
        )
        auto_minimize_check.pack(side=tk.LEFT, padx=(20, 0))
    '''
    content = content.replace("# Startup options", "# Startup options\n" + toggle_ui)

    update_patch = '''
        self.settings.update({
            'restore_on_startup': self.restore_on_startup_var.get(),
            'minimize_to_tray': self.minimize_to_tray_var.get(),
            'api_autostart': self.api_autostart_var.get(),
            'auto_minimize': self.auto_minimize_var.get()
        })
    '''
    content = content.replace("def on_startup_option_changed(self):", "def on_startup_option_changed(self):\n" + update_patch)

    # Apply minimize on startup
    content = content.replace("self._create_status_bar()", "self._create_status_bar()\n        if self.settings.get('auto_minimize', False): self.root.withdraw()")
    print("✅ Toggle for auto-minimize on startup added.")

with open(controller_path, "w") as f:
    f.write(content)
