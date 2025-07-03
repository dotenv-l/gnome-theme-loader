"""
Theme Scanner module for GNOME Theme Loader
Handles theme validation and scanning
"""

from pathlib import Path
from typing import Dict, List, Optional
import configparser

class ThemeScanner:
    """Escáner de temas para validación y detección"""
    
    def __init__(self):
        self.theme_dirs = [
            Path.home() / ".themes",
            Path("/usr/share/themes")
        ]
        self.icon_dirs = [
            Path.home() / ".icons",
            Path.home() / ".local/share/icons",
            Path("/usr/share/icons")
        ]
    
    def scan_gtk_themes(self) -> List[Dict]:
        """Escanear temas GTK"""
        themes = []
        for theme_dir in self.theme_dirs:
            if theme_dir.exists():
                for theme_path in theme_dir.iterdir():
                    if theme_path.is_dir() and self._is_valid_gtk_theme(theme_path):
                        themes.append({
                            "name": theme_path.name,
                            "path": theme_path,
                            "type": "gtk",
                            "source": "user" if theme_dir == Path.home() / ".themes" else "system"
                        })
        return themes
    
    def scan_shell_themes(self) -> List[Dict]:
        """Escanear temas Shell"""
        themes = []
        for theme_dir in self.theme_dirs:
            if theme_dir.exists():
                for theme_path in theme_dir.iterdir():
                    if theme_path.is_dir() and self._is_valid_shell_theme(theme_path):
                        themes.append({
                            "name": theme_path.name,
                            "path": theme_path,
                            "type": "shell",
                            "source": "user" if theme_dir == Path.home() / ".themes" else "system"
                        })
        return themes
    
    def scan_icon_themes(self) -> List[Dict]:
        """Escanear temas de iconos"""
        themes = []
        for icon_dir in self.icon_dirs:
            if icon_dir.exists():
                for icon_path in icon_dir.iterdir():
                    if icon_path.is_dir() and self._is_valid_icon_theme(icon_path):
                        themes.append({
                            "name": icon_path.name,
                            "path": icon_path,
                            "type": "icons",
                            "source": "user" if icon_dir.parent.name == "home" else "system"
                        })
        return themes
    
    def scan_cursor_themes(self) -> List[Dict]:
        """Escanear temas de cursor"""
        themes = []
        for icon_dir in self.icon_dirs:
            if icon_dir.exists():
                for cursor_path in icon_dir.iterdir():
                    if cursor_path.is_dir() and self._is_valid_cursor_theme(cursor_path):
                        themes.append({
                            "name": cursor_path.name,
                            "path": cursor_path,
                            "type": "cursor",
                            "source": "user" if icon_dir.parent.name == "home" else "system"
                        })
        return themes
    
    def scan_all_themes(self) -> Dict[str, List[Dict]]:
        """Escanear todos los tipos de temas"""
        return {
            "gtk": self.scan_gtk_themes(),
            "shell": self.scan_shell_themes(),
            "icons": self.scan_icon_themes(),
            "cursor": self.scan_cursor_themes()
        }
    
    def _is_valid_gtk_theme(self, theme_path: Path) -> bool:
        """Verificar si es un tema GTK válido"""
        gtk3_dir = theme_path / "gtk-3.0"
        gtk4_dir = theme_path / "gtk-4.0"
        
        # Verificar que existe al menos una versión de GTK
        if not (gtk3_dir.exists() or gtk4_dir.exists()):
            return False
        
        # Verificar archivos de configuración
        if gtk3_dir.exists():
            gtk3_css = gtk3_dir / "gtk.css"
            gtk3_dark_css = gtk3_dir / "gtk-dark.css"
            if not (gtk3_css.exists() or gtk3_dark_css.exists()):
                return False
        
        if gtk4_dir.exists():
            gtk4_css = gtk4_dir / "gtk.css"
            gtk4_dark_css = gtk4_dir / "gtk-dark.css"
            if not (gtk4_css.exists() or gtk4_dark_css.exists()):
                return False
        
        return True
    
    def _is_valid_shell_theme(self, theme_path: Path) -> bool:
        """Verificar si es un tema Shell válido"""
        shell_dir = theme_path / "gnome-shell"
        if not shell_dir.exists():
            return False
        
        # Verificar archivos principales
        shell_css = shell_dir / "gnome-shell.css"
        if not shell_css.exists():
            return False
        
        return True
    
    def _is_valid_icon_theme(self, icon_path: Path) -> bool:
        """Verificar si es un tema de iconos válido"""
        index_file = icon_path / "index.theme"
        if not index_file.exists():
            return False
        
        # Verificar que el archivo index.theme es válido
        try:
            config = configparser.ConfigParser()
            config.read(index_file)
            
            # Verificar sección [Icon Theme]
            if "Icon Theme" not in config:
                return False
            
            # Verificar que tiene al menos un directorio de iconos
            if "Directories" not in config["Icon Theme"]:
                return False
            
            return True
        except Exception:
            return False
    
    def _is_valid_cursor_theme(self, cursor_path: Path) -> bool:
        """Verificar si es un tema de cursor válido"""
        cursors_dir = cursor_path / "cursors"
        if not cursors_dir.exists():
            return False
        
        # Verificar que tiene al menos algunos archivos de cursor
        cursor_files = list(cursors_dir.glob("*.png")) + list(cursors_dir.glob("*.svg"))
        if len(cursor_files) == 0:
            return False
        
        return True
    
    def get_theme_info(self, theme_path: Path, theme_type: str) -> Optional[Dict]:
        """Obtener información detallada de un tema"""
        try:
            info = {
                "name": theme_path.name,
                "path": theme_path,
                "type": theme_type,
                "size": self._get_directory_size(theme_path),
                "files_count": self._count_files(theme_path)
            }
            
            # Información específica según el tipo
            if theme_type == "gtk":
                info.update(self._get_gtk_theme_info(theme_path))
            elif theme_type == "shell":
                info.update(self._get_shell_theme_info(theme_path))
            elif theme_type == "icons":
                info.update(self._get_icon_theme_info(theme_path))
            elif theme_type == "cursor":
                info.update(self._get_cursor_theme_info(theme_path))
            
            return info
        except Exception as e:
            print(f"Error obteniendo información del tema: {e}")
            return None
    
    def _get_directory_size(self, path: Path) -> int:
        """Obtener tamaño total de un directorio"""
        total_size = 0
        try:
            for file_path in path.rglob("*"):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
        except Exception:
            pass
        return total_size
    
    def _count_files(self, path: Path) -> int:
        """Contar archivos en un directorio"""
        try:
            return len([f for f in path.rglob("*") if f.is_file()])
        except Exception:
            return 0
    
    def _get_gtk_theme_info(self, theme_path: Path) -> Dict:
        """Obtener información específica de tema GTK"""
        info = {"gtk_versions": []}
        
        if (theme_path / "gtk-3.0").exists():
            info["gtk_versions"].append("3.0")
        if (theme_path / "gtk-4.0").exists():
            info["gtk_versions"].append("4.0")
        
        return info
    
    def _get_shell_theme_info(self, theme_path: Path) -> Dict:
        """Obtener información específica de tema Shell"""
        shell_dir = theme_path / "gnome-shell"
        info = {"has_dark_variant": False}
        
        if shell_dir.exists():
            info["has_dark_variant"] = (shell_dir / "gnome-shell-dark.css").exists()
        
        return info
    
    def _get_icon_theme_info(self, icon_path: Path) -> Dict:
        """Obtener información específica de tema de iconos"""
        info = {"directories": []}
        
        try:
            index_file = icon_path / "index.theme"
            if index_file.exists():
                config = configparser.ConfigParser()
                config.read(index_file)
                
                if "Icon Theme" in config and "Directories" in config["Icon Theme"]:
                    dirs = config["Icon Theme"]["Directories"].split(",")
                    info["directories"] = [d.strip() for d in dirs]
        except Exception:
            pass
        
        return info
    
    def _get_cursor_theme_info(self, cursor_path: Path) -> Dict:
        """Obtener información específica de tema de cursor"""
        cursors_dir = cursor_path / "cursors"
        info = {"cursor_count": 0}
        
        if cursors_dir.exists():
            try:
                cursor_files = list(cursors_dir.glob("*.png")) + list(cursors_dir.glob("*.svg"))
                info["cursor_count"] = len(cursor_files)
            except Exception:
                pass
        
        return info 