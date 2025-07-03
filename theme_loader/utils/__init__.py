"""
Utils module for GNOME Theme Loader
Contiene utilidades para instalación, gsettings y GRUB
"""

from .installer import install_archive, detect_type, move_to_dest, list_installed_applications, list_all_theme_icons, assign_custom_icon_to_app
from .gsettings import set_gtk_theme, set_shell_theme, set_icon_theme, set_cursor_theme
from .grub import list_grub_themes, install_grub_theme, apply_grub_theme, remove_grub_theme

__all__ = [
    'install_archive', 'detect_type', 'move_to_dest',
    'set_gtk_theme', 'set_shell_theme', 'set_icon_theme', 'set_cursor_theme',
    'list_grub_themes', 'install_grub_theme', 'apply_grub_theme', 'remove_grub_theme',
    'list_installed_applications', 'list_all_theme_icons', 'assign_custom_icon_to_app'
] 