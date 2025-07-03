"""
Theme Manager module for GNOME Theme Loader
Handles theme installation, detection, and management
"""

import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, GLib
from pathlib import Path
import tempfile
import zipfile
import tarfile
import os
import shutil
from typing import Dict, List, Optional, Tuple

# Importar módulos locales
from ..utils.installer import install_archive
from ..utils.gsettings import set_gtk_theme, set_shell_theme, set_icon_theme, set_cursor_theme
from ..utils.grub import list_grub_themes, install_grub_theme, apply_grub_theme

class ThemeManager:
    """Gestor principal de temas"""
    
    def __init__(self):
        # Directorios de temas
        self.theme_dir = Path.home() / ".themes"
        self.icon_dir = Path.home() / ".icons"
        self.local_icon_dir = Path.home() / ".local/share/icons"
        self.system_theme_dir = Path("/usr/share/themes")
        self.system_icon_dir = Path("/usr/share/icons")
        
        # Asegurar que los directorios existan
        self.theme_dir.mkdir(exist_ok=True)
        self.icon_dir.mkdir(exist_ok=True)
        self.local_icon_dir.mkdir(parents=True, exist_ok=True)
    
    def install_theme_archive(self, archive_path: Path, callback=None) -> Tuple[bool, str]:
        """Instalar un archivo de tema comprimido"""
        try:
            # Detectar tipo de tema
            theme_type = self._detect_theme_type(archive_path)
            if not theme_type:
                return False, "No se pudo detectar el tipo de tema"
            
            # Instalar el tema
            result = install_archive(archive_path, callback)
            if result:
                if callback:
                    callback(f"Tema {theme_type} instalado correctamente", "success")
                return True, f"Tema {theme_type} instalado correctamente"
            else:
                if callback:
                    callback("Error al instalar el tema", "error")
                return False, "Error al instalar el tema"
                
        except Exception as e:
            error_msg = f"Error durante la instalación: {str(e)}"
            if callback:
                callback(error_msg, "error")
            return False, error_msg
    
    def _detect_theme_type(self, file_path: Path) -> Optional[str]:
        """Detectar el tipo de tema basado en el contenido del archivo"""
        try:
            # Crear directorio temporal
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                
                # Extraer archivo
                if file_path.suffix == '.zip':
                    with zipfile.ZipFile(file_path, 'r') as zip_ref:
                        zip_ref.extractall(temp_path)
                elif file_path.suffix in ['.gz', '.xz', '.bz2'] or '.tar.' in file_path.name:
                    with tarfile.open(file_path, 'r:*') as tar_ref:
                        tar_ref.extractall(temp_path)
                else:
                    return None
                
                # Buscar archivos indicativos
                extracted_items = list(temp_path.iterdir())
                if len(extracted_items) == 1 and extracted_items[0].is_dir():
                    # Un solo directorio, verificar su contenido
                    theme_dir = extracted_items[0]
                    
                    # Verificar GTK theme
                    if (theme_dir / "gtk-3.0").exists() or (theme_dir / "gtk-4.0").exists():
                        return "gtk"
                    
                    # Verificar Shell theme
                    if (theme_dir / "gnome-shell").exists():
                        return "shell"
                    
                    # Verificar Icon theme
                    if (theme_dir / "index.theme").exists() or (theme_dir / "scalable").exists():
                        return "icons"
                    
                    # Verificar Cursor theme
                    if (theme_dir / "cursors").exists():
                        return "cursor"
                    
                    # Verificar GRUB theme
                    if (theme_dir / "theme.txt").exists():
                        return "grub"
                
                # Verificar múltiples directorios
                for item in extracted_items:
                    if item.is_dir():
                        # Verificar GTK themes
                        if (item / "gtk-3.0").exists() or (item / "gtk-4.0").exists():
                            return "gtk"
                        
                        # Verificar Shell themes
                        if (item / "gnome-shell").exists():
                            return "shell"
                        
                        # Verificar Icon themes
                        if (item / "index.theme").exists() or (item / "scalable").exists():
                            return "icons"
                        
                        # Verificar Cursor themes
                        if (item / "cursors").exists():
                            return "cursor"
                        
                        # Verificar GRUB themes
                        if (item / "theme.txt").exists():
                            return "grub"
                
                return None
                
        except Exception as e:
            print(f"Error detectando tipo de tema: {e}")
            return None
    
    def scan_themes(self):
        """Escanear temas instalados y devolver un diccionario por categorías"""
        def list_dir(path):
            if not path.exists():
                return []
            return [f for f in path.iterdir() if f.is_dir() and not f.name.startswith('.')]

        themes = {
            "gtk": [],
            "icons": [],
            "shell": [],
            "cursor": [],
            "grub": []
        }

        # GTK themes
        for folder in list_dir(self.theme_dir):
            themes["gtk"].append({"name": folder.name, "type": "gtk", "path": str(folder)})

        # Icon themes
        for folder in list_dir(self.icon_dir):
            themes["icons"].append({"name": folder.name, "type": "icons", "path": str(folder)})
        for folder in list_dir(self.local_icon_dir):
            if not any(t["name"] == folder.name for t in themes["icons"]):
                themes["icons"].append({"name": folder.name, "type": "icons", "path": str(folder)})

        # Shell themes
        for folder in list_dir(self.theme_dir):
            if (folder / "gnome-shell").exists():
                themes["shell"].append({"name": folder.name, "type": "shell", "path": str(folder)})

        # Cursor themes
        for folder in list_dir(self.icon_dir):
            if (folder / "cursors").exists():
                themes["cursor"].append({"name": folder.name, "type": "cursor", "path": str(folder)})
        for folder in list_dir(self.local_icon_dir):
            if (folder / "cursors").exists() and not any(t["name"] == folder.name for t in themes["cursor"]):
                themes["cursor"].append({"name": folder.name, "type": "cursor", "path": str(folder)})

        # GRUB themes (opcional, si tienes soporte)
        # Puedes usar list_grub_themes() si ya tienes esa función

        return themes
    
    def apply_theme(self, theme_type: str, theme_name: str, callback=None) -> bool:
        """Aplicar un tema específico"""
        try:
            success = False
            
            if theme_type == "gtk":
                success = set_gtk_theme(theme_name)
            elif theme_type == "shell":
                success = set_shell_theme(theme_name)
            elif theme_type == "icons":
                success = set_icon_theme(theme_name)
            elif theme_type == "cursor":
                success = set_cursor_theme(theme_name)
            elif theme_type == "grub":
                success = apply_grub_theme(theme_name)
            
            if success:
                if callback:
                    callback(f"Tema {theme_name} aplicado correctamente", "success")
                return True
            else:
                if callback:
                    callback(f"Error al aplicar el tema {theme_name}", "error")
                return False
                
        except Exception as e:
            error_msg = f"Error al aplicar tema: {str(e)}"
            if callback:
                callback(error_msg, "error")
            return False
    
    def _is_valid_gtk_theme(self, theme_path: Path) -> bool:
        """Verificar si es un tema GTK válido"""
        return (theme_path / "gtk-3.0").exists() or (theme_path / "gtk-4.0").exists()
    
    def _is_valid_shell_theme(self, theme_path: Path) -> bool:
        """Verificar si es un tema Shell válido"""
        return (theme_path / "gnome-shell").exists()
    
    def _is_valid_icon_theme(self, icon_path: Path) -> bool:
        """Verificar si es un tema de iconos válido"""
        return (icon_path / "index.theme").exists()
    
    def _is_valid_cursor_theme(self, cursor_path: Path) -> bool:
        """Verificar si es un tema de cursor válido"""
        return (cursor_path / "cursors").exists() 