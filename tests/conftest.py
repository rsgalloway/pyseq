import os
import shutil
import sysconfig


def get_installed_command(name):
    """Return the installed console script path for the active interpreter."""
    scripts_dir = sysconfig.get_path("scripts")
    candidates = [name]

    if os.name == "nt":
        candidates = [f"{name}.exe", f"{name}.cmd", f"{name}.bat", name]

    for candidate in candidates:
        path = os.path.join(scripts_dir, candidate)
        if os.path.exists(path):
            return path

    path = shutil.which(name)
    if path:
        return path

    raise FileNotFoundError(f"Could not find installed console script: {name}")
