import tempfile, tarfile, zipfile, shutil
from pathlib import Path
from .gsettings import set_gtk_theme, set_shell_theme, set_icon_theme, set_cursor_theme

THEME_DIR = Path.home() / ".themes"
ICON_DIR  = Path.home() / ".icons"

def install_archive(path: Path, msg_callback):
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        # descomprime
        if path.suffix == ".zip":
            with zipfile.ZipFile(path) as zf:
                zf.extractall(tmp)
        elif path.suffix in {".gz", ".xz", ".tar"} or path.suffixes[-2:] == [".tar", ".xz"]:
            with tarfile.open(path) as tf:
                tf.extractall(tmp)
        else:
            msg_callback(f"Formato no soportado: {path.name}", "error")
            return
        # detecta carpetas de tema
        for candidate in tmp.iterdir():
            if not candidate.is_dir():
                continue
            kind = detect_type(candidate)
            if not kind:
                continue
            move_to_dest(candidate, kind, msg_callback)
            # Aplicar el tema automáticamente
            if kind == "gtk":
                ok = set_gtk_theme(candidate.name)
                msg_callback(f"GTK aplicado: {candidate.name}" if ok else f"Error al aplicar GTK: {candidate.name}", "info" if ok else "error")
            elif kind == "shell":
                ok = set_shell_theme(candidate.name)
                msg_callback(f"Shell aplicado: {candidate.name}" if ok else f"Error al aplicar Shell: {candidate.name}", "info" if ok else "error")
            elif kind == "icons":
                ok = set_icon_theme(candidate.name)
                msg_callback(f"Iconos aplicados: {candidate.name}" if ok else f"Error al aplicar iconos: {candidate.name}", "info" if ok else "error")
            elif kind == "cursor":
                ok = set_cursor_theme(candidate.name)
                msg_callback(f"Cursor aplicado: {candidate.name}" if ok else f"Error al aplicar cursor: {candidate.name}", "info" if ok else "error")

def detect_type(folder: Path) -> str | None:
    if (folder / "gtk-4.0").exists():
        return "gtk"
    if (folder / "gnome-shell").exists():
        return "shell"
    if (folder / "cursors").exists():
        return "cursor"
    if (folder / "index.theme").exists():
        return "icons"
    return None

def move_to_dest(folder: Path, kind: str, msg_callback):
    dest_base = THEME_DIR if kind in {"gtk", "shell"} else ICON_DIR
    dest_base.mkdir(exist_ok=True)
    dest = dest_base / folder.name
    if dest.exists():
        shutil.rmtree(dest)
    shutil.move(str(folder), dest)
    msg_callback(f"✅ {folder.name} instalado en {dest_base}", "success")

def list_installed_applications():
    """Listar aplicaciones instaladas (archivos .desktop) en el sistema."""
    import configparser
    desktop_dirs = [
        Path.home() / ".local/share/applications",
        Path("/usr/share/applications")
    ]
    apps = []
    seen = set()
    for ddir in desktop_dirs:
        if not ddir.exists():
            continue
        for entry in ddir.glob("*.desktop"):
            if entry.name in seen:
                continue
            seen.add(entry.name)
            config = configparser.ConfigParser(interpolation=None)
            try:
                config.read(entry, encoding="utf-8")
                if "Desktop Entry" not in config:
                    continue
                section = config["Desktop Entry"]
                if section.get("NoDisplay", "false").lower() == "true":
                    continue
                name = section.get("Name")
                icon = section.get("Icon")
                exec_cmd = section.get("Exec")
                if name and icon:
                    apps.append({
                        "name": name,
                        "icon": icon,
                        "exec": exec_cmd,
                        "desktop_file": str(entry)
                    })
            except Exception:
                continue
    return apps

def list_all_theme_icons():
    """Listar todos los iconos de todos los temas agrupados por nombre de tema."""
    icon_dirs = [
        Path.home() / ".icons",
        Path.home() / ".local/share/icons",
        Path("/usr/share/icons")
    ]
    themes = {}
    for base in icon_dirs:
        if not base.exists():
            continue
        for theme_dir in base.iterdir():
            if not theme_dir.is_dir() or not (theme_dir / "index.theme").exists():
                continue
            theme_name = theme_dir.name
            icons = set()
            # Buscar en subdirectorios típicos
            for subdir in ["apps", "actions", "places", "devices", "categories", "mimetypes", "status"]:
                subpath = theme_dir / subdir
                if not subpath.exists():
                    continue
                for icon_file in subpath.rglob("*.svg"):
                    icons.add(str(icon_file))
                for icon_file in subpath.rglob("*.png"):
                    icons.add(str(icon_file))
            if icons:
                if theme_name not in themes:
                    themes[theme_name] = set()
                themes[theme_name].update(icons)
    # Convertir sets a listas
    return {k: sorted(list(v)) for k, v in themes.items()}

def assign_custom_icon_to_app(desktop_file_path, icon_name):
    """Crea un override en ~/.local/share/applications/ para el .desktop dado, cambiando solo la línea Icon= de forma segura."""
    from pathlib import Path
    import os
    src = Path(desktop_file_path)
    if not src.exists():
        return False, "Archivo .desktop no encontrado"
    dest_dir = Path.home() / ".local/share/applications"
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / src.name
    try:
        # Leer el archivo original
        with open(src, "r", encoding="utf-8") as f:
            lines = f.readlines()
        # Buscar sección [Desktop Entry]
        in_entry = False
        found_icon = False
        new_lines = []
        for line in lines:
            if line.strip().startswith("[Desktop Entry]"):
                in_entry = True
                new_lines.append(line)
                continue
            if in_entry and line.strip().startswith("Icon="):
                new_lines.append(f"Icon={icon_name}\n")
                found_icon = True
            else:
                new_lines.append(line)
            # Si termina la sección, salir
            if in_entry and line.strip().startswith("[") and not line.strip().startswith("[Desktop Entry]"):
                in_entry = False
        # Si no había Icon=, agregarlo al final de la sección
        if not found_icon:
            # Buscar el final de la sección [Desktop Entry]
            idx = None
            for i, line in enumerate(new_lines):
                if line.strip().startswith("[Desktop Entry]"):
                    idx = i
                elif idx is not None and line.strip().startswith("[") and not line.strip().startswith("[Desktop Entry]"):
                    idx = i
                    break
            if idx is not None:
                # Insertar después de [Desktop Entry]
                insert_at = idx + 1
                while insert_at < len(new_lines) and new_lines[insert_at].strip().startswith("#"):
                    insert_at += 1
                new_lines.insert(insert_at, f"Icon={icon_name}\n")
            else:
                # Si no hay sección, agregar al final
                new_lines.append(f"Icon={icon_name}\n")
        # Escribir el override local
        with open(dest, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
        # No cambiar permisos
        return True, f"Icono asignado correctamente a {dest.name} (solo override local)"
    except Exception as e:
        return False, f"Error al asignar icono: {e}" 