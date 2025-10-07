import os
from datetime import datetime

controller_path = "gui/controller.py"

with open(controller_path, "r") as f:
    content = f.read()

# 1. Export to Timestamped Filenames
if "def _export_logs" in content:
    content = content.replace(
        'with open("exported_logs.txt", "w") as f:',
        'filename = f"exported_logs_{datetime.now().strftime(\'%Y%m%d_%H%M%S\')}.txt"\n        with open(filename, "w") as f:'
    )
    content = content.replace(
        'print("Logs exported to exported_logs.txt")',
        'print(f"Logs exported to {filename}")'
    )

if "def _export_api_response" in content:
    content = content.replace(
        'with open("api_response.txt", "w") as f:',
        'filename = f"api_response_{datetime.now().strftime(\'%Y%m%d_%H%M%S\')}.txt"\n        with open(filename, "w") as f:'
    )
    content = content.replace(
        'print("API response exported to api_response.txt")',
        'print(f"API response exported to {filename}")'
    )
    print("✅ Timestamped export filenames added.")

# 2. Real-Time Log Tailing
if "def _load_logs" in content and "self.root.after(3000, self._tail_logs)" not in content:
    content = content.replace(
        "self._create_log_tab()",
        "self._create_log_tab()\n        self.root.after(3000, self._tail_logs)"
    )

    tail_method = '''
    def _tail_logs(self):
        try:
            from gui.core.constants import LOG_DIR, APP_NAME
            log_file = LOG_DIR / f"{APP_NAME.lower().replace(' ', '_')}.log"
            with open(log_file, "r") as f:
                lines = f.readlines()
            current = self.log_text.get(1.0, tk.END).splitlines()
            if lines[-10:] != current[-10:]:
                self.log_text.delete(1.0, tk.END)
                self.log_text.insert(tk.END, "".join(lines))
        except Exception as e:
            self.log_text.delete(1.0, tk.END)
            self.log_text.insert(tk.END, f"Log tailing error: {e}")
        self.root.after(3000, self._tail_logs)
    '''
    content += "\n" + tail_method
    print("✅ Real-time log tailing added.")

# 3. Tray Icon Click Actions
if "def _toggle_window_visibility" not in content:
    tray_click_patch = '''
        self.root.bind("<Unmap>", lambda e: self.root.withdraw())
        self.root.bind("<Map>", lambda e: self.root.deiconify())
        self.root.bind("<Button-3>", lambda e: self._toggle_window_visibility())
    '''
    content = content.replace("self._create_status_bar()", "self._create_status_bar()\n        " + tray_click_patch)

    toggle_method = '''
    def _toggle_window_visibility(self):
        if self.root.state() == "withdrawn":
            self.root.deiconify()
        else:
            self.root.withdraw()
    '''
    content += "\n" + toggle_method
    print("✅ Tray icon click actions added.")

with open(controller_path, "w") as f:
    f.write(content)
