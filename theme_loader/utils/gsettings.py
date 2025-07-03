import subprocess

def set_gtk_theme(theme_name: str) -> bool:
    try:
        subprocess.run([
            "gsettings", "set", "org.gnome.desktop.interface", "gtk-theme", theme_name
        ], check=True)
        return True
    except Exception:
        return False

def set_shell_theme(theme_name: str) -> bool:
    try:
        subprocess.run([
            "gsettings", "set", "org.gnome.shell.extensions.user-theme", "name", theme_name
        ], check=True)
        return True
    except Exception:
        return False

def set_icon_theme(theme_name: str) -> bool:
    try:
        subprocess.run([
            "gsettings", "set", "org.gnome.desktop.interface", "icon-theme", theme_name
        ], check=True)
        return True
    except Exception:
        return False

def set_cursor_theme(theme_name: str) -> bool:
    try:
        subprocess.run([
            "gsettings", "set", "org.gnome.desktop.interface", "cursor-theme", theme_name
        ], check=True)
        return True
    except Exception:
        return False 