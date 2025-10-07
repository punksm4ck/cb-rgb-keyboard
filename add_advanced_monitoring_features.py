import os

controller_path = "gui/controller.py"

with open(controller_path, "r") as f:
    content = f.read()

# 1. Tray Icon Integration
if "self.tray_icon" not in content:
    tray_setup = '''
        # System tray icon setup
        try:
            from PIL import Image, ImageTk
            icon_path = "assets/icon.png"
            if os.path.exists(icon_path):
                tray_image = Image.open(icon_path).resize((16, 16))
                self.tray_icon = ImageTk.PhotoImage(tray_image)
                self.root.iconphoto(False, self.tray_icon)
        except Exception as e:
            print(f"Tray icon setup failed: {e}")
    '''
    content = content.replace("self._create_status_bar()", "self._create_status_bar()\n        " + tray_setup)
    print("✅ Tray icon integration added.")

# 2. Log Filtering and Search
if "self.log_search_var" not in content:
    log_search_patch = '''
        ttk.Label(frame, text="Search Logs:").pack(anchor=tk.W)
        self.log_search_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.log_search_var, width=30).pack(anchor=tk.W, pady=5)
        search_button = ttk.Button(frame, text="Search", command=self._search_logs)
        search_button.pack(pady=5)
    '''
    content = content.replace("refresh_button.pack(pady=5)", "refresh_button.pack(pady=5)\n        " + log_search_patch)

    search_method = '''
    def _search_logs(self):
        query = self.log_search_var.get().lower()
        content = self.log_text.get(1.0, tk.END)
        lines = content.splitlines()
        matches = [line for line in lines if query in line.lower()]
        self.log_text.delete(1.0, tk.END)
        self.log_text.insert(tk.END, "\\n".join(matches) if matches else "No matches found.")
    '''
    content += "\n" + search_method
    print("✅ Log filtering and search added.")

# 3. Auto-refresh for API Tester
if "self.api_auto_refresh_var" not in content:
    auto_refresh_patch = '''
        self.api_auto_refresh_var = tk.BooleanVar(value=False)
        auto_refresh_check = ttk.Checkbutton(frame, text="Auto-refresh", variable=self.api_auto_refresh_var)
        auto_refresh_check.pack(anchor=tk.W, pady=5)
        self.root.after(5000, self._auto_refresh_api_test)
    '''
    content = content.replace("send_button.pack(pady=5)", "send_button.pack(pady=5)\n        " + auto_refresh_patch)

    auto_refresh_method = '''
    def _auto_refresh_api_test(self):
        if self.api_auto_refresh_var.get():
            self._send_api_test()
        self.root.after(5000, self._auto_refresh_api_test)
    '''
    content += "\n" + auto_refresh_method
    print("✅ Auto-refresh for API tester added.")

# 4. Export Logs and API Responses
if "Export Logs" not in content:
    export_buttons = '''
        export_log_button = ttk.Button(frame, text="Export Logs", command=self._export_logs)
        export_log_button.pack(pady=5)

        export_api_button = ttk.Button(self.api_test_tab, text="Export API Response", command=self._export_api_response)
        export_api_button.pack(pady=5)
    '''
    content = content.replace("search_button.pack(pady=5)", "search_button.pack(pady=5)\n        " + export_buttons)

    export_methods = '''
    def _export_logs(self):
        try:
            log_data = self.log_text.get(1.0, tk.END)
            with open("exported_logs.txt", "w") as f:
                f.write(log_data)
            print("Logs exported to exported_logs.txt")
        except Exception as e:
            print(f"Export failed: {e}")

    def _export_api_response(self):
        try:
            response = self.api_test_result.get(1.0, tk.END)
            with open("api_response.txt", "w") as f:
                f.write(response)
            print("API response exported to api_response.txt")
        except Exception as e:
            print(f"Export failed: {e}")
    '''
    content += "\n" + export_methods
    print("✅ Export functionality added.")

with open(controller_path, "w") as f:
    f.write(content)
