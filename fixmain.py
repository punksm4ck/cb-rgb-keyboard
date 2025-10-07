main_path = "__main__.py"

with open(main_path, "r") as f:
    lines = f.readlines()

patched = False
for i, line in enumerate(lines):
    if "success = start_flask_server()" in line:
        # Replace with correct call
        lines[i] = "        start_flask_server()\n"
        # Check next line for indentation fix
        if i + 1 < len(lines) and lines[i + 1].startswith("    controller.initialize_gui()"):
            lines[i + 1] = "        controller.initialize_gui()\n"
        patched = True
        break

if patched:
    with open(main_path, "w") as f:
        f.writelines(lines)
    print("✅ __main__.py patched successfully.")
else:
    print("⚠️ No patch applied. Pattern not found.")
