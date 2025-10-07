import os

controller_path = "gui/controller.py"

with open(controller_path, "r") as f:
    content = f.read()

# 1. Minimize-to-tray on close
if "def _on_close" not in content:
    close_hook = '''
    def _on_close(self):
        """Minimize to tray instead of closing"""
        self.root.withdraw()
    '''
    content += "\n" + close_hook
    content = content.replace("self._create_status_bar()", "self._create_status_bar()\n        self.root.protocol(\"WM_DELETE_WINDOW\", self._on_close)")
    print("✅ Minimize-to-tray on close added.")

# 2. Tray menu with quick actions
if "def _create_tray_menu" not in content:
    tray_menu_code = '''
    def _create_tray_menu(self):
        try:
            import pystray
            from PIL import Image

            def show_window(icon, item):
                self.root.deiconify()

            def hide_window(icon, item):
                self.root.withdraw()

            def exit_app(icon, item):
                icon.stop()
                self.root.quit()

            image = Image.open("assets/icon.png").resize((16, 16))
            menu = pystray.Menu(
                pystray.MenuItem("Show", show_window),
                pystray.MenuItem("Hide", hide_window),
                pystray.MenuItem("Exit", exit_app)
            )
            self.tray_icon = pystray.Icon("RGBController", image, "RGB Controller", menu)
            self.tray_icon.run_detached()
        except Exception as e:
            print(f"Tray menu setup failed: {e}")
    '''
    content += "\n" + tray_menu_code
    content = content.replace("self._create_status_bar()", "self._create_status_bar()\n        self._create_tray_menu()")
    print("✅ Tray menu with quick actions added.")

# 3. Log tailing filters and severity toggles
if "self.log_severity_var" not in content:
    filter_ui = '''
        ttk.Label(frame, text="Severity Filter:").pack(anchor=tk.W)
        self.log_severity_var = tk.StringVar(value="ALL")
        severity_combo = ttk.Combobox(frame, textvariable=self.log_severity_var, values=["ALL", "INFO", "WARNING", "ERROR", "CRITICAL"], state="readonly")
        severity_combo.pack(anchor=tk.W, pady=5)
        severity_combo.bind("<<ComboboxSelected>>", lambda e: self._tail_logs())
    '''
    content = content.replace("search_button.pack(pady=5)", "search_button.pack(pady=5)\n        " + filter_ui)

    tail_patch = '''
    def _tail_logs(self):
        try:
            from gui.core.constants import LOG_DIR, APP_NAME
            log_file = LOG_DIR / f"{APP_NAME.lower().replace(' ', '_')}.log"
            with open(log_file, "r") as f:
                lines = f.readlines()
            severity = self.log_severity_var.get()
            if severity != "ALL":
                lines = [line for line in lines if f" - {severity} -" in line]
            self.log_text.delete(1.0, tk.END)
            self.log_text.insert(tk.END, "".join(lines[-100:]))
        except Exception as e:
            self.log_text.delete(1.0, tk.END)
            self.log_text.insert(tk.END, f"Log tailing error: {e}")
        self.root.after(3000, self._tail_logs)
    '''
    content += "\n" + tail_patch
    print("✅ Log tailing filters and severity toggles added.")

with open(controller_path, "w") as f:
    f.write(content)
