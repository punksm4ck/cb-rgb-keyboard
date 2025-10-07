controller_path = "gui/controller.py"
with open(controller_path, "r") as f:
    content = f.read()

if "_add_help_box" not in content:
    help_function = '''
def _add_help_box(self, parent, text):
    help_frame = ttk.LabelFrame(parent, text="🛈 Help", padding=10)
    help_frame.pack(fill=tk.X, pady=5)
    ttk.Label(help_frame, text=text, wraplength=580, justify=tk.LEFT).pack()
'''
    content += help_function

    help_texts = {
        "audio_layering_tab": "Preview how zones respond to layered audio input. Toggle real-time layering and simulate zone behavior.",
        "rgbpreset_export_tab": "Export your current effect stack as a .rgbpreset file. Useful for sharing or reloading later.",
        "band_mapping_tab": "Assign specific zones to bass, mid, and treble bands. Preview the mapping with live color feedback.",
        "waveform_render_tab": "Load a .wav file and visualize its waveform. Useful for voice samples or audio-reactive design.",
        "changelog_diff_tab": "Compare plugin changelogs between versions. Syntax highlighting shows added and removed lines.",
        "gif_export_tab": "Export your timeline as an animated GIF. Choose frame count and preview the result.",
        "mqtt_listener_tab": "Start an MQTT listener to sync effects from external sources. Incoming messages trigger zone updates.",
        "freq_band_tab": "Customize frequency bands for bass, mid, and treble. These ranges affect how audio maps to zones.",
        "visualizer_presets_tab": "Choose visualizer styles like bars, waves, or pulses. Preview how each preset looks.",
        "audio_composer_tab": "Enable audio-reactive layering in your effect composer. Combine shimmer, pulse, and wave with live input."
    }

    for tab, text in help_texts.items():
        insert_point = f"self.{tab}"
        if insert_point in content:
            content = content.replace(insert_point, insert_point + f"\n        self._add_help_box(self.{tab}, \"{text}\")")

    with open(controller_path, "w") as f:
        f.write(content)

    print("✅ Help sections added to all GUI tabs.")
else:
    print("⚠️ Help sections already present.")
