
from flask import Flask, request, jsonify
app = Flask(__name__)

@app.route("/run_effect", methods=["POST"])
def run_effect():
    data = request.json
    effect = data.get("effect")
    # TODO: wire to controller
    return jsonify({"status": "triggered", "effect": effect})

@app.route("/status", methods=["GET"])
def status():
    return jsonify({"status": "running", "fps": 30})

if __name__ == "__main__":
    app.run(port=5050)


@app.route("/list_presets", methods=["GET"])
def list_presets():
    try:
        presets = []
        for fname in os.listdir("presets"):
            if fname.endswith(".rgbpreset"):
                with open(os.path.join("presets", fname)) as f:
                    data = json.load(f)
                    presets.append(data["name"])
        return jsonify({"presets": presets})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/run_plugin", methods=["POST"])
def run_plugin():
    plugin_name = request.json.get("plugin")
    from plugins.loader import load_plugins
    plugins = load_plugins()
    for plugin in plugins:
        if plugin["name"] == plugin_name:
            if "run" in plugin:
                plugin["run"](None)
                return jsonify({"status": "executed", "plugin": plugin_name})
    return jsonify({"error": "Plugin not found"}), 404


@app.route("/set_zone_color", methods=["POST"])
def set_zone_color():
    data = request.json
    zone = data.get("zone")
    color = data.get("color")
    try:
        from plugins.ectool_wrapper import set_zone_color
        set_zone_color(zone, color)
        return jsonify({"status": "ok", "zone": zone, "color": color})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    