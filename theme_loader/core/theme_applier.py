"""
Theme Applier module for GNOME Theme Loader
Handles theme application with feedback and error handling
"""

import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, GLib
from pathlib import Path
from typing import Callable, Optional
import subprocess
import os

# Importar módulos locales
from ..utils.gsettings import set_gtk_theme, set_shell_theme, set_icon_theme, set_cursor_theme
from ..utils.grub import apply_grub_theme

class ThemeApplier:
    """Aplicador de temas con manejo de errores y feedback"""
    
    def __init__(self, callback: Optional[Callable] = None):
        self.callback = callback
        self.current_themes = {
            "gtk": None,
            "shell": None,
            "icons": None,
            "cursor": None,
            "grub": None
        }
    
    def apply_theme(self, theme_type: str, theme_name: str, callback: Optional[Callable] = None) -> bool:
        """Aplicar un tema específico con feedback"""
        try:
            # Usar callback local si se proporciona, sino el global
            local_callback = callback or self.callback
            
            if local_callback:
                local_callback(f"Aplicando tema {theme_name}...", "info")
            
            success = False
            
            if theme_type == "gtk":
                success = self._apply_gtk_theme(theme_name, local_callback)
            elif theme_type == "shell":
                success = self._apply_shell_theme(theme_name, local_callback)
            elif theme_type == "icons":
                success = self._apply_icon_theme(theme_name, local_callback)
            elif theme_type == "cursor":
                success = self._apply_cursor_theme(theme_name, local_callback)
            elif theme_type == "grub":
                success = self._apply_grub_theme(theme_name, local_callback)
            else:
                if local_callback:
                    local_callback(f"Tipo de tema desconocido: {theme_type}", "error")
                return False
            
            if success:
                self.current_themes[theme_type] = theme_name
                if local_callback:
                    local_callback(f"Tema {theme_name} aplicado correctamente", "success")
                return True
            else:
                if local_callback:
                    local_callback(f"Error al aplicar el tema {theme_name}", "error")
                return False
                
        except Exception as e:
            error_msg = f"Error al aplicar tema: {str(e)}"
            if callback:
                callback(error_msg, "error")
            return False
    
    def apply_theme_combo(self, themes: dict, callback: Optional[Callable] = None) -> bool:
        """Aplicar múltiples temas a la vez"""
        try:
            local_callback = callback or self.callback
            
            if local_callback:
                local_callback("Aplicando combinación de temas...", "info")
            
            success_count = 0
            total_count = len(themes)
            
            for theme_type, theme_name in themes.items():
                if theme_name:
                    if self.apply_theme(theme_type, theme_name, local_callback):
                        success_count += 1
            
            if success_count == total_count:
                if local_callback:
                    local_callback(f"Todos los temas aplicados correctamente ({success_count}/{total_count})", "success")
                return True
            else:
                if local_callback:
                    local_callback(f"Algunos temas no se pudieron aplicar ({success_count}/{total_count})", "warning")
                return False
                
        except Exception as e:
            error_msg = f"Error al aplicar combinación de temas: {str(e)}"
            if callback:
                callback(error_msg, "error")
            return False
    
    def _apply_gtk_theme(self, theme_name: str, callback: Optional[Callable] = None) -> bool:
        """Aplicar tema GTK"""
        try:
            if callback:
                callback(f"Aplicando tema GTK: {theme_name}", "info")
            
            success = set_gtk_theme(theme_name)
            
            if success and callback:
                callback(f"Tema GTK {theme_name} aplicado", "success")
            
            return success
            
        except Exception as e:
            if callback:
                callback(f"Error aplicando tema GTK: {str(e)}", "error")
            return False
    
    def _apply_shell_theme(self, theme_name: str, callback: Optional[Callable] = None) -> bool:
        """Aplicar tema Shell"""
        try:
            if callback:
                callback(f"Aplicando tema Shell: {theme_name}", "info")
            
            success = set_shell_theme(theme_name)
            
            if success and callback:
                callback(f"Tema Shell {theme_name} aplicado", "success")
                callback("Reinicia GNOME Shell para ver los cambios (Alt+F2, r)", "info")
            
            return success
            
        except Exception as e:
            if callback:
                callback(f"Error aplicando tema Shell: {str(e)}", "error")
            return False
    
    def _apply_icon_theme(self, theme_name: str, callback: Optional[Callable] = None) -> bool:
        """Aplicar tema de iconos"""
        try:
            if callback:
                callback(f"Aplicando tema de iconos: {theme_name}", "info")
            
            success = set_icon_theme(theme_name)
            
            if success and callback:
                callback(f"Tema de iconos {theme_name} aplicado", "success")
            
            return success
            
        except Exception as e:
            if callback:
                callback(f"Error aplicando tema de iconos: {str(e)}", "error")
            return False
    
    def _apply_cursor_theme(self, theme_name: str, callback: Optional[Callable] = None) -> bool:
        """Aplicar tema de cursor"""
        try:
            if callback:
                callback(f"Aplicando tema de cursor: {theme_name}", "info")
            
            success = set_cursor_theme(theme_name)
            
            if success and callback:
                callback(f"Tema de cursor {theme_name} aplicado", "success")
            
            return success
            
        except Exception as e:
            if callback:
                callback(f"Error aplicando tema de cursor: {str(e)}", "error")
            return False
    
    def _apply_grub_theme(self, theme_name: str, callback: Optional[Callable] = None) -> bool:
        """Aplicar tema GRUB"""
        try:
            if callback:
                callback(f"Aplicando tema GRUB: {theme_name}", "info")
            
            success = apply_grub_theme(theme_name)
            
            if success and callback:
                callback(f"Tema GRUB {theme_name} aplicado", "success")
                callback("Los cambios se verán en el próximo reinicio", "info")
            
            return success
            
        except Exception as e:
            if callback:
                callback(f"Error aplicando tema GRUB: {str(e)}", "error")
            return False
    
    def get_current_themes(self) -> dict:
        """Obtener los temas actualmente aplicados"""
        return self.current_themes.copy()
    
    def reset_to_defaults(self, callback: Optional[Callable] = None) -> bool:
        """Restablecer a temas por defecto"""
        try:
            local_callback = callback or self.callback
            
            if local_callback:
                local_callback("Restableciendo a temas por defecto...", "info")
            
            # Temas por defecto comunes
            default_themes = {
                "gtk": "Adwaita",
                "shell": "default",
                "icons": "Adwaita",
                "cursor": "Adwaita"
            }
            
            success = self.apply_theme_combo(default_themes, local_callback)
            
            if success and local_callback:
                local_callback("Temas restablecidos a valores por defecto", "success")
            
            return success
            
        except Exception as e:
            error_msg = f"Error restableciendo temas: {str(e)}"
            if callback:
                callback(error_msg, "error")
            return False
    
    def refresh_gtk_cache(self, callback: Optional[Callable] = None) -> bool:
        """Refrescar caché de GTK"""
        try:
            local_callback = callback or self.callback
            
            if local_callback:
                local_callback("Refrescando caché de GTK...", "info")
            
            # Ejecutar gtk-update-icon-cache
            result = subprocess.run(
                ["gtk-update-icon-cache", "-f", "-t", str(Path.home() / ".icons")],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                if local_callback:
                    local_callback("Caché de GTK actualizado", "success")
                return True
            else:
                if local_callback:
                    local_callback(f"Error actualizando caché: {result.stderr}", "error")
                return False
                
        except Exception as e:
            if callback:
                callback(f"Error refrescando caché: {str(e)}", "error")
            return False 