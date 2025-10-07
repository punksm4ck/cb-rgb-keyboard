
def register_effect():
    return {
        "name": "PluginPulse",
        "type": "pulse",
        "color": "#FF00FF",
        "steps": 8,
        "delay": 80
    }

def run(controller):
    # Custom plugin logic
    controller.hardware.clear_all(0xFF00FF)
