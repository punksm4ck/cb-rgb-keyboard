import os

controller_path = "gui/controller.py"
os.makedirs("audio", exist_ok=True)

with open(controller_path, "r") as f:
    content = f.read()

if "def _create_audio_visualizer_tab" not in content:
    audio_visualizer_ui = '''
def _create_audio_visualizer_tab(self):
    self.audio_tab = ttk.Frame(self.notebook)
    self.notebook.add(self.audio_tab, text="Audio Visualizer")

    ttk.Label(self.audio_tab, text="Capture Source").pack()
    self.audio_source_var = tk.StringVar(value="default")
    ttk.Entry(self.audio_tab, textvariable=self.audio_source_var).pack()

    ttk.Button(self.audio_tab, text="Start Visualizer", command=self._start_audio_visualizer).pack(pady=5)
    self.audio_canvas = tk.Canvas(self.audio_tab, width=600, height=100, bg="black")
    self.audio_canvas.pack()

def _start_audio_visualizer(self):
    import sounddevice as sd
    import numpy as np
    import requests

    def audio_callback(indata, frames, time, status):
        if status:
            print(f"⚠️ Audio status: {status}")
        volume_norm = np.linalg.norm(indata) * 10
        freqs = np.abs(np.fft.rfft(indata[:, 0]))
        bands = {
            "wasd": np.mean(freqs[1:10]),
            "arrows": np.mean(freqs[10:40]),
            "function": np.mean(freqs[40:80])
        }
        colors = {
            "wasd": "#%02x00%02x" % (int(bands["wasd"] * 5) % 255, 255),
            "arrows": "#00%02x%02x" % (int(bands["arrows"] * 5) % 255, 255),
            "function": "#%02x%02x00" % (int(bands["function"] * 5) % 255, 255)
        }
        zone_map = {
            "wasd": [17, 18, 19, 20],
            "arrows": [21, 22, 23, 24],
            "function": [1, 2, 3, 4, 5]
        }
        for group, zones in zone_map.items():
            for z in zones:
                requests.post("http://127.0.0.1:5000/set_zone_color", json={"zone": z, "color": colors[group]})
        self.audio_canvas.delete("all")
        for i in range(100):
            height = int(freqs[i % len(freqs)] * 0.01)
            self.audio_canvas.create_line(i * 6, 50, i * 6, 50 - height, fill="lime")

    try:
        sd.InputStream(callback=audio_callback, channels=1, samplerate=44100, device=self.audio_source_var.get()).start()
        print("🎧 Audio visualizer started.")
    except Exception as e:
        print(f"❌ Audio visualizer error: {e}")
'''
    content += "\n" + audio_visualizer_ui
    content = content.replace("self._create_status_bar()", """self._create_status_bar()
        self._create_audio_visualizer_tab()""")

    with open(controller_path, "w") as f:
        f.write(content)

    print("✅ Real-time audio visualizer fully integrated into gui/controller.py")
else:
    print("⚠️ Audio visualizer already present in controller.py")
