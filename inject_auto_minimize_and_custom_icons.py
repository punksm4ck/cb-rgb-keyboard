import os

controller_path = "gui/controller.py"

with open(controller_path, "r") as f:
    content = f.read()

# 1. Auto-minimize only when launched from startup
if "auto_minimize_on_startup" not in content:
    startup_toggle = '''
        self.auto_minimize_var = tk.BooleanVar(value=self.settings.get("auto_minimize_on_startup", False))
        auto_minimize_check = ttk.Checkbutton(
            startup_frame,
            text="Auto-minimize on startup",
            variable=self.auto_minimize_var,
            command=self.on_startup_option_changed
        )
        auto_minimize_check.pack(side=tk.LEFT, padx=(20, 0))
    '''
    content = content.replace("# Startup options", "# Startup options\n" + startup_toggle)

    update_patch = '''
        self.settings.update({
            'restore_on_startup': self.restore_on_startup_var.get(),
            'minimize_to_tray': self.minimize_to_tray_var.get(),
            'api_autostart': self.api_autostart_var.get(),
            'auto_minimize_on_startup': self.auto_minimize_var.get()
        })
    '''
    content = content.replace("def on_startup_option_changed(self):", "def on_startup_option_changed(self):\n" + update_patch)

    minimize_logic = '''
        if self.settings.get("auto_minimize_on_startup", False) and "--startup" in sys.argv:
            self.root.withdraw()
    '''
    content = content.replace("self._create_status_bar()", "self._create_status_bar()\n        " + minimize_logic)
    print("✅ Auto-minimize only when launched from startup added.")

# 2. Replace all GUI icons with splash icon
if "rgb_controller_splash.png" not in content:
    splash_icon_patch = '''
        try:
            from PIL import Image, ImageTk
            splash_path = "assets/rgb_controller_splash.png"
            if os.path.exists(splash_path):
                splash_image = Image.open(splash_path).resize((16, 16))
                self.splash_icon = ImageTk.PhotoImage(splash_image)
                self.root.iconphoto(False, self.splash_icon)
        except Exception as e:
            print(f"Splash icon setup failed: {e}")
    '''
    content = content.replace("self._create_status_bar()", "self._create_status_bar()\n        " + splash_icon_patch)
    print("✅ GUI splash icon integration added.")

# 3. Use separate tray icon for notification area
if "rgb_controller_icon.png" not in content and "pystray.Icon" in content:
    content = content.replace(
        'image = Image.open("assets/icon.png").resize((16, 16))',
        'image = Image.open("assets/rgb_controller_icon.png").resize((16, 16))'
    )
    print("✅ Tray notification icon set to rgb_controller_icon.png.")

with open(controller_path, "w") as f:
    f.write(content)
